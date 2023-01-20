from typing import Optional

from sqlmodel import Column, Field, ForeignKey, Integer, SQLModel


class Table(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    report_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("report.id", ondelete="CASCADE"))
    )
    tag: str
    path: str
    title: str
    readable_names: str  # dict
