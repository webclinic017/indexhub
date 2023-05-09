from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Source(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    type: str
    variables: str
    fields: str
    output_path: Optional[str] = None
    msg: Optional[str] = None
