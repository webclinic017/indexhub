from typing import Any, Mapping, Optional

from indexhub.api.db import get_psql_conn_uri
from indexhub.api.models.chart import Chart
from indexhub.api.models.data_table import DataTable
from pydantic import BaseModel
from sqlmodel import Session, create_engine


def _create_chart_row(
    report_id: str,
    tag: str,
    path: str,
    title: str,
    axis_labels: str,
    readable_names: str,
    type: str,
):

    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        new_row = Chart(
            report_id=report_id,
            tag=tag,
            path=path,
            title=title,
            axis_labels=axis_labels,
            readable_names=readable_names,
            type=type,
        )
        session.add(new_row)
        session.commit()


def _create_data_table_row(
    report_id: str,
    tag: str,
    path: str,
    title: str,
    readable_names: str,
):
    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        new_row = DataTable(
            report_id=report_id,
            tag=tag,
            path=path,
            title=title,
            readable_names=readable_names,
        )
        session.add(new_row)
        session.commit()


class RunForecastFlowInput(BaseModel):
    s3_data_bucket: str
    s3_artifacts_bucket: str
    freq: str
    ftr_panel_path: str
    ftr_manual_path: Optional[str] = None
    allow_negatives: bool = False
    use_manual_zeros: bool = False


class RunForecastFlowOutput(BaseModel):
    # Paths to parquet files
    backtest: str
    forecast: str
    intervals: str
    risks: str
    metrics: Mapping[str, Mapping[str, Any]]
    params: Mapping[str, Mapping[str, Any]]
    strategies: Mapping[str, str]
