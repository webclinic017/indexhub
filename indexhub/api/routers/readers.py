from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.services.io import read_data_from_s3
from indexhub.api.services.secrets_manager import get_aws_secret


@router.get("/readers/s3/{user_id}")
def read_s3(
    user_id: str,
    bucket_name: str,
    object_path: str,
    file_ext: str,
    orient: str,
):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)

    # Get credentials
    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )

    data = read_data_from_s3(
        bucket_name=bucket_name,
        object_path=object_path,
        file_ext=file_ext,
        **storage_creds,
    )
    if orient == "records":
        return {"data": data.to_dicts()}
    elif orient == "list":
        return {"data": data.to_dict(as_series=False)}
