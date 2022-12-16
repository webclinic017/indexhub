from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    chart_id: Optional[str]
    table_id: Optional[str]
    status: str
    report_metadata: str


class CreateReport(BaseModel):
    user_id: str
