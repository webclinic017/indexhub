import json
import logging
from datetime import datetime
from typing import Any, List, Mapping, Union

import modal
import pandas as pd
import polars as pl
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.source import Source
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.deployment import IMAGE
from indexhub.flows.forecast import FREQ_TO_DURATION, get_user


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


stub = modal.Stub("indexhub-preprocess", image=IMAGE)


def _clean_panel(
    raw_panel_data: pl.DataFrame,
    entity_cols: List[str],
    time_col: str,
    datetime_fmt: str,
) -> pl.DataFrame:
    try:
        expr = [
            # Defensive replace #N/A generated by nulls/blanks to 0
            pl.col(entity_cols).str.replace("#N/A", "0"),
        ]
        if raw_panel_data.get_column(time_col).dtype not in [pl.Date, pl.Datetime]:
            expr.append(
                pl.col("time").cast(pl.Utf8).str.strptime(pl.Date, fmt=datetime_fmt)
            )

        panel_data = (
            raw_panel_data.rename({time_col: "time"}).with_columns(expr)
            # Downcast dtypes
            .select(pl.all().shrink_dtype())
            # Sort by entity and time
            .sort(by=[*entity_cols, "time"])
        )
    except Exception as err:
        raise ValueError(f"Data cleaning errors: {repr(err)}") from err
    return panel_data


def _make_output_path(source_id: int, updated_at: datetime) -> str:
    timestamp = datetime.strftime(updated_at, "%Y%m%dT%X").replace(":", "")
    path = f"staging/{source_id}/{timestamp}.parquet"
    return path


def _update_source(
    source_id: int,
    updated_at: datetime,
    output_path: Union[str, None],
    status: str,
    msg: str,
) -> Source:
    # Establish connection
    with Session(engine) as session:
        # Select rows with specific report_id only
        query = select(Source).where(Source.id == source_id)
        source = session.exec(query).one()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        # Update the fields based on the source_id
        source.updated_at = updated_at
        source.output_path = output_path
        source.status = status
        source.msg = msg
        # Add, commit and refresh the updated object
        session.add(source)
        session.commit()
        session.refresh(source)
        return source


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def run_preprocess(
    user_id: int,
    source_id: int,
    source_tag: str,
    source_variables: Mapping[str, Any],
    storage_tag: str,
    storage_bucket_name: str,
    entity_cols: List[str],
    time_col: str,
    datetime_fmt: str,
):
    """Load, clean, and write panel dataset."""
    try:
        # Get credentials
        source_creds = get_aws_secret(
            tag=source_tag, secret_type="sources", user_id=user_id
        )
        storage_creds = get_aws_secret(
            tag=storage_tag, secret_type="storage", user_id=user_id
        )
        # Read data from source
        read = SOURCE_TAG_TO_READER[source_tag]
        raw_panel_data = read(**source_variables, **source_creds)
        # Clean data
        panel_data = _clean_panel(
            raw_panel_data,
            entity_cols=entity_cols,
            time_col=time_col,
            datetime_fmt=datetime_fmt,
        )
        # Write data to data lake storage
        updated_at = datetime.utcnow()
        write = STORAGE_TAG_TO_WRITER[storage_tag]
        output_path = _make_output_path(source_id=source_id, updated_at=updated_at)
        write(
            panel_data,
            bucket_name=storage_bucket_name,
            object_path=output_path,
            **storage_creds,
        )
    except ClientError as exc:
        updated_at = datetime.utcnow()
        output_path = None
        status = "FAILED"
        error_code = exc.response["Error"]["Code"]

        if error_code == "InvalidSignatureException":
            msg = "Authentication secret errors"
        elif error_code == "AccessDeniedException":
            msg = "Insufficient permissions errors"
        else:
            msg = repr(exc)
    except HTTPException as exc:
        # Source file / table not found errors
        updated_at = datetime.utcnow()
        output_path = None
        status = "FAILED"
        msg = exc.detail
    except ValueError as exc:
        # Data cleaning errors
        updated_at = datetime.utcnow()
        output_path = None
        status = "FAILED"
        msg = exc
    except Exception as exc:
        updated_at = datetime.utcnow()
        output_path = None
        status, msg = "FAILED", repr(exc)
    else:
        status, msg = "SUCCESS", "OK"
    finally:
        _update_source(
            source_id=source_id,
            updated_at=updated_at,
            output_path=output_path,
            status=status,
            msg=msg,
        )


def _get_all_sources() -> List[Source]:
    with Session(engine) as session:
        query = select(Source)
        sources = session.exec(query).all()
        if not sources:
            raise HTTPException(status_code=404, detail="Source not found")
        return sources


@stub.function(
    memory=5120,
    cpu=4.0,
    timeout=900,
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ],
    schedule=modal.Cron("0 16 * * *"),  # run at 12am daily (utc 4pm)
)
def flow():
    logger.info("Flow started")
    # 1. Get all sources
    sources = _get_all_sources()

    futures = {}
    for source in sources:
        logger.info(f"Checking source: {source.id}")
        columns = json.loads(source.columns)

        # 2. Get user
        user = get_user(source.user_id)

        # 3. Check freq from source for schedule
        duration = FREQ_TO_DURATION[source.freq]
        updated_at = source.updated_at.replace(microsecond=0)
        if duration == "1mo":
            new_dt = updated_at + relativedelta(months=1)
            run_dt = datetime(new_dt.year, new_dt.month, 1)
        else:
            run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
        logger.info(f"Next run at: {run_dt}")

        # 4. Run preprocess flow
        current_datetime = datetime.now().replace(microsecond=0)
        if (current_datetime >= run_dt) or source.status == "FAILED":
            # Spawn preprocess flow for source
            futures[source.id] = run_preprocess.spawn(
                user_id=source.user_id,
                source_id=source.id,
                source_tag=source.tag,
                source_variables=json.loads(source.variables),
                storage_tag=user.storage_tag,
                storage_bucket_name=user.storage_bucket_name,
                entity_cols=columns["entity_cols"],
                time_col=columns["time_col"],
                datetime_fmt=source.datetime_fmt,
            )

    # 5. Get future for each source
    for source_id, future in futures.items():
        logger.info(f"Running preprocess flow for source: {source_id}")
        future.get()
        logger.info(f"Preprocess flow completed for source: {source_id}")

    logger.info("Flow completed")


@stub.local_entrypoint
def test():
    user_id = "indexhub-demo"

    # Source
    source_id = 1
    source_tag = "s3"
    source_variables = {
        "bucket_name": "indexhub-demo",
        "object_path": "tourism/tourism_20221212.parquet",
        "file_ext": "parquet",
    }
    columns = {
        "entity_cols": ["country", "territory", "state"],
        "time_col": "time",
        "feature_cols": ["trips_in_000s"],
    }
    datetime_fmt = "%Y-%m-%d"

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo"

    run_preprocess.call(
        user_id=user_id,
        source_id=source_id,
        source_tag=source_tag,
        source_variables=source_variables,
        storage_tag=storage_tag,
        storage_bucket_name=storage_bucket_name,
        entity_cols=columns["entity_cols"],
        time_col=columns["time_col"],
        datetime_fmt=datetime_fmt,
    )
