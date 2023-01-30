from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.models.source import Source
from indexhub.api.utils.init_db import engine

router = APIRouter()


class CreateSource(BaseModel):
    source_id: Optional[str] = None
    user_id: str
    name: str
    path: str
    freq: str
    level_cols: Optional[List[str]] = None


@router.post("/sources")
def create_source(create_source: CreateSource):
    with Session(engine) as session:

        if create_source.source_id:
            source_filter = select(Source).where(Source.id == create_source.source_id)
            results = session.exec(source_filter)
            if results:
                source = results.one()
            else:
                raise HTTPException(
                    status_code=400, detail="This source_id does not exist"
                )
        else:
            source = Source()

        source.user_id = create_source.user_id
        source.path = create_source.name
        source.status = "RUNNING"
        source.created_at = datetime.now()
        source.freq = create_source.freq
        source.name = create_source.name
        source.level_cols = create_source.level_cols

        session.add(source)
        session.commit()
        session.refresh(source)

        return {"user_id": create_source.user_id, "source_id": source.id}


@router.get("/sources")
def get_source(source_id: str = None, user_id: str = None):
    with Session(engine) as session:
        if source_id is None:
            if user_id is None:
                raise HTTPException(
                    status_code=400, detail="Either source_id or user_id is required"
                )
            else:
                query = select(Source).where(Source.user_id == user_id)
                sources = session.exec(query).all()
                if len(sources) == 0:
                    raise HTTPException(
                        status_code=400, detail="No records found for this user_id"
                    )
        else:
            query = select(Source).where(Source.id == source_id)
            sources = session.exec(query).all()
            if len(sources) == 0:
                raise HTTPException(
                    status_code=400, detail="No records found for this source_id"
                )

        return {"sources": sources}


@router.delete("/sources")
def delete_source(source_id: str):
    with Session(engine) as session:
        if source_id is None:
            raise HTTPException(status_code=400, detail="source_id is required")
        else:
            query = select(Source).where(Source.id == source_id)
            source = session.exec(query).first()
            if source is None:
                raise HTTPException(
                    status_code=400, detail="No record found for this source_id"
                )
            user_id = source.user_id
            session.delete(source)
            session.commit()

            return get_source(user_id=user_id)
