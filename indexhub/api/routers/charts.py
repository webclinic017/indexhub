import json
from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional
from fastapi import APIRouter
from indexhub.api.db import engine
from indexhub.api.services.io import read_data_from_s3
from indexhub.api.services.chart_builders import create_trend_chart

router = APIRouter()

class TrendChartParams(BaseModel):
    policy_id: str
    entity_id: Optional[str]

@router.post("/charts/trend_chart")
def get_trend_chart(params: TrendChartParams):
    with Session(engine) as session:

        # Hardcoded values to be pulled from Policy.outputs and params.policy_id
        policy_id = 2
        bucket_name = "indexhub-demo"
        actual_path = f"artifacts/{policy_id}/actual.parquet"
        backtest_path = f"artifacts/{policy_id}/backtest.parquet"
        forecast_path = f"artifacts/{policy_id}/forecast.parquet"
        

        actual_df = read_data_from_s3(bucket_name=bucket_name, object_path=actual_path, file_ext="parquet")
        backtest_df = read_data_from_s3(bucket_name=bucket_name, object_path=backtest_path, file_ext="parquet")
        forecast_df = read_data_from_s3(bucket_name=bucket_name, object_path=forecast_path, file_ext="parquet")

        trend_chart_json = json.loads(create_trend_chart(actual=actual_df, backtest=backtest_df, forecast=forecast_df))
        print(trend_chart_json)
        return trend_chart_json