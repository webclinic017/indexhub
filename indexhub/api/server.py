"""Defines the IndexHub FastAPI app.
"""

import uuid

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from jwt import exceptions
from sqlmodel import Session, SQLModel, create_engine, select

from .models.report import CreateReport, Report, RequestReport
from .models.user import CreateUser, User, UserPatch
from .utils.auth0 import VerifyToken

sqlite_url = "postgresql://localhost:5432"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


token_auth_scheme = HTTPBearer()


async def verify_oauth_token(token: str = Depends(token_auth_scheme)):
    try:
        _ = VerifyToken(token).verify()
    except exceptions.InvalidTokenError:
        raise


app = FastAPI(dependencies=[Depends(verify_oauth_token)])

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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/reports")
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

        # TODO: Consider normalisation
        filter_user_query = select(User).where(User.user_id == create_report.user_id)
        results = session.exec(filter_user_query)
        user = results.one()
        if user.report_ids is not None:
            user.report_ids = [*user.report_ids, report.report_id]
        else:
            user.report_ids = [report.report_id]

        session.add(user)
        session.commit()
        session.refresh(user)

        return {"user_id": create_report.user_id, "report_id": report.report_id}


@app.get("/reports")
def get_report(request_report: RequestReport):
    with Session(engine) as session:
        if request_report.report_id is None:
            if request_report.user_id is None:
                raise HTTPException(
                    status_code=400, detail="Either report_id or user_id is required"
                )
            else:
                report = session.get(Report, request_report.user_id)
        else:
            report = session.get(Report, request_report.report_id)
        return report


@app.post("/user")
def create_user(
    create_user: CreateUser,
):

    with Session(engine) as session:

        user = User()
        user.user_id = create_user.user_id
        user.name = create_user.name
        user.nickname = create_user.nickname
        user.email = create_user.email
        user.email_verified = create_user.email_verified

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "user_id": create_user.user_id,
            "message": "User creation on backend success",
        }


@app.get("/users/{user_id}")
def get_user(response: Response, user_id: str):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is not None:
            return user
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "User id not found"}


@app.patch("/users/{user_id}")
def patch_user(
    user_patch: UserPatch,
    user_id: str,
):

    with Session(engine) as session:
        filter_user_query = select(User).where(User.user_id == user_id)
        results = session.exec(filter_user_query)
        user = results.one()

        user.name = user_patch.name or user.name
        user.nickname = user_patch.nickname or user.nickname
        user.email = user_patch.email or user.email
        user.email_verified = user_patch.email_verified or user.email_verified
        user.report_ids = user_patch.report_ids or user.report_ids

        session.add(user)
        session.commit()
        session.refresh(user)

        return user
