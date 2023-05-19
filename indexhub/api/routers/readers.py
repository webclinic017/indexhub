from typing import Optional

from indexhub.api.routers import router
from indexhub.api.services.io import read_data_from_s3


@router.get("/readers/s3")
def read_s3(
    bucket_name: str,
    object_path: str,
    file_ext: str,
    orient: str,
    n_rows: Optional[int] = None,
):
    data = read_data_from_s3(
        bucket_name=bucket_name,
        object_path=object_path,
        file_ext=file_ext,
        n_rows=n_rows,
    )
    if orient == "records":
        return {"data": data.to_dicts()}
    elif orient == "list":
        return {"data": data.to_dict(as_series=False)}
