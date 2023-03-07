import os

from fastapi import APIRouter
from indexhub.api.db import engine
from indexhub.api.models.policies import TAG_TO_POLICY
from sqlmodel import Session, select

router = APIRouter()


DEMO_TABLE_IDS = []


@router.get("/tables")
def list_data_tables(policy_id: int, policy_tag: str):
    """Return Mapping of data_table_tag to (data_table_id, data_table_path)"""
    with Session(engine) as session:
        Policy = TAG_TO_POLICY[policy_tag]
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).first()
        data_tables = policy.data_tables  # noqa
        # TODO: coerce data_tables to JSON


@router.get("/tables/{table_id}")
def get_data_table(table_id: str):
    """Return CSV"""
    if table_id in DEMO_TABLE_IDS:
        s3_bucket = os.environ["DEMO__S3_BUCKET"]
        # Read parquet
        path = f"{s3_bucket}/{table_id}.parquet"  # noqa
    else:
        # TODO: Get S3 bucket associated with user
        # Use read_s3 code
        pass
