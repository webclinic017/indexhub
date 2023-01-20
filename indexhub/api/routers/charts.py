import json
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Union

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


@router.post("/charts")
def get_chart(report_id: str = None, tag: str = None, filters: dict = None):

    with Session(engine) as session:
        # Throw error if report_id is not provided
        if report_id is None or tag is None:
            raise HTTPException(status_code=400, detail="Report id and tag is required")
        else:
            # Get chart metadata
            filter_chart_query = (
                select(Chart)
                .where(Chart.report_id == report_id)
                .where(Chart.tag == tag)
            )
            charts = session.exec(filter_chart_query).all()

            # Throw error if chart is not found in database
            if len(charts) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No chart records found for this report_id and tag: {report_id}, {tag}",
                )
            else:
                # Get path to the parquet file containing relevant analytics values and create df
                path = charts[0].path
                df = pl.scan_parquet(path)

                # Apply all the filters that are available in this dataset if present in request body
                if filters is not None:
                    for filter, values in filters.items():
                        if not isinstance(values, Sequence):
                            values = [values]

                        if len(values) > 0 and filter in df.columns:
                            if filter == "time":
                                df = df.filter(
                                    (pl.col("time") > datetime(min(values) - 1, 12, 31))
                                    & (pl.col("time") < datetime(max(values) + 1, 1, 1))
                                )
                            else:
                                df = df.filter(
                                    pl.col(filter).cast(pl.Utf8).is_in(values)
                                )

                # Groupby the filtered df by time
                time_sorted_df = (
                    df.groupby("time").agg(pl.all().mean()).sort(by="time").collect()
                )

                # Populate response
                chart_data = ChartData(
                    time=time_sorted_df["time"].to_list(),
                    rpt_actual=time_sorted_df["target:actual"].to_list(),
                    rpt_manual=time_sorted_df["target:manual"].to_list(),
                    rpt_forecast=time_sorted_df["target:forecast"].to_list(),
                )

                response = ChartResponse(
                    chart_id=charts[0].id,
                    chart_data=chart_data,
                    title=charts[0].title,
                    axis_labels=json.loads(charts[0].axis_labels),
                    readable_names=json.loads(charts[0].readable_names),
                    chart_type=charts[0].type,
                )

                return response
