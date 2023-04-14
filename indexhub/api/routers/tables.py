from typing import Mapping

import polars as pl
from fastapi import APIRouter
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()

# POLICY RESULT TABLES
def _get_forecast_results(
    outputs: Mapping[str, str],
    user: User,
) -> pl.DataFrame:
    pl.toggle_string_cache(True)

    # Get credentials
    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )
    read = SOURCE_TAG_TO_READER[user.storage_tag]

    # Read artifacts
    best_model = outputs["best_model"]
    forecasts = read(
        bucket_name=user.storage_bucket_name,
        object_path=outputs["forecasts"][best_model],
        file_ext="parquet",
        **storage_creds
    ).lazy()
    quantiles = read(
        bucket_name=user.storage_bucket_name,
        object_path=outputs["quantiles"][best_model],
        file_ext="parquet",
        **storage_creds
    ).lazy()
    baseline = read(
        bucket_name=user.storage_bucket_name,
        object_path=outputs["baseline"],
        file_ext="parquet",
        **storage_creds
    ).lazy()

    index_cols = forecasts.columns[:-1]
    target_col = forecasts.columns[-1]

    # Pivot quantiles
    quantiles = (
        quantiles.filter(pl.col("quantile").is_in([10, 90]))
        .collect(streaming=True)
        .pivot(values=target_col, index=index_cols, columns="quantile")
        .select([*index_cols, pl.all().exclude(index_cols).prefix("forecast_")])
        .lazy()
    )

    # Concat dfs
    recommendation = (
        forecasts.rename({target_col: "forecast"})
        .join(baseline.rename({target_col: "baseline"}), on=index_cols, how="left")
        .join(quantiles, on=index_cols, how="left")
        .with_columns(
            pl.col("time").rank("ordinal").over(index_cols[:-1]).alias("fh"),
        )
    )

    pl.toggle_string_cache(False)
    return recommendation


POLICY_TAG_TO_GETTER = {"forecast": _get_forecast_results}


@router.get("/tables/{policy_id}")
def get_policy_table(policy_id: str, page: int, display_n: int = 5):
    if page < 1:
        raise ValueError("`page` must be an integer greater than 0")
    with Session(engine) as session:
        policy = get_policy(policy_id)
        getter = POLICY_TAG_TO_GETTER[policy.tag]
        user = session.get(User, policy.user_id)
        table = getter(
            policy.outputs, user
        )  # TODO: Cache using an in memory key-value store
    start = display_n * (page - 1)
    end = display_n * page
    filtered_table = table[start:end]
    return filtered_table.to_json()
