import enum
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel

from indexhub.api.models.user import User  # noqa


class StatusTypes(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RUNNING = "RUNNING"


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.user_id")
    name: str
    path: str
    freq: str
    created_at: Optional[datetime] = None
    status: Optional[StatusTypes] = Field(default="RUNNING")
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    levels: Optional[List[str]] = None
    msg: Optional[str] = None
