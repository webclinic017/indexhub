import json
from datetime import datetime

import modal
from fastapi import HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.db import engine
from indexhub.api.models.source import Source
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.schemas import CONNECTION_SCHEMA, DATASET_SCHEMA


class CreateSourceParams(BaseModel):
    user_id: str
    tag: str
    name: str
    type: str
    conn_fields: str
    data_fields: str


@router.get("/sources/conn_schema/{user_id}")
def list_conn_schemas(user_id: str):
    with Session(engine) as session:
        query = select(User).where(User.id == user_id)
        user = session.exec(query).first()
        return CONNECTION_SCHEMA(user=user)


@router.get("/sources/dataset_schema")
def list_dataset_schemas():
    return DATASET_SCHEMA


@router.post("/sources")
def create_source(params: CreateSourceParams):
    with Session(engine) as session:
        source = Source(**params.__dict__)
        user = session.get(User, source.user_id)
        source.status = "RUNNING"
        conn_fields = json.loads(source.conn_fields)
        data_fields = json.loads(source.data_fields)
        flow = modal.Function.lookup("indexhub-preprocess", "run_preprocess_and_embs")
        flow.call(
            user_id=source.user_id,
            source_id=source.id,
            source_tag=source.tag,
            conn_fields=conn_fields,
            data_fields=data_fields,
            storage_tag=user.storage_tag,
            storage_bucket_name=user.storage_bucket_name,
        )

        ts = datetime.utcnow()
        source.created_at = ts
        source.updated_at = ts
        session.add(source)
        session.commit()
        session.refresh(source)
        return {"user_id": params.user_id, "source_id": source.id}


@router.get("/sources")
def list_sources(user_id: str):
    with Session(engine) as session:
        query = select(Source).where(Source.user_id == user_id)
        sources = session.exec(query).all()
        return {"sources": sources}


@router.get("/sources/{source_id}")
def get_source(source_id: str):
    with Session(engine) as session:
        query = select(Source).where(Source.id == source_id)
        source = session.exec(query).first()
        return {"source": source}


@router.delete("/sources/{source_id}")
def delete_source(source_id: str):
    with Session(engine) as session:
        query = select(Source).where(Source.id == source_id)
        source = session.exec(query).first()
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        session.delete(source)
        session.commit()
        return {"ok": True}


@router.websocket("/sources/ws")
async def ws_get_sources(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        results = list_sources(**data)
        response = []
        for result in results["sources"]:
            values = {
                k: v for k, v in vars(result).items() if k != "_sa_instance_state"
            }
            response.append(values)
        response = {"sources": response}
        await websocket.send_text(json.dumps(response, default=str))
