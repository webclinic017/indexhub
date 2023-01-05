import json
import uuid

import polars as pl
from sqlmodel import Session

from indexhub.api.models.chart import Chart
from indexhub.api.models.report import Report
from indexhub.api.models.table import Table


async def populate_forecast_recommendations_data(report: Report, session: Session):
    # Populate chart related data
    chart = Chart()
    chart.chart_id = uuid.uuid4().hex

    # Needs to be dynamically set based on the parquet file generated
    chart.path = "rpt_forecast_sales.parquet"
    chart.title = "Sales Quantity Trendline - Including Forecast"
    chart.axis_labels = json.dumps({"x": "", "y": ""})

    # Constant for all forecast recommendations charts
    chart.readable_names = json.dumps(
        {
            "rpt_actual": "Actual",
            "rpt_manual": "Manual Forecast",
            "rpt_forecast": "AI Forecast",
        }
    )
    chart.chart_type = "line"

    session.add(chart)
    session.commit()
    session.refresh(chart)

    # Update report with the relevant chart_id
    report.chart_id = chart.chart_id
    report.status = "RUNNING"
    session.add(report)
    session.commit()
    session.refresh(report)

    # Populate table related data
    table = Table()
    table.table_id = uuid.uuid4().hex
    table.path = "rpt_forecast_scenario_sales.parquet"
    table.title = "Forecasting Scenarios"
    table.readable_names = json.dumps(
        {
            "month_year": "Month",
            "target:forecast_0.1": "AI Forecast (10%)",
            "target:forecast_0.3": "AI Forecast (30%)",
            "target:forecast_0.5": "AI Forecast (50%)",
            "target:forecast_0.7": "AI Forecast (70%)",
            "target:forecast_0.9": "AI Forecast (90%)",
        }
    )
    session.add(table)
    session.commit()
    session.refresh(table)

    # Update report with the relevant table_id
    report.table_id = table.table_id
    report.status = "RUNNING"
    session.add(report)
    session.commit()
    session.refresh(report)

    # Populate report filters
    df = pl.read_parquet(chart.path)
    entity_columns = [item for item in df.columns if "entity" in item]

    filters = {
        "time": {
            "title": "Year",
            "values": df["time"].dt.year().unique().to_list(),
            "multiple_choice": True,
        },
    }

    for entity in entity_columns:
        filters[entity] = {
            "title": entity,
            "values": df[entity].unique().to_list(),
            "multiple_choice": True,
        }

    filters["quantile"] = {
        "title": "Risk Metric (AI Forecast)",
        "values": df["quantile"].unique().to_list(),
        "multiple_choice": False,
    }

    report.filters = json.dumps(filters)
    report.status = "COMPLETE"
    session.add(report)
    session.commit()
    session.refresh(report)
