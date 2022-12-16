"""Defines the IndexHub FastAPI app.
"""

import uuid

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from jwt import exceptions
from sqlmodel import Session, SQLModel, create_engine

from .models.models import CreateReport, Report
from .utils.auth0 import VerifyToken

sqlite_file_name = "indexhub.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

token_auth_scheme = HTTPBearer()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/reports")
def create_report(
    response: Response,
    create_report: CreateReport,
    token: str = Depends(token_auth_scheme),
):
    try:
        verification_result = VerifyToken(token.credentials).verify()
    except exceptions.InvalidTokenError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return verification_result
    else:
        with Session(engine) as session:

            report = Report()
            report.report_id = uuid.uuid4().hex
            report.chart_id = uuid.uuid4().hex
            report.table_id = uuid.uuid4().hex
            report.status = "RUNNING"
            report.report_metadata = uuid.uuid4().hex

            session.add(report)
            session.commit()
            session.refresh(report)
            return {"user_id": create_report.user_id, "report_id": report.report_id}


@app.get("/reports/{report_id}")
def get_report(
    response: Response, report_id: str, token: str = Depends(token_auth_scheme)
):
    try:
        verification_result = VerifyToken(token.credentials).verify()
    except exceptions.InvalidTokenError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return verification_result
    else:
        with Session(engine) as session:
            report = session.get(Report, report_id)
            return report
