from typing import Optional

from sqlmodel import Field, SQLModel


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    user_id: str
    chart_id: Optional[str] = None
    table_id: Optional[str] = None
    status: str
    report_metadata: str
