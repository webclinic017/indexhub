import modal
import polars as pl
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.policy import Policy
from indexhub.api.services.io import read_data_from_s3, write_data_to_s3
from indexhub.deployment import IMAGE

stub = modal.Stub(name="rolling", image=IMAGE)


def get_updated_at(policy_id: str):
    # Establish connection
    with Session(engine) as session:
        # Select row with specific policy_id only
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        # Return from the "updated_at" column in policy
        return policy.updated_at


@stub.function()
def concat_latest(cached: pl.DataFrame, latest: pl.DataFrame):
    rolling = (
        pl.concat([cached, latest]).select(
            [
                pl.all().exclude(["forecast", "actual", "residual", "best_model"]),
                "forecast",
                "actual",
                "residual",
                "best_model",
            ]
        )
        # Sort by time_col, entity_col, updated_at
        .pipe(lambda df: df.sort(df.columns[:3]))
    )
    return rolling


@stub.function(
    secrets=[
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("aws-credentials"),
    ]
)
def flow(output_json: str, s3_bucket: str, policy_id: int):
    # Unpack metadata from output_json
    best_model = output_json["best_model"]
    path = output_json["forecasts"][best_model]
    # Get the updated at based on policy_id (sqlmodel)
    dt = get_updated_at(policy_id).replace(microsecond=0)

    # Read forecast artifacts from s3 and postproc
    forecast = read_data_from_s3(s3_bucket, path, file_ext="parquet").pipe(
        # Rename target_col to "forecast"
        lambda df: df.rename({df.columns[-1]: "forecast"}).with_columns(
            [
                # Assign updated_at column
                pl.lit(dt).alias("updated_at"),
                # Assign best_model column
                pl.lit(best_model).alias("best_model"),
                # Assign fh column
                pl.col("time").rank("ordinal").over(df.columns[0]).alias("fh"),
                # Defensive cast - to avoid global string cache during concat
                pl.col(pl.Categorical).cast(pl.Utf8),
            ]
        )
    )

    # Read actual from y panel in s3 and postproc
    actual = read_data_from_s3(
        s3_bucket, output_json["panel"], file_ext="parquet"
    ).pipe(
        # Defensive cast - to avoid global string cache during concat
        lambda df: df.with_columns([pl.col(pl.Categorical).cast(pl.Utf8)]).rename(
            # Rename target_col to "actual"
            {df.columns[-1]: "actual"}
        )
    )

    # Combine forecast and actual artifacts
    latest_forecasts = forecast.join(
        actual, on=forecast.columns[:2], how="left"
    ).with_columns(
        [(pl.col("forecast") - pl.col("actual")).alias("residual").cast(pl.Float32)]
    )

    try:
        cached_forecasts = read_data_from_s3(
            s3_bucket,
            object_path=f"artifacts/{policy_id}/rolling_forecasts.parquet",
            file_ext="parquet",
        )
        # Get the latest `updated_at` date from cached rolling forecast
        last_dt = cached_forecasts.get_column("updated_at").unique().max()
        if dt > last_dt:
            # Concat latest forecasts artifacts with cached rolling forecasts
            rolling_forecasts = concat_latest(cached_forecasts, latest_forecasts)
            # Export merged data as rolling forecasts artifact
            write_data_to_s3(
                rolling_forecasts,
                s3_bucket,
                f"artifacts/{policy_id}/rolling_forecasts.parquet",
            )

    except HTTPException as err:
        if (
            err.status_code == 400
            and err.detail == "Invalid S3 path when reading from source"
        ):
            # Export latest forecasts as initial rolling forecasts artifact
            write_data_to_s3(
                latest_forecasts,
                s3_bucket,
                f"artifacts/{policy_id}/rolling_forecasts.parquet",
            )


@stub.local_entrypoint()
def main():
    """Combines the forecasts artifacts with actual (y) and export rolling forecasts (artifacts) to s3"""
    output_json = {
        "best_model": "naive",
        "forecasts": {
            "ensemble[automl]": "artifacts/1/20230412T111037//forecasts__ensemble[automl].parquet",
            "lightgbm__regression": "artifacts/1/20230412T111037/forecasts__lightgbm__regression.parquet",
            "lightgbm__regression_l1": "artifacts/1/20230412T111037/forecasts__lightgbm__regression_l1.parquet",
            "lightgbm__weighted__regression_l1": "artifacts/1/20230412T111037/forecasts__lightgbm__weighted__regression_l1.parquet",
            "naive": "artifacts/1/20230412T111037/forecasts__naive.parquet",
            "snaive": "artifacts/1/20230412T111037/forecasts__snaive.parquet",
            "zero_inflated__lightgbm__regression": "artifacts/1/20230412T111037/forecasts__zero_inflated__lightgbm__regression.parquet",
            "zero_inflated__lightgbm__regression_l1": "artifacts/1/20230412T111037/forecasts__zero_inflated__lightgbm__regression_l1.parquet",
        },
        "panel": "artifacts/1/20230412T111037/y.parquet",
    }
    policy_id = 1
    s3_bucket = "indexhub-demo"
    flow.call(output_json, s3_bucket, policy_id)
