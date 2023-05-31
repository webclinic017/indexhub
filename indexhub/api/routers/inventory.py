import itertools
import json
import logging
from functools import partial
from typing import Any, List, Mapping

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
) -> Mapping[str, List[Mapping[str, str]]]:
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
        forecast_entities = (
            forecasts.get_column(forecasts.columns[0]).unique().to_list()
        )

        # Get inventory entities
        inventory_source = get_source(sources["inventory"])["source"]
        inventory = read(object_path=inventory_source.output_path)
        inventory_entities = (
            inventory.get_column(inventory.columns[0]).unique().to_list()
        )

        entities = {
            "forecast_entities": [{'id': index, 'entity': entity} for index, entity in enumerate(forecast_entities)],
            "inventory_entities":[{'id': index, 'entity': entity} for index, entity in enumerate(inventory_entities)],
        }

    return entities


def _create_inventory_table(
    sources: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    forecast_entities: List[str],
    inventory_entity: str,
    quantile_lower: int = 10,
    quantile_upper: int = 90,
) -> pl.DataFrame:
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
        )
    except HTTPException:
        # If plan.parquet not found, use best plan as plan
        # This happens if user has not clicked on execute plan
        logger.warning("`plan.parquet` not found, use best plan as plan.")
        plan = read(object_path=outputs["best_plan"]).rename(
            {entity_col: "entity", "best_plan": "plan"}
        )

    # Join dfs and filter by entities
    indexhub = pl.concat([backtest, forecast]).rename({target_col: "ai"})
    forecast_df = (
        actual.rename({target_col: "actual"})
        .join(
            y_baseline.rename({target_col: "baseline"}),
            on=idx_cols,
            how="outer",
        )
        .join(indexhub, on=idx_cols, how="outer")
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
            plan.select(pl.all().exclude(["^fh.*$", "^use.*$"])).rename(
                {"entity": entity_col}
            ),
            on=idx_cols,
            how="outer",
        )
        .sort(idx_cols)
        .filter(pl.col(entity_col).is_in(forecast_entities))
    )

    # Read inventory and filter by entities
    inventory_df = read(object_path=inventory_source.output_path)
    inv_entity_col, inv_time_col, inv_target_col = inventory_df.columns
    inventory_df = inventory_df.filter(
        pl.col(inv_entity_col) == inventory_entity
    ).rename({inv_target_col: "inventory"})

    # Join forecast and inventory
    agg_expr = {
        "sum": pl.exclude("inventory").sum(),
        "mean": pl.exclude("inventory").mean(),
        "median": pl.exclude("inventory").median(),
    }

    data_fields = json.loads(forecast_source.data_fields)
    entity_cols = data_fields["entity_cols"]
    # Use agg method from panel source settings
    forecast_agg_method = data_fields.get("agg_method", "sum")

    # Use mean for inventory if levels not equal
    # Otherwise use agg method from inventory source settings
    inventory_agg_method = json.loads(inventory_source.data_fields).get(
        "agg_method", "sum"
    )
    if entity_col == inv_entity_col:
        inventory_agg_expr = AGG_METHODS[inventory_agg_method]
    else:
        inventory_agg_expr = pl.mean

    table = (
        forecast_df
        # Split entity cols
        .with_columns(
            pl.col(entity_col)
            .cast(pl.Utf8)
            .str.split_exact(" - ", len(entity_cols))
            .struct.rename_fields(entity_cols)
            .alias("entities")
        )
        .unnest("entities")
        # Cast entity cols to categorical
        .with_columns([pl.col(col).cast(pl.Categorical) for col in entity_cols])
        # Join with inventory
        .join(inventory_df, on=[inv_entity_col, time_col], how="left")
        # Reorder cols
        .select([entity_col, pl.exclude([entity_col, *entity_cols])])
        # Group by time and agg
        .groupby("time", maintain_order=True)
        .agg(agg_expr[forecast_agg_method], inventory_agg_expr("inventory"))
        .drop(entity_col)
        .sort("time")
    )
    return table


def _create_inventory_chart(
    chart_data: pl.DataFrame,
    quantile_lower: int = 10,
    quantile_upper: int = 90,
):
    time_col = chart_data.columns[0]

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

    # for i in range(2, 7):
    #     line_chart.options["series"][i]["endLabel"] = {
    #         "show": True,
    #         "formatter": "{a}",
    #         "color": "inherit",
    #     }

    return line_chart.dump_options()


class Params(BaseModel):
    forecast_entities: List[str]
    inventory_entity: str


@router.post("/inventory/table/{objective_id}")
def get_inventory_table(
    objective_id: str,
    params: Params,
) -> List[Mapping[str, Any]]:
    objective = get_objective(objective_id)["objective"]
    sources = json.loads(objective.sources)
    outputs = json.loads(objective.outputs)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    table = None
    if sources.get("inventory", None):
        table = (
            _create_inventory_table(
                sources=sources,
                outputs=outputs,
                user=user,
                forecast_entities=params.forecast_entities,
                inventory_entity=params.inventory_entity,
            )
            .with_row_count()
            .rename({"row_nr": "id"})
            .drop_nulls(subset=["ai"])
            .to_dicts()
        )

    return table


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
        table = _create_inventory_table(
            sources=sources,
            outputs=outputs,
            user=user,
            forecast_entities=params.forecast_entities,
            inventory_entity=params.inventory_entity,
        )
        chart_json = _create_inventory_chart(table)

    return chart_json
