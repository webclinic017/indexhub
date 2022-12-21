from typing import List, Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    user_id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool
    report_ids: Optional[List[str]] = None
