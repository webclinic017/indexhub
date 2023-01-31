from indexhub.ingestion.status import get_psql_conn_uri
from sqlmodel import Session, create_engine
from indexhub.api.models.table import Table
from indexhub.api.models.chart import Chart

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
        new_row = Table(
            report_id=report_id,
            tag=tag,
            path=path,
            title=title,
            readable_names=readable_names,
        )
        session.add(new_row)
        session.commit()