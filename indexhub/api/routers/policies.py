import json
from datetime import datetime
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, WebSocket
from indexhub.api.db import engine
from indexhub.api.models.policies import TAG_TO_POLICY
from sqlmodel import Session, select


router = APIRouter()


@router.post("/policies")
def create_policy(params: Mapping[str, Any], tag: str):
    with Session(engine) as session:
        policy = TAG_TO_POLICY[tag](**params)
        policy.status = "RUNNING"
        ts = datetime.utcnow()
        policy.created_at = ts
        policy.updated_at = ts
        session.add(policy)
        session.commit()
        session.refresh(policy)
        return {"user_id": params["user_id"], "policy_id": policy.id}


@router.get("/policies")
def list_policies(user_id: str, tag: str):
    with Session(engine) as session:
        Policy = TAG_TO_POLICY[tag]
        query = select(Policy).where(Policy.user_id == user_id)
        policies = session.exec(query).all()
        return {"policies": policies}


@router.get("/policies/{policy_id}")
def get_policy(policy_id: str, tag: str):
    with Session(engine) as session:
        Policy = TAG_TO_POLICY[tag]
        query = select(Policy).where(Policy.id == policy_id)
        policy = session.exec(query).all()
        return {"policy": policy}


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: str, tag: str):
    with Session(engine) as session:
        Policy = TAG_TO_POLICY[tag]
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
        result = list_policies(**data)
        response = {"policies": result["policies"]}
        await websocket.send_text(json.dumps(response, default=str))
