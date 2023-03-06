import codecs
import json
from datetime import datetime
from typing import List, Optional

import botocore
import polars as pl
from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket
from indexhub.api.background_tasks.populate_report import populate_report_data
from indexhub.api.check_source import read_source_file
from indexhub.api.db import engine
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.report import Report, Source
from pydantic import BaseModel
from sqlmodel import Session, select
from ydata_profiling import ProfileReport

router = APIRouter()


class CreateReport(BaseModel):
    user_id: str
    level_cols: List[str]
    target_col: str
    source_id: Optional[str] = None
    report_id: Optional[str] = None


@router.post("/reports")
def create_report(create_report: CreateReport, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        if create_report.report_id:
            report_filter = select(Report).where(Report.id == create_report.report_id)
            results = session.exec(report_filter)
            if results:
                report = results.one()
            else:
                raise HTTPException(
                    status_code=400, detail="This report_id does not exist"
                )
        else:
            report = Report()

        if create_report.source_id:
            sources = select(Source).where(Source.id == create_report.source_id)
            source_name = session.exec(sources).one().name

        report.source_id = create_report.source_id or None
        report.user_id = create_report.user_id
        report.status = "RUNNING"
        report.created_at = datetime.now()
        report.source_name = source_name or ""
        report.level_cols = json.dumps(create_report.level_cols)
        report.target_col = create_report.target_col

        session.add(report)
        session.commit()
        session.refresh(report)

        background_tasks.add_task(populate_report_data, report)

        return {"user_id": create_report.user_id, "report_id": report.id}


@router.get("/reports")
def get_report(report_id: str = None, user_id: str = None):
    with Session(engine) as session:
        if report_id is None:
            if user_id is None:
                raise HTTPException(
                    status_code=400, detail="Either report_id or user_id is required"
                )
            else:
                query = select(Report).where(Report.user_id == user_id)
                reports = session.exec(query).all()
                if len(reports) == 0:
                    raise HTTPException(
                        status_code=400, detail="No records found for this user_id"
                    )
        else:
            query = select(Report).where(Report.id == report_id)
            reports = session.exec(query).all()
            if len(reports) == 0:
                raise HTTPException(
                    status_code=400, detail="No records found for this report_id"
                )

        # Cast level_cols from json string to List[str]
        for report in reports:
            report.level_cols = json.loads(report.level_cols)

        return {"reports": reports}


@router.delete("/reports")
def delete_report(report_id: str):
    with Session(engine) as session:
        if report_id is None:
            raise HTTPException(status_code=400, detail="report_id is required")
        else:
            query = select(Report).where(Report.id == report_id)
            report = session.exec(query).first()
            if report is None:
                raise HTTPException(
                    status_code=400, detail="No record found for this report_id"
                )
            session.delete(report)
            session.commit()

            user_id = report.user_id

            try:
                response = get_report(user_id=user_id)
            except HTTPException:
                response = {
                    "status": report.status,
                    "message": f"Record for report_id ({report_id}) is deleted. No other records found for the user_id ({user_id})",
                }
            return response


@router.get("/reports/profiling")
def get_source_profiling(source_id: str):
    s3_bucket = None
    s3_path = None
    with Session(engine) as session:
        if source_id is None:
            raise HTTPException(status_code=400, detail="source_id is required")
        else:
            query = select(Source).where(Source.id == source_id)
            source = session.exec(query).first()
            if source is None:
                raise HTTPException(
                    status_code=400, detail="No record found for this source_id"
                )
            s3_bucket = source.s3_data_bucket
            s3_path = source.raw_data_path

    try:
        df = read_source_file(s3_bucket=s3_bucket, s3_path=s3_path)
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail="Invalid S3 path") from err

    profile = ProfileReport(df.to_pandas(), title="Profiling Report", tsmode=True)
    profile.to_file("your_report.html")

    page = codecs.open("your_report.html", "rb").read()
    return {"data": page}


@router.get("/reports/levels")
def get_report_levels(report_id: str):
    with Session(engine) as session:
        # Throw error if table_id is not provided
        if report_id is None:
            raise HTTPException(status_code=400, detail="Report id and tag is required")
        else:
            # Get table metadata
            filter_table_query = (
                select(DataTable)
                .where(DataTable.report_id == report_id)
                .where(DataTable.tag == "backtests")
            )
            tables = session.exec(filter_table_query).all()

            # Throw error if table is not found in database
            if len(tables) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No levels data found for this report_id: {report_id}",
                )
            else:
                # Get path to the parquet file containing relevant analytics values and create df
                path = tables[0].path
                df = pl.read_csv(path)
                df_cols = df.columns
                levels_data = {}
                for col in df_cols:
                    if "entity_" in col:
                        levels_data[col] = df[col].unique().to_list()

            return {"levels_data": levels_data}


@router.websocket("/reports/ws")
async def ws_get_reports(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        report_id = data.get("report_id")
        user_id = data.get("user_id")
        results = get_report(report_id=report_id, user_id=user_id)

        response = []
        for result in results["reports"]:
            values = {
                k: v for k, v in vars(result).items() if k != "_sa_instance_state"
            }
            response.append(values)
        response = {"reports": response}
        await websocket.send_text(json.dumps(response, default=str))
