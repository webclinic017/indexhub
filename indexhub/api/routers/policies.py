import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.policy import Policy
from indexhub.api.models.source import Source
from indexhub.api.schemas import POLICY_SCHEMAS


router = APIRouter()


@router.get("/policies/schema/{user_id}")
def list_policy_schemas(user_id: str):
    with Session(engine) as session:
        query = select(Source).where(Source.user_id == user_id)
        sources = session.exec(query).all()
        schemas = POLICY_SCHEMAS(sources=sources)
    return schemas


class CreatePolicyParams(BaseModel):
    user_id: str
    tag: str
    name: str
    fields: str


@router.post("/policies")
def create_policy(params: CreatePolicyParams):
    with Session(engine) as session:
        policy = Policy(**params.__dict__)
        policy.status = "RUNNING"
        ts = datetime.utcnow()
        policy.created_at = ts
        policy.updated_at = ts
        session.add(policy)
        session.commit()
        session.refresh(policy)
        return {"user_id": params.user_id, "policy_id": policy.id}


@router.get("/policies")
def list_policies(user_id: str):
    with Session(engine) as session:
        query = select(Policy).where(Policy.user_id == user_id)
        policies = session.exec(query).all()
        return {"policies": policies}


@router.get("/policies/{policy_id}")
def get_policy(policy_id: str):
    with Session(engine) as session:
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).first()
        return {"policy": policy}


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: str):
    with Session(engine) as session:
        query = select(Policy).where(Policy.id == policy_id)
        report = session.exec(query).first()
        if report is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        session.delete(report)
        session.commit()
        return {"ok": True}


@router.websocket("/policies/ws")
async def ws_get_policies(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        results = list_policies(**data)
        response = []
        for result in results["policies"]:
            values = {
                k: v for k, v in vars(result).items() if k != "_sa_instance_state"
            }
            response.append(values)
        response = {"policies": response}
        await websocket.send_text(json.dumps(response, default=str))
