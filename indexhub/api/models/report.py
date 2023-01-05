from typing import Optional

from sqlmodel import Field, SQLModel

from indexhub.api.models.source import Source  # noqa


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    source_id: Optional[int] = Field(default=None, foreign_key="source.id")
    user_id: str
    status: str
    created_at: str
    chart_id: Optional[str] = None
    table_id: Optional[str] = None
    filters: Optional[str] = None
