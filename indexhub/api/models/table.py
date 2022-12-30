from sqlmodel import Field, SQLModel


class Table(SQLModel, table=True):
    table_id: str = Field(default=None, primary_key=True)
    path: str
    title: str
    readable_names: str  # dict
