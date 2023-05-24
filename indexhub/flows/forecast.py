import json
import logging
import os
from datetime import datetime
from functools import partial
from typing import Any, Callable, List, Mapping, Optional

import modal
import pandas as pd
import polars as pl
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.objective import Objective
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
        "indexhub-forecast",
        image=IMAGE,
        secrets=[
            modal.Secret.from_name("aws-credentials"),
            modal.Secret.from_name("postgres-credentials"),
            modal.Secret.from_name("env-name"),
        ]
    )
else:
    stub = modal.Stub(
        "dev-indexhub-forecast",
        image=IMAGE,
        secrets=[
            modal.Secret.from_name("aws-credentials"),
            modal.Secret.from_name("dev-postgres-credentials"),
            modal.Secret.from_name("dev-env-name"),
        ]
    )


@stub.function()
def compute_rolling_forecast(
    output_json: Mapping[str, Any],
    objective_id: int,
    updated_at: datetime,
    read: Callable,
    write: Callable,
):
    logger.info("Running rolling forecast")
    pl.toggle_string_cache(True)
    # Get the updated at based on objective_id (sqlmodel)
    dt = updated_at.replace(microsecond=0)

    # List of columns for rolling forecast panel
    selected_cols = [
        "actual",
        "ai",
        "baseline",
        "best_plan",
        "plan",
        "residual_ai",
        "residual_baseline",
        "residual_best_plan",
        "residual_plan",
        "best_model",
    ]

    # Read forecast artifacts from s3 and postproc
    best_models = output_json["best_models"]
    forecast = (
        read(object_path=output_json["forecasts"]["best_models"])
        .pipe(
            # Rename target_col to "forecast"
            lambda df: df.rename({df.columns[-1]: "ai"}).with_columns(
                [
                    # Assign updated_at column
                    pl.lit(dt).alias("updated_at"),
                    # Assign best_model column
                    pl.col(df.columns[0]).map_dict(best_models).alias("best_model"),
                    # Assign fh column
                    pl.col("time")
                    .rank("ordinal")
                    .over(df.columns[0])
                    .cast(pl.Int32)
                    .alias("fh"),
                ]
            )
        )
        .select(pl.all().shrink_dtype())
    )

    # Read actual from y panel in s3 and postproc
    actual = (
        read(object_path=output_json["y"])
        .pipe(
            lambda df: df.rename(
                # Rename target_col to "actual"
                {df.columns[-1]: "actual"}
            )
        )
        .select(pl.all().shrink_dtype())
    )

    # Read baseline from y_baseline panel in s3 and postproc
    baseline = (
        read(object_path=output_json["y_baseline"])
        .pipe(
            lambda df: df.rename(
                # Rename target_col to "actual"
                {df.columns[-1]: "baseline"}
            )
        )
        .select(pl.all().shrink_dtype())
    )

    # Read best plan from best_plan panel in s3 and postproc
    forecast_best_plan = read(object_path=output_json["best_plan"]).select(
        pl.all().shrink_dtype()
    )

    # Combine forecast and actual artifacts
    latest_forecasts = (
        forecast.join(actual, on=forecast.columns[:2], how="left")
        .join(baseline, on=forecast.columns[:2], how="left")
        .join(forecast_best_plan, on=[*forecast.columns[:2], "fh"], how="left")
        .with_columns(
            [
                (pl.col("ai") - pl.col("actual")).alias("residual_ai"),
                (pl.col("baseline") - pl.col("actual")).alias("residual_baseline"),
                (pl.col("best_plan") - pl.col("actual")).alias("residual_best_plan"),
                # For user chosen plan, default to best plan first
                # Will update user chosen plan when user click on execute plan or upload csv
                pl.col("best_plan").alias("plan"),
                (pl.col("best_plan") - pl.col("actual")).alias("residual_plan"),
            ]
        )
        # Reorder columns
        .select(
            [
                pl.all().exclude(
                    [
                        *selected_cols,
                        "use",
                    ]
                ),
                *selected_cols,
            ]
        )
        .select(pl.all().shrink_dtype())
    )

    try:
        cached_forecasts = read(
            object_path=f"artifacts/{objective_id}/rolling_forecasts.parquet",
        )
        # Get the latest `updated_at` date from cached rolling forecast
        last_dt = cached_forecasts.get_column("updated_at").unique().max()
        if dt > last_dt:
            # Concat latest forecasts artifacts with cached rolling forecasts
            rolling_forecasts = (
                pl.concat([cached_forecasts, latest_forecasts])
                .join(actual, on=cached_forecasts.columns[:2], how="left")
                # Coalesce actual to get the first non-null value
                .pipe(
                    lambda df: df.with_columns(
                        pl.coalesce(df["actual"], df["actual_right"]).alias("actual")
                    )
                )
                # Calculate residuals
                .with_columns(
                    [
                        (pl.col("ai") - pl.col("actual")).alias("residual_ai"),
                        (pl.col("baseline") - pl.col("actual")).alias(
                            "residual_baseline"
                        ),
                        (pl.col("best_plan") - pl.col("actual")).alias(
                            "residual_best_plan"
                        ),
                    ]
                )
                .select([pl.all().exclude(selected_cols), *selected_cols])
                # Sort by time_col, entity_col, updated_at
                .pipe(lambda df: df.sort(df.columns[:3]))
            )
            # Export merged data as rolling forecasts artifact
            write(
                rolling_forecasts,
                object_path=f"artifacts/{objective_id}/rolling_forecasts.parquet",
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
                object_path=f"artifacts/{objective_id}/rolling_forecasts.parquet",
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
            # Rolling mean for absolute uplift
            (
                pl.col("^*__uplift$").cumsum() / (pl.col("^*__uplift$").cumcount() + 1)
            ).suffix("__rolling_mean"),
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
            pl.when(pl.col([pl.Float32, pl.Float64]).is_infinite())
            .then(None)
            .otherwise(pl.col([pl.Float32, pl.Float64]))
            .keep_name()
        )
    )
    return new_data


@stub.function()
def compute_rolling_uplift(
    output_json: Mapping[str, Any],
    objective_id: int,
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
            object_path=f"artifacts/{objective_id}/rolling_uplift.parquet"
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
                object_path=f"artifacts/{objective_id}/rolling_uplift.parquet",
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
                object_path=f"artifacts/{objective_id}/rolling_uplift.parquet",
            )
            logger.info("Rolling uplift completed")
    finally:
        pl.toggle_string_cache(False)


@stub.function()
def create_best_plan(
    output_json: Mapping[str, Any],
    objective: str,
    read: Callable,
    write: Callable,
    output_path: str,
):
    logger.info("Creating best plan")
    pl.toggle_string_cache(True)

    try:
        forecast = read(object_path=output_json["forecasts"]["best_models"])
        y_baseline = read(object_path=output_json["y_baseline"])
        uplift = read(object_path=output_json["uplift"])
        entity_col, time_col, target_col = forecast.columns
        idx_cols = entity_col, time_col

        # Create best plan
        best_plan = (
            forecast.lazy()
            .rename({target_col: "forecast"})
            # Join with baseline
            .join(
                y_baseline.lazy().rename({target_col: "baseline"}),
                on=idx_cols,
                how="left",
            )
            # Join with uplift
            .join(uplift.lazy(), on=entity_col)
            # Set default `use` and `best_plan`
            .with_columns(
                pl.when(pl.col(f"{objective}__uplift_pct") >= 0)
                .then("ai")
                .otherwise("baseline")
                .alias("use"),
                pl.when(pl.col(f"{objective}__uplift_pct") >= 0)
                .then(pl.col("forecast"))
                .otherwise(pl.col("baseline"))
                .alias("best_plan"),
            )
            # Add fh column
            .groupby(entity_col, maintain_order=True)
            .agg(pl.all(), pl.col(time_col).rank("ordinal").cast(pl.Int64).alias("fh"))
            .pipe(lambda df: df.explode(df.columns[1:]))
            .select([entity_col, "time", "fh", "best_plan", "use"])
            .collect()
        )

        # Export best_plan artifact
        write(best_plan, object_path=output_path)
    except Exception as err:
        raise err
    finally:
        pl.toggle_string_cache(False)
        logger.info("Best plan created and exported")


def _make_output_path(objective_id: int, updated_at: datetime, prefix: str) -> str:
    timestamp = datetime.strftime(updated_at, "%Y%m%dT%X").replace(":", "")
    path = f"artifacts/{objective_id}/{timestamp}/{prefix}.parquet"
    return path


def _update_objective(
    objective_id: int,
    updated_at: datetime,
    outputs: Mapping[str, Any],
    status: str,
    msg: str,
) -> Objective:
    # Establish connection
    engine = create_sql_engine()
    with Session(engine) as session:
        # Select rows with specific report_id only
        query = select(Objective).where(Objective.id == objective_id)
        objective = session.exec(query).one()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective not found")
        # Update the fields based on the objective_id
        objective.outputs = outputs
        objective.updated_at = updated_at
        objective.status = status
        objective.msg = msg

        # Add, commit and refresh the updated object
        session.add(objective)
        session.commit()
        session.refresh(objective)
        return objective


@stub.function(
    memory=5120,
    cpu=8.0,
    timeout=3600,  # 60 mins
)
def run_forecast(
    user_id: int,
    objective_id: int,
    panel_path: str,
    storage_tag: str,
    bucket_name: str,
    target_col: str,
    entity_cols: List[str],
    min_lags: int,
    max_lags: int,
    fh: int,
    freq: str,
    sp: int,
    n_splits: int,
    feature_cols: Optional[List[str]] = None,
    holiday_regions: Optional[List[str]] = None,
    objective: Optional[str] = "mae",
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
            _make_output_path, objective_id=objective_id, updated_at=updated_at
        )

        # 4. Read y from storage
        # Entity cols are merged into a single column in preprocess
        entity_col = "__".join(entity_cols)
        # Time column is renamed to "time" in preprocess
        time_col = "time"
        select_cols = [entity_col, time_col, target_col]
        if feature_cols is not None:
            select_cols = [*select_cols, *feature_cols]
        y_panel = read(
            object_path=panel_path,
            columns=select_cols,
        )

        # 5. Run automl flow
        automl_flow = modal.Function.lookup("functime-forecast-automl", "flow")
        if feature_cols is not None and len(feature_cols) > 0:
            X = y_panel.select([entity_col, time_col, *feature_cols])
            y = y_panel.select(pl.exclude(feature_cols))
        else:
            X = None
            y = y_panel

        y, outputs = automl_flow.call(
            y=y,
            min_lags=min_lags,
            max_lags=max_lags,
            fh=fh,
            freq=freq,
            n_splits=n_splits,
            holiday_regions=holiday_regions,
            X=X,
        )
        outputs["y"] = make_path(prefix="y")

        write(y, object_path=make_path(prefix="y"))

        # 6. Compute uplift
        # NOTE: Only compares against BEST MODEL
        if baseline_path:
            # Read baseline from storage
            y_baseline = read(object_path=baseline_path)
        else:
            y_baseline_backtest = (
                outputs["backtests"][baseline_model]
                .groupby([entity_col, time_col])
                .agg(pl.mean(target_col))
            )
            y_baseline_forecast = outputs["forecasts"][baseline_model]
            y_baseline = pl.concat([y_baseline_backtest, y_baseline_forecast])

        if inventory_path:
            inventory = read(
                bucket_name=bucket_name,
                object_path=inventory_path,
                file_ext="parquet",
                **storage_creds,
            )
            outputs["inventory"] = make_path(prefix="inventory")
            write(inventory, object_path=outputs["inventory"])
        else:
            outputs["inventory"] = None

        # Score baseline compared to best scores
        uplift_flow = modal.Function.lookup("functime-forecast-uplift", "flow")
        kwargs = {"y": y, "y_baseline": y_baseline}
        baseline_scores, baseline_metrics, uplift = uplift_flow.call(
            outputs["scores"]["best_models"],
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

        # 9. Create and export best plan
        output_path = make_path(prefix="best_plan")
        create_best_plan.call(
            output_json=outputs,
            objective=objective,
            read=read,
            write=write,
            output_path=output_path,
        )
        outputs["best_plan"] = output_path

        # 10. Run rolling forecast
        compute_rolling_forecast.call(
            output_json=outputs,
            objective_id=objective_id,
            updated_at=updated_at,
            read=read,
            write=write,
        )

        # 11. Run rolling uplift
        compute_rolling_uplift.call(
            output_json=outputs,
            objective_id=objective_id,
            updated_at=updated_at,
            sp=sp,
            read=read,
            write=write,
        )

    except (Exception, pl.PolarsPanicError) as exc:
        updated_at = datetime.utcnow()
        outputs = None
        status = "FAILED"
        msg = repr(exc)
        logger.exception(exc)
    finally:
        pl.toggle_string_cache(False)
        _update_objective(
            objective_id=objective_id,
            updated_at=updated_at,
            outputs=json.dumps(outputs),
            status=status,
            msg=msg,
        )


def _get_all_objectives() -> List[Objective]:
    engine = create_sql_engine()
    with Session(engine) as session:
        query = select(Objective)
        objectives = session.exec(query).all()
        if not objectives:
            raise HTTPException(status_code=404, detail="Objective not found")
        return objectives


def get_user(user_id: str) -> User:
    engine = create_sql_engine()
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
    cpu=8.0,
    timeout=3600,
    schedule=modal.Cron("0 17 * * *"),  # run at 1am daily (utc 5pm)
)
def flow():
    logger.info("Flow started")
    # 1. Get all objectives
    objectives = _get_all_objectives()

    futures = {}
    for objective in objectives:
        logger.info(f"Checking objective: {objective.id}")
        fields = json.loads(objective.fields)
        sources = json.loads(objective.sources)

        # 2. Get user and source
        user = get_user(objective.user_id)
        panel_source = get_source(sources["panel"])["source"]
        source_fields = json.loads(panel_source.data_fields)
        freq = source_fields["freq"]

        # 3. Check freq from source for schedule
        duration = FREQ_TO_DURATION[freq]
        updated_at = objective.updated_at.replace(microsecond=0)
        if duration == "1mo":
            new_dt = updated_at + relativedelta(months=1)
            run_dt = datetime(new_dt.year, new_dt.month, 1)
        else:
            run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
        logger.info(f"Next run at: {run_dt}")

        # 4. Run forecast flow
        current_datetime = datetime.now().replace(microsecond=0)
        if (current_datetime >= run_dt) or objective.status == "FAILED":
            # Get staging path for each source
            panel_path = panel_source.output_path
            if sources["baseline"]:
                baseline_path = get_source(sources["baseline"])["source"].output_path
            else:
                baseline_path = None
            if sources["inventory"]:
                inventory_path = get_source(sources["inventory"])["source"].output_path
            else:
                inventory_path = None

            holiday_regions = fields["holiday_regions"]
            if holiday_regions is not None:
                holiday_regions = [
                    SUPPORTED_COUNTRIES[country]
                    for country in fields["holiday_regions"]
                ]

            # Set quantity as target if transaction type
            target_col = source_fields.get(
                "target_col", source_fields.get("quantity_col")
            )
            entity_cols = source_fields["entity_cols"]
            if panel_source.dataset_type == "transaction":
                # Set product as entity if transaction type
                entity_cols = [source_fields["product_col"], *entity_cols]

            # Spawn forecast flow for objective
            futures[objective.id] = run_forecast.spawn(
                user_id=objective.user_id,
                objective_id=objective.id,
                panel_path=panel_path,
                storage_tag=user.storage_tag,
                bucket_name=user.storage_bucket_name,
                target_col=target_col,
                entity_cols=entity_cols,
                min_lags=fields["min_lags"],
                max_lags=fields["max_lags"],
                fh=fields["fh"],
                freq=SUPPORTED_FREQ[freq],
                sp=FREQ_TO_SP[freq],
                n_splits=fields["n_splits"],
                feature_cols=source_fields["feature_cols"],
                holiday_regions=holiday_regions,
                objective=SUPPORTED_ERROR_TYPE[fields["error_type"]],
                baseline_model=fields.get("baseline_model", None),
                baseline_path=baseline_path,
                inventory_path=inventory_path,
            )

    # 5. Get future for each objective
    for objective_id, future in futures.items():
        logger.info(f"Running forecast flow for objective: {objective_id}")
        future.get()
        logger.info(f"Forecast flow completed for objective: {objective_id}")

    logger.info("Flow completed")


@stub.local_entrypoint
def test(user_id: str = "indexhub-demo-dev"):
    # Objective
    objective_id = 1
    fields = {
        "sources": {
            "panel": 1,
            "baseline": None,
            "inventory": 2,
        },
        "error_type": "mae",
        "min_lags": 6,
        "max_lags": 6,
        "fh": 3,
        "n_splits": 3,
        "holiday_regions": ["AU"],
        "baseline_model": "snaive",
    }

    source_fields = {
        "target_col": "trips_in_000s",
        "entity_cols": ["country", "territory", "state"],
        "freq": "1mo",
        "agg_method": "sum",
        "impute_method": 0,
    }

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo-dev"

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

    run_forecast.call(
        user_id=user_id,
        objective_id=objective_id,
        panel_path=panel_path,
        storage_tag=storage_tag,
        bucket_name=storage_bucket_name,
        target_col=source_fields["target_col"],
        entity_cols=source_fields["entity_cols"],
        min_lags=fields["min_lags"],
        max_lags=fields["max_lags"],
        fh=fields["fh"],
        freq=source_fields["freq"],
        sp=FREQ_TO_SP[source_fields["freq"]],
        n_splits=fields["n_splits"],
        holiday_regions=fields["holiday_regions"],
        objective=fields["error_type"],  # default is mae
        agg_method=source_fields["agg_method"],  # default is mean
        impute_method=source_fields["impute_method"],  # default is 0
        baseline_model=fields["baseline_model"],  # default is snaive
        baseline_path=baseline_path,
        inventory_path=inventory_path,
    )
