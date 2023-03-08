from datetime import datetime
from typing import List, Optional

from indexhub.api.models._status import StatusTypes
from indexhub.api.models.data_table import DataTable
from indexhub.api.models.source import Source  # noqa
from sqlmodel import Field, Relationship, SQLModel


def TARGET_COL_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def LEVEL_COLS_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def POLICY_SCHEMAS(col_names):
    return {
        "forecast": {
            "description": "Reduce {direction} forecast error for {risks} entitie).",
            "fields": {
                "direction": {
                    "title": "",
                    "subtitle": "",
                    "values": ["over", "under", "overall"],
                },
                "risks": {"title": "", "subtitle": "", "values": ["low volatility"]},
                "target_col": TARGET_COL_SCHEMA(col_names),
                "level_cols": LEVEL_COLS_SCHEMA(col_names),
            },
            "sources": [
                {"name": "panel", "title": "", "subtitle": ""},
                {"name": "benchmark", "title": "", "subtitle": ""},
            ],
        }
    }


class Policy(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    tag: str
    name: str
    status: StatusTypes
    created_at: datetime
    updated_at: datetime
    # Policy specific variables
    source_ids: int = Field(default=None, foreign_key="source.id")
    schema: str
    # Outputs
    data_tables: List[DataTable] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    msg: Optional[str] = None
