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


class Source(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Source specific variables
    variables: str
    freq: str
    datetime_fmt: str
    entity_cols: List[str]
    time_col: str
    feature_cols: List[str]
    policies: List["Policy"] = Relationship(
        back_populates="sources", link_model=PolicySourceLink
    )
    output_path: Optional[str] = None
    msg: Optional[str] = None
