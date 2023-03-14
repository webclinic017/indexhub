from datetime import datetime
from typing import List, Optional

from indexhub.api.models.data_table import DataTable
from sqlmodel import Field, Relationship, SQLModel


class Policy(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    fields: str
    # Outputs
    data_tables: Optional[List[DataTable]] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    msg: Optional[str] = None
