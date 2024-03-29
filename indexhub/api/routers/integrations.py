import json
from typing import List

from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.integration import Integration
from indexhub.api.models.user import User
from indexhub.api.routers import router


@router.get("/integrations")
def list_integrations():
    engine = create_sql_engine()
    with Session(engine) as session:
        query = select(Integration)
        integrations = session.exec(query).all()
        return {"integrations": integrations}


@router.get("/integrations/{user_id}")
def list_user_integrations(user_id: str):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        user_integrations = []
        if user.integration_ids:
            user_integration_ids = json.loads(user.integration_ids)
            query = select(Integration).where(Integration.id.in_(user_integration_ids))
            user_integrations = session.exec(query).all()
        return {"user_integrations": user_integrations}


class SetUserIntegrationsParams(BaseModel):
    user_integrations: List[int]


@router.post("/integrations/{user_id}")
def set_user_integrations(params: SetUserIntegrationsParams, user_id: str):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        user.integration_ids = json.dumps(params.user_integrations)
        session.add(user)
        session.commit()
        return {"ok": True}


@router.delete("/integrations/{user_id}/{integration_id}")
def delete_user_integration(user_id: str, integration_id: int):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user.integration_ids:
            user_integration_ids = json.loads(user.integration_ids)
            user_integration_ids.remove(integration_id)
            user.integration_ids = json.dumps(user_integration_ids)

        session.add(user)
        session.commit()
        return {"ok": True}
