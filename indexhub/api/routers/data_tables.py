import os

from fastapi import APIRouter
from indexhub.api.db import engine
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.policy import Policy
from indexhub.api.models.user import User
from indexhub.api.services.io import read_data_from_s3
from sqlmodel import Session, select

router = APIRouter()


DEMO_TABLE_IDS = []


@router.get("/tables")
def list_data_tables(policy_id: int):
    """Return Mapping of data_table_tag to (data_table_id, data_table_path)"""
    with Session(engine) as session:
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).first()
        data_tables = [table.dict(exclude_unset=True) for table in policy.data_tables]
        return {"data_tables": data_tables}


@router.get("/tables/{table_id}")
def get_data_table(table_id: str, user_id: str):
    """Return CSV"""
    with Session(engine) as session:
        if table_id in DEMO_TABLE_IDS:
            bucket_name = os.environ.get("DEMO__BUCKET_NAME", "indexhub-demo")
            object_path = f"{bucket_name}/{table_id}.parquet"  # noqa
        else:
            # Get S3 bucket associated with user
            query = select(User).where(User.id == user_id)
            user = session.exec(query).first()
            bucket_name = user.bucket_name

            # Get S3 path from DataTable
            query = select(DataTable).where(DataTable.id == table_id)
            table = session.exec(query).first()
            object_path = table.path

        data = read_data_from_s3(bucket_name, object_path, "parquet")
        return {"data": data}
