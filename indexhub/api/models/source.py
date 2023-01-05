from typing import Dict, Optional

from sqlmodel import JSON, Column, Field, SQLModel


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    name: Optional[str] = id
    path: Optional[str] = None
    status: Optional[str] = None
    freq: Optional[str] = None
    created_at: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    levels: Dict = Field(default={}, sa_column=Column(JSON))
