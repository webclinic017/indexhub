import json
from datetime import datetime

import modal
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.policy import Policy
from indexhub.api.models.source import Source
from indexhub.api.models.user import User
from indexhub.api.schemas import FREQ_NAME_TO_ALIAS, POLICY_SCHEMAS, SUPPORTED_COUNTRIES


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
        user = session.get(User, policy.user_id)
        policy.status = "RUNNING"
        policy_sources = json.loads(policy.sources)
        policy_fields = json.loads(policy.fields)
        if policy.tag == "forecast":
            flow = modal.Function.lookup("indexhub-forecast", "flow")
            flow.call(
                user_id=policy.user_id,
                policy_id=policy.id,
                panel_path=policy_sources["panel"],
                baseline_path=policy_sources("baseline"),
                storage_tag=user.storage_tag,
                bucket_name=user.storage_bucket_name,
                level_cols=policy_fields["level_cols"],
                target_col=policy_fields["target_col"],
                min_lags=int(policy_fields["min_lags"]),
                max_lags=int(policy_fields["max_lags"]),
                fh=int(policy_fields["fh"]),
                freq=FREQ_NAME_TO_ALIAS[policy_fields["freq"]],
                n_splits=policy_fields["n_splits"],
                holiday_regions=[
                    SUPPORTED_COUNTRIES[country]
                    for country in policy_fields["holiday_regions"]
                ],
            )
        else:
            raise ValueError(f"Policy tag `{policy.tag}` not found")

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
