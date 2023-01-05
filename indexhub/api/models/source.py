from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    name: str
    path: str
    freq: str
    status: Optional[str] = Field(default="RUNNING")
    created_at: datetime
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    levels: Optional[List[str]] = None
