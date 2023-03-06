from indexhub.api.db import engine
from indexhub.api.models.report import Report
from sqlmodel import Session

from ._includes import populate_forecast_recommendations_data


async def populate_report_data(report: Report):
    with Session(engine) as session:

        # Populate all forecast recommendations artifacts
        await populate_forecast_recommendations_data(report, session)
