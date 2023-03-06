import io
import json
from datetime import datetime
from hashlib import md5
from typing import Any, List, Mapping, Optional, Union

import boto3
import polars as pl
from functime.preprocessing import reindex_panel
from indexhub.api.db import get_psql_conn_uri
from indexhub.api.models.report import Report
from indexhub.api.models.source import Source
from prefect import flow, task
from pydantic import BaseModel
from sqlmodel import Session, create_engine, select
from typing_extensions import Literal


def update_source_row(
    paths: Mapping[str, Union[str, Mapping[str, Any]]], metadata: Mapping[str, Any]
):
    # Unpack the metadata
    source_id = metadata["source_id"]
    paths = {k: v for k, v in paths.items() if k != "metadata"}
    fct_panel_paths = metadata.get("fct_panel_paths", None)
    start_date = metadata.get("start_date", None)
    end_date = metadata.get("end_date", None)
    status = metadata["status"]
    msg = metadata.get("msg", None)

    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        # Select rows with specific report_id only
        statement = select(Source).where(Source.id == source_id)
        result = session.exec(statement).one()
        # Update the fields based on the source_id
        result.status = status
        result.fct_panel_paths = json.dumps(fct_panel_paths)
        result.updated_at = datetime.utcnow()
        result.start_date = start_date
        result.end_date = end_date
        result.msg = msg
        # Add, commit and refresh the updated object
        session.add(result)
        session.commit()
        session.refresh(result)


def update_report_row(metadata: Mapping[str, Any]):
    # Unpack metadata
    report_id = metadata["report_id"]
    status = metadata["status"]
    completed_at = datetime.strptime(metadata["completed_at"], "%Y-%m-%d")
    entities = metadata["entities"]
    msg = metadata["msg"]
    completion_pct = metadata["completion_pct"]

    # Establish connection
    engine = create_engine(get_psql_conn_uri())

    with Session(engine) as session:
        # Select rows with specific report_id only
        statement = select(Report).where(Report.id == report_id)
        result = session.exec(statement).one()
        # Update the fields based on the report_id
        result.status = status
        result.completed_at = completed_at
        result.completion_pct = completion_pct
        result.entities = entities
        result.msg = msg
        # Add, commit and refresh the updated object
        session.add(result)
        session.commit()
        session.refresh(result)


class PreprocessPanelInput(BaseModel):
    s3_bucket: str
    time_col: str
    entity_cols: List[str]
    freq: str
    source_id: str
    raw_panel_path: str
    raw_manual_path: Optional[str] = None


class PreprocessPanelOutput(BaseModel):
    metadata: Mapping[str, str]
    actual: str
    manual: Optional[str] = None


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
        raise ValueError(f"Failed to parse datetime: {dt}")
    return fmt


@task
def load_file_raw_panel(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    # io.BytesIO fails to change blanks to "#N/A"
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    raw_panel = pl.read_excel(
        io.BytesIO(obj),
        # Ignore infer datatype to float as it is not supported by xlsx2csv
        xlsx2csv_options={"ignore_formats": "float"},
        read_csv_options={"infer_schema_length": None},
    )
    return raw_panel.lazy()


@task
def load_batch_raw_panel(
    s3_bucket: str, s3_dir: str, time_col: str, entity_cols: List[str]
) -> pl.LazyFrame:
    s3_client = boto3.client("s3")
    # Get mapping of the all the keys with their last modified date
    key_to_last_modified = {
        obj["Key"]: obj["LastModified"]
        for obj in s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_dir)["Contents"]
    }
    # Get mapping date_uploaded to objects based on the list of keys
    date_to_objects = {
        date.strftime("%Y-%m-%d %H:%M:%S"): s3_client.get_object(
            Bucket=s3_bucket, Key=key
        )["Body"].read()
        for key, date in key_to_last_modified.items()
    }
    # Read all files and append 'upload_date' column
    raw_panels = [
        pl.read_excel(
            io.BytesIO(obj),
            xlsx2csv_options={"ignore_formats": "float"},
            read_csv_options={"infer_schema_length": None},
        ).with_column(pl.lit(date).alias("upload_date"))
        for date, obj in date_to_objects.items()
    ]
    # Concat and drop duplicates based on time_col and entity_cols
    raw_panel = pl.concat(raw_panels).unique(
        subset=[time_col, *entity_cols], keep="last"
    )
    return raw_panel.lazy()


def load_raw_panel(s3_bucket: str, s3_path: str, time_col: str, entity_cols: str):
    if s3_path.endswith(".xlsx"):
        df = load_file_raw_panel(s3_bucket, s3_path)
    else:
        df = load_batch_raw_panel(s3_bucket, s3_path, time_col, entity_cols)
    return df


@task
def clean_raw_panel(
    df: pl.LazyFrame,
    time_col: str,
    entity_cols: List[str],
) -> pl.LazyFrame:

    # Infer datetime format by using the first value
    fmt = infer_dt_format(str(df.collect().select([time_col])[0, 0]))
    new_col_names = {time_col: "time"}
    df_new = (
        df.rename(new_col_names)
        .with_columns(
            [
                # Parse datatime
                (pl.col("time").cast(pl.Utf8).str.strptime(pl.Date, fmt=fmt)),
                # Cast all float cols to int
                pl.col(pl.Float32).cast(pl.Int32),
                pl.col(pl.Float64).cast(pl.Int64),
                # Defensive replace #N/A generated by nulls/blanks to 0
                pl.col(entity_cols).str.replace("#N/A", "0"),
            ]
        )
        # Downcast numeric dtypes
        .select(pl.all().shrink_dtype())
        # Sort by entity and time
        .sort(by=[*entity_cols, "time"])
        .collect(streaming=True)
    )
    return df_new.lazy()


@task
def export_fct_panel(
    df: pl.LazyFrame, s3_bucket: str, raw_data_path: str, suffix: Optional[str] = None
) -> str:
    # Use the first 7 characters of the hash of raw data path as ID
    identifer = md5(raw_data_path.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"processed/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}_{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@flow
def preprocess_panel(inputs: PreprocessPanelInput) -> PreprocessPanelOutput:

    # Unpack configs
    s3_bucket = inputs.s3_bucket
    time_col = inputs.time_col
    entity_cols = inputs.entity_cols
    raw_panel_path = inputs.raw_panel_path
    raw_manual_path = inputs.raw_manual_path

    try:
        # Load clean raw actual data
        raw_panel = load_raw_panel(s3_bucket, raw_panel_path, time_col, entity_cols)
        fct_panel = raw_panel.pipe(clean_raw_panel, time_col, entity_cols)
        fct_panel_path = export_fct_panel(fct_panel, s3_bucket, raw_panel_path)
        # Compute fct_panel metadata
        start_date = fct_panel.collect().select(pl.min("time"))[0, 0]
        end_date = fct_panel.collect().select(pl.max("time"))[0, 0]

        fct_manual_path = None
        if raw_manual_path is not None:
            # Load clean manual forecast
            raw_manual = load_raw_panel(
                s3_bucket, raw_manual_path, time_col, entity_cols
            )
            fct_manual = raw_manual.pipe(clean_raw_panel, time_col, entity_cols)
            fct_manual_path = export_fct_panel(
                fct_manual, s3_bucket, raw_manual_path, suffix="manual"
            )

        metadata = {
            "source_id": inputs.source_id,
            "freq": inputs.freq,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "status": "SUCCESS",
        }
        result = {
            "actual": fct_panel_path,
            "manual": fct_manual_path,
            "metadata": metadata,
        }
    except Exception as exc:
        result = {
            "metadata": {
                "source_id": inputs.source_id,
                "freq": inputs.freq,
                "status": "FAILED",
                "msg": str(repr(exc)),
            }
        }
    return result


class PrepareHierarchicalPanelInput(BaseModel):
    s3_bucket: str
    level_cols: List[str]
    target_col: str
    freq: str
    agg_method: Literal["sum", "mean"]
    fct_panel_path: str
    fct_manual_path: Optional[str] = None
    allow_negatives: Optional[bool] = False


class PrepareHierarchicalPanelOutput(BaseModel):
    actual: str
    manual: str


@task
def load_fct_panel(s3_bucket: str, s3_path: str):
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    fct_panel = pl.read_parquet(io.BytesIO(obj))
    return fct_panel


@task
def prepare_fct_panel(
    df: pl.DataFrame,
    label: str,
    level_cols: List[str],
    target_col: str,
    agg_method: str,
    freq: str,
    allow_negatives: bool,
):

    if not allow_negatives:
        df = df.with_column(
            # Remove negative values from target col
            pl.when(pl.col(target_col) <= 0)
            .then(0)
            .otherwise(pl.col(target_col))
            .keep_name()
        )

    entity_id = ":".join(level_cols)
    agg_methods = {
        "sum": pl.sum(target_col),
        "mean": pl.mean(target_col),
    }
    agg_expr = agg_methods[agg_method]
    df_new = (
        # Assign new col with entity_id
        df.with_column(pl.concat_str(level_cols, sep=":").alias(entity_id))
        .sort("time")
        .groupby(["time", entity_id], maintain_order=True)
        .agg(agg_expr)
        # Defensive reorder columns
        .select([entity_id, "time", target_col])
        # Defensive resampling
        .groupby_dynamic("time", every=freq, by=entity_id)
        .agg(agg_expr)
        # Defensive cast datetime col to pl.Datetime
        .with_column(pl.col("time").cast(pl.Datetime))
        # Reindex full (entity, time) index
        .pipe(reindex_panel(freq=freq, sort=True))
        .rename({target_col: f"target:{label}"})
        # TODO: relax assumption that gaps are 0
        .fill_null(0)
        # Coerce entity column name and defensive sort columns
        .select(
            [
                # Coerce entity column name
                pl.col(entity_id).alias("entity"),
                pl.col("time"),
                # Include target col with prefix "target"
                pl.col("^target_.*$"),
                # Drop original entity_id col
                pl.all().exclude(["time", entity_id]),
            ]
        )
    )

    return df_new


@task
def export_ftr_panel(
    df: pl.LazyFrame, s3_bucket: str, fct_data_path: str, suffix: Optional[str] = None
):
    # Use hash of fct data path and entity col as ID
    dataset_id = fct_data_path + df.columns[0]
    identifer = md5(dataset_id.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"processed/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}_{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@flow
def prepare_hierarchical_panel(
    inputs: PrepareHierarchicalPanelInput,
) -> PrepareHierarchicalPanelOutput:
    # Configs
    s3_bucket = inputs.s3_bucket
    preproc_kwargs = {
        "level_cols": inputs.level_cols,
        "target_col": inputs.target_col,
        "agg_method": inputs.agg_method,
        "freq": inputs.freq,
        "allow_negatives": inputs.allow_negatives,
    }
    # Preprocess fact table
    fct_panel = load_fct_panel(s3_bucket, inputs.fct_panel_path)
    ftr_panel = fct_panel.pipe(prepare_fct_panel, **preproc_kwargs, label="actual")
    ftr_panel_path = export_ftr_panel(
        ftr_panel, inputs.s3_bucket, inputs.fct_panel_path
    )
    # Preprocess manual forecast
    ftr_manual_path = None
    if inputs.ftr_manual_path is not None:
        fct_manual = load_fct_panel(s3_bucket, inputs.fct_manual_path)
        ftr_manual = fct_manual.pipe(
            prepare_fct_panel, **preproc_kwargs, label="manual"
        )
        ftr_manual_path = export_ftr_panel(
            ftr_manual,
            inputs.s3_bucket,
            inputs.fct_panel_path,
            suffix="manual",
        )
    # Return paths to exported data
    paths = {"actual": ftr_panel_path, "manual": ftr_manual_path}
    return paths
