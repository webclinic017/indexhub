from sqlmodel import Field, SQLModel


class DataTable(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    tag: str
    path: str
    policy_id: int = Field(default=None, foreign_key="policy.id")
