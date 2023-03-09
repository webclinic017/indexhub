from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool
    s3_bucket: Optional[str] = None
    source_ids: Optional[str] = None  # List[str]
    policy_ids: Optional[str] = None  # List[str]
