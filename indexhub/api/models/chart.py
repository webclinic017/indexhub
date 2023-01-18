from typing import Optional

from sqlmodel import Field, SQLModel


class Chart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    path: str
    title: str
    axis_labels: str
    readable_names: str  # dict
    chart_type: str
