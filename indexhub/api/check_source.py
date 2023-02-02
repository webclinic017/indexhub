import io
import json
from typing import List

import boto3
import polars as pl


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


def read_source_file(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
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
