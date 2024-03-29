import json
import logging
from enum import Enum
from typing import List, Mapping

from fastapi import Request
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.services.chart_builders import (
    create_multi_forecast_chart,
    create_rolling_forecasts_chart,
    create_segmentation_chart,
    create_single_forecast_chart,
)


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

OBJECTIVE_TAG_TO_BUILDERS = {
    "reduce_errors": {
        "single_forecast": create_single_forecast_chart,
        "multi_forecast": create_multi_forecast_chart,
        "segment": create_segmentation_chart,
        "rolling_forecast": create_rolling_forecasts_chart,
    }
}


class ChartTag(str, Enum):
    single_forecast = "single_forecast"
    multi_forecast = "multi_forecast"
    segment = "segment"
    cluster_3d = "cluster_3d"
    rolling_forecast = "rolling_forecast"


class AggregationMethod(str, Enum):
    sum = "sum"
    mean = "mean"


class TrendChartParams(BaseModel):
    filter_by: Mapping[str, List[str]] = None
    agg_by: str = None


class SegmentationFactor(str, Enum):
    volatility = "volatility"
    total_value = "total value"
    historical_growth_rate = "historical growth rate"
    predicted_growth_rate = "predicted growth rate"
    predictability = "predictability"


class SegChartParams(BaseModel):
    segmentation_factor: SegmentationFactor = SegmentationFactor.volatility


OBJECTIVE_TAG_TO_PARAMS = {
    "reduce_errors": {
        "single_forecast": TrendChartParams,
        "multi_forecast": TrendChartParams,
        "segment": SegChartParams,
    }
}


@router.post("/charts/{objective_id}/{chart_tag}")
async def get_chart(objective_id: str, chart_tag: ChartTag, request: Request):
    try:
        chart_json = None
        engine = create_sql_engine()
        with Session(engine) as session:
            # Get the metadata on tag to define which chart to return
            objective = get_objective(objective_id)["objective"]
            params = json.loads(await request.body())
            build = OBJECTIVE_TAG_TO_BUILDERS[objective.tag][chart_tag]
            user = session.get(User, objective.user_id)
            source = get_source(json.loads(objective.sources)["panel"])["source"]
            chart_json = build(
                fields=json.loads(objective.fields),
                outputs=json.loads(objective.outputs),
                source_fields=json.loads(source.data_fields),
                user=user,
                objective_id=objective_id,
                **params,
            )
    except Exception as err:
        logger.exception(f"Error in get_chart: {err}")
        raise err

    return chart_json
