import io
import logging
import os
from typing import List, Optional, Union

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


def check_s3_path(
    bucket_name: str,
    object_path: str,
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_KEY_ID: Optional[str] = None,
) -> str:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_KEY_ID,
    )
    try:
        # Check if the key represents a file or a directory
        obj = s3_client.head_object(Bucket=bucket_name, Key=object_path)
        if obj["ContentLength"] > 0:  # If the key represents a file
            logger.info(f"📄 The key provided represents a file")
            path_type = ""
        else:  # If the key represents a directory
            logger.info(f"📁 The key provided represents a directory/folder")
            path_type = "_batch"

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
    finally:
        s3_client.close()
    return path_type


def read_batch_from_s3(
    bucket_name: str,
    object_path: str,
    file_ext: str,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_KEY_ID: Optional[str] = None,
) -> Union[pl.DataFrame, List[pl.DataFrame]]:
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_KEY_ID,
        )
        # Get mapping of the all the keys with their last modified date
        objs = s3_client.list_objects(Bucket=bucket_name, Prefix=object_path)
        if objs.get("Contents") is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 path when reading from storage. Please check if the directory exists.",
            )
        key_to_last_modified = {
            obj["Key"]: obj["LastModified"]
            for obj in objs["Contents"]
            if not obj["Key"].endswith("/")
        }
        # Get mapping date_uploaded to objects based on the list of keys
        date_to_objects = {
            date.strftime("%Y-%m-%d %H:%M:%S"): s3_client.get_object(
                Bucket=bucket_name, Key=key
            )["Body"].read()
            for key, date in key_to_last_modified.items()
        }
        # Read all files and append 'upload_date' column
        parser = FILE_EXT_TO_PARSER.get(file_ext)
        raw_panels = [
            parser(obj=obj, columns=columns, dateformat=dateformat).with_columns(
                [
                    pl.col(pl.Datetime("ns")).dt.cast_time_unit("us"),
                    pl.lit(date).alias("upload_date"),
                ]
            )
            for date, obj in date_to_objects.items()
        ]

    except botocore.exceptions.ClientError as err:
        logger.exception("❌ Error occured when reading from s3 storage.")
        error_code = err.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise HTTPException(
                status_code=400, detail="Invalid S3 bucket when reading from storage."
            ) from err
        elif error_code == "NoSuchKey":
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 path when reading from storage.",
            ) from err
        elif error_code == "InvalidAccessKeyId":
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 access key when reading from storage.",
            ) from err
        elif error_code == "SignatureDoesNotMatch":
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 access secret when reading from storage.",
            ) from err
        else:
            raise err
    finally:
        s3_client.close()
    return raw_panels


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
                    status_code=400,
                    detail="Invalid S3 bucket when reading from source.",
                ) from err
            elif error_code == "NoSuchKey":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid S3 path when reading from source. Please ensure that '/' is included at the end of the path if reading from a directory or folder.",
                ) from err
            elif error_code == "InvalidAccessKeyId":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid S3 access key when reading from source.",
                ) from err
            elif error_code == "SignatureDoesNotMatch":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid S3 access secret when reading from source.",
                ) from err
            else:
                raise err
        finally:
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
    finally:
        s3_client.close()
    return data


SOURCE_TAG_TO_READER = {
    "s3": read_data_from_s3,
    "s3_batch": read_batch_from_s3,
}


STORAGE_TAG_TO_WRITER = {
    "s3": write_data_to_s3,
}
