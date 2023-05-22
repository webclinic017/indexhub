from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Objective(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Sources
    # panel: int (id from source table)
    # baseline: Optional[int] = None (id from source table)
    # inventory: Optional[int] = None (id from source table)
    sources: str
    # Fields
    # fh: int
    # description: str
    # error_type: str
    # min_lags: int
    # max_lags: int
    # n_splits: int
    # holiday_regions: Optional[List[str]] = None
    # baseline_model: Optional[str] = None
    # goal: int
    fields: str
    # Outputs
    outputs: Optional[str] = None
    msg: Optional[str] = None
