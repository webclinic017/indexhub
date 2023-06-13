import io
import logging
import os
from typing import List, Optional

import boto3
import botocore
import polars as pl
from fastapi import HTTPException

from indexhub.api.cache import CACHE
from indexhub.api.services.parsers import (
    parse_csv,
    parse_excel,
    parse_json,
    parse_parquet,
)


def _logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Prevent the modal client from double-logging.
    return logger


logger = _logger(name=__name__)


FILE_EXT_TO_PARSER = {
    "xlsx": parse_excel,
    "csv": parse_csv,
    "parquet": parse_parquet,
    "json": parse_json,
}


def read_data_from_s3(
    bucket_name: str,
    object_path: str,
    file_ext: str,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_KEY_ID: Optional[str] = None,
):
    key = f"{bucket_name}/{object_path}.{file_ext}"
    if columns is not None:
        key = f"{key}:{columns}"
    data = CACHE.get(key)
    if data is not None:
        return data

    if file_ext == "lance":
        import lance
        import polars as pl

        uri = f"s3://{bucket_name}/{object_path}"
        ds = lance.dataset(uri)
        table = ds.to_table(columns=columns)
        obj = pl.from_arrow(table)
    else:
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_KEY_ID,
                region_name=os.environ["AWS_DEFAULT_REGION"],
            )
            obj = s3_client.get_object(Bucket=bucket_name, Key=object_path)[
                "Body"
            ].read()
        except botocore.exceptions.ClientError as err:
            logger.exception("❌ Error occured when reading from s3 storage.")
            error_code = err.response["Error"]["Code"]
            if error_code == "NoSuchBucket":
                raise HTTPException(
                    status_code=400, detail="Invalid S3 bucket when reading from source"
                ) from err
            elif error_code == "NoSuchKey":
                raise HTTPException(
                    status_code=400, detail="Invalid S3 path when reading from source"
                ) from err
            elif error_code == "InvalidAccessKeyId":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid S3 access key when reading from source",
                ) from err
            elif error_code == "SignatureDoesNotMatch":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid S3 access secret when reading from source",
                ) from err
            else:
                raise err
        s3_client.close()
    parser = FILE_EXT_TO_PARSER.get(file_ext)
    if parser is not None:
        data = parser(obj=obj, columns=columns, dateformat=dateformat)
    else:
        data = obj
    CACHE.set(key, data)
    return data


def write_data_to_s3(
    data: pl.DataFrame,
    bucket_name: str,
    object_path: str,
    file_ext: str = "parquet",
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_KEY_ID: Optional[str] = None,
    datetime_format: str = "%Y-%m-%d",
):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_KEY_ID,
    )
    f = io.BytesIO()
    if file_ext == "parquet":
        data.write_parquet(f)
    elif file_ext == "csv":
        data.write_csv(f, datetime_format=datetime_format)
    f.seek(0)
    body = f.read()
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_path, Body=body)
    except botocore.exceptions.ClientError as err:
        logger.exception("❌ Error occured when writing to s3 storage.")
        error_code = err.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise HTTPException(
                status_code=400, detail="Invalid S3 bucket when writing to storage"
            ) from err
        elif error_code == "NoSuchKey":
            raise HTTPException(
                status_code=400, detail="Invalid S3 path when writing to storage"
            ) from err
        elif error_code == "InvalidAccessKeyId":
            raise HTTPException(
                status_code=400, detail="Invalid S3 access key when writing to storage"
            ) from err
        elif error_code == "SignatureDoesNotMatch":
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 access secret when writing to storage",
            ) from err
        else:
            raise err
    s3_client.close()
    return data


SOURCE_TAG_TO_READER = {
    "s3": read_data_from_s3,
}


STORAGE_TAG_TO_WRITER = {
    "s3": write_data_to_s3,
}
