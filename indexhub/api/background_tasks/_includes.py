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

    # Populate chart entities
    df = pl.read_parquet(chart.path)
    chart.entities = json.dumps(
        {
            "year": {
                "title": "Year",
                "values": df["time"].dt.year().unique().to_list(),
            },
            "region": {
                "title": "Region",
                "values": df["territory"].unique().to_list(),
            },
            "risk_metric": {
                "title": "Risk Metric (Indexhub Forecast)",
                "values": df["quantile"].unique().to_list(),
            },
        }
    )

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
    table.path = "rpt_tourism_forecast_by_territory_state_quantile_20221222.parquet"
    table.title = "Forecasting Scenarios"
    table.readable_names = json.dumps(
        {
            "month_year": "Month",
            "trips_in_000s:indexhub_forecast_0.1": "Indexhub Forecast (10%)",
            "trips_in_000s:indexhub_forecast_0.3": "Indexhub Forecast (30%)",
            "trips_in_000s:indexhub_forecast_0.5": "Indexhub Forecast (50%)",
            "trips_in_000s:indexhub_forecast_0.7": "Indexhub Forecast (70%)",
            "trips_in_000s:indexhub_forecast_0.9": "Indexhub Forecast (90%)",
        }
    )
    session.add(table)
    session.commit()
    session.refresh(table)

    # Update report with the relevant table_id
    report.table_id = table.table_id
    report.status = "COMPLETE"
    session.add(report)
    session.commit()
    session.refresh(report)
