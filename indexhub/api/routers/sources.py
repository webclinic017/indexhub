import json
from datetime import datetime
from typing import List, Optional

import botocore
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session, select

from indexhub.api.check_source import (
    check_duplicates,
    check_filters,
    check_time_col_fmt,
    read_source_file,
)
from indexhub.api.db import engine
from indexhub.api.models.source import Source

router = APIRouter()


class CreateSource(BaseModel):
    source_id: Optional[str] = None
    user_id: str
    name: str
    raw_data_path: str
    freq: str
    s3_data_bucket: str
    time_col: str
    entity_cols: List[str]
    target_cols: List[str]
    filters: Optional[str]
    manual_forecast_path: Optional[str] = None


@router.post("/sources")
def create_source(create_source: CreateSource):
    # Check if the raw_data_path is readable
    try:
        raw_panel = read_source_file(
            s3_bucket=create_source.s3_data_bucket, s3_path=create_source.raw_data_path
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail="Invalid raw data path") from err
    # Check if the manual_forecast_path is readable
    if create_source.manual_forecast_path:
        try:
            raw_panel = read_source_file(
                s3_bucket=create_source.s3_data_bucket,
                s3_path=create_source.manual_forecast_path,
            )
        except Exception as err:
            raise HTTPException(
                status_code=400, detail="Invalid manual data path"
            ) from err
    # Check if there are duplication between time/entity/target col
    if check_duplicates(
        create_source.time_col, create_source.entity_cols, create_source.target_cols
    ):
        raise HTTPException(
            status_code=400, detail="Duplicates in time, entity and target columns"
        )
    # Check if the time_col can be parsed into the acceptable format
    if check_time_col_fmt(raw_panel, create_source.time_col) is None:
        raise HTTPException(
            status_code=400, detail="Time column not in the right format"
        )
    # Check if filter keys are subset of the entity columns
    if create_source.filters:
        len_duplicates = len(
            check_filters(create_source.entity_cols, create_source.filters)
        )
    if create_source.filters and len_duplicates > 0:
        raise HTTPException(
            status_code=400, detail="Invalid filter keys - not in entity columns"
        )
    # Create new record in postgres
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
        source.raw_data_path = create_source.raw_data_path
        source.status = "RUNNING"
        source.created_at = datetime.now()
        source.s3_data_bucket = create_source.s3_data_bucket
        source.freq = create_source.freq
        source.name = create_source.name
        source.time_col = create_source.time_col
        source.entity_cols = json.dumps(create_source.entity_cols)
        source.target_cols = json.dumps(create_source.target_cols)

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
        # Cast entity_cols and target_cols from json string to List[str]
        for source in sources:
            source.entity_cols = json.loads(source.entity_cols)
            source.target_cols = json.loads(source.target_cols)

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


@router.get("/sources/columns")
def read_source_cols(s3_data_bucket: str, path: str):
    try:
        raw_panel = read_source_file(s3_bucket=s3_data_bucket, s3_path=path)
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail="Invalid S3 path") from err
    columns = [col for col in raw_panel.columns if col]

    return {"columns": columns}


@router.websocket("/sources/ws")
async def ws_get_sources(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        source_id = data.get("source_id")
        user_id = data.get("user_id")
        results = get_source(source_id=source_id, user_id=user_id)

        response = []
        for result in results["sources"]:
            values = {
                k: v for k, v in vars(result).items() if k != "_sa_instance_state"
            }
            response.append(values)
        response = {"sources": response}
        await websocket.send_text(json.dumps(response, default=str))
