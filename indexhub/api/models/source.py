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
    s3_data_bucket: str
    time_col: str
    freq: str
    entity_cols: List[str]
    target_cols: List[str]
    raw_data_path: str
    filters: Optional[str]  # Json string of Union[str, str]
    manual_forecast_path: Optional[str]
    fct_panel_paths: Optional[str]  # Json string of Union[str, str]
    created_at: Optional[datetime] = None
    status: Optional[StatusTypes] = Field(default="RUNNING")
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    msg: Optional[str] = None
