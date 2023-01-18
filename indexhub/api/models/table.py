from typing import Optional

from sqlmodel import Field, SQLModel


class Table(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    path: str
    title: str
    readable_names: str  # dict
