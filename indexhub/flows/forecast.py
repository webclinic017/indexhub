import logging
from datetime import datetime
from typing import Any, List, Mapping, Optional

import modal
import polars as pl
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.policy import Policy
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.deployment import IMAGE


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


stub = modal.Stub("indexhub-forecast", image=IMAGE)


def _generate_output_path(policy_id: int, updated_at: datetime, prefix: str) -> str:
    timestamp = datetime.strftime(updated_at, "%Y%m%dT%X").replace(":", "")
    path = f"artifacts/{policy_id}/{prefix}_{timestamp}.parquet"
    return path


def _update_policy(
    policy_id: int,
    updated_at: datetime,
    outputs: Mapping[str, Any],
    status: str,
    msg: str,
) -> Policy:
    # Establish connection
    with Session(engine) as session:
        # Select rows with specific report_id only
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).one()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        # Update the fields based on the policy_id
        policy.outputs = outputs
        policy.updated_at = updated_at
        policy.status = status
        policy.msg = msg

        # Add, commit and refresh the updated object
        session.add(policy)
        session.commit()
        session.refresh(policy)
        return policy


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def flow(
    user_id: int,
    policy_id: int,
    panel_path: str,
    storage_tag: str,
    storage_bucket_name: str,
    level_cols: List[str],
    target_col: str,
    min_lags: int,
    max_lags: int,
    fh: int,
    freq: str,
    n_splits: int,
    holiday_regions: Optional[List[str]] = None,
):
    try:
        # Get credentials
        storage_creds = get_aws_secret(
            tag=storage_tag, secret_type="storage", user_id=user_id
        )
        # Read y from storage
        read = SOURCE_TAG_TO_READER[storage_tag]
        y_panel = read(
            bucket_name=storage_bucket_name,
            object_path=panel_path,
            file_ext="parquet",
            **storage_creds,
        )

        # Run automl flow
        automl_flow = modal.Function.lookup("functime-forecast-automl", "flow")
        time_col = y_panel.select(pl.col([pl.Date, pl.Datetime])).columns[0]
        y, outputs = automl_flow.call(
            y=y_panel.select([*level_cols, time_col, target_col]),
            min_lags=min_lags,
            max_lags=max_lags,
            fh=fh,
            freq=freq,
            n_splits=n_splits,
            holiday_regions=holiday_regions,
        )

        # Write artifacts from "outputs" to data lake storage
        updated_at = datetime.utcnow()
        write = STORAGE_TAG_TO_WRITER[storage_tag]

        # Export y
        output_path = _generate_output_path(
            policy_id=policy_id, updated_at=updated_at, prefix="y"
        )
        write(
            y,
            bucket_name=storage_bucket_name,
            object_path=output_path,
            **storage_creds,
        )

        # Export artifacts for each model
        model_artifacts_keys = [
            "forecasts",
            "backtests",
            "residuals",
            "scores",
            "quantiles",
            "risks",
        ]

        for key in model_artifacts_keys:
            model_artifacts = outputs[key]
            paths = {}

            for model, df in model_artifacts.items():
                output_path = _generate_output_path(
                    policy_id=policy_id, updated_at=updated_at, prefix=f"{key}__{model}"
                )
                write(
                    df,
                    bucket_name=storage_bucket_name,
                    object_path=output_path,
                    **storage_creds,
                )
                paths[model] = output_path

            outputs[key] = paths

        # Export statistics
        for key, df in outputs["statistics"].items():
            output_path = _generate_output_path(
                policy_id=policy_id, updated_at=updated_at, prefix=f"statistics__{key}"
            )
            write(
                df,
                bucket_name=storage_bucket_name,
                object_path=output_path,
                **storage_creds,
            )

            outputs["statistics"][key] = output_path

    except ClientError as exc:
        updated_at = datetime.utcnow()
        outputs = None
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
        outputs = None
        status = "FAILED"
        msg = exc.detail
    except ValueError as exc:
        # Data cleaning errors
        updated_at = datetime.utcnow()
        outputs = None
        status = "FAILED"
        msg = exc
    except Exception as exc:
        updated_at = datetime.utcnow()
        outputs = None
        status, msg = "FAILED", repr(exc)
    else:
        status, msg = "SUCCESS", "OK"
    finally:
        _update_policy(
            policy_id=policy_id,
            updated_at=updated_at,
            outputs=outputs,
            status=status,
            msg=msg,
        )


@stub.local_entrypoint
def test():
    user_id = "indexhub-demo"

    # Policy
    policy_id = 1
    fields = {
        "sources": {"panel": "staging/1/20230411T093305.parquet", "baseline": None},
        "direction": "over",
        "risks": "low volatility",
        "target_col": "trips_in_000s",
        "level_cols": ["state"],
        "description": "Reduce trips_in_000s over forecast error for low volatility state.",
        "min_lags": 6,
        "max_lags": 6,
        "fh": 3,
        "freq": "1mo",
        "n_splits": 3,
        "holiday_regions": ["AU"],
    }

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo"

    flow.call(
        user_id=user_id,
        policy_id=policy_id,
        panel_path=fields["sources"]["panel"],
        storage_tag=storage_tag,
        storage_bucket_name=storage_bucket_name,
        level_cols=fields["level_cols"],
        time_col=fields["time_col"],
        target_col=fields["target_col"],
        min_lags=fields["min_lags"],
        max_lags=fields["max_lags"],
        fh=fields["fh"],
        freq=fields["freq"],
        n_splits=fields["n_splits"],
        holiday_regions=fields["holiday_regions"],
    )
