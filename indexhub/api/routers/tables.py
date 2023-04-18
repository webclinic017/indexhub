import json
from enum import Enum
from functools import partial, reduce
from typing import Any, List, Mapping

import numpy as np
import pandas as pd
import polars as pl
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.routers.stats import ERROR_TYPE_TO_METRIC
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()


class TableTag(str, Enum):
    forecast = "forecast"
    uplift = "uplift"


class TableParams(BaseModel):
    policy_id: str
    table_tag: TableTag
    filter_by: Mapping[str, List[str]] = None
    page: int
    display_n: int


# POLICY RESULT TABLES
def _get_forecast_table(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    policy_id: str,
    filter_by: Mapping[str, List[str]],
) -> pd.DataFrame:

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

    # Read artifacts
    best_model = outputs["best_model"]
    forecast = read(object_path=outputs["forecasts"][best_model])
    quantiles = read(object_path=outputs["quantiles"][best_model])
    y_baseline = read(object_path=outputs["y_baseline"])

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    # Read rolling uplift and take the latest stats
    metric = ERROR_TYPE_TO_METRIC[fields["error_type"]]
    rolling_uplift = (
        read(object_path=f"artifacts/{policy_id}/rolling_uplift.parquet")
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

    # Create stats
    stats = (
        # Read last_window__sum from statistics
        read(object_path=outputs["statistics"]["last_window__sum"])
        .lazy()
        .pipe(lambda df: df.rename({df.columns[-1]: "last_window__sum"}))
        # Join with forecast to compute current_window__sum
        .join(
            forecast.lazy()
            .groupby(entity_col)
            .agg(pl.sum(target_col))
            .rename({target_col: "current_window__sum"}),
            on=entity_col,
        )
        # Select last_window__sum, current_window__sum, diff, pct_change as stats
        .select(
            entity_col,
            pl.col("last_window__sum"),
            pl.col("current_window__sum"),
            (pl.col("current_window__sum") - pl.col("last_window__sum")).alias("diff"),
            (
                ((pl.col("current_window__sum") / pl.col("last_window__sum")) - 1) * 100
            ).alias("pct_change"),
        )
        # Join with rolling uplift
        .join(rolling_uplift, on=entity_col)
    )

    # Pivot quantiles
    quantiles = (
        quantiles.lazy()
        .filter(pl.col("quantile").is_in([10, 90]))
        .collect(streaming=True)
        .pivot(values=target_col, index=idx_cols, columns="quantile")
        .select([*idx_cols, pl.all().exclude(idx_cols).prefix("forecast_")])
        .lazy()
    )

    # Concat forecasts
    table = (
        forecast.lazy()
        .rename({target_col: "forecast"})
        .join(
            y_baseline.lazy().rename({target_col: "baseline"}), on=idx_cols, how="left"
        )
        .join(quantiles, on=idx_cols, how="left")
        .with_columns(
            [
                pl.col(time_col).rank("ordinal").over(entity_col).alias("fh"),
                pl.lit(None).alias("override"),  # for FE
            ]
        )
        # Reorder
        .select(
            [
                entity_col,
                time_col,
                "fh",
                "baseline",
                "forecast",
                "forecast_10",
                "forecast_90",
                "override",
            ]
        )
        # Rename to label for FE
        .rename(
            {
                time_col: "",  # Empty string
                "fh": "Forecast Period",
                "forecast": "Forecast",
                "baseline": "Baseline",
                "forecast_10": "Forecast (10% quantile)",
                "forecast_90": "Forecast (90% quantile)",
            }
        )
        # Round all floats to 2 decimal places
        # NOTE: Rounding not working for Float32
        .with_columns(pl.col([pl.Float64, pl.Float32]).cast(pl.Float64).round(2))
        .groupby(entity_col, maintain_order=True)
        .agg(pl.struct(pl.all().exclude(entity_col)).alias("tables"))
        # Sort table by rolling uplift
        .join(stats, on=entity_col)
        .sort("score__uplift_pct__rolling_mean", descending=True)
        .rename({entity_col: "entity"})
        # Round all floats to 2 decimal places
        # NOTE: Rounding not working for Float32
        .with_columns(pl.col([pl.Float32, pl.Float64]).cast(pl.Float64).round(2))
        .select(
            [
                pl.col("entity"),
                pl.col("tables"),
                pl.struct(pl.all().exclude(["entity", "tables"])).alias("stats"),
            ]
        )
    )

    # Filter by specific columns
    if filter_by:
        expr = [pl.col(col).is_in(values) for col, values in filter_by.items()]
        # Combine expressions with 'and'
        filter_expr = reduce(lambda x, y: x & y, expr)
        table = table.filter(filter_expr)

    return table


def _get_uplift_table():
    pass


TAGS_TO_GETTER = {
    "forecast": {
        "forecast": _get_forecast_table,
        "uplift": _get_uplift_table,
    }
}


class TableResponse(BaseModel):
    pagination: Mapping[str, int]
    results: List[Mapping[Any, Any]]


@router.get("/tables/{policy_id}/{table_tag}")
def get_policy_table(params: TableParams) -> TableResponse:
    if params.page < 1:
        raise ValueError("`page` must be an integer greater than 0")
    with Session(engine) as session:
        policy = get_policy(params.policy_id)["policy"]
        getter = TAGS_TO_GETTER[policy.tag][params.table_tag]
        user = session.get(User, policy.user_id)
        # TODO: Cache using an in memory key-value store
        pl.toggle_string_cache(True)
        table = getter(
            json.loads(policy.fields),
            json.loads(policy.outputs),
            user,
            params.policy_id,
            params.filter_by,
        ).collect(streaming=True)
        pl.toggle_string_cache(False)

    start = params.display_n * (params.page - 1)
    end = params.display_n * params.page
    max_page = int(np.ceil(table.get_column("entity").n_unique() / params.display_n))
    filtered_table = {
        "pagination": {
            "current": params.page,
            "end": max_page,
        },
        "results": table[start:end].to_dicts(),
    }

    return filtered_table
