import json
from datetime import datetime

import modal
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.objective import Objective
from indexhub.api.models.source import Source
from indexhub.api.models.user import User
from indexhub.api.routers.sources import get_source
from indexhub.api.schemas import (
    OBJECTIVE_SCHEMAS,
    SUPPORTED_COUNTRIES,
    SUPPORTED_ERROR_TYPE,
    SUPPORTED_FREQ,
)

FREQ_TO_SP = {
    "Hourly": 24,
    "Daily": 30,
    "Weekly": 52,
    "Monthly": 12,
}


router = APIRouter()


@router.get("/objectives/schema/{user_id}")
def list_objective_schemas(user_id: str):
    with Session(engine) as session:
        query = select(Source).where(Source.user_id == user_id)
        sources = session.exec(query).all()
        schemas = OBJECTIVE_SCHEMAS(sources=sources)
    return schemas


class CreateObjectiveParams(BaseModel):
    user_id: str
    tag: str
    name: str
    sources: str
    fields: str


@router.post("/objectives")
def create_objective(params: CreateObjectiveParams):

    with Session(engine) as session:
        objective = Objective(**params.__dict__)
        user = session.get(User, objective.user_id)
        objective.status = "RUNNING"
        objective_sources = json.loads(objective.sources)
        objective_fields = json.loads(objective.fields)
        source = get_source(objective_sources["panel"])["source"]
        source_fields = json.loads(source.fields)
        if objective.tag == "forecast_panel":
            flow = modal.Function.lookup("indexhub-forecast", "run_forecast")
            holiday_regions = objective_fields["holiday_regions"]
            if holiday_regions is not None:
                holiday_regions = [
                    SUPPORTED_COUNTRIES[country]
                    for country in objective_fields["holiday_regions"]
                ]
            flow.call(
                user_id=objective.user_id,
                objective_id=objective.id,
                panel_path=objective_sources["panel"],
                storage_tag=user.storage_tag,
                bucket_name=user.storage_bucket_name,
                target_col=source_fields["target_col"],
                min_lags=int(objective_fields["min_lags"]),
                max_lags=int(objective_fields["max_lags"]),
                fh=int(objective_fields["fh"]),
                freq=SUPPORTED_FREQ[source.freq],
                sp=FREQ_TO_SP[source.freq],
                n_splits=objective_fields["n_splits"],
                holiday_regions=holiday_regions,
                objective=SUPPORTED_ERROR_TYPE[objective_fields["error_type"]],
                baseline_model=objective_fields.get("baseline_model", None),
                baseline_path=objective_sources["baseline"],
                inventory_path=objective_sources["inventory"],
            )
        else:
            raise ValueError(f"Objective tag `{objective.tag}` not found")

        ts = datetime.utcnow()
        objective.created_at = ts
        objective.updated_at = ts
        session.add(objective)
        session.commit()
        session.refresh(objective)

        return {"user_id": params.user_id, "objective_id": objective.id}


@router.get("/objectives")
def list_objectives(user_id: str):
    with Session(engine) as session:
        query = select(Objective).where(Objective.user_id == user_id)
        objectives = session.exec(query).all()
        return {"objectives": objectives}


@router.get("/objectives/{objective_id}")
def get_objective(objective_id: str):
    with Session(engine) as session:
        query = select(Objective).where(Objective.id == objective_id)
        objective = session.exec(query).first()
        return {"objective": objective}


@router.delete("/objectives/{objective_id}")
def delete_objective(objective_id: str):
    with Session(engine) as session:
        query = select(Objective).where(Objective.id == objective_id)
        report = session.exec(query).first()
        if report is None:
            raise HTTPException(status_code=404, detail="Objective not found")
        session.delete(report)
        session.commit()
        return {"ok": True}


@router.websocket("/objectives/ws")
async def ws_get_objectives(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        results = list_objectives(**data)
        response = []
        for result in results["objectives"]:
            values = {
                k: v for k, v in vars(result).items() if k != "_sa_instance_state"
            }
            response.append(values)
        response = {"objectives": response}
        await websocket.send_text(json.dumps(response, default=str))
