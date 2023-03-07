import codecs
import io
import json
from datetime import datetime
from typing import List, Optional

import boto3
import botocore
import polars as pl
from fastapi import APIRouter, HTTPException, WebSocket
from indexhub.api.db import engine
from indexhub.api.models.source import Source
from pydantic import BaseModel
from sqlmodel import Session, select
from ydata_profiling import ProfileReport


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


def infer_dt_format(dt: str):
    n_chars = len(dt)
    if n_chars == 19:
        fmt = "%Y-%m-%d %H:%M:%S"
    elif n_chars == 10:
        fmt = "%Y-%m-%d"
    elif n_chars == 7:
        if "-" in dt:
            fmt = "%Y-%m"
    elif n_chars == 6:
        fmt = "%Y%m"
    else:
        fmt = False
    return fmt


def read_source_excel(s3_bucket: str, s3_path: str) -> pl.DataFrame:
    s3_client = boto3.client("s3")
    obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_path)["Body"].read()
    raw_panel = pl.read_excel(
        io.BytesIO(obj),
        # Ignore infer datatype to float as it is not supported by xlsx2csv
        xlsx2csv_options={"ignore_formats": "float"},
        read_csv_options={
            "infer_schema_length": None,
            "parse_dates": True,
            "use_pyarrow": True,
        },
    )
    s3_client.close()
    return raw_panel


def check_duplicates(time_col: str, entity_cols: List[str], target_cols: List[str]):
    columns_set = {
        time_col,
        *entity_cols,
        *target_cols,
    }
    columns = [
        time_col,
        *entity_cols,
        *target_cols,
    ]
    has_duplicates = len(columns) != len(columns_set)
    return has_duplicates


def check_time_col_fmt(df: pl.DataFrame, time_col: str):
    fmt = infer_dt_format(str(df.select([time_col])[0, 0]))
    try:
        df = df.select(pl.col(time_col).cast(pl.Utf8).str.strptime(pl.Date, fmt=fmt))
    except Exception as err:
        return err
    return df


def check_filters(entity_cols: List[str], filters: str):
    filters = json.loads(filters)
    return [col for col in filters.keys() if col not in entity_cols]


@router.post("/sources")
def create_source(create_source: CreateSource):
    # Check if the raw_data_path is readable
    try:
        raw_panel = read_source_excel(
            s3_bucket=create_source.s3_data_bucket, s3_path=create_source.raw_data_path
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail="Invalid raw data path") from err
    # Check if the manual_forecast_path is readable
    if create_source.manual_forecast_path:
        try:
            raw_panel = read_source_excel(
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
        raw_panel = read_source_excel(s3_bucket=s3_data_bucket, s3_path=path)
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


@router.get("/sources/profile")
def get_source_profile(source_id: str):
    s3_bucket = None
    s3_path = None
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
            s3_bucket = source.s3_data_bucket
            s3_path = source.raw_data_path

    try:
        df = read_source_excel(s3_bucket=s3_bucket, s3_path=s3_path)
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail="Invalid S3 path") from err

    profile = ProfileReport(df.to_pandas(), title="Profiling Report", tsmode=True)
    profile.to_file("your_report.html")

    page = codecs.open("your_report.html", "rb").read()
    return {"data": page}
