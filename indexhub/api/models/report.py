import json
from datetime import datetime
import enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

from indexhub.api.models.chart import Chart
from indexhub.api.models.source import Source, StatusTypes  # noqa
from indexhub.api.models.table import Table

class AggMethods(str, enum.Enum):
    SUM = "SUM"
    MEAN = "MEAN"

class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    source_id: Optional[int] = Field(default=None, foreign_key="source.id")
    source_name: str
    user_id: str
    status: Optional[StatusTypes] = Field(default="RUNNING")
    created_at: datetime
    completed_at: Optional[datetime] = None
    entities: Optional[str] = json.dumps({"forecast_recommendations": {}})
    charts: List[Chart] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
        },
    )
    tables: List[Table] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
        },
    )
    level_cols: List[str]
    target_col: str
    completion_pct: Optional[float]
    date_features: Optional[List[str]]
    lags: Optional[List[int]]
    agg_method: Optional[StatusTypes] = Field(default="SUM")
    allow_negatives: Optional[bool] = False
    use_manual_zeros: Optional[bool] = False
    msg: Optional[str]
