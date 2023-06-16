import itertools
import json
import logging
from functools import partial
from typing import Any, List, Mapping, Optional, Tuple, Union

import polars as pl
from fastapi import HTTPException
from pydantic import BaseModel
from pyecharts import options as opts
from pyecharts.charts import Line
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.routers.stats import AGG_METHODS
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


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


@router.get("/inventory/{objective_id}")
def get_entities(
    objective_id: str,
) -> Mapping[str, List[Union[str, Mapping[str, str]]]]:
    objective = get_objective(objective_id)["objective"]
    sources = json.loads(objective.sources)
    outputs = json.loads(objective.outputs)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    entities = None
    if sources.get("inventory", None):
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

        # Get forecast entities
        forecasts = read(object_path=outputs["forecasts"]["best_models"])
        entity_cols = forecasts.columns[0].split("__")
        forecast_entities = (
            forecasts.select(
                pl.col(forecasts.columns[0])
                .cast(pl.Utf8)
                .str.split_exact(" - ", len(entity_cols))
                .struct.rename_fields(entity_cols)
                .alias("entities")
            )
            .unnest("entities")
            .unique()
            .sort(entity_cols)
            .with_row_count("id")
            .to_dicts()
        )

        # Get inventory entities
        inventory_source = get_source(sources["inventory"])["source"]
        inventory = read(object_path=inventory_source.output_path)
        inv_entity_cols = inventory.columns[0].split("__")
        inventory_entities = (
            inventory.select(
                pl.col(inventory.columns[0])
                .cast(pl.Utf8)
                .str.split_exact(" - ", len(inv_entity_cols))
                .struct.rename_fields(inv_entity_cols)
                .alias("entities")
            )
            .unnest("entities")
            .unique()
            .sort(inv_entity_cols)
            .with_row_count("id")
            .to_dicts()
        )

        entities = {
            "forecast_entities": forecast_entities,
            "inventory_entities": inventory_entities,
            "forecast_entity_cols": entity_cols,
            "inventory_entity_cols": inv_entity_cols,
        }

    return entities


class Columns(BaseModel):
    field: str
    headerName: str
    aggregation: Optional[str] = None
    type: str  # string or number


def _create_inventory_table(
    sources: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    forecast_entities: List[str],
    inventory_entities: List[str],
    quantile_lower: int = 10,
    quantile_upper: int = 90,
) -> Tuple[pl.DataFrame, List[Mapping[str, str]]]:
    forecast_source = get_source(sources["panel"])["source"]
    inventory_source = get_source(sources["inventory"])["source"]

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

    # Read forecast artifacts
    forecast = read(object_path=outputs["forecasts"]["best_models"])
    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    backtest = read(object_path=outputs["backtests"]["best_models"]).pipe(
        lambda df: df.groupby(df.columns[:2]).agg(pl.mean(df.columns[-2]))
    )
    actual = read(object_path=outputs["y"])
    y_baseline = read(object_path=outputs["y_baseline"])
    quantiles = read(object_path=outputs["quantiles"]["best_models"])
    quantiles_lower = quantiles.filter(pl.col("quantile") == quantile_lower).drop(
        "quantile"
    )
    quantiles_upper = quantiles.filter(pl.col("quantile") == quantile_upper).drop(
        "quantile"
    )
    best_plan = read(object_path=outputs["best_plan"])
    try:
        plan = read(
            object_path=outputs["best_plan"].replace(
                "best_plan.parquet", "plan.parquet"
            )
        ).rename({"entity": entity_col})
    except HTTPException:
        # If plan.parquet not found, use best plan as plan
        # This happens if user has not clicked on execute plan
        logger.warning("`plan.parquet` not found, use best plan as plan.")
        plan = read(object_path=outputs["best_plan"]).rename({"best_plan": "plan"})

    # Join dfs and filter by entities
    forecast_df = (
        actual.rename({target_col: "actual"})
        .join(
            y_baseline.rename({target_col: "baseline"}),
            on=idx_cols,
            how="outer",
        )
        .join(
            pl.concat([backtest, forecast]).rename({target_col: "ai"}),
            on=idx_cols,
            how="outer",
        )
        # Join quantiles
        .join(
            quantiles_lower.rename({target_col: f"ai_{quantile_lower}"}),
            on=idx_cols,
            how="outer",
        )
        .join(
            quantiles_upper.rename({target_col: f"ai_{quantile_upper}"}),
            on=idx_cols,
            how="outer",
        )
        .join(
            best_plan.select(pl.all().exclude(["^fh.*$", "^use.*$"])),
            on=idx_cols,
            how="outer",
        )
        .join(
            plan.select(pl.all().exclude(["^fh.*$", "^use.*$"])),
            on=idx_cols,
            how="outer",
        )
        .sort(idx_cols)
        .filter(pl.col(entity_col).is_in(forecast_entities))
    )

    # Read entity cols
    entity_cols = forecast_df.columns[0].split("__")
    inventory_data_fields = json.loads(inventory_source.data_fields)
    inv_entity_cols = inventory_data_fields["entity_cols"]
    inv_entity_col = "__".join(inv_entity_cols)
    inv_target_col = inventory_data_fields["target_col"]

    # Read inventory and filter by entities
    inventory_df = (
        read(
            object_path=inventory_source.output_path,
            columns=[inv_entity_col, "time", inv_target_col],
        )
        .filter(pl.col(inv_entity_col).is_in(inventory_entities))
        .rename({inv_target_col: "inventory"})
    )

    # Join forecast and inventory
    unique_entity_cols = [col for col in entity_cols if col not in inv_entity_cols]
    join_entity_cols = [col for col in entity_cols if col in inv_entity_cols]

    rows = (
        forecast_df
        # Split entity cols
        .with_columns(
            pl.col(entity_col)
            .cast(pl.Utf8)
            .str.split_exact(" - ", len(entity_cols))
            .struct.rename_fields(entity_cols)
            .alias("entities")
        )
        .drop(entity_col)
        .unnest("entities")
        # Cast entity cols to categorical
        .with_columns([pl.col(col).cast(pl.Categorical) for col in entity_cols])
        # Join with inventory
        .join(
            inventory_df
            # Split entity cols
            .with_columns(
                pl.col(inv_entity_col)
                .cast(pl.Utf8)
                .str.split_exact(" - ", len(inv_entity_cols))
                .struct.rename_fields(inv_entity_cols)
                .alias("entities")
            )
            .drop(inv_entity_col)
            .unnest("entities")
            # Cast entity cols to categorical
            .with_columns(
                [pl.col(col).cast(pl.Categorical) for col in inv_entity_cols]
            ),
            on=[*join_entity_cols, time_col],
            how="left",
        )
        .sort(["time", *inv_entity_cols, *unique_entity_cols])
        # Reorder cols
        .select(
            [
                "time",
                *inv_entity_cols,
                "inventory",
                *unique_entity_cols,
                pl.exclude(
                    ["time", *inv_entity_cols, "inventory", *unique_entity_cols]
                ),
            ]
        )
    )

    # Use agg method from panel source settings
    forecast_data_fields = json.loads(forecast_source.data_fields)
    forecast_agg_method = forecast_data_fields.get("agg_method", "sum")

    # Use mean for inventory if levels not equal
    # Otherwise use agg method from inventory source settings
    if entity_col == inv_entity_col:
        inventory_agg_method = inventory_data_fields.get("agg_method", "sum")
    else:
        inventory_agg_method = "mean"

    # Create columns for MUI column properties
    agg_methods = {
        col: forecast_agg_method
        for col in rows.columns
        if col not in ["time", *entity_cols, *inv_entity_cols, "inventory"]
    }
    agg_methods["inventory"] = inventory_agg_method
    columns = [
        Columns(
            field=col,
            headerName=col.replace("_", " ").title(),
            aggregation=agg_methods.get(col, None),
            type="number" if dtype in pl.NUMERIC_DTYPES else "string",
        ).__dict__
        for col, dtype in rows.schema.items()
    ]
    return rows, columns


def _create_inventory_chart(
    chart_data: pl.DataFrame,
    sources: Mapping[str, str],
    quantile_lower: int = 10,
    quantile_upper: int = 90,
):
    time_col = chart_data.columns[0]

    # If forecast and inventory have different entity cols
    # Group by time + inventory entity cols and agg inventory by mean
    # Then group by time and agg using user selected agg method
    forecast_source = get_source(sources["panel"])["source"]
    forecast_data_fields = json.loads(forecast_source.data_fields)
    forecast_entity_cols = forecast_data_fields["entity_cols"]
    forecast_agg_method = forecast_data_fields.get("agg_method", "sum")

    inventory_source = get_source(sources["inventory"])["source"]
    inventory_data_fields = json.loads(inventory_source.data_fields)
    inventory_entity_cols = inventory_data_fields["entity_cols"]
    inventory_agg_method = inventory_data_fields.get("agg_method", "sum")

    agg_expr = {
        "sum": pl.exclude("inventory").sum(),
        "mean": pl.exclude("inventory").mean(),
        "median": pl.exclude("inventory").median(),
    }

    if forecast_entity_cols != inventory_entity_cols:
        chart_data = chart_data.groupby(
            [time_col, *inventory_entity_cols], maintain_order=True
        ).agg(pl.col("inventory").mean(), agg_expr[forecast_agg_method])

    chart_data = chart_data.groupby(time_col, maintain_order=True).agg(
        AGG_METHODS[inventory_agg_method]("inventory"), agg_expr[forecast_agg_method]
    )

    # Generate the chart
    line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
    line_chart.add_xaxis(chart_data[time_col].to_list())

    # Quantile range charts
    line_chart.add_yaxis(
        "",
        chart_data[f"ai_{quantile_upper}"].to_list(),
        color="white",
        symbol=None,
        is_symbol_show=False,
        areastyle_opts=opts.AreaStyleOpts(opacity=0.25, color="#5B90AA"),
    )
    line_chart.add_yaxis(
        "",
        chart_data[f"ai_{quantile_lower}"].to_list(),
        color="white",
        symbol=None,
        is_symbol_show=False,
        areastyle_opts=opts.AreaStyleOpts(opacity=1, color="white"),
    )

    # Set color scheme based on guidelines
    colors_base = itertools.cycle(
        ["#0a0a0a", "#11a9ba", "#003DFD", "#b512b8", "#ffa500"]
    )

    # Add lines for latest forecasts and panels
    for col in [
        colname
        for colname in chart_data.columns
        if colname in ["actual", "ai", "baseline", "plan", "inventory"]
    ]:
        # Do not add line for the col if all data are nulls
        # Otherwise will throw error when labeling the line
        if len(chart_data.drop_nulls(col)) > 0:
            if col == "plan":
                line_type = "dashed"
            else:
                line_type = "solid"
            line_chart.add_yaxis(
                f"{col.title().replace('Ai','AI')}",
                chart_data[col].to_list(),
                color=next(colors_base),
                symbol=None,
                linestyle_opts=opts.LineStyleOpts(width=2, type_=line_type),
                is_symbol_show=False,
                tooltip_opts=opts.TooltipOpts(is_show=True),
                markpoint_opts=opts.MarkPointOpts,
            )

    # Get the range of the x-axis
    x_data = sorted(chart_data[time_col].to_list())
    initial_range = ((len(x_data) - 12) / len(x_data)) * 100
    if len(x_data) <= 12:
        initial_range = 0

    line_chart.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
    ).set_global_opts(
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(is_show=True, formatter="{c}"),
        xaxis_opts=opts.AxisOpts(
            type_=time_col,
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(is_show=False),
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(is_show=False),
            axispointer_opts=opts.AxisPointerOpts(is_show=True),
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            orient="horizontal",
            pos_left="100",
            feature={
                "dataZoom": {
                    "yAxisIndex": "none"
                },  # Enable data zoom with no y-axis filtering
            },
        ),
        datazoom_opts=[
            opts.DataZoomOpts(
                type_="slider",  # Set datazoom type to slider
                range_start=initial_range,  # Set initial range to start from last 12months
                range_end=100,
            ),
            opts.DataZoomOpts(
                type_="inside",  # Allow movement of x-axis inside the chart area
                filter_mode="empty",
                range_start=0,
                range_end=50,
            ),
        ],
    )

    for i in range(len(line_chart.options["series"])):
        if line_chart.options["series"][i]["name"]:
            line_chart.options["series"][i]["endLabel"] = {
                "show": True,
                "formatter": "{a}",
                "color": "inherit",
            }

    return line_chart.dump_options()


class Params(BaseModel):
    forecast_entities: List[str]
    inventory_entities: List[str]


@router.post("/inventory/table/{objective_id}")
def get_inventory_table(
    objective_id: str,
    params: Params,
) -> Mapping[str, List[Mapping[str, Any]]]:
    objective = get_objective(objective_id)["objective"]
    sources = json.loads(objective.sources)
    outputs = json.loads(objective.outputs)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    response = None
    if sources.get("inventory", None):
        rows, columns = _create_inventory_table(
            sources=sources,
            outputs=outputs,
            user=user,
            forecast_entities=params.forecast_entities,
            inventory_entities=params.inventory_entities,
        )

        rows = rows.drop_nulls(subset=["inventory"]).with_row_count("id").to_dicts()

        response = {"columns": columns, "rows": rows}

    return response


@router.post("/inventory/chart/{objective_id}")
def get_inventory_chart(objective_id: str, params: Params):
    objective = get_objective(objective_id)["objective"]
    sources = json.loads(objective.sources)
    outputs = json.loads(objective.outputs)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    chart_json = None
    if sources.get("inventory", None):
        chart_data, _ = _create_inventory_table(
            sources=sources,
            outputs=outputs,
            user=user,
            forecast_entities=params.forecast_entities,
            inventory_entities=params.inventory_entities,
        )
        chart_json = _create_inventory_chart(chart_data=chart_data, sources=sources)

    return chart_json
