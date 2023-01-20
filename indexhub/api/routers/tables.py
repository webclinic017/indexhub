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


class ForecastRecommendationsData(BaseModel):
    time: datetime
    month_year: str
    rpt_forecast_10: Union[float, None]
    rpt_forecast_30: Union[float, None]
    rpt_forecast_50: Union[float, None]
    rpt_forecast_70: Union[float, None]
    rpt_forecast_90: Union[float, None]


class ForecastRecommendationsTable(BaseModel):
    data: List[ForecastRecommendationsData]
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


@router.post("/tables")
def get_table(report_id: str = None, tag: str = None, filters: dict = None):

    with Session(engine) as session:
        # Throw error if table_id is not provided
        if report_id is None or tag is None:
            raise HTTPException(status_code=400, detail="Report id and tag is required")
        else:
            # Get table metadata
            filter_table_query = (
                select(Table)
                .where(Table.report_id == report_id)
                .where(Table.tag == tag)
            )
            tables = session.exec(filter_table_query).all()

            # Throw error if table is not found in database
            if len(tables) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No table records found for this report_id and tag: {report_id}, {tag}",
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
                    .rename(
                        {
                            "target:forecast_0.1": "rpt_forecast_10",
                            "target:forecast_0.3": "rpt_forecast_30",
                            "target:forecast_0.5": "rpt_forecast_50",
                            "target:forecast_0.7": "rpt_forecast_70",
                            "target:forecast_0.9": "rpt_forecast_90",
                        }
                    )
                )

                # Populate response
                forecast_recommendations_table = ForecastRecommendationsTable(
                    data=time_sorted_df.to_dicts(),
                    title=tables[0].title,
                    readable_names=json.loads(tables[0].readable_names),
                )

                response = TableResponse(
                    table_id=tables[0].id,
                    forecast_recommendations=forecast_recommendations_table,
                )

                return response
