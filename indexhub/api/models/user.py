from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool
    has_s3_creds: bool = False
    has_azure_creds: bool = False
    storage_tag: Optional[str] = None
    storage_bucket_name: Optional[str] = None
    storage_created_at: Optional[datetime] = None
    integration_ids: Optional[str] = None  # list[int]

