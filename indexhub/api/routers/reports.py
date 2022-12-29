import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.background_tasks.populate_report import populate_report_data
from indexhub.api.models.report import Report
from indexhub.api.utils.init_db import engine

router = APIRouter()


class CreateReport(BaseModel):
    user_id: str


@router.post("/reports")
def create_report(create_report: CreateReport, background_tasks: BackgroundTasks):
    with Session(engine) as session:

        report = Report()
        report.report_id = uuid.uuid4().hex
        report.user_id = create_report.user_id
        report.status = "RUNNING"
        report.created_at = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        session.add(report)
        session.commit()
        session.refresh(report)

        background_tasks.add_task(populate_report_data, report.report_id)

        return {"user_id": create_report.user_id, "report_id": report.report_id}


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
            query = select(Report).where(Report.report_id == report_id)
            reports = session.exec(query).all()
            if len(reports) == 0:
                raise HTTPException(
                    status_code=400, detail="No records found for this report_id"
                )

        return {"reports": reports}
