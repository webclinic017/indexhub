from typing import List, Optional

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlmodel import Field, Session, select

from indexhub.api.models.user import User
from indexhub.api.utils.init_db import engine

router = APIRouter()


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


@router.post("/users")
def create_user(
    create_user: CreateUser,
):

    with Session(engine) as session:

        user = User()
        user.user_id = create_user.user_id
        user.name = create_user.name
        user.nickname = create_user.nickname
        user.email = create_user.email
        user.email_verified = create_user.email_verified

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "user_id": create_user.user_id,
            "message": "User creation on backend success",
        }


@router.get("/users/{user_id}")
def get_user(response: Response, user_id: str):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is not None:
            return user
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "User id not found"}


@router.patch("/users/{user_id}")
def patch_user(
    user_patch: UserPatch,
    user_id: str,
):

    with Session(engine) as session:
        filter_user_query = select(User).where(User.user_id == user_id)
        results = session.exec(filter_user_query)
        user = results.one()

        user.name = user_patch.name or user.name
        user.nickname = user_patch.nickname or user.nickname
        user.email = user_patch.email or user.email
        user.email_verified = user_patch.email_verified or user.email_verified
        user.report_ids = user_patch.report_ids or user.report_ids

        session.add(user)
        session.commit()
        session.refresh(user)

        return user
