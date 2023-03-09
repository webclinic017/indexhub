import os

from fastapi import APIRouter
from indexhub.api.db import engine
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.policy_source import Policy
from indexhub.api.models.user import User
from indexhub.api.routers.readers import read_s3
from sqlmodel import Session, select

router = APIRouter()


DEMO_TABLE_IDS = []


@router.get("/tables")
def list_data_tables(policy_id: int):
    """Return Mapping of data_table_tag to (data_table_id, data_table_path)"""
    with Session(engine) as session:
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).first()
        data_tables = policy.data_tables  # noqa
        return {"data_tables": data_tables}
        # TODO: coerce data_tables to JSON


@router.get("/tables/{table_id}")
def get_data_table(table_id: str, user_id: str):
    """Return CSV"""
    with Session(engine) as session:
        if table_id in DEMO_TABLE_IDS:
            s3_bucket = os.environ.get("DEMO__S3_BUCKET", "indexhub-demo")
            s3_path = f"{s3_bucket}/{table_id}.parquet"  # noqa
        else:
            # Get S3 bucket associated with user
            query = select(User).where(User.id == user_id)
            user = session.exec(query).first()
            s3_bucket = (
                user.s3_bucket
            )  # TODO: Update accordingly when model created for connections

            # Get S3 path from DataTable
            query = select(DataTable).where(DataTable.id == table_id)
            table = session.exec(query).first()
            s3_path = table.path

        data = read_s3(
            s3_bucket, s3_path, "parquet"
        )  # QUESTION: Can we file ext here to parquet or should we create a field in DataTable schema
        return {"data": data}
