import json
import os
from datetime import datetime
from typing import Any, Mapping, Optional, Union

from prefect import flow, task
from sqlmodel import Session, create_engine, select

from indexhub.api.models.source import Source


def get_psql_conn_uri():
    username = os.environ["PSQL_USERNAME"]
    password = os.environ["PSQL_PASSWORD"]
    host = os.environ["PSQL_HOST"]
    port = os.environ["PSQL_PORT"]
    dbname = os.environ["PSQL_NAME"]
    sslmode = os.environ.get("PSQL_SSLMODE", "require")
    uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    return uri


@task
def update_metadata(
    report_id: str,
    freq: str,
    status: str,
    paths: Optional[Mapping[str, str]],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    msg: Optional[str] = None,
):

    if start_date and end_date is not None:
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.min.time())
    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        # Select rows with specific report_id only
        statement = select(Source).where(Source.name == report_id)
        result = session.exec(statement).one()
        # Update the fields based on the report_id
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


@flow
def update_status(
    paths: Mapping[str, Union[str, Mapping[str, Any]]], metadata: Mapping[str, Any]
):
    # Unpack the metadata
    report_id = metadata["report_id"]
    paths = {k: v for k, v in paths.items() if k != "metadata"}
    freq = metadata["freq"]
    start_date = metadata.get("start_date", None)
    end_date = metadata.get("end_date", None)
    status = metadata["status"]
    msg = metadata.get("msg", None)

    update_metadata(
        report_id=report_id,
        paths=paths,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        status=status,
        msg=msg,
    )
