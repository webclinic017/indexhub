import json
import os
from datetime import datetime
from typing import Any, List, Literal, Mapping, Union

from sqlmodel import Session, create_engine, select

from indexhub.api.models.chart import Chart
from indexhub.api.models.report import Report
from indexhub.api.models.source import Source
from indexhub.api.models.table import Table


def get_psql_conn_uri():
    username = os.environ["PSQL_USERNAME"]
    password = os.environ["PSQL_PASSWORD"]
    host = os.environ["PSQL_HOST"]
    port = os.environ["PSQL_PORT"]
    dbname = os.environ["PSQL_NAME"]
    sslmode = os.environ.get("PSQL_SSLMODE", "require")
    uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    return uri


def update_source(
    paths: Mapping[str, Union[str, Mapping[str, Any]]], metadata: Mapping[str, Any]
):
    # Unpack the metadata
    report_id = metadata["report_id"]
    source_id = metadata["source_id"]
    paths = {k: v for k, v in paths.items() if k != "metadata"}
    freq = metadata["freq"]
    start_date = metadata.get("start_date", None)
    end_date = metadata.get("end_date", None)
    status = metadata["status"]
    msg = metadata.get("msg", None)

    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        # Select rows with specific report_id only
        statement = select(Source).where(Source.id == source_id)
        result = session.exec(statement).one()
        # Update the fields based on the report_id
        result.report_id = report_id
        result.status = status
        result.freq = freq
        result.path = json.dumps(paths)
        result.updated_at = datetime.utcnow()
        result.start_date = start_date
        result.end_date = end_date
        result.msg = msg
        # Add, commit and refresh the updated object
        session.add(result)
        session.commit()
        session.refresh(result)


def update_report(
    report_id: str,
    status: Literal["SUCCESS", "RUNNING", "FAILED"],
    completed_at: datetime,
    entities: List[str],
):
    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        # Select rows with specific report_id only
        statement = select(Report).where(Report.id == report_id)
        result = session.exec(statement).one()
        # Update the fields based on the report_id
        result.status = status
        result.completed_at = completed_at
        result.entities = entities
        # Add, commit and refresh the updated object
        session.add(result)
        session.commit()
        session.refresh(result)


def create_chart(
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


def create_data_table(
    report_id: str,
    tag: str,
    path: str,
    title: str,
    readable_names: str,
):
    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        new_row = Table(
            report_id=report_id,
            tag=tag,
            path=path,
            title=title,
            readable_names=readable_names,
        )
        session.add(new_row)
        session.commit()
