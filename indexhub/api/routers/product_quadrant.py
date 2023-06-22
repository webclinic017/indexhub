import json
import logging
from typing import Any, List, Mapping, Optional, Tuple

import polars as pl
from pydantic import BaseModel
from pyecharts import options as opts
from pyecharts.charts import Line, Scatter
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
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


class Columns(BaseModel):
    field: str
    headerName: str
    aggregation: Optional[str] = None
    type: str  # string or number


def _create_product_quadrant_table(
    staging_path: str, user: User, product_col: str, quantity_col: str, value_col: str
) -> Tuple[pl.DataFrame, List[Mapping[str, str]]]:
    # Read staging data with specific cols
    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )
    staging_data = SOURCE_TAG_TO_READER[user.storage_tag](
        object_path=staging_path,
        bucket_name=user.storage_bucket_name,
        file_ext="parquet",
        **storage_creds,
    )

    # Create product quadrant df
    entity_col = staging_data.columns[0]
    entity_cols = entity_col.split("__")
    product_quadrant = (
        staging_data.with_columns(
            pl.col(entity_col)
            .cast(pl.Utf8)
            .str.split_exact(" - ", len(entity_cols))
            .struct.rename_fields(entity_cols)
            .alias("entities")
        )
        .drop(entity_col)
        .unnest("entities")
        .groupby(product_col)
        .agg([pl.col(quantity_col).sum(), pl.col(value_col).sum()])
    )

    # Assign product quadrant column
    quantity_mean = product_quadrant.get_column(quantity_col).mean()
    value_mean = product_quadrant.get_column(value_col).mean()

    rows = product_quadrant.with_columns(
        pl.when(
            (pl.col(quantity_col) >= quantity_mean) & (pl.col(value_col) >= value_mean)
        )
        .then("Top Right")
        .otherwise(
            pl.when(
                (pl.col(quantity_col) < quantity_mean)
                & (pl.col(value_col) >= value_mean)
            )
            .then("Top Left")
            .otherwise(
                pl.when(
                    (pl.col(quantity_col) >= quantity_mean)
                    & (pl.col(value_col) < value_mean)
                )
                .then("Bottom Right")
                .otherwise("Bottom Left")
            )
        )
        .alias("product_quadrant")
    ).sort(product_col)

    columns = [
        Columns(
            field=col,
            headerName=col.replace("_", " ").title(),
            aggregation="sum" if dtype in pl.NUMERIC_DTYPES else None,
            type="number" if dtype in pl.NUMERIC_DTYPES else "string",
        ).__dict__
        for col, dtype in rows.schema.items()
    ]
    return rows, columns


def _create_product_quadrant_chart(
    chart_data: pl.DataFrame,
    product_col: str,
    quantity_col: str,
    value_col: str,
    chart_height: str = "500px",
    chart_width: str = "800px",
    symbol_size: int = 5,
):
    # Create scatterplot
    scatter = Scatter(
        init_opts=opts.InitOpts(
            bg_color="white", height=chart_height, width=chart_width
        )
    )
    products = chart_data.get_column(product_col).unique()
    for product in products:
        filtered = chart_data.filter(pl.col(product_col) == product)
        x_data = filtered.get_column(quantity_col).to_list()
        y_data = filtered.get_column(value_col).to_list()
        scatter.add_xaxis(xaxis_data=x_data)
        scatter.add_yaxis(
            series_name=product,
            y_axis=y_data,
            symbol_size=symbol_size,
            label_opts=opts.LabelOpts(is_show=False),
            color="#1B57F1",
        )

    quantity_caption = quantity_col.replace("_", " ").title()
    value_caption = value_col.replace("_", " ").title()
    quantity_mean = chart_data.get_column(quantity_col).mean()
    value_mean = chart_data.get_column(value_col).mean()
    quantity_max = chart_data.get_column(quantity_col).max()
    value_max = chart_data.get_column(value_col).max()
    quantity_min = chart_data.get_column(quantity_col).min()
    value_min = chart_data.get_column(value_col).min()

    scatter.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=False, border_width=0),
        xaxis_opts=opts.AxisOpts(
            name=quantity_caption,
            name_location="middle",
            name_gap=30,
            type_="value",
            min_=quantity_min,
            max_=quantity_max,
        ),
        yaxis_opts=opts.AxisOpts(
            name=value_caption, type_="value", min_=value_min, max_=value_max
        ),
        tooltip_opts=opts.TooltipOpts(
            formatter="{a}: <br> "
            + f"({quantity_caption})"
            + " {c} "
            + f"({value_caption})"
        ),
    )

    # Create lines
    vertical_line = (
        Line()
        .add_xaxis([quantity_mean, quantity_mean])
        .add_yaxis(
            f"Mean of {quantity_caption}",
            [0, value_max],
            linestyle_opts=opts.LineStyleOpts(color="#5A5A5A", type_="dashed"),
            is_symbol_show=False,
        )
    )

    horizontal_line = (
        Line()
        .add_xaxis([0, quantity_max])
        .add_yaxis(
            f"Mean of {value_caption}",
            [value_mean, value_mean],
            linestyle_opts=opts.LineStyleOpts(color="#5A5A5A", type_="dashed"),
            is_symbol_show=False,
        )
    )

    scatter = scatter.overlap(vertical_line).overlap(horizontal_line)
    return scatter.dump_options()


@router.post("/product_quadrant/table/{objective_id}")
def get_product_quadrant_table(
    objective_id: str,
) -> Mapping[str, List[Mapping[str, Any]]]:
    objective = get_objective(objective_id)["objective"]
    source = get_source(json.loads(objective.sources)["panel"])["source"]
    fields = json.loads(objective.fields)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    product_col = fields.get("product_col")
    quantity_col = fields.get("quantity_col")
    value_col = fields.get("value_col")
    if product_col and quantity_col and value_col:
        rows, columns = _create_product_quadrant_table(
            staging_path=source.output_path,
            user=user,
            product_col=product_col,
            quantity_col=quantity_col,
            value_col=value_col,
        )
        response = {"columns": columns, "rows": rows.with_row_count("id").to_dicts()}
    else:
        response = None

    return response


@router.post("/product_quadrant/chart/{objective_id}")
def get_product_quadrant_chart(objective_id: str):
    objective = get_objective(objective_id)["objective"]
    source = get_source(json.loads(objective.sources)["panel"])["source"]
    fields = json.loads(objective.fields)

    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, objective.user_id)

    product_col = fields.get("product_col")
    quantity_col = fields.get("quantity_col")
    value_col = fields.get("value_col")
    if product_col and quantity_col and value_col:
        kwargs = {
            "product_col": product_col,
            "quantity_col": quantity_col,
            "value_col": value_col,
        }
        chart_data, _ = _create_product_quadrant_table(
            staging_path=source.output_path, user=user, **kwargs
        )
        chart_json = _create_product_quadrant_chart(chart_data=chart_data, **kwargs)
    else:
        chart_json = None

    return chart_json
