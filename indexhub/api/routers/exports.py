import io

import boto3
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


@router.post("/exports/list-exports/{objective_id}")
def list_exports(objective_id: str):
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        user = session.get(User, objective.user_id)
        # Get credentials
        storage_creds = get_aws_secret(
            tag=user.storage_tag, secret_type="storage", user_id=user.id
        )
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=storage_creds["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=storage_creds["AWS_SECRET_KEY_ID"],
        )
        prefix = f"exports/{objective_id}/"
        objects = s3_client.list_objects_v2(
            Bucket=user.storage_bucket_name, Prefix=prefix
        )

        files = [file["Key"].replace(prefix, "") for file in objects["Contents"]]

    return files


@router.post("/exports/download-file/{objective_id}/{filename}")
def download_file(objective_id: str, filename: str):
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        user = session.get(User, objective.user_id)
        # Get credentials
        storage_creds = get_aws_secret(
            tag=user.storage_tag, secret_type="storage", user_id=user.id
        )

        # Read file
        path = f"exports/{objective_id}/{filename}"
        data = SOURCE_TAG_TO_READER[user.storage_tag](
            bucket_name=user.storage_bucket_name,
            object_path=path,
            file_ext="csv",
            **storage_creds,
        )
        f = io.BytesIO()
        data.write_csv(f, datetime_format="%Y-%m-%d")
        f.seek(0)
        output = f.read()

    return output
