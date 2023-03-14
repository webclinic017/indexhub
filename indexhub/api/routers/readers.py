from typing import Optional

from fastapi import APIRouter
from indexhub.api.routers.readers import load_s3_data


router = APIRouter()


@router.get("/readers/s3")
def read_s3(s3_bucket: str, s3_path: str, file_ext: str, n_rows: Optional[int] = None):
    data = load_s3_data(
        s3_bucket=s3_bucket, s3_path=s3_path, file_ext=file_ext, n_rows=n_rows
    )
    return data
