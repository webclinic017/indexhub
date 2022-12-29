from typing import Optional

from sqlmodel import Field, SQLModel


class Chart(SQLModel, table=True):
    chart_id: str = Field(default=None, primary_key=True)
    path: str
    title: str
    axis_labels: str
    readable_names: str  # dict
    chart_type: str
    entity_id: Optional[float] = None
