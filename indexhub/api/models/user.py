from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    user_id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool
    report_ids: Optional[List[str]] = None


class CreateUser(BaseModel):
    user_id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool


class UserPatch(BaseModel):
    name: Optional[str] = None
    nickname: str
    email: Optional[str] = None
    email_verified: Optional[str] = None
    report_ids: Optional[List[str]] = None
