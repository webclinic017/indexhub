from typing import Optional

from sqlmodel import Field, SQLModel


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    user_id: str
    status: str
    created_at: str
    chart_id: Optional[str] = None
    table_id: Optional[str] = None
