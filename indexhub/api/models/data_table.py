import enum

from sqlmodel import Field, SQLModel


class DataTableTags(str, enum.Enum):
    pass


class DataTable(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    tag: DataTableTags
    path: str
    policy_id: int = Field(default=None, foreign_key="policy.id")
