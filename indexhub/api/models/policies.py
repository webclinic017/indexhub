from datetime import datetime
from typing import List, Optional

from indexhub.api.models._status import StatusTypes
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.source import Source  # noqa
from sqlmodel import Field, Relationship, SQLModel

POLICY_SCHEMAS = {
    "forecast": {
        "description": "Reduce {direction} forecast error for {risks} entities (e.g. items, clients, locations).",
        "direction": {
            "title": "",
            "subtitle": "",
            "values": ["over", "under", "overall"],
        },
        "risks": {"title": "", "subtitle": "", "values": []},
    }
}

POLICY_VARIABLES = {
    "forecast": {
        "panel_source_id": {
            "title": "",
            "subtitle": "",
        },
        "benchmark_source_id": {
            "title": "",
            "subtitle": "",
        },
        "level_cols": {
            "title": "",
            "subtitle": "",
        },
        "target_col": {
            "title": "",
            "subtitle": "",
        },
    }
}


class ForecastPolicy(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    name: str
    status: StatusTypes
    created_at: datetime
    updated_at: datetime
    # Policy specific variables
    panel_source_id: int = Field(default=None, foreign_key="source.id")
    benchmark_source_id: int = Field(default=None, foreign_key="source.id")
    level_cols: List[str]
    target_col: str
    # Outputs
    data_tables: List[DataTable] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    msg: Optional[str] = None


TAG_TO_POLICY = {"forecast": ForecastPolicy}
