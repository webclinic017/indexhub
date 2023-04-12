import io
from typing import Optional

import boto3
import botocore
import polars as pl
from fastapi import APIRouter, HTTPException

from indexhub.api.services.parsers import parse_csv, parse_excel, parse_parquet


FILE_EXT_TO_PARSER = {"excel": parse_excel, "csv": parse_csv, "parquet": parse_parquet}

router = APIRouter()


def read_data_from_s3(
    bucket_name: str,
    object_path: str,
    file_ext: str,
    n_rows: Optional[int] = None,
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_ACCESS_KEY: Optional[str] = None,
):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=object_path)["Body"].read()
    except botocore.exceptions.ClientError as err:
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
                status_code=400, detail="Invalid S3 access key when reading from source"
            ) from err
        elif error_code == "SignatureDoesNotMatch":
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 access secret when reading from source",
            ) from err
        else:
            raise err
    s3_client.close()
    parser = FILE_EXT_TO_PARSER[file_ext]
    data = parser(obj, n_rows)
    return data


def write_data_to_s3(
    data: pl.DataFrame,
    bucket_name: str,
    object_path: str,
    AWS_ACCESS_KEY_ID: Optional[str] = None,
    AWS_SECRET_ACCESS_KEY: Optional[str] = None,
):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    f = io.BytesIO()
    data.write_parquet(f)
    f.seek(0)
    body = f.read()
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_path, Body=body)
    except botocore.exceptions.ClientError as err:
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
