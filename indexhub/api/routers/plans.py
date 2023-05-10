import json
from functools import partial
from typing import Any, List, Mapping

import polars as pl
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.objectives import get_objective
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()


def _execute_forecast_plan(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    objective_id: str,
    updated_plans: List[Mapping[str, Any]],
):
    # Create dataframe from updated_plans
    if updated_plans is not None:
        updated_plans = (
            pl.DataFrame(updated_plans)
            .lazy()
            .with_columns(pl.col("entity").cast(pl.Categorical))
        )

    # Get credentials
    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )
    read = partial(
        SOURCE_TAG_TO_READER[user.storage_tag],
        bucket_name=user.storage_bucket_name,
        file_ext="parquet",
        **storage_creds,
    )

    # Read forecast and baseline artifacts
    best_model = outputs["best_model"]
    forecast = read(object_path=outputs["forecasts"][best_model])
    y_baseline = read(object_path=outputs["y_baseline"])

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    # Read rolling uplift and take the latest stats
    metric = SUPPORTED_ERROR_TYPE[fields["error_type"]]
    rolling_uplift = (
        read(object_path=f"artifacts/{objective_id}/rolling_uplift.parquet")
        .lazy()
        .sort(entity_col, "updated_at")
        .groupby(entity_col)
        .tail(1)
        .select(
            entity_col,
            (pl.col(f"{metric}__uplift_pct__rolling_mean").fill_nan(None) * 100).alias(
                "score__uplift_pct__rolling_mean"
            ),
        )
    )

    # Create forecast plans
    forecast_plans = (
        forecast.lazy()
        .rename({target_col: "forecast"})
        # Join with baseline
        .join(
            y_baseline.lazy().rename({target_col: "baseline"}), on=idx_cols, how="left"
        )
        # Join with rolling uplift
        .join(rolling_uplift, on=entity_col)
        # Set default `use_ai` and `use_benchmark`
        .with_columns(
            pl.when(pl.col("score__uplift_pct__rolling_mean") >= 0)
            .then(True)
            .otherwise(False)
            .alias("use_ai"),
            pl.when(pl.col("score__uplift_pct__rolling_mean") < 0)
            .then(True)
            .otherwise(False)
            .alias("use_benchmark"),
        )
        # Add fh column
        .groupby(entity_col, maintain_order=True)
        .agg(pl.all(), pl.col(time_col).rank("ordinal").cast(pl.Int64).alias("fh"))
        .pipe(lambda df: df.explode(df.columns[1:]))
        .rename({entity_col: "entity"})
        .with_columns(
            pl.when(pl.col("use_ai"))
            .then(pl.col("forecast"))
            .otherwise(pl.col("baseline"))
            .alias("forecast_plan")
        )
    )

    if updated_plans is not None:
        forecast_plans = (
            forecast_plans
            # Join with updated plan
            .join(updated_plans, on=["entity", "fh"], how="left").with_columns(
                # If "use" is null, use default
                pl.when(pl.col("use").is_null())
                .then(pl.col("forecast_plan"))
                # Otherwise, override default
                .otherwise(
                    pl.when(pl.col("use") == "override")
                    .then(pl.col("override"))
                    .otherwise(
                        pl.when(pl.col("use") == "ai")
                        .then(pl.col("forecast"))
                        .otherwise(pl.col("baseline"))
                    )
                )
                .alias("forecast_plan"),
            )
        )

    forecast_plans = forecast_plans.select(["entity", time_col, "forecast_plan"])

    # Export to parquet
    path = f"artifacts/{objective_id}/forecast_plan.parquet"
    write = STORAGE_TAG_TO_WRITER[user.storage_tag]
    write(
        data=forecast_plans.collect(streaming=True),
        bucket_name=user.storage_bucket_name,
        object_path=path,
        **storage_creds,
    )

    return path


TAGS_TO_GETTER = {"reduce_errors": _execute_forecast_plan}


class ExecutePlanParams(BaseModel):
    updated_plans: List[Mapping[str, Any]] = None


@router.post("/plans/{objective_id}")
def execute_plan(objective_id: str, params: ExecutePlanParams):
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        getter = TAGS_TO_GETTER[objective.tag]
        user = session.get(User, objective.user_id)
        pl.toggle_string_cache(True)
        path = getter(
            json.loads(objective.fields),
            json.loads(objective.outputs),
            user,
            objective_id,
            params.updated_plans,
        )
        pl.toggle_string_cache(False)

    return {"path": path}
