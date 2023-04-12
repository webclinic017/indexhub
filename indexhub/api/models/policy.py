from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


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
    outputs: str
    msg: Optional[str] = None
