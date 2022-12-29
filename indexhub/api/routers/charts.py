import json
from datetime import datetime
from typing import Dict, List, Optional, Union

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.models.chart import Chart
from indexhub.api.utils.init_db import engine

router = APIRouter()


class ChartData(BaseModel):
    time: List[datetime]
    rpt_actual: List[Union[float, None]]
    rpt_manual: List[Union[float, None]]
    rpt_forecast: List[Union[float, None]]
    entity_id: Optional[str] = None
    entity_x_dim: Optional[str] = None
    entity_y_dim: Optional[str] = None


class ChartResponse(BaseModel):
    chart_id: str
    chart_data: ChartData
    title: str
    axis_labels: Dict[str, str]
    readable_names: Dict[str, str]
    chart_type: str
    entity_id: Optional[str] = None


@router.post("/charts")
def get_chart(chart_id: str = None, filters: dict = None, year: list[int] = None):

    with Session(engine) as session:
        # Throw error if chart_id is not provided
        if chart_id is None:
            raise HTTPException(status_code=400, detail="Chart id is required")
        else:
            # Get chart metadata
            filter_chart_query = select(Chart).where(Chart.chart_id == chart_id)
            charts = session.exec(filter_chart_query).all()

            # Throw error if chart_id is not found in database
            if len(charts) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No records found for this chart_id: {chart_id}",
                )
            else:
                # Get path to the parquet file containing relevant analytics values and create df
                path = charts[0].path
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

                # Apply year filter if present in request body
                if year is not None:
                    filtered_df = filtered_df.filter(
                        (pl.col("time") > datetime(min(year) - 1, 12, 31))
                        & (pl.col("time") < datetime(max(year) + 1, 1, 1))
                    )

                # Groupby the filtered df by time
                time_sorted_df = filtered_df.groupby("time", maintain_order=True).mean()

                # Populate response
                chart_data = ChartData(
                    time=time_sorted_df["time"].to_list(),
                    rpt_actual=time_sorted_df["trips_in_000s:actual"].to_list(),
                    rpt_manual=time_sorted_df["trips_in_000s:forecast"].to_list(),
                    rpt_forecast=time_sorted_df[
                        "trips_in_000s:indexhub_forecast"
                    ].to_list(),
                )

                response = ChartResponse(
                    chart_id=chart_id,
                    chart_data=chart_data,
                    title=charts[0].title,
                    axis_labels=json.loads(charts[0].axis_labels),
                    readable_names=json.loads(charts[0].readable_names),
                    chart_type=charts[0].chart_type,
                    entity_id=charts[0].entity_id,
                )

                return response
