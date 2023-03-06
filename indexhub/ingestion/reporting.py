from indexhub.api.db import get_psql_conn_uri
from indexhub.api.models.chart import Chart
from indexhub.api.models.data_table import DataTable
from sqlmodel import Session, create_engine


def create_chart_row(
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


def create_data_table_row(
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
