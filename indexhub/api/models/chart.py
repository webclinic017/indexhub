from typing import Optional

from sqlmodel import Field, SQLModel


class Chart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    report_id: Optional[int] = Field(default=None, foreign_key="report.id")
    tag: str
    path: str
    title: str
    axis_labels: str
    readable_names: str  # dict
    type: str
