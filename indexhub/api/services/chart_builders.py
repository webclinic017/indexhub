import itertools
from functools import partial, reduce
from typing import Any, Literal, Mapping

import lance
import polars as pl
from pyecharts import options as opts
from pyecharts.charts import Grid, Line, Scatter, Scatter3D
from pyecharts.commons.utils import JsCode

from indexhub.api.models.user import User
from indexhub.api.routers.stats import AGG_METHODS
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.flows.preprocess import _reindex_panel


def create_single_forecast_chart(
    outputs: Mapping[str, str],
    source_fields: Mapping[str, str],
    user: User,
    filter_by: Mapping[str, Any] = None,
    agg_by: str = None,
    quantile_lower: int = 10,
    quantile_upper: int = 90,
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

    # Read artifacts
    forecast = read(object_path=outputs["forecasts"]["best_models"])
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

    entity_col, time_col, target_col = forecast.columns
    idx_cols = entity_col, time_col
    agg_method = source_fields["agg_method"]

    # Postproc - join data together
    indexhub = pl.concat(
        [
            backtest.rename({target_col: "indexhub"}),
            forecast.rename({target_col: "indexhub"}),
        ]
    )
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
            quantiles_lower.rename({target_col: f"indexhub_{quantile_lower}"}),
            on=idx_cols,
            how="outer",
        )
        .join(
            quantiles_upper.rename({target_col: f"indexhub_{quantile_upper}"}),
            on=idx_cols,
            how="outer",
        )
        .select(pl.exclude("^target.*$"))
        .sort("time")
    )
    inventory_path = outputs["inventory"]
    if inventory_path:
        inventory_data = (
            read(object_path=inventory_path)
            .pipe(lambda df: df.rename({target_col: "inventory"}))
            .with_columns(pl.col(entity_col).cast(pl.Categorical))
        )
        joined = joined.join(inventory_data, on=idx_cols, how="outer")

    # Rename entity col
    joined = joined.rename({entity_col: "entity"})

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
    colors = ["#0a0a0a", "#194fdc", "#44aa7e", "#b56321"]

    # Generate the chart options
    line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
    line_chart.add_xaxis(chart_data[time_col].to_list())

    line_chart.add_yaxis(
        "Actual", chart_data["actual"].to_list(), color=colors[0], symbol=None
    )
    line_chart.add_yaxis(
        "Indexhub", chart_data["indexhub"].to_list(), color=colors[1], symbol=None
    )
    line_chart.add_yaxis(
        "Baseline",
        chart_data["baseline"].to_list(),
        color=colors[3],
        symbol=None,
    )
    line_chart.add_yaxis(
        "",
        chart_data[f"indexhub_{quantile_upper}"].to_list(),
        color="lightblue",
        symbol=None,
        is_symbol_show=False,
        areastyle_opts=opts.AreaStyleOpts(opacity=0.2, color="grey"),
    )
    line_chart.add_yaxis(
        "",
        chart_data[f"indexhub_{quantile_lower}"].to_list(),
        color="lightblue",
        symbol=None,
        is_symbol_show=False,
        areastyle_opts=opts.AreaStyleOpts(opacity=1, color="white"),
    )
    if inventory_path:
        line_chart.add_yaxis(
            "Inventory", chart_data["inventory"].to_list(), color=colors[2], symbol=None
        )

    # Get the range of the x-axis
    x_data = sorted(chart_data[time_col].to_list())
    initial_range = ((len(x_data) - 12) / len(x_data)) * 100
    if len(x_data) <= 12:
        initial_range = 0

    line_chart.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False)
    ).set_global_opts(
        legend_opts=opts.LegendOpts(
            orient="horizontal",
            align="right",
            pos_right=100,
        ),
        xaxis_opts=opts.AxisOpts(
            type_=time_col,
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(is_show=False),
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(is_show=False),
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

    # Export chart options to JSON
    chart_json = line_chart.dump_options()
    return chart_json


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


def create_segmentation_chart(
    fields: Mapping[str, str],
    outputs: Mapping[str, str],
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
        if segmentation_factor == "predicted_growth_rate":
            stat_key = SEGMENTATION_FACTOR_TO_KEY[
                f"{segmentation_factor}__{fields['agg_method']}"
            ]
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


def create_3d_cluster_chart(outputs: Mapping[str, str], user: User, **kwargs):
    # Get bucket and path
    bucket_name = user.storage_bucket_name
    path = outputs["embeddings"]["cluster"]

    # Load .lance directory and parse as pl.DataFrame
    lance_obj = lance.dataset(f"s3://{bucket_name}/{path}/")
    data = pl.from_arrow(lance_obj.to_table())
    # Unpack columns from data
    product_col = data.columns[0]
    cluster_col = data.columns[-1]
    # Define colors with darker theme and set cycler
    colors = [
        "#4D2A7F",
        "#6D4DBE",
        "#9B9EEC",
        "#A5E1AD",
        "#8BD46C",
        "#58B033",
        "#28A08B",
        "#1F6D65",
        "#204051",
        "#292F36",
    ]
    colors_cycle = itertools.cycle(colors)

    # Scale 3D axes to origin and remove gridlines
    axis3d_opts = opts.Axis3DOpts(
        type_="value",
        name=" ",
        is_scale=True,
        splitline_opts=opts.SplitLineOpts(is_show=False),
    )
    # Get unique clusters - filter out unclustered data ("-1")
    clusters = (
        data.filter(pl.col(cluster_col) >= 0).get_column(cluster_col).unique().to_list()
    )
    # Create scatter plot based on each cluster id
    cluster_3d = Scatter3D(init_opts=opts.InitOpts(bg_color="white"))
    for cluster_id in clusters:
        df = (
            data.filter(pl.col(cluster_col) == cluster_id)
            .select(
                pl.all().exclude(product_col, cluster_col),
                pl.col(product_col),
                pl.col(cluster_col),
            )
            .to_numpy()
            .tolist()
        )
        cluster_3d.add(
            "",
            df,
            itemstyle_opts=opts.ItemStyleOpts(color=next(colors_cycle)),
            grid3d_opts=opts.Grid3DOpts(
                is_show=False,
                height=100,
                width=100,
                depth=100,
                axislabel_opts=opts.AxisLineOpts(is_show=False),  # removes axis labels
                axistick_opts=opts.AxisTickOpts(is_show=False),  # removes axis ticks
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=False
                ),  # Removes 3d axis pointers
                axisline_opts=opts.AxisLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(opacity=0.5)
                ),  # Axis lines
            ),
            xaxis3d_opts=axis3d_opts,
            yaxis3d_opts=axis3d_opts,
            zaxis3d_opts=axis3d_opts,
        ).set_series_opts(
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    # params.value is based on columns in the zip passed in final_y
                    "function (params) {return params.value[3] + '<br>' + 'Cluster: ' + params.value[4];}"
                ),
                position="top",
            ),
        ).set_global_opts(
            legend_opts=opts.LegendOpts(is_show=False),
            visualmap_opts=[
                # Set the size of the dots to fixed size
                opts.VisualMapOpts(
                    type_="size",
                    range_size=[5, 5],  # set fixed size at 50% normal size
                    is_show=False,
                ),
            ],
        )
    return cluster_3d.dump_options()


def create_rolling_forecasts_chart(user: User, objective_id: str, **kwargs):
    """
    Creates rolling forecasts chart using the baseline and rolling forecasts artifacts.
    The line chart includes baseline and forecasts based on the `updated_at` column.

    Returns a dictionary of {entity: chart_json} for each of the entities in the rolling forecasts.
    """
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
        "ai": ["#14399a", "#1b57f1", "#194fdc"],
        "best_plan": ["#177548", "#2A9162", "#44aa7e"],
        "baseline": ["#7F3808", "#994C17", "#b56321"],
        # TODO: Add plan after implemented in flow
        # "plan": ["#0a0a0a", "#666666", "#9e9e9e"],
    }
    _type_to_name = {
        "ai": "AI",
        "best_plan": "Best Plan",
        "baseline": "Baseline",
        # TODO: Add plan after implemented in flow
        # "plan": "Plan",
    }

    # Reindex panel to get all time periods for each "updated_at"
    rolling_forecasts = rolling_forecasts.select(
        pl.col("updated_at"), pl.col("time"), pl.all().exclude(["updated_at", "time"])
    ).pipe(lambda x: _reindex_panel(X=x.lazy(), freq="1mo"))

    output_json = {}
    for entity in entities:
        updated_dates = rolling_forecasts.get_column("updated_at").unique().to_list()

        line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
        for type, colors in _type_to_colors.items():
            # Create each lines based on the line_type
            colors_cycle = itertools.cycle(colors)

            rolling_latest = rolling_forecasts.filter(
                pl.col("updated_at") == updated_dates[-1]
            )
            rolling_second = (
                rolling_forecasts.filter(pl.col("updated_at") == updated_dates[-2])
                if len(updated_dates) >= 2
                else None
            )
            rolling_third = (
                rolling_forecasts.filter(pl.col("updated_at") == updated_dates[-3])
                if len(updated_dates) >= 3
                else None
            )
            x_values = (
                rolling_latest.with_columns(pl.col("time").cast(pl.Date))
                .get_column("time")
                .to_list()
            )
            y_d1 = rolling_latest.get_column(f"residual_{type}").to_list()
            selected_series = {
                f"{_type_to_name[type]} ({date.strftime('%Y-%m-%d')})": False
                for type in ["ai"]  # TODO: Add "plan" after it is implemented
                for date in updated_dates
            }

            line_chart.add_xaxis(x_values)
            line_chart.add_yaxis(
                f"{_type_to_name[type]} ({updated_dates[-1].strftime('%Y-%m-%d')})",
                y_d1,
                label_opts=opts.LabelOpts(is_show=False),
                color=next(colors_cycle),
                linestyle_opts=opts.LineStyleOpts(width=3),
                symbol_size=7,
            )
            if rolling_second is not None:
                y_d2 = rolling_second.get_column(f"residual_{type}").to_list()
                line_chart.add_yaxis(
                    f"{_type_to_name[type]} ({updated_dates[-2].strftime('%Y-%m-%d')})",
                    y_d2,
                    label_opts=opts.LabelOpts(is_show=False),
                    color=next(colors_cycle),
                    linestyle_opts=opts.LineStyleOpts(width=1, type_="dashed"),
                    symbol_size=1,
                )
            if rolling_third is not None:
                y_d3 = rolling_third.get_column(f"residual_{type}").to_list()
                line_chart.add_yaxis(
                    f"{_type_to_name[type]} ({updated_dates[-3].strftime('%Y-%m-%d')})",
                    y_d3,
                    label_opts=opts.LabelOpts(is_show=False),
                    color=next(colors_cycle),
                    linestyle_opts=opts.LineStyleOpts(width=1, type_="dotted"),
                    symbol_size=1,
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
            xaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=False)),
            yaxis_opts=opts.AxisOpts(
                name="Residuals",
                is_show=True,
                splitline_opts=opts.SplitLineOpts(is_show=False),
                offset=20,
                is_scale=True,
            ),
        )
        output_json[entity] = line_chart.dump_options()

    return output_json
