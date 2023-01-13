import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from indexhub.api.models.source import Source  # noqa


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    source_id: Optional[int] = Field(default=None, foreign_key="source.id")
    source_name: str
    user_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    chart_id: Optional[str] = None
    table_id: Optional[str] = None
    entities: Optional[str] = json.dumps({"forecast_recommendations": {}})
