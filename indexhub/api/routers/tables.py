import json
from enum import Enum
from functools import partial, reduce
from typing import Any, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


MODEL_NAME_TO_SHORT = {
    "knn": "KNN",
    "linear": "Linear",
    "lasso": "Lasso",
    "ridge": "Ridge",
    "elastic_net": "Elastic Net",
    "ensemble[automl]": "Ensemble[AutoML]",
    # lightgbm
    "lightgbm__regression_l1": "LGB L1",
    "lightgbm__regression": "LGB L2",
    "lightgbm__huber": "LGB Huber",
    "lightgbm__gamma": "LGB Gamma",
    "lightgbm__poisson": "LGB Poisson",
    "lightgbm__tweedie": "LGB Tweedie",
    # lightgbm weighted
    "lightgbm__weighted__regression_l1": "LGBW L1",
    "lightgbm__weighted__regression": "LGBW L2",
    "lightgbm__weighted__huber": "LGBW Huber",
    "lightgbm__weighted__gamma": "LGBW Gamma",
    "lightgbm__weighted__poisson": "LGBW Poisson",
    "lightgbm__weighted__tweedie": "LGBW Tweedie",
    # zero inflated
    "zero_inflated__lightgbm__regression_l1": "Zero LGB L1",
    "zero_inflated__lightgbm__regression": "Zero LGB L2",
    "zero_inflated__lightgbm__huber": "Zero LGB Huber",
    "zero_inflated__lightgbm__gamma": "Zero LGB Gamma",
    "zero_inflated__lightgbm__poisson": "Zero LGB Poisson",
    "zero_inflated__lightgbm__tweedie": "Zero LGB Tweedie",
    "zero_inflated__knn": "Zero KNN",
    "zero_inflated__linear": "Zero Linear",
    "zero_inflated__lasso": "Zero Lasso",
    "zero_inflated__ridge": "Zero Ridge",
    "zero_inflated__elastic_net": "Zero Elastic Net",
}


def _create_sparkline(y_data: List[int]):

    from pyecharts import options as opts
    from pyecharts.charts import Line

    # Define sparkline color based on first and last values
    if y_data[0] <= y_data[-1]:
        color = "#44aa7e"  # green
    else:
        color = "#9e2b2b"  # red

    # Generate sparkline
    sparkline = Line()
    sparkline.add_xaxis(list(range(len(y_data))))
    sparkline.add_yaxis(
        "",
        y_data,
        is_symbol_show=False,
        linestyle_opts=opts.LineStyleOpts(width=3),
        color=color,
    )

    # Update markpoint to show only first and last data label
    markpoint_data = [
        {"coord": [0, y_data[0]], "value": y_data[0]},
        {"coord": [len(y_data) - 1, y_data[-1]], "value": y_data[-1]},
    ]
    sparkline.set_series_opts(
        markpoint_opts=opts.MarkPointOpts(
            data=markpoint_data,
            symbol="circle",
            symbol_size=7,
            label_opts=opts.LabelOpts(position="outside", font_size=12),
        ),
    )
    # Remove legends, axis, tooltip
    sparkline.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(is_show=False),
        yaxis_opts=opts.AxisOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(is_show=False),
    )

    # Export chart options to JSON
    sparkline_json = sparkline.dump_options()
    return sparkline_json


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

    # Read forecast
    forecast = read(object_path=outputs["forecasts"]["best_models"])
    best_models = outputs["best_models"]
    agg_method = source_fields.get("agg_method", "sum")
    entity_col, time_col, target_col = forecast.columns

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

    # Create sparklines
    # Filter y to last 12 datetimes
    y = read(object_path=outputs["y"])
    y_last12 = (
        y.with_columns(
            [
                pl.col(time_col).rank("ordinal").over(entity_col).alias("i"),
                # Rounding only works for f64
                pl.col(target_col).cast(pl.Float64),
            ]
        )
        .filter(pl.col("i") > pl.col("i").max() - 12)
        .select(pl.all().exclude("i"))
    )
    # Join with forecast and groupby entity_col
    groupby = pl.concat(
        [
            y_last12,
            # Rounding only works for f64
            forecast.with_columns(pl.col(target_col).cast(pl.Float64)),
        ]
    ).groupby(entity_col)

    sparklines = {}
    for entity, df in groupby:
        # Cast to f64 for rounding
        y_data = df.get_column(target_col).round(1).to_list()
        sparklines[entity] = _create_sparkline(y_data)

    # Return entity, stats, best_model, and sparklines
    table = (
        stats.sort("score__uplift_pct__rolling_mean", descending=True)
        .rename({entity_col: "entity"})
        # Round all floats to 2 decimal places
        # NOTE: Rounding not working for Float32
        .with_columns(pl.col([pl.Float32, pl.Float64]).cast(pl.Float64).round(2))
        .select(
            [
                pl.col("entity"),
                pl.struct(pl.all().exclude("entity")).alias("stats"),
                # Add best model by entity
                pl.col("entity")
                .map_dict(best_models)
                .map_dict(MODEL_NAME_TO_SHORT)
                .alias("best_model"),
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


class Columns(BaseModel):
    field: str
    headerName: str
    aggregation: Optional[str] = None
    type: str  # string or number


def _get_forecast_table_view(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    source_fields: Mapping[str, str],
    user: User,
    objective_id: str,
    filter_by: Mapping[str, List[str]],
) -> Tuple[pl.DataFrame, List[Mapping[str, str]]]:
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

    agg_method = source_fields.get("agg_method", "sum")
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

    # Set default `use_ai`, `use_baseline`, and `use_override`
    plans = rolling_uplift.select(
        entity_col,
        pl.when(pl.col("score__uplift_pct__rolling_mean") >= 0)
        .then(True)
        .otherwise(False)
        .alias("use_ai"),
        pl.when(pl.col("score__uplift_pct__rolling_mean") < 0)
        .then(True)
        .otherwise(False)
        .alias("use_baseline"),
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

    # Concat forecasts
    rows = (
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
        .rename({entity_col: "entity"})
    )

    # Filter by specific columns
    if filter_by:
        expr = [pl.col(col).is_in(values) for col, values in filter_by.items()]
        # Combine expressions with 'and'
        filter_expr = reduce(lambda x, y: x & y, expr)
        rows = rows.filter(filter_expr)

    # Split entity cols and process data after filter
    entity_cols = entity_col.split("__")
    rows = (
        rows.rename({"entity": entity_col})
        # Split entity cols
        .with_columns(
            pl.col(entity_col)
            .cast(pl.Utf8)
            .str.split_exact(" - ", len(entity_cols))
            .struct.rename_fields(entity_cols)
            .alias("entities")
        )
        .unnest("entities")
        .sort([*entity_cols, time_col])
        .select(
            [
                *entity_cols,
                time_col,
                "fh",
                "baseline",
                "forecast",
                "forecast_10",
                "forecast_90",
                "use_ai",
                "use_baseline",
                "use_override",
                "override",
            ]
        )
        # Round all floats to 2 decimal places
        # NOTE: Rounding not working for Float32
        .with_columns(pl.col([pl.Float64, pl.Float32]).cast(pl.Float64).round(2))
    )

    # Create columns for MUI column properties
    cols_to_headers = {
        "fh": "Forecast Period",
        "forecast_10": "Forecast (10% quantile)",
        "forecast_90": "Forecast (90% quantile)",
    }
    columns = [
        Columns(
            field=col,
            headerName=cols_to_headers[col]
            if col in cols_to_headers.keys()
            else col.replace("_", " ").title(),
            aggregation=agg_method
            if dtype in pl.NUMERIC_DTYPES and col != "fh"
            else None,
            type="number"
            if dtype in pl.NUMERIC_DTYPES or col == "override"
            else "string",
        ).__dict__
        for col, dtype in rows.schema.items()
    ]
    return rows.collect(), columns


TAGS_TO_GETTER = {
    "reduce_errors": {
        "forecast": _get_forecast_table,
        "uplift": _get_uplift_table,
    }
}

TAGS_TO_TABLE_VIEW = {
    "reduce_errors": {
        "forecast": _get_forecast_table_view,
        "uplift": None,
    }
}


class TableResponse(BaseModel):
    pagination: Mapping[str, int]
    results: List[Mapping[Any, Any]]


class TableParams(BaseModel):
    filter_by: Mapping[str, List[str]] = None
    page: int
    display_n: int


class TableViewParams(BaseModel):
    filter_by: Mapping[str, List[str]] = None


@router.post("/tables/{objective_id}/{table_tag}")
def get_objective_table(
    params: TableParams, objective_id: str, table_tag: TableTag
) -> TableResponse:
    if params.page < 1:
        raise ValueError("`page` must be an integer greater than 0")

    objective = get_objective(objective_id)["objective"]
    getter = TAGS_TO_GETTER[objective.tag][table_tag]
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    source = get_source(json.loads(objective.sources)["panel"])["source"]
    # TODO: Cache using an in memory key-value store
    pl.toggle_string_cache(True)
    table = getter(
        fields=json.loads(objective.fields),
        outputs=json.loads(objective.outputs),
        source_fields=json.loads(source.data_fields),
        user=user,
        objective_id=objective_id,
        filter_by=params.filter_by,
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


@router.post("/tables/{objective_id}/{table_tag}/table_view")
def get_objective_table_view(
    params: TableViewParams, objective_id: str, table_tag: TableTag
) -> Mapping[str, List[Mapping[str, Any]]]:
    objective = get_objective(objective_id)["objective"]
    table_view = TAGS_TO_TABLE_VIEW[objective.tag][table_tag]

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    source = get_source(json.loads(objective.sources)["panel"])["source"]
    rows, columns = table_view(
        fields=json.loads(objective.fields),
        outputs=json.loads(objective.outputs),
        source_fields=json.loads(source.data_fields),
        user=user,
        objective_id=objective_id,
        filter_by=params.filter_by,
    )

    rows = rows.with_row_count("id").to_dicts()

    response = {"columns": columns, "rows": rows}

    return response
