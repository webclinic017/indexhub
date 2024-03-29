import itertools
import logging
from functools import partial, reduce
from typing import Any, Literal, Mapping

import polars as pl
from fastapi import HTTPException
from pyecharts import options as opts
from pyecharts.charts import Grid, Line, Scatter

from indexhub.api.models.user import User
from indexhub.api.routers.stats import AGG_METHODS
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.flows.preprocess import _reindex_panel


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


def create_single_forecast_chart(
    outputs: Mapping[str, str],
    fields: Mapping[str, str],
    source_fields: Mapping[str, str],
    objective_id: str,
    user: User,
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    quantile_lower: int = 10,
    quantile_upper: int = 90,
    **kwargs,
):
    pl.toggle_string_cache(True)
    series_name_to_legend_show = {}
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
    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col
    agg_method = source_fields.get("agg_method", "sum")

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

    rolling = read(
        object_path=f"artifacts/{objective_id}/rolling_forecasts.parquet",
        columns=[
            entity_col,
            time_col,
            "fh",
            "updated_at",
            "ai",
            "best_plan",
            "plan",
            "baseline",
            "actual",
        ],
    ).rename({entity_col: "entity"})

    # Get historical_dates from rolling forecasts parquet
    historical_dates = [
        date.strftime("%Y-%m-%d")
        for date in rolling.get_column("updated_at").unique().to_list()
    ]

    # Postproc
    rolling_forecasts = (
        rolling.sort(["entity", "updated_at"])
        .with_columns(pl.col("updated_at").cast(pl.Date))
        .groupby(["entity", "updated_at"], maintain_order=True)
        .agg(pl.all().exclude(["entity", "updated_at"]))
        .tail(3)
        .head(2)
        .explode(pl.all().exclude(["entity", "updated_at"]))
        .drop("actual")
        .pivot(
            values=["ai", "best_plan", "plan", "baseline"],
            columns="updated_at",
            index=["entity", "time"],
        )
    )

    # Postproc - join data together
    indexhub = pl.concat([backtest, forecast]).rename({target_col: "ai"})
    joined = (
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
        .rename({entity_col: "entity"})
        .join(
            plan.select(pl.all().exclude(["^fh.*$", "^use.*$"])),
            on=["entity", time_col],
            how="outer",
        )
        .sort(["entity", time_col])
        .join(rolling_forecasts, on=["entity", time_col], how="outer")
    )

    # Filter by specific columns
    if filter_by:
        expr = [pl.col(col).is_in(values) for col, values in filter_by.items()]
        # Combine expressions with 'and'
        filter_expr = reduce(lambda x, y: x & y, expr)
        joined = joined.filter(filter_expr)

    # Get expression for agg by
    agg_exprs = [
        AGG_METHODS[agg_method](col)
        for col in joined.select(
            pl.col([pl.Int16, pl.Int32, pl.Int64, pl.Float64, pl.Float32])
        ).columns
    ]
    # Aggredate data and round to two d.p.
    group_by_cols = [time_col, *agg_by] if agg_by else [time_col]
    chart_data = (
        joined.groupby(group_by_cols)
        .agg(agg_exprs)
        .sort(pl.col(time_col))
        .with_columns([pl.col(pl.Float32).round(2), pl.col(pl.Float64).round(2)])
    )
    # Set color scheme based on guidelines
    colors = {
        # From unit8
        "base": [
            "#0a0a0a",
            "#11a9ba",
            "#003DFD",
            "#b512b8",
        ],
        "historical": ["#003DFD", "#0a0a0a", "#11a9ba"],
    }
    colors_base = itertools.cycle(colors["base"])
    colors_historical = itertools.cycle(colors["historical"])

    # Postproc
    # Hack: Append last value from actual to plan to connect the line
    last_dt = chart_data.filter(pl.col("plan").is_null()).get_column(time_col).max()
    additional_value = chart_data.filter(pl.col(time_col) == last_dt).get_column(
        "actual"
    )[0]
    if additional_value:
        additional_value = round(additional_value, 2)
    series_plan = chart_data.get_column("plan").to_list()
    idx = fields["fh"] + 1
    series_plan[-idx] = additional_value
    chart_data = chart_data.with_columns(pl.Series(name="plan", values=series_plan))

    # Generate the chart
    line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
    line_chart.add_xaxis(
        chart_data[time_col].cast(pl.Date).to_list(),
    )

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

    if len(historical_dates) >= 2:
        secondary_cols = [
            f"ai_{historical_dates[1]}",
            f"plan_{historical_dates[1]}",
            f"baseline_{historical_dates[1]}",
        ]

        # Add lines for secondary historical forecasts
        for col in [
            colname for colname in chart_data.columns if colname in secondary_cols
        ]:
            series_name = f"{col.split('_')[0].title().replace('Ai','AI')} ({historical_dates[1]})"
            # Set the series to False for legend
            series_name_to_legend_show[series_name] = False

            # Y data
            y_data = chart_data[col].to_list()
            line_chart.add_yaxis(
                series_name,
                y_data,
                color=next(colors_historical),
                symbol="diamond",
                linestyle_opts=opts.LineStyleOpts(width=0),
                itemstyle_opts=opts.ItemStyleOpts(opacity=0.7),
                symbol_size=8,
            )
    if len(historical_dates) >= 3:
        tertiary_cols = [
            f"ai_{historical_dates[0]}",
            f"plan_{historical_dates[0]}",
            f"baseline_{historical_dates[0]}",
        ]
        # Add lines for tertiary historical forecasts
        for col in [
            colname for colname in chart_data.columns if colname in tertiary_cols
        ]:
            series_name = f"{col.split('_')[0].title().replace('Ai','AI')} ({historical_dates[0]})"
            # Set the series to False for legend
            series_name_to_legend_show[series_name] = False
            line_chart.add_yaxis(
                series_name,
                chart_data[col].to_list(),
                color=next(colors_historical),
                symbol="square",
                linestyle_opts=opts.LineStyleOpts(width=0),
                itemstyle_opts=opts.ItemStyleOpts(opacity=0.7),
                symbol_size=8,
            )

    # Add lines for latest forecasts and panels
    for col in [
        colname
        for colname in chart_data.columns
        if colname in ["actual", "ai", "baseline", "plan"]
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
        legend_opts={
            "data": list(series_name_to_legend_show.keys()),
            "orient": "vertical",
            "align": "right",
            "right": "0%",
            "textStyle": {"fontSize": 10},
            "border_width": 0,
            "pos_right": 0,
            "selected": series_name_to_legend_show,
            "item_width": 50,
        },
        tooltip_opts=opts.TooltipOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            type_=time_col,
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(is_show=False),
            axispointer_opts=opts.AxisPointerOpts(is_show=True),
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(is_show=False),
            axispointer_opts=opts.AxisPointerOpts(is_show=True),
            is_scale=True,
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

    # Add endlabels for main lines
    for i in range(len(line_chart.options["series"])):
        if line_chart.options["series"][i]["name"]:
            line_chart.options["series"][i]["endLabel"] = {
                "show": True,
                "formatter": "{a}",
                "color": "inherit",
            }
    # Export chart options to JSON
    return line_chart.dump_options()


def create_multi_forecast_chart(
    outputs: Mapping[str, str],
    user: User,
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    agg_method: Literal["sum", "mean"] = "sum",
    top_k: int = 6,
    num_cols: int = 3,
    chart_height: str = "300px",
    gap: str = "5%",
    **kwargs,
):
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

    read = partial(
        SOURCE_TAG_TO_READER[user.storage_tag],
        bucket_name=user.storage_bucket_name,
        file_ext="parquet",
        **storage_creds,
    )

    # Read artifacts
    forecast = read(object_path=outputs["forecasts"]["best_models"])
    backtest = read(object_path=outputs["backtests"]["best_models"]).pipe(
        lambda df: df.groupby(df.columns[:2]).agg(pl.mean(df.columns[-2]))
    )
    actual = read(object_path=outputs["y"])

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    dfs = {"actual": actual, "backtest": backtest, "forecast": forecast}

    data = []
    for colname, df in dfs.items():
        if colname in ["backtest", "forecast"]:
            colname = "indexhub"
        data.append(
            df.with_columns(
                [pl.col("entity").cast(pl.Utf8), pl.col("target").alias(colname)]
            )
        )

    # Concat backtest and forecast
    indexhub = pl.concat([data[1], data[2]])
    # Join indexhub and actual dataframes
    joined = (
        data[0]
        .join(indexhub, on=idx_cols, how="outer")
        .select(pl.exclude("^target.*$"))
    )

    # Filter by specific columns
    if filter_by:
        expr = [pl.col(col).is_in(values) for col, values in filter_by.items()]
        # Combine expressions with 'and'
        filter_expr = reduce(lambda x, y: x & y, expr)
        joined = joined.filter(filter_expr)

    # Get expression for agg by
    mapping = {
        "sum": pl.sum,
        "mean": pl.mean,
    }
    agg_exprs = [
        mapping[agg_method](col)
        for col in joined.select(
            [pl.col(pl.Int64), pl.col(pl.Float64), pl.col(pl.Float32)]
        ).columns
    ]
    # Aggredate data and round to two d.p.
    group_by_cols = [time_col, *agg_by] if agg_by else [time_col]
    agg_data = (
        joined.groupby(group_by_cols)
        .agg(agg_exprs)
        .sort(pl.col(time_col))
        .with_columns([pl.col(pl.Float32).round(2), pl.col(pl.Float64).round(2)])
    )

    # Get top_k_entities
    top_k_entities = (
        agg_data.sort("actual", descending=True).head(top_k)["entity"].to_list()
    )

    entity_data = []
    for entity in top_k_entities:
        entity_data.append(agg_data.filter(pl.col("entity") == entity))

    num_charts = len(entity_data)

    # Set color scheme based on guidelines
    colors = ["#0a0a0a", "#194fdc"]
    line_charts = []
    for i, entity in enumerate(top_k_entities):
        chart_data = (
            entity_data[i].sort("time").with_columns([pl.col("indexhub").round(2)])
        )
        line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
        line_chart.add_xaxis(chart_data["time"].to_list())

        line_chart.add_yaxis(
            "Actual", chart_data["actual"].to_list(), color=colors[0], symbol=None
        )
        line_chart.add_yaxis(
            "Indexhub", chart_data["indexhub"].to_list(), color=colors[1], symbol=None
        )

        line_chart.set_global_opts(
            # title_opts=opts.TitleOpts(title=f"{entity.title()}"),
            legend_opts=opts.LegendOpts(pos_right="20%", border_width=0),
            xaxis_opts=opts.AxisOpts(
                type_="time", splitline_opts=opts.SplitLineOpts(is_show=False)
            ),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                is_scale=True,
            ),
            tooltip_opts=opts.TooltipOpts(
                formatter=f"{entity.title()}" + "<br/>{a}: {c}"
            ),
        )
        # Remove the text label
        line_chart.set_series_opts(label_opts=opts.LabelOpts(is_show=False))

        line_charts.append(line_chart)

    # Calculate grid parameters
    num_rows = (len(line_charts) - 1) // num_cols + 1
    grid_height = (
        f"{int((int(chart_height[:-2]) + int(gap[:-1])) * num_rows - int(gap[:-1]))}px"
    )

    # Create grid and respective position
    grid = Grid(
        init_opts=opts.InitOpts(
            width=f"{400*num_charts}", height=grid_height, bg_color="#fff"
        )
    )
    for i, line in enumerate(line_charts):
        row = i // num_cols
        col = i % num_cols
        grid.add(
            line,
            grid_opts=opts.GridOpts(
                pos_left=f"{(100 // num_cols) * col + int(gap[:-1])}%",
                pos_right=f"{100 - (100 // num_cols) * (col + 1) + int(gap[:-1])}%",
                pos_top=f"{(100 // num_rows) * row + int(gap[:-1])}%"
                if row < num_rows - 1
                else f"{(100 // num_rows) * row}%",
                pos_bottom=f"{100 - (100 // num_rows) * (row + 1) + int(gap[:-1])}%"
                if row > 0
                else f"{100 - (100 // num_rows) * (row + 1)}%",
                background_color="#fff",
            ),
        )
    # Export chart options to JSON
    chart_json = line_chart.dump_options()
    return chart_json


SEGMENTATION_FACTOR_TO_KEY = {
    "volatility": "rolling__cv",
    "total value": "groupby__sum",
    "historical growth rate": "rolling__sum",
    "predicted growth rate": "predicted_growth_rate",
    "predictability": None,
}

SEGMENTATION_FACTOR_TO_EXPR = {
    "volatility": pl.mean("seg_factor"),
    "total value": pl.sum("seg_factor"),
    "historical growth rate": pl.col("seg_factor").diff().mean(),
    "predicted growth rate": None,
    "predictability": None,
}


def create_segmentation_chart(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    source_fields: Mapping[str, str],
    user: User,
    objective_id: str,
    segmentation_factor: Literal[
        "volatility",
        "total value",
        "historical growth rate",
        "predicted growth rate",
        "predictability",
    ] = "volatility",
    chart_height: str = "500px",
    chart_width: str = "800px",
    symbol_size: int = 12,
    **kwargs,
):
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

    # Read forecast
    forecast = read(object_path=outputs["forecasts"]["best_models"])
    scores = read(object_path=outputs["scores"]["best_models"])
    entity_col, time_col, target_col = forecast.columns
    entities = forecast.get_column(entity_col).unique()

    # Read uplift
    metric = SUPPORTED_ERROR_TYPE[fields["error_type"]]
    rolling_uplift = (
        read(object_path=f"artifacts/{objective_id}/rolling_uplift.parquet")
        .lazy()
        .sort(entity_col, "updated_at")
        .groupby(entity_col)
        .tail(1)
        .select(
            entity_col,
            (pl.col(f"{metric}__uplift__rolling_sum") * 100).alias(
                "score__uplift__rolling_sum"
            ),
        )
    )

    # Segmentation factor
    # Only predictability takes from `scores`, others take from `statistics`
    if segmentation_factor == "predictability":
        seg_factor_stat = (
            scores.lazy().select([entity_col, "crps"]).rename({"crps": "seg_factor"})
        )
    else:
        if segmentation_factor == "predicted growth rate":
            stat_key = f"{SEGMENTATION_FACTOR_TO_KEY[segmentation_factor]}__{source_fields.get('agg_method', 'sum')}"
        else:
            stat_key = SEGMENTATION_FACTOR_TO_KEY[segmentation_factor]
        seg_factor_stat = (
            read(object_path=outputs["statistics"][stat_key])
            .lazy()
            .pipe(lambda df: df.rename({df.columns[-1]: "seg_factor"}))
        )
        expr = SEGMENTATION_FACTOR_TO_EXPR[segmentation_factor]
        if expr is not None:
            seg_factor_stat = seg_factor_stat.groupby(entity_col).agg(expr)

    # Join uplift and segmentation factor
    data = rolling_uplift.join(seg_factor_stat, on=entity_col).collect(streaming=True)

    # Create scatterplot
    scatter = Scatter(
        init_opts=opts.InitOpts(
            bg_color="white", height=chart_height, width=chart_width
        )
    )

    # Add x and y data for each entity
    for entity in entities:
        filtered = data.filter(pl.col(entity_col) == entity).with_columns(
            # NOTE: Rounding doesn't work for float32.
            [
                pl.col("seg_factor").cast(pl.Float64).round(2),
                pl.col("score__uplift__rolling_sum").cast(pl.Float64).round(2),
            ]
        )
        x_data = filtered.get_column("seg_factor").to_list()
        y_data = filtered.get_column("score__uplift__rolling_sum").to_list()
        scatter.add_xaxis(xaxis_data=x_data)
        scatter.add_yaxis(
            series_name=entity,
            y_axis=y_data,
            symbol_size=symbol_size,
            label_opts=opts.LabelOpts(is_show=False),
        )

    scatter.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=False, border_width=0),
        xaxis_opts=opts.AxisOpts(
            name=f"Segmentation Factor ({segmentation_factor.title()})",
            name_location="middle",
            name_gap=30,
            type_="value",
        ),
        yaxis_opts=opts.AxisOpts(
            name="AI Uplift (Cumulative)", type_="value", is_scale=True
        ),
        tooltip_opts=opts.TooltipOpts(
            formatter="{a}: <br> (Segmentation Factor) {c} (AI Uplift)"
        ),
        visualmap_opts=opts.VisualMapOpts(
            is_piecewise=True,
            pieces=[
                {"min": float("-inf"), "max": 0, "color": "red", "label": "Baseline"},
                {"min": 0, "max": float("inf"), "color": "green", "label": "AI"},
            ],
            pos_top="top",
            pos_right="10%",
        ),
    )

    # Export chart options to JSON
    chart_json = scatter.dump_options()
    pl.toggle_string_cache(False)
    return chart_json


def create_rolling_forecasts_chart(user: User, objective_id: str, **kwargs):
    """
    Creates rolling forecasts chart using the baseline and rolling forecasts artifacts.
    The line chart includes baseline and forecasts based on the `updated_at` column.

    Returns a dictionary of {entity: chart_json} for each of the entities in the rolling forecasts.
    """
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
    rolling_forecasts = read(
        object_path=f"artifacts/{objective_id}/rolling_forecasts.parquet"
    )

    entity_col = rolling_forecasts.columns[0]
    entities = rolling_forecasts.get_column(entity_col).unique().to_list()

    _type_to_colors = {
        "ai": ["#003DFD"],
        "best_plan": ["#b512b8"],
        "baseline": ["#11a9ba"],
        "plan": ["#0a0a0a"],
    }
    _type_to_name = {
        "ai": "AI",
        "best_plan": "Best Plan",
        "baseline": "Baseline",
        "plan": "Plan",
    }

    # Reindex panel to get all time periods for each "updated_at"
    rolling_forecasts = rolling_forecasts.select(
        pl.col("updated_at"), pl.col("time"), pl.all().exclude(["updated_at", "time"])
    ).pipe(lambda x: _reindex_panel(X=x.lazy(), freq="1mo"))
    updated_dates = rolling_forecasts.get_column("updated_at").unique().to_list()

    output_json = {}
    for entity in entities:
        try:
            # Initial the chart objective
            line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
            for type, colors in _type_to_colors.items():
                # Create each lines based on the line_type
                colors_cycle = itertools.cycle(colors)
                # Get the x and y values for each line
                x_values = (
                    rolling_forecasts.filter(pl.col(entity_col) == entity)
                    .with_columns(pl.col("time").cast(pl.Date))
                    .filter(pl.col("updated_at") == updated_dates[-1])
                    .get_column("time")
                    .to_list()
                )
                y1 = (
                    rolling_forecasts.filter(pl.col(entity_col) == entity)
                    .filter(pl.col("updated_at") == updated_dates[-1])
                    .get_column(f"residual_{type}")
                    .to_list()
                )
                y2 = (
                    rolling_forecasts.filter(pl.col(entity_col) == entity)
                    .filter(pl.col("updated_at") == updated_dates[-2])
                    .get_column(f"residual_{type}")
                    .to_list()
                    if len(updated_dates) >= 2
                    else None
                )
                y3 = (
                    rolling_forecasts.filter(pl.col(entity_col) == entity)
                    .filter(pl.col("updated_at") == updated_dates[-3])
                    .get_column(f"residual_{type}")
                    .to_list()
                    if len(updated_dates) >= 3
                    else None
                )
                # Configure the default visibility option for chart legends
                selected_series = {
                    f"{_type_to_name[type]} ({date.strftime('%Y-%m-%d')})": False
                    for type in ["ai", "plan"]
                    for date in updated_dates
                }

                line_chart.add_xaxis(x_values)
                # Initial the check for empty values in line charts
                check_empty = False
                if y3 is not None:
                    check_empty = True if all(value is None for value in y3) else False
                    line_chart.add_yaxis(
                        f"{_type_to_name[type]} ({updated_dates[-3].strftime('%Y-%m-%d')})",
                        y3,
                        label_opts=opts.LabelOpts(is_show=False),
                        color=next(colors_cycle),
                        linestyle_opts=opts.LineStyleOpts(width=1, type_="dashed"),
                        is_symbol_show=True,
                        symbol_size=1,
                    )
                if y2 is not None:
                    check_empty = True if all(value is None for value in y2) else False
                    line_chart.add_yaxis(
                        f"{_type_to_name[type]} ({updated_dates[-2].strftime('%Y-%m-%d')})",
                        y2,
                        label_opts=opts.LabelOpts(is_show=False),
                        color=next(colors_cycle),
                        linestyle_opts=opts.LineStyleOpts(width=1, type_="dashed"),
                        is_symbol_show=True,
                        symbol_size=1,
                    )
                check_empty = True if all(value is None for value in y1) else False
                if check_empty is True:
                    raise ValueError(
                        f"There is no rolling forecasts data for {entity}..."
                    )
                line_chart.add_yaxis(
                    f"{_type_to_name[type]} ({updated_dates[-1].strftime('%Y-%m-%d')})",
                    y1,
                    label_opts=opts.LabelOpts(is_show=False),
                    color=next(colors_cycle),
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    symbol_size=7,
                )

                line_chart.set_global_opts(
                    legend_opts=opts.LegendOpts(
                        is_show=True,
                        orient="vertical",
                        align="right",
                        border_width=0,
                        pos_right="0%",
                        selected_map=selected_series,
                        textstyle_opts=opts.TextStyleOpts(font_size=10),
                    ),
                    xaxis_opts=opts.AxisOpts(
                        splitline_opts=opts.SplitLineOpts(is_show=False)
                    ),
                    yaxis_opts=opts.AxisOpts(
                        name="Residuals",
                        is_show=True,
                        splitline_opts=opts.SplitLineOpts(is_show=False),
                        offset=20,
                        is_scale=True,
                        axispointer_opts=opts.AxisPointerOpts(is_show=True),
                    ),
                )
                output_json[entity] = line_chart.dump_options()
        except ValueError:
            output_json[entity] = None
    logger.info(
        f"✔️ All rolling forecasts charts for {objective_id} are successfully created"
    )
    return output_json
