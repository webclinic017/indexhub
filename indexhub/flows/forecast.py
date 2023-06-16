import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from functools import partial
from typing import Any, Callable, List, Mapping, Optional

import modal
import pandas as pd
import polars as pl
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from functime.metrics.multi_objective import score_forecast, summarize_scores
from sqlmodel import Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.objective import Objective
from indexhub.api.routers.sources import get_source
from indexhub.api.routers.stats import FREQ_TO_SP
from indexhub.api.routers.users import get_user_by_id
from indexhub.api.schemas import (
    FREQ_TO_DURATION,
    SUPPORTED_BASELINE_MODELS,
    SUPPORTED_COUNTRIES,
    SUPPORTED_ERROR_TYPE,
    SUPPORTED_FREQ,
)
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.modal_stub import stub


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


env_prefix = os.environ.get("ENV_NAME", "dev")
IMAGE = modal.Image.from_name(f"{env_prefix}-indexhub-image")


def _compute_rolling_forecast(
    output_json: Mapping[str, Any],
    objective_id: int,
    updated_at: datetime,
    read: Callable,
    write: Callable,
):
    logger.info("Computing rolling forecast...")
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
    forecast = read(object_path=output_json["forecasts"]["best_models"]).pipe(
        # Rename target_col to "ai"
        lambda df: df.rename({df.columns[-1]: "ai"}).with_columns(
            [
                # Assign updated_at column
                pl.lit(dt).alias("updated_at"),
                # Assign best_model column
                pl.col(df.columns[0]).map_dict(best_models).alias("best_model"),
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

    # Read baseline from y_baseline panel in s3 and postproc
    baseline = read(object_path=output_json["y_baseline"]).pipe(
        lambda df: df.rename(
            # Rename target_col to "baseline"
            {df.columns[-1]: "baseline"}
        )
    )

    # Read best plan from best_plan panel in s3 and postproc
    best_plan = read(object_path=output_json["best_plan"]).select(
        pl.exclude("use").shrink_dtype()
    )

    # Combine forecast and actual artifacts
    idx_cols = forecast.columns[:2]
    latest_forecasts = (
        forecast.join(actual, on=idx_cols, how="left")
        .join(
            baseline,
            on=idx_cols,
            how="left",
        )
        .join(best_plan, on=idx_cols, how="left")
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
        .select([pl.all().exclude(selected_cols), *selected_cols])
    )

    path = f"artifacts/{objective_id}/rolling_forecasts.parquet"
    try:
        cached_forecasts = read(object_path=path)
        # Get the latest `updated_at` date from cached rolling forecast
        last_dt = cached_forecasts.get_column("updated_at").unique().max()
        if dt > last_dt:
            # Concat latest forecasts artifacts with cached rolling forecasts
            rolling_forecasts = (
                pl.concat([cached_forecasts, latest_forecasts])
                .join(
                    actual.rename({"actual": "updated_actual"}), on=idx_cols, how="left"
                )
                # Coalesce actual to get the first non-null value
                .pipe(
                    lambda df: df.with_columns(
                        pl.coalesce(df["actual"], df["updated_actual"]).alias("actual")
                    )
                )
                .drop("updated_actual")
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
                        (pl.col("plan") - pl.col("actual")).alias("residual_plan"),
                    ]
                )
                .select([pl.all().exclude(selected_cols), *selected_cols])
                # Sort by entity_col, time_col, updated_at
                .pipe(lambda df: df.sort(df.columns[:3]))
            )
            # Export merged data as rolling forecasts artifact
            write(
                rolling_forecasts,
                object_path=path,
            )
    except HTTPException as err:
        if (
            err.status_code == 400
            and err.detail == "Invalid S3 path when reading from source"
        ):
            # Export latest forecasts as initial rolling forecasts artifact
            write(
                latest_forecasts,
                object_path=path,
            )
    finally:
        logger.info("Rolling forecast exported.")


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


def _compute_rolling_uplift(
    output_json: Mapping[str, Any],
    objective_id: int,
    updated_at: datetime,
    sp: int,
    read: Callable,
    write: Callable,
):
    logger.info("Computing rolling uplift...")
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

    path = f"artifacts/{objective_id}/rolling_uplift.parquet"
    try:
        cached_uplift = read(object_path=path)

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
                object_path=path,
            )
    except HTTPException as err:
        if (
            err.status_code == 400
            and err.detail == "Invalid S3 path when reading from source"
        ):
            # Export latest uplift as initial rolling uplift artifact
            write(latest_uplift, object_path=path)
    finally:
        logger.info("Rolling uplift exported.")


def _create_best_plan(
    output_json: Mapping[str, Any],
    objective: str,
    read: Callable,
) -> pl.DataFrame:
    logger.info("Creating best plan...")
    # Read artifacts
    forecast = read(object_path=output_json["forecasts"]["best_models"])
    y_baseline = read(object_path=output_json["y_baseline"])
    uplift = read(object_path=output_json["uplift"])
    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    # Create best plan
    best_plan = (
        forecast.lazy()
        .rename({target_col: "ai"})
        # Join with baseline
        .join(
            y_baseline.lazy().rename({target_col: "baseline"}),
            on=idx_cols,
            how="left",
        )
        # Join with uplift
        .join(uplift.lazy(), on=entity_col)
        # Use AI forecast if positive uplift otherwise baseline as best plan
        .with_columns(
            pl.when(pl.col(f"{objective}__uplift_pct") >= 0)
            .then("ai")
            .otherwise("baseline")
            .alias("use"),
            pl.when(pl.col(f"{objective}__uplift_pct") >= 0)
            .then(pl.col("ai"))
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

    logger.info("Best plan created.")
    return best_plan


# def _load_integrations(
#     user_id: str, entity_col: str, entities: List[str], freq: str, read: Callable
# ):
#     logger.info("Loading integrations...")
#     integrations_df = None
#     # 1. Load user's integrations
#     engine = create_sql_engine()
#     with Session(engine) as session:
#         query = select(User).where(User.id == user_id)
#         user = session.exec(query).first()
#         if user.integration_ids:
#             integration_ids = json.loads(user.integration_ids)
#             query = select(Integration).where(Integration.id.in_(integration_ids))
#             integrations = session.exec(query).all()
#         else:
#             integrations = None

#     if integrations:
#         futures = []
#         for integration in integrations:
#             # 2. Read integration from feature store
#             fields = json.loads(integration.fields)
#             outputs = json.loads(integration.outputs)
#             bucket_name = outputs["bucket_name"]
#             raw_panel = read(
#                 bucket_name=bucket_name, object_path=outputs["object_path"]
#             ).to_arrow()

#             # 3. Spawn exogenous flow
#             # flow = modal.Function.lookup("tsdata-exogenous", "process_integration")
#             # TODO: Will come from functime instead
#             futures.append(
#                 flow.spawn(
#                     raw_panel=raw_panel,
#                     ticker=integration.ticker,
#                     entities=entities,
#                     # Use user selected freq
#                     freq=freq,
#                     # Use default agg_method for integration
#                     agg_method=fields.get("agg_method", "sum"),
#                     # Use default impute_method for integration
#                     impute_method=fields.get("impute_method", "ffill"),
#                 )
#             )

#         # 4. Gather futures
#         integrations_dfs = []
#         for future in futures:
#             try:
#                 integrations_dfs.append(
#                     pl.from_arrow(future.get()).pipe(
#                         lambda df: df.rename({df.columns[0]: entity_col})
#                     )
#                 )
#             except Exception as err:
#                 # Skip and log exception if failed to process integration
#                 logger.exception(
#                     f"Failed to load integration {integration.ticker}: {err}"
#                 )

#         # 5. Join integrations by entity and time columns
#         if len(integrations_dfs) > 0:
#             integrations_df = reduce(
#                 lambda x, y: x.join(y, on=x.columns[:2], how="outer"),
#                 integrations_dfs,
#             ).select(
#                 [
#                     entity_col,
#                     "time",
#                     # Add prefix
#                     pl.exclude([entity_col, "time"]).prefix("exog__"),
#                 ]
#             )

#     logger.info("Integrations loaded.")
#     return integrations_df


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


def _compare_scores(
    scores: pl.DataFrame,
    scores_baseline: pl.DataFrame,
) -> pl.DataFrame:
    """Given two DataFrame of metrics (columns) across entities,
    return DataFrame with difference in levels and percent between scores and baseline scores.
    """
    # Select metrics column
    entity_col = scores.columns[0]
    score_cols = scores.columns[1:]
    # Defensive sort
    scores = scores.sort(entity_col)
    scores_baseline = scores_baseline.sort(entity_col)
    scores_values = scores.select(score_cols)
    scores_baseline_values = scores_baseline.select(score_cols)
    # Uplift
    scores_diff = scores_values - scores_baseline_values
    scores_diff_pct = (scores_diff) / scores_baseline_values
    uplift = pl.concat(
        [
            scores.select(entity_col),
            scores_diff.select(pl.all().suffix("__uplift")),
            scores_diff_pct.select(pl.all().suffix("__uplift_pct")),
        ],
        how="horizontal",
    )
    return uplift


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

        # 4. Read y from storage with selected cols
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

        # 5. Create X from features
        if feature_cols is not None and len(feature_cols) > 0:
            X = y_panel.select([entity_col, time_col, *feature_cols])
            y = y_panel.select(pl.exclude(feature_cols))
        else:
            X = None
            y = y_panel

        # 6. Load user subscribed integrations and append integrations to X
        # NOTE: Temp disable integrations, pending fixes from fuzzy match
        # integrations_df = _load_integrations(
        #     user_id=user_id,
        #     entity_col=entity_col,
        #     entities=y.get_column(entity_col).unique().to_list(),
        #     freq=freq,
        #     read=read,
        # )
        integrations_df = None

        if integrations_df is not None:
            dtypes = y.select([entity_col, time_col]).dtypes
            # Coerce dtypes
            integrations_df = integrations_df.with_columns(
                pl.col(entity_col).cast(dtypes[0]), pl.col(time_col).cast(dtypes[1])
            )
            # Join with X
            if X is not None:
                X = X.join(integrations_df, on=[entity_col, time_col], how="left")
            else:
                X = y.join(integrations_df, on=[entity_col, time_col], how="left").drop(
                    target_col
                )

        # 7. Run automl flow
        env_prefix = os.environ.get("ENV_NAME", "dev")
        automl_flow = modal.Function.lookup(
            f"{env_prefix}-functime-flows", "run_automl_flow"
        )

        # Convert X to pyarrow
        if X is not None:
            X = X.to_arrow()

        outputs = automl_flow.call(
            y=y.to_arrow(),
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

        # 8. Compute uplift
        # NOTE: Only compares against BEST MODEL
        if baseline_path:
            # Read baseline from storage
            y_baseline = read(object_path=baseline_path)
        else:
            # Read baseline from selected baseline model
            y_baseline_backtest = (
                pl.from_arrow(outputs["backtests"][baseline_model])
                .groupby([entity_col, time_col])
                .agg(pl.mean(target_col))
            )
            y_baseline_forecast = pl.from_arrow(outputs["forecasts"][baseline_model])
            y_baseline = pl.concat([y_baseline_backtest, y_baseline_forecast])

        # Score baseline compared to best scores
        dates = (
            pl.from_arrow(outputs["backtests"]["best_models"])
            .get_column(time_col)
            .unique()
        )
        baseline_scores = score_forecast(
            y,
            y_baseline
            # Filter backtest and fh period
            .filter(pl.col(time_col).is_in(dates)),
            y_train=y,
        )
        baseline_metrics = asdict(summarize_scores(baseline_scores))
        uplift = _compare_scores(
            baseline_scores, pl.from_arrow(outputs["scores"]["best_models"])
        )

        # Append paths to outputs
        outputs["y_baseline"] = make_path(prefix="y_baseline")
        outputs["baseline__scores"] = make_path(prefix="baseline__scores")
        outputs["baseline__metrics"] = baseline_metrics
        outputs["uplift"] = make_path(prefix="uplift")

        # Export to artifacts
        write(
            y_baseline
            # Cast entity col to categorical
            .pipe(
                lambda df: df.with_columns(pl.col(df.columns[0]).cast(pl.Categorical))
            ),
            object_path=outputs["y_baseline"],
        )
        write(baseline_scores, object_path=outputs["baseline__scores"])
        write(uplift, object_path=make_path(prefix="uplift"))

        # 9. Export artifacts for each model
        for key in [
            "forecasts",
            "backtests",
            "residuals",
            "scores",
            "quantiles",
        ]:
            model_artifacts = outputs[key]
            for model, df in model_artifacts.items():
                output_path = make_path(prefix=f"{key}__{model}")
                write(
                    pl.from_arrow(df)
                    # Cast entity col to categorical
                    .pipe(
                        lambda df: df.with_columns(
                            pl.col(df.columns[0]).cast(pl.Categorical)
                        )
                    ),
                    object_path=output_path,
                )
                outputs[key][model] = output_path

        # 10. Export statistics
        for key, df in outputs["statistics"].items():
            output_path = make_path(prefix=f"statistics__{key}")
            write(
                pl.from_arrow(df)
                # Cast entity col to categorical
                .pipe(
                    lambda df: df.with_columns(
                        pl.col(df.columns[0]).cast(pl.Categorical)
                    )
                ),
                object_path=output_path,
            )
            outputs["statistics"][key] = output_path

        # 11. Create and export best plan
        best_plan = _create_best_plan(
            output_json=outputs,
            objective=objective,
            read=read,
        )
        output_path = make_path(prefix="best_plan")
        write(best_plan, object_path=output_path)
        outputs["best_plan"] = output_path

        # 12. Run rolling forecast
        _compute_rolling_forecast(
            output_json=outputs,
            objective_id=objective_id,
            updated_at=updated_at,
            read=read,
            write=write,
        )

        # 13. Run rolling uplift
        _compute_rolling_uplift(
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


@stub.function(
    memory=5120,
    cpu=8.0,
    timeout=3600,
    schedule=modal.Cron("0 18 * * *"),  # run at 2am daily (utc 6pm)
)
def schedule_forecast():
    # 1. Get all objectives
    engine = create_sql_engine()
    with Session(engine) as session:
        query = select(Objective)
        objectives = session.exec(query).all()

    if objectives:
        futures = []
        for objective in objectives:
            logger.info(f"Checking objective: {objective.id}")
            fields = json.loads(objective.fields)
            sources = json.loads(objective.sources)

            # 2. Get user and source
            user = get_user_by_id(objective.user_id)
            panel_source = get_source(sources["panel"])["source"]
            source_fields = json.loads(panel_source.data_fields)
            freq = source_fields["freq"]

            # 3. Check freq from source for schedule
            duration = FREQ_TO_DURATION[freq]
            updated_at = objective.updated_at.replace(microsecond=0)
            if duration == "1mo":
                new_dt = updated_at + relativedelta(months=1)
                run_dt = datetime(new_dt.year, new_dt.month, 1)
            elif duration == "3mo":
                new_dt = updated_at + relativedelta(months=3)
                run_dt = datetime(new_dt.year, new_dt.month, 1)
            else:
                run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
            logger.info(f"Next run for {objective.id} at: {run_dt}")
            # 4. Run forecast flow
            current_datetime = datetime.now().replace(microsecond=0)
            if (current_datetime >= run_dt) or objective.status == "FAILED":
                # Get staging path for each source
                panel_path = panel_source.output_path
                if sources["baseline"]:
                    baseline_path = get_source(sources["baseline"])[
                        "source"
                    ].output_path
                else:
                    baseline_path = None

                if fields.get("holiday_regions", None) is not None:
                    holiday_regions = [
                        SUPPORTED_COUNTRIES[country]
                        for country in fields["holiday_regions"]
                    ]
                else:
                    holiday_regions = None

                if fields.get("baseline_model", None) is not None:
                    baseline_model = SUPPORTED_BASELINE_MODELS[fields["baseline_model"]]
                else:
                    baseline_model = None

                # Set quantity as target if transaction type
                target_col = source_fields.get(
                    "target_col", source_fields.get("quantity_col")
                )
                entity_cols = source_fields["entity_cols"]
                if panel_source.dataset_type == "transaction":
                    # Set product as entity if transaction type
                    entity_cols = [source_fields["product_col"], *entity_cols]

                # Spawn forecast flow for objective
                futures.append(
                    run_forecast.spawn(
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
                        feature_cols=source_fields.get("feature_cols", None),
                        holiday_regions=holiday_regions,
                        objective=SUPPORTED_ERROR_TYPE[fields["error_type"]],
                        baseline_model=baseline_model,
                        baseline_path=baseline_path,
                    )
                )

        for future in futures:
            future.get()


@stub.local_entrypoint()
def test(user_id: str = "indexhub-demo-dev"):
    # Objective
    objective_id = 9
    fields = {
        "direction": "Minimize",
        "description": "Minimize {target_col} mean absolute error (MAE) for {entity_cols}.",
        "error_type": "mean absolute error (MAE)",
        "fh": 6,
        "goal": 80,
        "holiday_regions": ["Australia"],
        "max_lags": 24,
        "min_lags": 12,
        "baseline_model": "Seasonal Naive",
        "n_splits": 3,
        "invoice_col": "",
        "product_col": "",
    }

    sources = {"panel": 92, "baseline": "", "inventory": "", "transaction": ""}

    source_fields = {
        "entity_cols": ["state"],
        "time_col": "time",
        "target_col": "trips_in_000s",
        "freq": "Monthly",
        "datetime_fmt": "Year-Month-Day",
    }

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo-dev"

    # Get staging path for each source
    panel_path = get_source(sources["panel"])["source"].output_path
    if sources["baseline"]:
        baseline_path = get_source(sources["baseline"])["source"].output_path
    else:
        baseline_path = None

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
        freq=SUPPORTED_FREQ[source_fields["freq"]],
        sp=FREQ_TO_SP[source_fields["freq"]],
        n_splits=fields["n_splits"],
        holiday_regions=fields["holiday_regions"],
        objective=fields["error_type"],  # default is mae
        baseline_model=SUPPORTED_BASELINE_MODELS[
            fields["baseline_model"]
        ],  # default is snaive
        baseline_path=baseline_path,
    )
