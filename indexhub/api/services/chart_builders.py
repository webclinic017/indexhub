import pandas as pd
import polars as pl
from functools import reduce
from pyecharts.charts import Line
from pyecharts import options as opts
import json

def create_trend_chart(
    actual: pd.DataFrame, backtest: pd.DataFrame, forecast: pd.DataFrame
):
    
    # Postproc - join data together and rename colname
    dfs = {"actual": actual, "backtest": backtest, "forecast": forecast}
    join_keys = ["entity", "time"]

    data = []
    for colname, df in dfs.items():
        if colname in ["backtest", "forecast"]:
            colname = "indexhub"
        data.append(
            df.with_columns(
                [pl.col("entity").cast(pl.Utf8), pl.col("target").alias(colname)]
            )
        )

    joined_data = reduce(
        lambda left, right: left.join(right, on=join_keys, how="outer").select(
            pl.exclude("^target.*$")
        ),
        data,
    )

   
    # Wrangle chart data
    chart_data = joined_data.to_pandas().reset_index(drop=True).drop(["entity"], axis=1).groupby("time").sum().round(2).reset_index()
    
    # Set color scheme based on guidelines
    colors = ["#0a0a0a", "#194fdc"]

    line_charts = []

    # Create line chart
    line_chart = Line(init_opts=opts.InitOpts(bg_color="white"))
    line_chart.add_xaxis(chart_data["time"].tolist())

    line_chart.add_yaxis(
        "Actual", chart_data["actual"].tolist(), color=colors[0], symbol=None
    )
    line_chart.add_yaxis(
        "Indexhub", chart_data["indexhub"].tolist(), color=colors[1], symbol=None
    )

    line_chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title="Actual vs Indexhub Forecast (Backtest + Forecast)"
        ),
        legend_opts=opts.LegendOpts(),
        xaxis_opts=opts.AxisOpts(type_="time"),
    )
    # remove the text label
    line_chart.set_series_opts(label_opts=opts.LabelOpts(is_show=False))

    line_charts.append(line_chart)

    # Render all line charts in a grid
    grid_chart = (
        Line(init_opts=opts.InitOpts(width="1500px", bg_color="white"))
        .overlap(*line_charts)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=None),
            legend_opts=opts.LegendOpts(pos_right="20%"),
            xaxis_opts=opts.AxisOpts(
                type_="time", splitline_opts=opts.SplitLineOpts(is_show=False)
            ),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
            ),
        )
    )

    # Export chart options to JSON
    chart_json = grid_chart.dump_options()
    return chart_json