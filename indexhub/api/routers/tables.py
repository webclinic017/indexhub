import json
from datetime import datetime
from typing import Dict, List, Sequence, Union

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
                df = pl.scan_parquet(path)

                # Apply all filters that are available in this dataset if present in request body
                if filters is not None:
                    for filter, values in filters.items():
                        if not isinstance(values, Sequence):
                            values = [values]

                        if (
                            len(values) > 0
                            and filter in df.columns
                            and filter != "time"
                        ):
                            filter_expr = [{filter: item} for item in values]
                            df = df.filter(pl.struct([filter]).is_in(filter_expr))

                # Groupby the filtered df by time
                time_sorted_df = (
                    df.groupby(["time", "month_year"])
                    .agg(pl.all().mean())
                    .sort(by="time")
                    .collect()
                )

                # Populate response
                forecast_recommendations_table = ForecastRecommendationsTable(
                    time_series=ForecastRecommendationsTimeSeries(
                        time=time_sorted_df["time"].to_list(),
                        month_year=time_sorted_df["month_year"].to_list(),
                        rpt_forecast_10=time_sorted_df["target:forecast_0.1"].to_list(),
                        rpt_forecast_30=time_sorted_df["target:forecast_0.3"].to_list(),
                        rpt_forecast_50=time_sorted_df["target:forecast_0.5"].to_list(),
                        rpt_forecast_70=time_sorted_df["target:forecast_0.7"].to_list(),
                        rpt_forecast_90=time_sorted_df["target:forecast_0.9"].to_list(),
                    ),
                    title=tables[0].title,
                    readable_names=json.loads(tables[0].readable_names),
                )

                response = TableResponse(
                    table_id=tables[0].table_id,
                    forecast_recommendations=forecast_recommendations_table,
                )

                return response
