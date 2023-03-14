from typing import Optional

import boto3
import botocore
from fastapi import APIRouter, HTTPException
from indexhub.api.services.parsers import parse_csv, parse_excel, parse_parquet


FILE_EXT_TO_PARSER = {"excel": parse_excel, "csv": parse_csv, "parquet": parse_parquet}


router = APIRouter()


def read_data_from_s3(
    s3_bucket: str,
    s3_path: str,
    file_ext: str,
    n_rows: Optional[int] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_path)["Body"].read()
    except botocore.exceptions.ClientError as err:
        error_code = err.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise HTTPException(status_code=400, detail="Invalid S3 bucket") from err
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=400, detail="Invalid S3 path") from err
    s3_client.close()
    parser = FILE_EXT_TO_PARSER[file_ext]
    data = parser(obj, n_rows)
    return data
