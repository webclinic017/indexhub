import json
import logging
import os
from datetime import datetime
from typing import Mapping

import modal
import pandas as pd
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.integration import Integration
from indexhub.api.services.io import STORAGE_TAG_TO_WRITER
from indexhub.flows.forecast import FREQ_TO_DURATION


def _logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Prevent the modal client from double-logging.
    return logger


logger = _logger(name=__name__)

IMAGE = modal.Image.from_name("indexhub-image")

if os.environ.get("ENV_NAME", "dev") == "prod":
    stub = modal.Stub(
        "indexhub-integrations",
        image=IMAGE,
        secrets=[
            modal.Secret.from_name("aws-credentials"),
            modal.Secret.from_name("postgres-credentials"),
            modal.Secret.from_name("env-name"),
        ],
    )
else:
    stub = modal.Stub(
        "dev-indexhub-integrations",
        image=IMAGE,
        secrets=[
            modal.Secret.from_name("aws-credentials"),
            modal.Secret.from_name("dev-postgres-credentials"),
            modal.Secret.from_name("dev-env-name"),
        ],
    )


def _update_integration(
    integration_id: int,
    updated_at: datetime,
    outputs: Mapping[str, str],
    status: str,
    msg: str,
) -> Integration:
    # Establish connection
    engine = create_sql_engine()
    with Session(engine) as session:
        # Select rows with specific report_id only
        query = select(Integration).where(Integration.id == integration_id)
        integration = session.exec(query).one()
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        # Update the fields based on the integration_id
        integration.updated_at = updated_at
        integration.outputs = json.dumps(outputs)
        integration.status = status
        integration.msg = msg
        # Add, commit and refresh the updated object
        session.add(integration)
        session.commit()
        session.refresh(integration)
        return integration


@stub.function()
def run_integration_etl(
    integration_id: int,
    ticker: str,
    provider: str,
):
    """Load integration dataset then export to feature store."""
    try:
        status, msg = "SUCCESS", "OK"

        # Call tsdata integration etl flow
        flow = modal.Function.lookup("tsdata-integrations-etl", "integration_etl")

        raw_panel = flow.call(ticker=ticker, provider=provider)

        # Write data to data lake storage
        write = STORAGE_TAG_TO_WRITER["s3"]
        outputs = {
            "object_path": f"{provider}/{ticker.lower()}",
            "bucket_name": "indexhub-feature-store",
            "file_ext": "parquet",
        }
        output_path = f"{outputs['object_path']}.{outputs['file_ext']}"
        write(
            raw_panel,
            bucket_name=outputs["bucket_name"],
            object_path=output_path,
        )
    except Exception as exc:
        status = "FAILED"
        outputs = None
        msg = repr(exc)
        logger.exception(exc)
    finally:
        # Update state in database
        _update_integration(
            integration_id=integration_id,
            updated_at=datetime.utcnow(),
            outputs=outputs,
            status=status,
            msg=msg,
        )


@stub.function(
    memory=5120,
    cpu=4.0,
    timeout=900,
    schedule=modal.Cron("0 17 * * *"),  # run at 1am daily (utc 5pm)
)
def flow():
    # 1. Get all integrations
    engine = create_sql_engine()
    with Session(engine) as session:
        query = select(Integration)
        integrations = session.exec(query).all()
        if not integrations:
            raise HTTPException(status_code=404, detail="Integration not found")

    futures = []
    for integration in integrations:
        logger.info(f"Checking integration: {integration.id}")
        fields = json.loads(integration.fields)

        # 2. Check freq from integration for schedule
        duration = FREQ_TO_DURATION[fields["freq"]]
        updated_at = integration.updated_at.replace(microsecond=0)
        if duration == "1mo":
            new_dt = updated_at + relativedelta(months=1)
            run_dt = datetime(new_dt.year, new_dt.month, 1)
        elif duration == "3mo":
            new_dt = updated_at + relativedelta(months=3)
            run_dt = datetime(new_dt.year, new_dt.month, 1)
        else:
            run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
        logger.info(f"Next run for {integration.id} at: {run_dt}")
        # 4. Run preprocess flow
        current_datetime = datetime.now().replace(microsecond=0)
        if (current_datetime >= run_dt) or integration.status == "FAILED":
            # Spawn preprocess and embs flow for source
            futures.append(
                run_integration_etl.spawn(
                    integration_id=integration.id,
                    ticker=integration.ticker,
                    provider=integration.provider,
                )
            )

    for future in futures:
        future.get()


@stub.local_entrypoint()
def test():
    flow.call()
