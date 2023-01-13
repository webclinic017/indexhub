import json
import uuid
from datetime import datetime

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
            "rpt_forecast_10": "AI Forecast (10%)",
            "rpt_forecast_30": "AI Forecast (30%)",
            "rpt_forecast_50": "AI Forecast (50%)",
            "rpt_forecast_70": "AI Forecast (70%)",
            "rpt_forecast_90": "AI Forecast (90%)",
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

    # Populate report entities specific for forecast recommendations
    df = pl.read_parquet(chart.path)
    entity_keys = [item for item in df.columns if "entity" in item]

    entities = json.loads(report.entities)

    for entity_key in entity_keys:
        entities["forecast_recommendations"][entity_key] = {
            "title": entity_key,
            "values": df[entity_key].unique().to_list(),
            "multiple_choice": True,
        }

    report.entities = json.dumps(entities)
    report.status = "COMPLETE"
    report.completed_at = datetime.now()
    session.add(report)
    session.commit()
    session.refresh(report)
