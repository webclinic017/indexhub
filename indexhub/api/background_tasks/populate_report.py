from sqlmodel import Session, select

from indexhub.api.models.report import Report
from indexhub.api.utils.init_db import engine

from ._includes import populate_forecast_recommendations_data


async def populate_report_data(report_id: str):
    with Session(engine) as session:
        # Get the current report
        filter_report_query = select(Report).where(Report.report_id == report_id)
        report = session.exec(filter_report_query).one()

        # Populate all forecast recommendations artifacts
        await populate_forecast_recommendations_data(report, session)
