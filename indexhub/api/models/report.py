import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from indexhub.api.models.source import Source, StatusTypes  # noqa


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    source_id: Optional[int] = Field(default=None, foreign_key="source.id")
    source_name: str
    user_id: str
    status: Optional[StatusTypes] = Field(default="RUNNING")
    created_at: datetime
    completed_at: Optional[datetime] = None
    entities: Optional[str] = json.dumps({"forecast_recommendations": {}})
