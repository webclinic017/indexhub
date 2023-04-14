import json
import logging
from datetime import datetime
from functools import partial
from typing import Any, List, Mapping, Optional

import modal
import polars as pl
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


def _make_output_path(policy_id: int, updated_at: datetime, prefix: str) -> str:
    timestamp = datetime.strftime(updated_at, "%Y%m%dT%X").replace(":", "")
    path = f"artifacts/{policy_id}/{timestamp}/{prefix}.parquet"
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
    bucket_name: str,
    level_cols: List[str],
    target_col: str,
    min_lags: int,
    max_lags: int,
    fh: int,
    freq: str,
    n_splits: int,
    holiday_regions: Optional[List[str]] = None,
    baseline_path: Optional[str] = None,
):
    try:
        status, msg = "SUCCESS", "OK"
        # Get credentials
        storage_creds = get_aws_secret(
            tag=storage_tag, secret_type="storage", user_id=user_id
        )
        # Setup writer to upload artifacts to data lake storage
        updated_at = datetime.utcnow()
        write = partial(
            STORAGE_TAG_TO_WRITER[storage_tag],
            bucket_name=bucket_name,
            **storage_creds,
        )
        make_path = partial(
            _make_output_path, policy_id=policy_id, updated_at=updated_at
        )

        # Read y from storage
        read = SOURCE_TAG_TO_READER[storage_tag]
        y_panel = read(
            bucket_name=bucket_name,
            object_path=panel_path,
            file_ext="parquet",
            **storage_creds,
        )

        # Run automl flow
        automl_flow = modal.Function.lookup("functime-forecast-automl", "flow")
        time_col = y_panel.select(
            pl.col([pl.Date, pl.Datetime, pl.Datetime("ns")])
        ).columns[0]

        y, outputs = automl_flow.call(
            y=y_panel.select([*level_cols, time_col, target_col]),
            min_lags=min_lags,
            max_lags=max_lags,
            fh=fh,
            freq=freq,
            n_splits=n_splits,
            holiday_regions=holiday_regions,
        )
        entity_col = y.columns[0]
        outputs["y"] = make_path(prefix="y")

        write(y, object_path=make_path(prefix="y"))

        # Compute uplift if applicable
        # NOTE: Only compares against BEST MODEL
        if baseline_path:
            # Read baseline from storage
            y_baseline = read(
                bucket_name=bucket_name,
                object_path=baseline_path,
                file_ext="parquet",
                **storage_creds,
            )
        else:
            y_baseline = (
                outputs["backtests"]["snaive"]
                .groupby([entity_col, time_col])
                .agg(pl.mean(target_col))
            )

        # Score baseline compared to best scores
        uplift_flow = modal.Function.lookup("functime-forecast-uplift", "flow")
        kwargs = {"y": y, "y_baseline": y_baseline, "freq": freq}
        baseline_scores, baseline_metrics, uplift = uplift_flow.call(
            outputs["scores"][outputs["best_model"]],
            **kwargs,
        )
        outputs["y_baseline"] = make_path(prefix="y_baseline")
        outputs["baseline__scores"] = make_path(prefix="baseline__scores")
        outputs["baseline__metrics"] = baseline_metrics
        outputs["uplift"] = make_path(prefix="uplift")

        write(y_baseline, object_path=outputs["y_baseline"])
        write(baseline_scores, object_path=outputs["baseline__scores"])
        write(uplift, object_path=make_path(prefix="uplift"))

        # Export artifacts for each model
        model_artifacts_keys = [
            "forecasts",
            "backtests",
            "residuals",
            "scores",
            "quantiles",
        ]

        for key in model_artifacts_keys:
            model_artifacts = outputs[key]

            for model, df in model_artifacts.items():
                output_path = make_path(prefix=f"{key}__{model}")
                write(df, object_path=output_path)
                outputs[key][model] = output_path

        # Export statistics
        for key, df in outputs["statistics"].items():
            output_path = make_path(prefix=f"statistics__{key}")
            write(df, object_path=output_path)
            outputs["statistics"][key] = output_path

        outputs = json.dumps(outputs)
    except Exception as exc:
        updated_at = datetime.utcnow()
        outputs = None
        status = "FAILED"
        msg = repr(exc)

    finally:
        _update_policy(
            policy_id=policy_id,
            updated_at=updated_at,
            outputs=outputs,
            status=status,
            msg=msg,
        )


@stub.local_entrypoint
def test(user_id: str = "indexhub-demo"):

    # Policy
    policy_id = 1
    fields = {
        "sources": {"panel": "staging/1/20230411T093305.parquet", "baseline": None},
        "error_type": "over-forecast",
        "segmentation_factor": "volatility",
        "target_col": "trips_in_000s",
        "level_cols": ["state"],
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
        baseline_path=fields["sources"]["baseline"],
        storage_tag=storage_tag,
        bucket_name=storage_bucket_name,
        level_cols=fields["level_cols"],
        target_col=fields["target_col"],
        min_lags=fields["min_lags"],
        max_lags=fields["max_lags"],
        fh=fields["fh"],
        freq=fields["freq"],
        n_splits=fields["n_splits"],
        holiday_regions=fields["holiday_regions"],
    )
