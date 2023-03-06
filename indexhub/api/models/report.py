import enum
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from indexhub.api.models.chart import Chart
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.source import Source  # noqa


class AggMethods(str, enum.Enum):
    SUM = "SUM"
    MEAN = "MEAN"


class Report(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    source_id: int = Field(default=None, foreign_key="source.id")
    source_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    target_col: str
    level_cols: List[str]
    charts: List[Chart] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    tables: List[DataTable] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    agg_method: AggMethods = Field(default="SUM")
    allow_negatives: bool = False
    msg: Optional[str] = None
