import json
from datetime import datetime
from functools import partial
from typing import Any, List, Mapping

import polars as pl
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret


def update_rolling_forecast(
    plan: pl.LazyFrame,
    rolling_forecast: pl.LazyFrame,
):
    entity_col = rolling_forecast.columns[0]
    dtypes = rolling_forecast.select([entity_col, "time", "fh", "plan"]).dtypes

    plan = (
        plan.rename({"entity": entity_col, "plan": "revised_plan"}).select(
            [entity_col, "time", "fh", "revised_plan"]
        )
        # Coerce dtypes
        .pipe(
            lambda df: df.with_columns(
                pl.col(col).cast(dtypes[i]).keep_name()
                for i, col in enumerate(df.columns)
            )
        )
    )

    # Update rolling forecast
    updated_rolling_forecast = (
        rolling_forecast.join(plan, on=[entity_col, "time", "fh"], how="left")
        .with_columns(
            [
                # Replace existing plan in rolling forecast
                pl.col("revised_plan").alias("plan"),
                # Replace existing residual_plan in rolling forecast
                (pl.col("revised_plan") - pl.col("actual")).alias("residual_plan"),
            ]
        )
        .drop("revised_plan")
    )
    return updated_rolling_forecast


def _execute_forecast_plan(
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
            .rename({"use": "updated_use"})
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

    # Read best plan
    revised_plan = (
        read(object_path=outputs["best_plan"])
        .lazy()
        .pipe(lambda df: df.rename({df.columns[0]: "entity", "best_plan": "plan"}))
    )

    if updated_plans is not None:
        revised_plan = (
            revised_plan
            # Join with updated plan
            .join(updated_plans, on=["entity", "fh"], how="left").with_columns(
                [
                    # If "use" is null, use default
                    pl.when(pl.col("updated_use").is_null()).then(pl.col("plan"))
                    # Otherwise, override default
                    .otherwise(
                        pl.when(pl.col("updated_use") == "override")
                        .then(pl.col("override"))
                        .otherwise(
                            pl.when(pl.col("updated_use") == "ai")
                            .then(pl.col("ai"))
                            .otherwise(pl.col("baseline"))
                        )
                    ).alias("plan"),
                    pl.when(pl.col("updated_use").is_null())
                    .then(pl.col("use"))
                    .otherwise(pl.col("updated_use"))
                    .alias("use"),
                ]
            )
        )

    revised_plan = revised_plan.select(["entity", "time", "fh", "plan", "use"])

    # Export to parquet
    timestamp = outputs["best_plan"].split("/")[2]
    path = f"artifacts/{objective_id}/{timestamp}/plan.parquet"
    write = STORAGE_TAG_TO_WRITER[user.storage_tag]
    write(
        data=revised_plan.collect(),
        bucket_name=user.storage_bucket_name,
        object_path=path,
        **storage_creds,
    )

    # Export to csv
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_path = f"exports/{objective_id}/plan_{timestamp}.csv"
    write(
        data=revised_plan.collect(),
        bucket_name=user.storage_bucket_name,
        object_path=csv_path,
        file_ext="csv",
        **storage_creds,
    )

    # Update rolling forecast
    path = f"artifacts/{objective_id}/rolling_forecasts.parquet"
    rolling_forecast = read(object_path=path).lazy()
    updated_rolling_forecast = update_rolling_forecast(
        plan=revised_plan, rolling_forecast=rolling_forecast
    )
    write(
        data=updated_rolling_forecast.collect(),
        bucket_name=user.storage_bucket_name,
        object_path=path,
        **storage_creds,
    )

    return csv_path


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
            json.loads(objective.outputs),
            user,
            objective_id,
            params.updated_plans,
        )
        pl.toggle_string_cache(False)

    return {"path": path}
