import uuid

from api.models.report import Report
from api.utils.init_db import engine
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

router = APIRouter()


class CreateReport(BaseModel):
    user_id: str


@router.post("/reports")
def create_report(
    create_report: CreateReport,
):
    with Session(engine) as session:

        report = Report()
        report.report_id = uuid.uuid4().hex
        report.user_id = create_report.user_id
        report.chart_id = uuid.uuid4().hex
        report.table_id = uuid.uuid4().hex
        report.status = "RUNNING"
        report.report_metadata = uuid.uuid4().hex

        session.add(report)
        session.commit()
        session.refresh(report)

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
