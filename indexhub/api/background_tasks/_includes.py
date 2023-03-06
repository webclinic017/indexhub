import json
from datetime import datetime

from indexhub.api.models.chart import Chart
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.report import Report
from sqlmodel import Session


async def populate_forecast_recommendations_data(report: Report, session: Session):
    # Populate chart related data
    chart = Chart()
    chart.report_id = report.id
    chart.tag = "forecast_recommendation"

    # Needs to be dynamically set based on the parquet file generated
    chart.path = "rpt_forecast.csv"
    chart.title = "Sales Quantity Trendline - Including Forecast"
    chart.axis_labels = json.dumps({"x": "", "y": ""})

    # Constant for all forecast recommendations charts
    chart.readable_names = json.dumps(
        {
            "rpt_actual": "Actual",
            "rpt_manual": "Benchmark",
            "rpt_forecast": "AI Forecast",
        }
    )
    chart.type = "line"

    session.add(chart)
    session.commit()
    session.refresh(chart)

    # Populate table related data
    table = DataTable()
    table.report_id = report.id
    table.tag = "forecast_recommendation"

    # Needs to be dynamically set based on the parquet file generated
    table.path = "rpt_forecast_scenario.csv"
    table.title = "Forecasting Scenarios"
    table.readable_names = json.dumps(
        {
            "month_year": "Month Year",
            "rpt_forecast_50": "AI Forecast (50%)",
        }
    )
    session.add(table)
    session.commit()
    session.refresh(table)

    # Populate table related data
    table = DataTable()
    table.report_id = report.id
    table.tag = "backtests"

    # Needs to be dynamically set based on the parquet file generated
    table.path = "rpt_metrics.csv"
    table.title = "Backtests"
    table.readable_names = json.dumps(
        {
            "month_year": "Month Year",
            "rpt_forecast_50": "AI Forecast (50%)",
        }
    )
    session.add(table)
    session.commit()
    session.refresh(table)

    report.status = "COMPLETE"
    report.completed_at = datetime.now()

    session.add(report)
    session.commit()
    session.refresh(report)
