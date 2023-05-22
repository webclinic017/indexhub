import json
from functools import partial

import polars as pl
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.plans import update_rolling_forecast
from indexhub.api.services.io import SOURCE_TAG_TO_READER, STORAGE_TAG_TO_WRITER
from indexhub.api.services.secrets_manager import get_aws_secret


@router.post("/upload/upload_plan/{objective_id}/{filename}/{csv_content}")
def upload_plan(objective_id: str, filename: str, csv_content: str):
    pl.toggle_string_cache(True)
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        user = session.get(User, objective.user_id)
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
        write = partial(
            STORAGE_TAG_TO_WRITER[user.storage_tag],
            bucket_name=user.storage_bucket_name,
            **storage_creds,
        )

        updated_plan = pl.read_csv(csv_content)

        # Export csv to s3
        csv_path = f"exports/{objective_id}/{filename}"
        write(
            data=updated_plan,
            object_path=csv_path,
        )

        # Read best plan
        outputs = json.loads(objective.outputs)
        best_plan = read(object_path=outputs["best_plan"]).lazy()

        # Compare to the updated plan to update "use"
        entity_col, time_col = best_plan.columns[:2]
        dtypes = best_plan.select([entity_col, time_col]).dtypes
        revised_plan = (
            best_plan.rename({entity_col: "entity"})
            .join(
                updated_plan.lazy()
                # Coerce dtypes
                .with_columns(
                    pl.col("entity").cast(dtypes[0]),
                    pl.col(time_col).str.strptime(pl.Date).cast(dtypes[1]),
                ),
                on=["entity", "time"],
                how="left",
            )
            .with_columns(
                [
                    # If plan != best_plan, set use = "override"
                    pl.when(pl.col("plan") != pl.col("best_plan"))
                    .then("override")
                    .otherwise(pl.col("use"))
                    .alias("use"),
                    # Update plan
                    pl.when(pl.col("plan") != pl.col("best_plan"))
                    .then(pl.col("plan"))
                    .otherwise(pl.col("best_plan"))
                    .alias("plan"),
                ]
            )
            .select(["entity", time_col, "fh", "plan", "use"])
        )

        # Export to plan.parquet
        timestamp = outputs["best_plan"].split("/")[2]
        path = f"artifacts/{objective_id}/{timestamp}/plan.parquet"
        write(
            data=revised_plan.collect(),
            object_path=path,
        )

        # Update rolling forecast
        path = f"artifacts/{objective_id}/rolling_forecasts.parquet"
        rolling_forecast = read(object_path=path).lazy()
        updated_rolling_forecast = update_rolling_forecast(
            plan=revised_plan, rolling_forecast=rolling_forecast
        )
        write(
            data=updated_rolling_forecast.collect(),
            object_path=path,
        )

    pl.toggle_string_cache(False)
    return csv_path
