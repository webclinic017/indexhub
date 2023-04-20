import json
from enum import Enum
from typing import List, Mapping, Union

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.services.chart_builders import (
    _create_multi_forecast_chart,
    _create_segmentation_chart,
    _create_single_forecast_chart,
)

router = APIRouter()


POLICY_TAG_TO_BUILDERS = {
    "forecast_panel": {
        "single_forecast": _create_single_forecast_chart,
        "multi_forecast": _create_multi_forecast_chart,
        "segment": _create_segmentation_chart,
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
    agg_method: AggregationMethod = AggregationMethod.sum


class SegmentationFactor(str, Enum):
    volatility = "volatility"
    total_value = "total value"
    historical_growth_rate = "historical growth rate"
    predicted_growth_rate = "predicted growth rate"
    predictability = "predictability"


class SegChartParams(BaseModel):
    segmentation_factor: SegmentationFactor = SegmentationFactor.volatility


POLICY_TAG_TO_PARAMS = {
    "forecast_panel": {
        "single_forecast": TrendChartParams,
        "multi_forecast": TrendChartParams,
        "segment": SegChartParams,
    }
}


@router.post("/charts/{policy_id}/{chart_tag}")
async def get_chart(
    policy_id: str, chart_tag: ChartTag, request: Request
):
    with Session(engine) as session:
        # Get the metadata on tag to define which chart to return
        policy = get_policy(policy_id)["policy"]
        params = json.loads(await request.body())
        build = POLICY_TAG_TO_BUILDERS[policy.tag][chart_tag]
        user = session.get(User, policy.user_id)
        chart_json = build(
            fields=json.loads(policy.fields),
            outputs=json.loads(policy.outputs),
            user=user,
            policy_id=policy_id,
            **params,
        )

        return chart_json
