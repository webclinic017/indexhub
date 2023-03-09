from datetime import datetime
from typing import List, Optional

from indexhub.api.models.data_table import DataTable
from sqlmodel import Field, Relationship, SQLModel

# =========================== POLICY SOURCE LINK MODEL =========================== #


class PolicySourceLink(SQLModel, table=True):
    policy_id: Optional[int] = Field(
        default=None, foreign_key="policy.id", primary_key=True
    )
    source_id: Optional[int] = Field(
        default=None, foreign_key="source.id", primary_key=True
    )


# =========================== POLICY MODEL =========================== #


def TARGET_COL_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def LEVEL_COLS_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def POLICY_SCHEMAS(entity_cols, feature_cols):
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
                "target_col": TARGET_COL_SCHEMA(feature_cols),
                "level_cols": LEVEL_COLS_SCHEMA(entity_cols),
            },
            "sources": [
                {"name": "panel", "title": "", "subtitle": ""},
                {"name": "benchmark", "title": "", "subtitle": ""},
            ],
        }
    }


class Policy(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Policy specific variables
    sources: List["Source"] = Relationship(
        back_populates="policies", link_model=PolicySourceLink
    )
    structure: str
    # Outputs
    data_tables: Optional[List[DataTable]] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    msg: Optional[str] = None


# =========================== SOURCE MODEL =========================== #


SUPPORTED_FILE_EXT = {"title": "", "subtitle": "", "values": ["csv", "xlsx", "parquet"]}


SOURCE_SCHEMAS = {
    "s3": {
        "description": "",
        "variables": {
            "bucket_name": {
                "title": "",
                "subtitle": "",
            },
            "object_path": {
                "title": "",
                "subtitle": "",
            },
            "file_ext": SUPPORTED_FILE_EXT,
        },
    },
    "azure": {
        "description": "",
        "variables": {
            "bucket_name": {
                "title": "",
                "subtitle": "",
            },
            "object_path": {
                "title": "",
                "subtitle": "",
            },
            "file_ext": SUPPORTED_FILE_EXT,
        },
    },
}


class Source(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Source specific variables
    attributes: str
    freq: str
    datetime_fmt: str
    entity_cols: List[str]
    time_col: str
    feature_cols: List[str]
    policies: List[Policy] = Relationship(
        back_populates="sources", link_model=PolicySourceLink
    )
    msg: Optional[str] = None
