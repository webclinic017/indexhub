from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Report(SQLModel, table=True):
    report_id: str = Field(default=None, primary_key=True)
    user_id: str
    chart_id: Optional[str] = None
    table_id: Optional[str] = None
    status: str
    report_metadata: str


class CreateReport(BaseModel):
    user_id: str


class RequestReport(BaseModel):
    report_id: Optional[str] = None
    user_id: Optional[str] = None
