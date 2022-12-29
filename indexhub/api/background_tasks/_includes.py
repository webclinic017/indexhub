import json
import uuid

from sqlmodel import Session

from indexhub.api.models.chart import Chart
from indexhub.api.models.report import Report


async def populate_forecast_recommendations_data(report: Report, session: Session):

    # Populate chart related data
    chart = Chart()
    chart.chart_id = uuid.uuid4().hex

    # Needs to be dynamically set based on the parquet file generated
    chart.path = "rpt_tourism_forecast_by_territory_state_20221222.parquet"
    chart.title = "Sales Quantity Trendline - Including Forecast"
    chart.axis_labels = json.dumps({"x": "", "y": ""})

    # Constant for all forecast recommendations charts
    chart.readable_names = json.dumps(
        {
            "rpt_actual": "Actual",
            "rpt_manual": "Manual Forecast",
            "rpt_forecast": "Indexhub Forecast",
        }
    )
    chart.chart_type = "line"
    session.add(chart)
    session.commit()
    session.refresh(chart)

    # Update report with the relevant chart_id
    report.chart_id = chart.chart_id
    report.status = "COMPLETE"
    session.add(report)
    session.commit()
    session.refresh(report)
