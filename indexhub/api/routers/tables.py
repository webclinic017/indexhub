from functools import partial
from typing import List, Mapping

import pandas as pd
import polars as pl
from fastapi import APIRouter
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()

SEGMENTATION_FACTOR_TO_KEY = {
    "volatility": "rolling__cv",
    "total value": "groupby__sum",
    "historical growth rate": "rolling__sum",
    "predicted growth rate": "last_window__sum",
}

SEGMENTATION_FACTOR_TO_EXPR = {
    "volatility": pl.mean("seg_factor"),
    "total value": pl.sum("seg_factor"),
    "historical growth rate": pl.col("seg_factor").diff().mean(),
    "predicted growth rate": None,
}

# POLICY RESULT TABLES
def _get_forecast_table(
    fields: Mapping[str, str], outputs: Mapping[str, str], user: User
) -> pd.DataFrame:

    pl.toggle_string_cache(True)

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
    baseline = read(object_path=outputs["baseline"])

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    # Segmentation factor
    segmentation_factor = fields["segmentation_factor"]
    stat_key = SEGMENTATION_FACTOR_TO_KEY[segmentation_factor]
    stat = (
        read(object_path=outputs["statistics"][stat_key])
        .lazy()
        .pipe(lambda df: df.rename({df.columns[-1]: "seg_factor"}))
    )
    if stat_key == "last_window__sum":
        stat = stat.join(
            forecast.lazy()
            .groupby(entity_col)
            .agg(pl.sum(target_col))
            .rename({target_col: "seg_factor_forecast"}),
            on=entity_col,
        ).select(
            entity_col,
            (pl.col("seg_factor_forecast") - pl.col("seg_factor")).alias("seg_factor"),
        )
    else:
        expr = SEGMENTATION_FACTOR_TO_EXPR[segmentation_factor]
        stat = stat.groupby(entity_col).agg(expr)

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
    desc_order = False if segmentation_factor == "volatility" else True
    table = (
        forecast.lazy()
        .rename({target_col: "forecast"})
        .join(baseline.lazy().rename({target_col: "baseline"}), on=idx_cols, how="left")
        .join(quantiles, on=idx_cols, how="left")
        .with_columns(
            pl.col(time_col).rank("ordinal").over(entity_col).alias("fh"),
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
            ]
        )
        # Sort table by segmentation factor
        .join(stat, on=entity_col)
        .sort(stat.columns[-1], descending=desc_order)
        # Rename to label for FE
        .rename(
            {
                time_col: "",  # Empty string
                "fh": "Forecast Period",
                "forecast": "Forecast",
                "baseline": "Baseline",
                "forecast_10": "Forecast (10% quantile)",
                "forecast_90": "Forecast (90% quantile)",
                "seg_factor": segmentation_factor,
            }
        )
        .groupby(entity_col, maintain_order=True)
        .agg(pl.struct(pl.all().exclude(entity_col)).alias("table"))
    )

    pl.toggle_string_cache(False)
    return table


def _get_uplift_table():
    pass


TAGS_TO_GETTER = {
    "forecast": {
        "forecast": _get_forecast_table,
        "uplift": _get_uplift_table,
    }
}


@router.get("/tables/{policy_id}/{table_tag}")
def get_policy_table(
    policy_id: str,
    table_tag: str,
    page: int,
    display_n: int = 5,
) -> List[Mapping[str, str]]:
    if page < 1:
        raise ValueError("`page` must be an integer greater than 0")
    with Session(engine) as session:
        policy = get_policy(policy_id)
        getter = TAGS_TO_GETTER[policy.tag][table_tag]
        user = session.get(User, policy.user_id)
        # TODO: Cache using an in memory key-value store
        table = getter(policy.fields, policy.outputs, user)

    start = display_n * (page - 1)
    end = display_n * page
    filtered_table = table[start:end].collect(streaming=True).to_dicts()
    return filtered_table
