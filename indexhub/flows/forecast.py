import json
import logging
from datetime import datetime
from functools import partial
from typing import Any, Callable, List, Mapping, Optional

import modal
import pandas as pd
import polars as pl
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.policy import Policy
from indexhub.api.models.user import User
from indexhub.api.routers.sources import get_source
from indexhub.api.routers.stats import FREQ_TO_SP
from indexhub.api.schemas import (
    SUPPORTED_COUNTRIES,
    SUPPORTED_ERROR_TYPE,
    SUPPORTED_FREQ,
)
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


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def compute_rolling_forecast(
    output_json: Mapping[str, Any],
    policy_id: int,
    updated_at: datetime,
    read: Callable,
    write: Callable,
):
    logger.info("Running rolling forecast")
    pl.toggle_string_cache(True)
    # Get the updated at based on policy_id (sqlmodel)
    dt = updated_at.replace(microsecond=0)

    # Read forecast artifacts from s3 and postproc
    best_model = output_json["best_model"]
    forecast = read(object_path=output_json["forecasts"][best_model]).pipe(
        # Rename target_col to "forecast"
        lambda df: df.rename({df.columns[-1]: "forecast"}).with_columns(
            [
                # Assign updated_at column
                pl.lit(dt).alias("updated_at"),
                # Assign best_model column
                pl.lit(best_model).alias("best_model"),
                # Assign fh column
                pl.col("time").rank("ordinal").over(df.columns[0]).alias("fh"),
            ]
        )
    )

    # Read actual from y panel in s3 and postproc
    actual = read(object_path=output_json["y"]).pipe(
        lambda df: df.rename(
            # Rename target_col to "actual"
            {df.columns[-1]: "actual"}
        )
    )

    # Combine forecast and actual artifacts
    latest_forecasts = (
        forecast.join(actual, on=forecast.columns[:2], how="left").with_columns(
            [(pl.col("forecast") - pl.col("actual")).alias("residual").cast(pl.Float32)]
        )
        # Reorder columns
        .select(
            [
                pl.all().exclude(["forecast", "actual", "residual", "best_model"]),
                "forecast",
                "actual",
                "residual",
                "best_model",
            ]
        )
    )

    try:
        cached_forecasts = read(
            object_path=f"artifacts/{policy_id}/rolling_forecasts.parquet",
        )
        # Get the latest `updated_at` date from cached rolling forecast
        last_dt = cached_forecasts.get_column("updated_at").unique().max()
        if dt > last_dt:
            # Concat latest forecasts artifacts with cached rolling forecasts
            rolling_forecasts = (
                pl.concat([cached_forecasts, latest_forecasts]).select(
                    [
                        pl.all().exclude(
                            ["forecast", "actual", "residual", "best_model"]
                        ),
                        "forecast",
                        "actual",
                        "residual",
                        "best_model",
                    ]
                )
                # Sort by time_col, entity_col, updated_at
                .pipe(lambda df: df.sort(df.columns[:3]))
            )
            # Export merged data as rolling forecasts artifact
            write(
                rolling_forecasts,
                object_path=f"artifacts/{policy_id}/rolling_forecasts.parquet",
            )
            logger.info("Rolling forecast completed")
    except HTTPException as err:
        if (
            err.status_code == 400
            and err.detail == "Invalid S3 path when reading from source"
        ):
            # Export latest forecasts as initial rolling forecasts artifact
            write(
                latest_forecasts,
                object_path=f"artifacts/{policy_id}/rolling_forecasts.parquet",
            )
            logger.info("Rolling forecast completed")
    finally:
        pl.toggle_string_cache(False)


def _groupby_rolling(data: pl.DataFrame, entity_col: str, sp: int):
    new_data = (
        data
        # Select rows from last sp
        .groupby(entity_col, maintain_order=True)
        .tail(sp)
        .groupby(entity_col, maintain_order=True)
        .agg(
            pl.all(),
            # Rolling sum for absolute uplift
            pl.col("^*__uplift$").cumsum().suffix("__rolling_sum"),
            # Rolling mean for uplift pct
            (
                pl.col("^*__uplift_pct$").cumsum()
                / (pl.col("^*__uplift_pct$").cumcount() + 1)
            ).suffix("__rolling_mean"),
            # Diff for both
            pl.col("^*__uplift.*$").diff().suffix("__diff"),
            # Add window
            pl.col("updated_at").rank("ordinal").alias("window"),
        )
        .pipe(lambda df: df.explode(df.columns[1:]))
        # Replace inf with null
        .with_columns(
            pl.when(
                pl.all().exclude([entity_col, "updated_at", "window"]).is_infinite()
            )
            .then(None)
            .otherwise(pl.all())
            .keep_name()
        )
    )
    return new_data


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def compute_rolling_uplift(
    output_json: Mapping[str, Any],
    policy_id: int,
    updated_at: datetime,
    sp: int,
    read: Callable,
    write: Callable,
):
    logger.info("Running rolling uplift")
    pl.toggle_string_cache(True)

    dt = updated_at.replace(microsecond=0)

    # Read latest uplift artifacts from s3
    latest_uplift = read(object_path=output_json["uplift"])
    entity_col = latest_uplift.columns[0]
    time_col = "updated_at"
    idx_cols = [entity_col, time_col]

    latest_uplift = (
        latest_uplift
        # Add updated_at
        .with_columns(
            pl.lit(dt).alias(time_col),
        )
        # Generate rolling stats by groupby entity col
        .pipe(_groupby_rolling, entity_col, sp)
        # Reorder columns
        .select([*idx_cols, "window", pl.all().exclude([*idx_cols, "window"])])
    )

    try:
        cached_uplift = read(
            object_path=f"artifacts/{policy_id}/rolling_uplift.parquet"
        )

        # Get the latest `updated_at` date from cached rolling forecast
        last_dt = cached_uplift.get_column(time_col).unique().max()
        if dt > last_dt:
            # Concat latest uplift artifacts with cached rolling uplift
            rolling_uplift = (
                pl.concat([cached_uplift, latest_uplift])
                # Sort by entity_col, updated_at
                .sort(idx_cols).select(
                    [
                        *idx_cols,
                        pl.col("^*__uplift$"),
                        pl.col("^*__uplift_pct$"),
                    ]
                )
                # Generate rolling stats by groupby entity col
                .pipe(_groupby_rolling, entity_col, sp)
                # Reorder columns
                .select([*idx_cols, "window", pl.all().exclude([*idx_cols, "window"])])
            )

            # Export merged data as rolling uplift artifact
            write(
                rolling_uplift,
                object_path=f"artifacts/{policy_id}/rolling_uplift.parquet",
            )
        logger.info("Rolling uplift completed")
    except HTTPException as err:
        if (
            err.status_code == 400
            and err.detail == "Invalid S3 path when reading from source"
        ):
            # Export latest uplift as initial rolling uplift artifact
            write(
                latest_uplift,
                object_path=f"artifacts/{policy_id}/rolling_uplift.parquet",
            )
            logger.info("Rolling uplift completed")
    finally:
        pl.toggle_string_cache(False)


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


def _merge_multilevels(X: pl.DataFrame) -> pl.DataFrame:
    level_cols = X.columns[:-2]
    entity_col = "__".join(level_cols)
    time_col, target_col = X.columns[-2:]
    X_new = (
        # Combine subset of entity columns
        X.lazy()
        .with_columns(pl.concat_str(level_cols, separator="__").alias(entity_col))
        # Select and sort columns
        .select([entity_col, time_col, target_col])
        .sort([entity_col, time_col])
        .with_columns([pl.col(entity_col).set_sorted(), pl.col(time_col).set_sorted()])
        .collect()
    )
    return X_new


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def run_forecast(
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
    sp: int,
    n_splits: int,
    holiday_regions: Optional[List[str]] = None,
    objective: Optional[str] = "mae",
    agg_method: Optional[str] = "mean",
    baseline_model: Optional[str] = "snaive",
    baseline_path: Optional[str] = None,
    inventory_path: Optional[str] = None,
):
    try:
        pl.toggle_string_cache(True)
        status, msg = "SUCCESS", "OK"
        updated_at = datetime.utcnow()

        # 1. Get credentials
        storage_creds = get_aws_secret(
            tag=storage_tag, secret_type="storage", user_id=user_id
        )
        # 2. Setup reader to read artifacts from data lake storage
        read = partial(
            SOURCE_TAG_TO_READER[storage_tag],
            bucket_name=bucket_name,
            file_ext="parquet",
            **storage_creds,
        )
        # 3. Setup writer to upload artifacts to data lake storage
        write = partial(
            STORAGE_TAG_TO_WRITER[storage_tag],
            bucket_name=bucket_name,
            **storage_creds,
        )
        make_path = partial(
            _make_output_path, policy_id=policy_id, updated_at=updated_at
        )

        # 4. Read y from storage
        y_panel = read(object_path=panel_path)

        # 5. Run automl flow
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
            objective=objective,
            agg_method=agg_method,
        )
        entity_col = y.columns[0]
        outputs["y"] = make_path(prefix="y")

        write(y, object_path=make_path(prefix="y"))

        # 6. Compute uplift
        # NOTE: Only compares against BEST MODEL
        agg_exprs = {
            "sum": pl.sum(target_col),
            "mean": pl.mean(target_col),
            "median": pl.median(target_col),
        }
        if baseline_path:
            # Read baseline from storage
            y_baseline = (
                read(object_path=baseline_path)
                .select([*level_cols, time_col, target_col])
                .pipe(_merge_multilevels)
                .groupby([entity_col, time_col])
                .agg(agg_exprs[agg_method])
            )
        else:
            y_baseline_backtest = (
                outputs["backtests"][baseline_model]
                .groupby([entity_col, time_col])
                .agg(pl.mean(target_col))
            )
            y_baseline_forecast = outputs["forecasts"][baseline_model]
            y_baseline = pl.concat([y_baseline_backtest, y_baseline_forecast])

        if inventory_path:
            inventory = (
                read(
                    bucket_name=bucket_name,
                    object_path=inventory_path,
                    file_ext="parquet",
                    **storage_creds,
                )
                .select([*level_cols, time_col, target_col])
                .pipe(_merge_multilevels)
                .groupby([entity_col, time_col])
                .agg(agg_exprs[agg_method])
            )
            outputs["inventory"] = make_path(prefix="inventory")
            write(inventory, object_path=outputs["inventory"])
        else:
            outputs["inventory"] = None

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

        # 7. Export artifacts for each model
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

        # 8. Export statistics
        for key, df in outputs["statistics"].items():
            output_path = make_path(prefix=f"statistics__{key}")
            write(df, object_path=output_path)
            outputs["statistics"][key] = output_path

        # 9. Run rolling forecast
        compute_rolling_forecast.call(
            output_json=outputs,
            policy_id=policy_id,
            updated_at=updated_at,
            read=read,
            write=write,
        )

        # 10. Run rolling uplift
        compute_rolling_uplift.call(
            output_json=outputs,
            policy_id=policy_id,
            updated_at=updated_at,
            sp=sp,
            read=read,
            write=write,
        )

    except Exception as exc:
        updated_at = datetime.utcnow()
        outputs = None
        status = "FAILED"
        msg = repr(exc)

    finally:
        pl.toggle_string_cache(False)
        _update_policy(
            policy_id=policy_id,
            updated_at=updated_at,
            outputs=json.dumps(outputs),
            status=status,
            msg=msg,
        )


def _get_all_policies() -> List[Policy]:
    with Session(engine) as session:
        query = select(Policy)
        policies = session.exec(query).all()
        if not policies:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policies


def get_user(user_id: str) -> User:
    with Session(engine) as session:
        query = select(User).where(User.id == user_id)
        user = session.exec(query).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


FREQ_TO_DURATION = {
    "Hourly": "1h",  # Run if current date >= last run + 1h
    "Daily": "24h",  # Run if current date >= last run + 1d
    "Weekly": "168h",  # Run if current date >= last run + 7d
    "Monthly": "1mo",  # Run on first day of every month
}


@stub.function(
    memory=5120,
    cpu=4.0,
    timeout=900,
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ],
    schedule=modal.Cron("0 17 * * *"),  # run at 1am daily (utc 5pm)
)
def flow():
    logger.info("Flow started")
    # 1. Get all policies
    policies = _get_all_policies()

    futures = {}
    for policy in policies:
        logger.info(f"Checking policy: {policy.id}")
        fields = json.loads(policy.fields)
        sources = json.loads(policy.sources)

        # 2. Get user
        user = get_user(policy.user_id)

        # 3. Check freq from source for schedule
        duration = FREQ_TO_DURATION[fields["freq"]]
        updated_at = policy.updated_at.replace(microsecond=0)
        if duration == "1mo":
            new_dt = updated_at + relativedelta(months=1)
            run_dt = datetime(new_dt.year, new_dt.month, 1)
        else:
            run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
        logger.info(f"Next run at: {run_dt}")

        # 4. Run forecast flow
        current_datetime = datetime.now().replace(microsecond=0)
        if (current_datetime >= run_dt) or policy.status == "FAILED":
            # Get staging path for each source
            panel_path = get_source(sources["panel"])["source"].output_path
            if sources["baseline"]:
                baseline_path = get_source(sources["baseline"])["source"].output_path
            else:
                baseline_path = None
            if sources["inventory"]:
                inventory_path = get_source(sources["inventory"])["source"].output_path
            else:
                inventory_path = None
            # Spawn forecast flow for policy
            futures[policy.id] = run_forecast.spawn(
                user_id=policy.user_id,
                policy_id=policy.id,
                panel_path=panel_path,
                baseline_path=baseline_path,
                inventory_path=inventory_path,
                storage_tag=user.storage_tag,
                bucket_name=user.storage_bucket_name,
                level_cols=fields["level_cols"],
                target_col=fields["target_col"],
                min_lags=fields["min_lags"],
                max_lags=fields["max_lags"],
                fh=fields["fh"],
                freq=SUPPORTED_FREQ[fields["freq"]],
                sp=FREQ_TO_SP[fields["freq"]],
                n_splits=fields["n_splits"],
                holiday_regions=[
                    SUPPORTED_COUNTRIES[country]
                    for country in fields["holiday_regions"]
                ],
                objective=SUPPORTED_ERROR_TYPE[fields["error_type"]],
                agg_method=fields["agg_method"],
                baseline_model=fields["baseline_model"],
            )

    # 5. Get future for each policy
    for policy_id, future in futures.items():
        logger.info(f"Running forecast flow for policy: {policy_id}")
        future.get()
        logger.info(f"Forecast flow completed for policy: {policy_id}")

    logger.info("Flow completed")


@stub.local_entrypoint
def test(user_id: str = "indexhub-demo"):

    # Policy
    policy_id = 1
    fields = {
        "sources": {
            "panel": 1,
            "baseline": None,
            "inventory": 2,
        },
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
        "objective": "mae",
        "agg_method": "sum",
        "baseline_model": "snaive",
    }

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo"

    # Get staging path for each source
    sources = fields["sources"]
    panel_path = get_source(sources["panel"])["source"].output_path
    if sources["baseline"]:
        baseline_path = get_source(sources["baseline"])["source"].output_path
    else:
        baseline_path = None
    if sources["inventory"]:
        inventory_path = get_source(sources["inventory"])["source"].output_path
    else:
        inventory_path = None

    flow.call(
        user_id=user_id,
        policy_id=policy_id,
        panel_path=panel_path,
        baseline_path=baseline_path,
        inventory_path=inventory_path,
        storage_tag=storage_tag,
        bucket_name=storage_bucket_name,
        level_cols=fields["level_cols"],
        target_col=fields["target_col"],
        min_lags=fields["min_lags"],
        max_lags=fields["max_lags"],
        fh=fields["fh"],
        freq=fields["freq"],
        sp=FREQ_TO_SP[fields["freq"]],
        n_splits=fields["n_splits"],
        holiday_regions=fields["holiday_regions"],
        objective=fields["error_type"],  # default is mae
        agg_method=fields["agg_method"],  # default is mean
        baseline_mode=fields["baseline_model"],  # default is snaive
    )
