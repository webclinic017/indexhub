from enum import Enum
from typing import List, Mapping

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session
import json

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.services.chart_builders import (
    _create_multi_forecast_chart,
    _create_single_forecast_chart,
)

router = APIRouter()

POLICY_TAG_TO_BUILDERS = {
    "forecast": {
        "single_forecast": _create_single_forecast_chart,
        "multi_forecast": _create_multi_forecast_chart,
    }
}


class AggregationMethod(str, Enum):
    sum = "sum"
    mean = "mean"


class ChartTag(str, Enum):
    single_forecast = "single_forecast"
    multi_forecast = "multi_forecast"


class TrendChartParams(BaseModel):
    policy_id: str
    chart_tag: ChartTag
    filter_by: Mapping[str, List[str]]
    agg_by: str = None
    agg_method: AggregationMethod = AggregationMethod.sum


@router.post("/charts/{policy_id}/{chart_tag}")
def get_chart(params: TrendChartParams):
    with Session(engine) as session:
        # Get the metadata on tag to define which chart to return
        policy = get_policy(params.policy_id)["policy"]
        build = POLICY_TAG_TO_BUILDERS[policy.tag][params.chart_tag]
        user = session.get(User, policy.user_id)
        trend_chart_json = build(
            json.loads(policy.fields),
            json.loads(policy.outputs),
            user,
            params.filter_by,
            params.agg_by,
            params.agg_method,
        )

        return trend_chart_json
