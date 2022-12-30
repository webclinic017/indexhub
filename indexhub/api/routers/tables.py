import json
from datetime import datetime
from typing import Dict, List, Union

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.models.table import Table
from indexhub.api.utils.init_db import engine

router = APIRouter()


class ForecastRecommendationsTimeSeries(BaseModel):
    time: list[datetime]
    month_year: list[str]
    rpt_forecast_10: List[Union[float, None]]
    rpt_forecast_30: List[Union[float, None]]
    rpt_forecast_50: List[Union[float, None]]
    rpt_forecast_70: List[Union[float, None]]
    rpt_forecast_90: List[Union[float, None]]


class ForecastRecommendationsTable(BaseModel):
    time_series: ForecastRecommendationsTimeSeries
    title: str
    readable_names: Dict[str, str]


class PastReviewTable(BaseModel):
    pass


class VolatilityAnalysisTable(BaseModel):
    pass


class TableResponse(BaseModel):
    table_id: str
    forecast_recommendations: ForecastRecommendationsTable = None
    past_review: PastReviewTable = None
    volatility_analysis: VolatilityAnalysisTable = None


@router.post("/table")
def get_table(table_id: str = None, filters: dict = None):

    with Session(engine) as session:
        # Throw error if table_id is not provided
        if table_id is None:
            raise HTTPException(status_code=400, detail="Table id is required")
        else:
            # Get table metadata
            filter_table_query = select(Table).where(Table.table_id == table_id)
            tables = session.exec(filter_table_query).all()

            # Throw error if table_id is not found in database
            if len(tables) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No records found for this table_id: {table_id}",
                )
            else:
                # Get path to the parquet file containing relevant analytics values and create df
                path = tables[0].path
                original_df = pl.read_parquet(path)

                # Init filtered_df
                filtered_df = original_df

                # Apply filters for all the entities that are available in this dataset if present in request body
                if filters is not None:
                    for entity, value in filters.items():
                        if isinstance(value, list):
                            dfs = []
                            for item in value:
                                dfs.append(filtered_df.filter(pl.col(entity) == item))
                            filtered_df = pl.concat(dfs)
                        else:
                            filtered_df = filtered_df.filter(pl.col(entity) == value)

                # Groupby the filtered df by time
                time_sorted_df = filtered_df.groupby(
                    ["time", "month_year"], maintain_order=True
                ).mean()

                # Populate response
                forecast_recommendations_table = ForecastRecommendationsTable(
                    time_series=ForecastRecommendationsTimeSeries(
                        time=time_sorted_df["time"].to_list(),
                        month_year=time_sorted_df["month_year"].to_list(),
                        rpt_forecast_10=time_sorted_df[
                            "trips_in_000s:indexhub_forecast_0.1"
                        ].to_list(),
                        rpt_forecast_30=time_sorted_df[
                            "trips_in_000s:indexhub_forecast_0.3"
                        ].to_list(),
                        rpt_forecast_50=time_sorted_df[
                            "trips_in_000s:indexhub_forecast_0.5"
                        ].to_list(),
                        rpt_forecast_70=time_sorted_df[
                            "trips_in_000s:indexhub_forecast_0.7"
                        ].to_list(),
                        rpt_forecast_90=time_sorted_df[
                            "trips_in_000s:indexhub_forecast_0.9"
                        ].to_list(),
                    ),
                    title=tables[0].title,
                    readable_names=json.loads(tables[0].readable_names),
                )

                response = TableResponse(
                    table_id=tables[0].table_id,
                    forecast_recommendations=forecast_recommendations_table,
                )

                return response
