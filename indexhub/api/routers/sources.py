import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, WebSocket
from indexhub.api.db import engine
from indexhub.api.models.source import SOURCE_SCHEMAS, Source
from pydantic import BaseModel
from sqlmodel import Session, select

router = APIRouter()


class CreateSourceParams(BaseModel):
    user_id: str
    tag: str
    name: str
    metadata: str
    freq: str
    datetime_fmt: str
    entity_cols: List[str]
    time_col: str
    target_cols: List[str]


@router.get("sources/tags")
def list_source_tags():
    return list(SOURCE_SCHEMAS.keys())


@router.post("/sources")
def create_source(params: CreateSourceParams):
    with Session(engine) as session:
        source = Source(**params)
        source.status = "RUNNING"
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
        source = session.exec(query).all()
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
        result = list_sources(**data)
        response = {"sources": result["sources"]}
        await websocket.send_text(json.dumps(response, default=str))
