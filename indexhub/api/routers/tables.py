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
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.chart_builders import _create_sparkline
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()


class TableTag(str, Enum):
    forecast = "forecast"
    uplift = "uplift"


# OBJECTIVE RESULT TABLES
def _get_forecast_table(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    source_fields: Mapping[str, str],
    user: User,
    objective_id: str,
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
    forecast = read(object_path=outputs["forecasts"]["best_models"])
    quantiles = read(object_path=outputs["quantiles"]["best_models"])
    y_baseline = read(object_path=outputs["y_baseline"])
    y = read(object_path=outputs["y"])

    agg_method = source_fields["agg_method"]
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
            pl.col(f"{metric}__uplift__rolling_{agg_method}").alias(
                f"score__uplift__rolling_{agg_method}"
            ),
            (pl.col(f"{metric}__uplift_pct__rolling_mean").fill_nan(None) * 100).alias(
                "score__uplift_pct__rolling_mean"
            ),
        )
    )

    # Create stats
    stats = (
        # Read last_window__{agg_method} from statistics
        read(object_path=outputs["statistics"][f"last_window__{agg_method}"])
        .lazy()
        .pipe(lambda df: df.rename({df.columns[-1]: "last_window__stat"}))
        # Read current_window__{agg_method} from statistics
        .join(
            read(object_path=outputs["statistics"][f"current_window__{agg_method}"])
            .lazy()
            .pipe(lambda df: df.rename({df.columns[-1]: "current_window__stat"})),
            on=entity_col,
        )
        # Read predicted_growth_rate from statistics
        .join(
            read(
                object_path=outputs["statistics"][
                    f"predicted_growth_rate__{agg_method}"
                ]
            )
            .lazy()
            .pipe(lambda df: df.rename({df.columns[-1]: "pct_change"})),
            on=entity_col,
        )
        # Select last_window__sum, current_window__sum, diff, pct_change as stats
        .select(
            entity_col,
            pl.col("last_window__stat"),
            pl.col("current_window__stat"),
            (pl.col("current_window__stat") - pl.col("last_window__stat")).alias(
                "diff"
            ),
            pl.when(
                (pl.col("pct_change").is_infinite()) | (pl.col("pct_change").is_nan())
            )
            .then(0)
            .otherwise(pl.col("pct_change"))
            .keep_name(),
            pl.lit(fields["goal"]).alias("goal"),
        )
        # Join with rolling uplift
        .join(rolling_uplift, on=entity_col)
        .with_columns(
            (pl.col("score__uplift_pct__rolling_mean") / pl.col("goal") * 100).alias(
                "progress"
            )
        )
        # Progress cap at 100
        .with_columns(
            pl.when(pl.col("progress") > 100)
            .then(100)
            .otherwise(pl.col("progress"))
            .keep_name()
        )
    )

    # Set default `use_ai`, `use_benchmark`, and `use_override`
    plans = stats.select(
        entity_col,
        pl.when(pl.col("score__uplift_pct__rolling_mean") >= 0)
        .then(True)
        .otherwise(False)
        .alias("use_ai"),
        pl.when(pl.col("score__uplift_pct__rolling_mean") < 0)
        .then(True)
        .otherwise(False)
        .alias("use_benchmark"),
        pl.lit(False).alias("use_override"),
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

    # Create sparklines
    # Filter y to last 12 datetimes
    y_last12 = (
        y.with_columns(
            [
                pl.col(time_col).rank("ordinal").over(entity_col).alias("i"),
                pl.col(target_col).cast(pl.Float64),
            ]
        )
        .filter(pl.col("i") > pl.col("i").max() - 12)
        .select(pl.all().exclude("i"))
    )
    # Join with forecast and groupby entity_col
    groupby = pl.concat([y_last12, forecast]).groupby(entity_col)

    sparklines = {}
    for entity, df in groupby:
        # Cast to f64 for rounding
        y_data = df.get_column(target_col).round(1).to_list()
        sparklines[entity] = _create_sparkline(y_data)

    # Concat forecasts
    table = (
        forecast.lazy()
        .rename({target_col: "forecast"})
        .join(
            y_baseline.lazy().rename({target_col: "baseline"}), on=idx_cols, how="left"
        )
        .join(quantiles, on=idx_cols, how="left")
        .join(plans, on=entity_col, how="left")
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
                "use_ai",
                "use_benchmark",
                "use_override",
                "override",
            ]
        )
        # Rename to label for FE
        .rename(
            {
                time_col: "Time",  # Empty string
                "fh": "Forecast Period",
                "forecast": "Forecast",
                "baseline": "Baseline",
                "forecast_10": "Forecast (10% quantile)",
                "forecast_90": "Forecast (90% quantile)",
                "override": "Override",
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
        # Append sparklines to table
        .pipe(
            lambda df: df.with_columns(
                pl.col("entity")
                .apply(lambda x: sparklines.get(x, "N/A"))
                .alias("sparklines")
            )
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
    "reduce_errors": {
        "forecast": _get_forecast_table,
        "uplift": _get_uplift_table,
    }
}


class TableResponse(BaseModel):
    pagination: Mapping[str, int]
    results: List[Mapping[Any, Any]]


class TableParams(BaseModel):
    filter_by: Mapping[str, List[str]] = None
    page: int
    display_n: int


@router.post("/tables/{objective_id}/{table_tag}")
def get_objective_table(
    params: TableParams, objective_id: str, table_tag: TableTag
) -> TableResponse:
    if params.page < 1:
        raise ValueError("`page` must be an integer greater than 0")
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        getter = TAGS_TO_GETTER[objective.tag][table_tag]
        user = session.get(User, objective.user_id)
        source = get_source(json.loads(objective.sources)["panel"])["source"]
        # TODO: Cache using an in memory key-value store
        pl.toggle_string_cache(True)
        table = getter(
            json.loads(objective.fields),
            json.loads(objective.outputs),
            json.loads(source.fields),
            user,
            objective_id,
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
