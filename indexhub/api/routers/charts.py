import json
from enum import Enum
from typing import List, Mapping

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.services.chart_builders import (
    _create_3d_cluster_chart,
    _create_multi_forecast_chart,
    _create_segmentation_chart,
    _create_single_forecast_chart,
)

router = APIRouter()


OBJECTIVE_TAG_TO_BUILDERS = {
    "forecast_panel": {
        "single_forecast": _create_single_forecast_chart,
        "multi_forecast": _create_multi_forecast_chart,
        "segment": _create_segmentation_chart,
        "3d_cluster": _create_3d_cluster_chart,
    }
}


class ChartTag(str, Enum):
    single_forecast = "single_forecast"
    multi_forecast = "multi_forecast"
    segment = "segment"


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
    "forecast_panel": {
        "single_forecast": TrendChartParams,
        "multi_forecast": TrendChartParams,
        "segment": SegChartParams,
    }
}


@router.post("/charts/{objective_id}/{chart_tag}")
async def get_chart(objective_id: str, chart_tag: ChartTag, request: Request):
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
            source_fields=json.loads(source.fields),
            user=user,
            objective_id=objective_id,
            **params,
        )

        return chart_json
