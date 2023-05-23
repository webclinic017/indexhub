import json
import logging
from functools import partial
from typing import Callable, Mapping, Optional

import altair as alt
import polars as pl
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.demos import DEMO_BUCKET, DEMO_SCHEMAS
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
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

pl.toggle_string_cache(True)


def _load_trend_datasets(
    read: Callable,
    paths: Mapping[str, str],
):
    actual = read(object_path=paths["y"])
    entity_col, time_col, target_col = actual.columns
    forecasts = read(object_path=paths["forecasts"])
    backtests = (
        read(object_path=paths["backtests"])
        .groupby([entity_col, time_col])
        .agg(pl.col(target_col).mean())
    )
    quantiles = read(object_path=paths["quantiles"])
    logger.info("Loaded trend datasets")
    return actual, forecasts, quantiles, backtests


def _create_trend_data(
    actual: pl.DataFrame,
    forecasts: pl.DataFrame,
    quantiles: pl.DataFrame,
    backtests: pl.DataFrame,
    entity_id: str,
    quantile_lower: int = 10,
    quantile_upper: int = 90,
    display_length: int = 24,
) -> pl.DataFrame:
    # pl.toggle_string_cache(True)
    entity_col, time_col, target_col = forecasts.columns
    actual = actual.rename({target_col: "actual"})
    quantiles_lower = (
        quantiles.filter(pl.col("quantile") == quantile_lower)
        .drop("quantile")
        .rename({target_col: f"{quantile_lower}%"})
    )
    quantiles_upper = (
        quantiles.filter(pl.col("quantile") == quantile_upper)
        .drop("quantile")
        .rename({target_col: f"{quantile_upper}%"})
    )

    # Join tables
    chart_data = (
        actual.join(
            pl.concat([backtests, forecasts]).rename({target_col: "target"}),
            on=[entity_col, time_col],
            how="outer",
        )
        .join(quantiles_lower, on=[entity_col, time_col], how="outer")
        .join(quantiles_upper, on=[entity_col, time_col], how="outer")
        .filter(pl.col(entity_col) == entity_id)
        .drop(entity_col)
        .sort(time_col)
        # Round all floats to 2 decimal places
        # NOTE: Rounding not working for Float32
        .with_columns(pl.col([pl.Float64, pl.Float32]).cast(pl.Float64).round(2))
    )

    if len(chart_data) > display_length:
        chart_data = chart_data.tail(display_length)

    # pl.toggle_string_cache(False)
    logger.info("Created trend data")
    return chart_data


def _create_trend_chart(chart_data: pl.DataFrame):
    time_col = chart_data.columns[0]

    # Get trend direction
    start_value = chart_data.head(1).get_column("actual")[0]
    end_value = chart_data.tail(1).get_column("target")[0]
    if end_value >= start_value:
        direction = "#44AA7E"
    else:
        direction = "#9E2B2B"

    # Create range to scale y
    min_value = chart_data.select(chart_data.columns[1:]).min().min(axis=1)[0]
    max_value = chart_data.select(chart_data.columns[1:]).max().max(axis=1)[0]

    # Create chart
    pd_chart_df = chart_data.to_pandas()

    actual_line = (
        alt.Chart(pd_chart_df)
        .mark_line(color="gray")
        .encode(
            x=alt.X(
                f"{time_col}:T",
                axis=alt.Axis(labelAngle=45, format="%Y-%b"),
                title="Time",
            ),
            y=alt.Y(
                "actual:Q",
                title=None,
                scale=alt.Scale(domain=(min_value, max_value)),
                axis=None,
            ),
        )
    )

    forecast_line = (
        alt.Chart(pd_chart_df)
        .mark_line(color=direction)
        .encode(
            x=f"{time_col}:T",
            y="target:Q",
        )
    )

    area = (
        alt.Chart(pd_chart_df)
        .mark_area(opacity=0.3)
        .encode(x=f"{time_col}:T", y="10%:Q", y2="90%:Q")
    )

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=[time_col], empty="none"
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(pd_chart_df)
        .mark_point()
        .encode(
            x=f"{time_col}:T",
            opacity=alt.value(0),
        )
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    forecast_points = forecast_line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    forecast_text = forecast_line.mark_text(
        color="#101010", align="left", dx=5, dy=-5
    ).encode(text=alt.condition(nearest, "target:Q", alt.value(" ")))

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(pd_chart_df)
        .mark_rule(color="gray")
        .encode(
            x=f"{time_col}:T",
        )
        .transform_filter(nearest)
    )

    chart = (
        alt.layer(
            actual_line,
            forecast_line,
            area,
            selectors,
            rules,
            forecast_points,
            forecast_text,
        )
        .configure(font="Inter")
        .configure_axis(grid=False)
        .configure_view(strokeWidth=0)
        .properties(height=100, width="container")
    )
    logger.info("Created trend chart")
    return chart


class EmbeddingsParams(BaseModel):
    dim_size: Optional[int] = 3


@router.post("/trends/public/vectors/{dataset_id}")
def get_public_embs(dataset_id: str, params: EmbeddingsParams):
    dim_size = params.dim_size
    read = partial(
        SOURCE_TAG_TO_READER["s3"],
        bucket_name=DEMO_BUCKET,
        file_ext="lance",
    )
    entity_col = DEMO_SCHEMAS[dataset_id]["entity_col"]
    path = DEMO_SCHEMAS[dataset_id]["vectors"]
    data = read(
        object_path=path, columns=[entity_col, f"emb(n={dim_size})", "cluster_id"]
    )
    # Return spec for scatter gl
    # TODO: Replace labels with cluster IDs and add entities field
    spec = {
        "ids": list(range(len(data))),
        "clusters": list(range(len(data))),
        "entityIds": data.get_column(entity_col).to_list(),
        "projections": data.get_column(f"emb(n={dim_size})").to_list(),
    }
    return spec


@router.get("/trends/private/vectors/{objective_id}")
def get_private_embs(objective_id: int, dim_size: int = 3):
    pass


@router.get("/trends/public/charts/{dataset_id}/{entity_id}")
def get_public_trend_chart(dataset_id: str, entity_id: str):
    # pl.toggle_string_cache(True)
    read = partial(
        SOURCE_TAG_TO_READER["s3"],
        bucket_name=DEMO_BUCKET,
        file_ext="parquet",
    )
    # Read artifacts
    paths = DEMO_SCHEMAS[dataset_id]
    trend_datasets = _load_trend_datasets(read, paths)
    chart_data = _create_trend_data(
        *trend_datasets,
        entity_id=entity_id,
    )
    # Create chart
    chart = _create_trend_chart(chart_data).to_json()
    # pl.toggle_string_cache(False)
    return chart


@router.get("/trends/private/charts/{objective_id}/{entity_id}")
def get_private_trend_chart(objective_id: int, entity_id: str):
    engine = create_sql_engine()
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        user = session.get(User, objective.user_id)
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
        outputs = json.loads(objective.outputs)
        paths = {
            "y": outputs["y"],
            "forecasts": outputs["forecasts"]["best_models"],
            "backtests": outputs["backtests"]["best_models"],
            "quantiles": outputs["quantiles"]["best_models"],
        }
        trend_datasets = _load_trend_datasets(read, paths)
        chart_data = _create_trend_data(
            *trend_datasets,
            entity_id=entity_id,
        )
        # Create chart
        chart = _create_trend_chart(chart_data).to_json()
    return chart
