import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.background_tasks.populate_report import populate_report_data
from indexhub.api.db import engine
from indexhub.api.models.report import Report, Source

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
