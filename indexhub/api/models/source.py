import enum
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel, JSON

from indexhub.api.models.user import User  # noqa


class SourceTypes(str, enum.Enum):
    S3 = "S3"
    XERO = "XERO"


class Source(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    name: str
    type: SourceTypes
    created_at: datetime
    updated_at: datetime
    freq: str
    time_col: str
    entity_cols: List[str]
    target_cols: List[str]
    metadata: JSON
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    msg: Optional[str] = None
