from functools import partial, reduce
from typing import Any, Literal, Mapping

import polars as pl
from pyecharts import options as opts
from pyecharts.charts import Grid, Line, Scatter

from indexhub.api.models.user import User
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


def _create_single_forecast_chart(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    policy_id: str,
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    agg_method: Literal["sum", "mean"] = "sum",
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

    # Read artifacts
    best_model = outputs["best_model"]
    forecast = read(object_path=outputs["forecasts"][best_model])
    backtest = read(object_path=outputs["backtests"][best_model]).pipe(
        lambda df: df.groupby(df.columns[:2]).agg(pl.mean(df.columns[-2]))
    )
    actual = read(object_path=outputs["y"])

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col

    # Postproc - join data together and rename colname
    dfs = {"actual": actual, "backtest": backtest, "forecast": forecast}

    data = []
    for colname, df in dfs.items():
        if colname in ["backtest", "forecast"]:
            colname = "indexhub"
        data.append(
            df.with_columns(
                [pl.col(entity_col).cast(pl.Utf8), pl.col(target_col).alias(colname)]
            )
        )

    indexhub = pl.concat([data[1], data[2]])
    joined = (
        data[0]
        .join(indexhub, on=idx_cols, how="outer")
        .select(pl.exclude("^target.*$"))
        .sort("time")
        .rename({entity_col: "entity"})
    )
    inventory_path = outputs["inventory"]
    if inventory_path:
        inventory_data = read(object_path=inventory_path).pipe(
            lambda df: df.rename({df.columns[-1]: "inventory"})
        )
        joined = joined.join(inventory_data, on=idx_cols, how="outer")

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
    chart_data = (
        joined.groupby(group_by_cols)
        .agg(agg_exprs)
        .sort(pl.col(time_col))
        .with_columns([pl.col(pl.Float32).round(2), pl.col(pl.Float64).round(2)])
    )

    # Set color scheme based on guidelines
    colors = ["#0a0a0a", "#194fdc", "#44aa7e"]

    # Generate the chart options
    line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
    line_chart.add_xaxis(chart_data[time_col].to_list())

    line_chart.add_yaxis(
        "Actual", chart_data["actual"].to_list(), color=colors[0], symbol=None
    )
    line_chart.add_yaxis(
        "Indexhub", chart_data["indexhub"].to_list(), color=colors[1], symbol=None
    )
    if inventory_path:
        line_chart.add_yaxis(
            "Inventory", chart_data["inventory"].to_list(), color=colors[2], symbol=None
        )

    line_chart.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False)
    ).set_global_opts(
        legend_opts=opts.LegendOpts(orient="right", align="right", pos_right=100),
        xaxis_opts=opts.AxisOpts(
            type_=time_col,
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(is_show=False),
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(is_show=False),
        ),
    )

    # Export chart options to JSON
    chart_json = line_chart.dump_options()
    return chart_json


def _create_multi_forecast_chart(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    policy_id: str,
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    agg_method: Literal["sum", "mean"] = "sum",
    top_k: int = 6,
    num_cols: int = 3,
    chart_height: str = "300px",
    gap: str = "5%",
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
    best_model = outputs["best_model"]
    forecast = read(object_path=outputs["forecasts"][best_model])
    backtest = read(object_path=outputs["backtests"][best_model]).pipe(
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
            legend_opts=opts.LegendOpts(pos_right="20%"),
            xaxis_opts=opts.AxisOpts(
                type_="time", splitline_opts=opts.SplitLineOpts(is_show=False)
            ),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
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


def _create_segmentation_chart(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
    user: User,
    policy_id: str,
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
    # Added following params to silence undefined params error, might have to think of a better solution here
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    agg_method: Literal["sum", "mean"] = "sum",
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
    best_model = outputs["best_model"]
    forecast = read(object_path=outputs["forecasts"][best_model])
    scores = read(object_path=outputs["scores"][best_model])
    entity_col, time_col, target_col = forecast.columns
    entities = forecast.get_column(entity_col).unique()

    # Read uplift
    metric = SUPPORTED_ERROR_TYPE[fields["error_type"]]
    rolling_uplift = (
        read(object_path=f"artifacts/{policy_id}/rolling_uplift.parquet")
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
        filtered = data.filter(pl.col(entity_col) == entity)
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
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            name=f"Segmentation Factor ({segmentation_factor.title()})",
            name_location="middle",
            name_gap=30,
            type_="value",
        ),
        yaxis_opts=opts.AxisOpts(
            name="AI Uplift (Cumulative)",
            type_="value",
        ),
        tooltip_opts=opts.TooltipOpts(formatter="{a}: {c}"),
        visualmap_opts=opts.VisualMapOpts(
            is_piecewise=True,
            pieces=[
                {"min": float("-inf"), "max": 0, "color": "red", "label": "Benchmark"},
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
