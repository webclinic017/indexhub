import json
import logging
from datetime import datetime
from typing import List, Mapping, Optional, Union

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Field, Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.schemas import STORAGE_SCHEMAS
from indexhub.api.services.secrets_manager import create_aws_secret


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


class CreateUser(BaseModel):
    user_id: str = Field(default=None, primary_key=True)
    name: str
    nickname: str
    email: str
    email_verified: bool


@router.post("/users")
def create_user(
    create_user: CreateUser,
):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = User()
        user.id = create_user.user_id
        user.name = create_user.name
        user.nickname = create_user.nickname
        user.email = create_user.email
        user.email_verified = create_user.email_verified

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "user_id": user.id,
            "message": "User creation on backend success",
        }


@router.get("/users/{user_id}")
def get_user(response: Response, user_id: str):
    engine = create_sql_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is not None:
            return user
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "User id not found"}


class UserPatch(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None


@router.patch("/users/{user_id}")
def patch_user(
    user_patch: UserPatch,
    user_id: str,
):
    engine = create_sql_engine()
    with Session(engine) as session:
        filter_user_query = select(User).where(User.id == user_id)
        results = session.exec(filter_user_query)
        user = results.one()

        user.name = user_patch.name or user.name
        user.nickname = user_patch.nickname or user.nickname
        user.email = user_patch.email or user.email

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


class CreateSourceCreds(BaseModel):
    tag: str
    secret: Mapping[str, str]


@router.post("/users/{user_id}/credentials")
def add_source_credentials(params: CreateSourceCreds, user_id: str):
    try:
        create_aws_secret(
            tag=params.tag,
            secret_type="sources",
            user_id=user_id,
            secret=params.secret,
        )
    except ClientError as err:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        logger.exception("❌ Error occured when adding source credentials")

        raise HTTPException(
            status_code=500,
            detail="Something went wrong with storing your credentials. Please contact our support team for help.",
        ) from err
    else:
        engine = create_sql_engine()
        with Session(engine) as session:
            query = select(User).where(User.id == user_id)
            user = session.exec(query).first()
            if params.tag == "s3":
                user.has_s3_creds = True
            elif params.tag == "azure":
                user.has_azure_creds = True

            session.add(user)
            session.commit()
            return {"ok": True}


class CreateStorageCreds(BaseModel):
    tag: str
    secret: Mapping[str, str]
    storage_bucket_name: str


@router.post("/users/{user_id}/storage")
def add_storage_credentials(params: CreateStorageCreds, user_id: str):
    try:
        create_aws_secret(
            tag=params.tag,
            secret_type="storage",
            user_id=user_id,
            secret=params.secret,
        )
    except ClientError as err:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        logger.exception("❌ Error occured when adding storage credentials")

        raise HTTPException(
            status_code=500,
            detail="Something went wrong with creating your storage. Please contact our support team for help.",
        ) from err
    else:
        engine = create_sql_engine()
        with Session(engine) as session:
            query = select(User).where(User.id == user_id)
            user = session.exec(query).first()
            user.storage_tag = params.tag
            user.storage_bucket_name = params.storage_bucket_name
            ts = datetime.utcnow()
            user.storage_created_at = ts

            session.add(user)
            session.commit()
            return {"ok": True}


@router.get("/users/schema/storage")
def list_storage_schemas():
    return STORAGE_SCHEMAS


class UserContextParams(BaseModel):
    user_id: str
    persona: Mapping[str, Union[str, List[str]]]
    company: Mapping[str, Union[str, List[str]]]


# FOR DEMO PURPOSE ONLY
@router.post("/users/context")
def store_user_context(params: UserContextParams):
    # Set up the S3 client
    s3 = boto3.client("s3")

    # Define the S3 bucket and JSON file names
    bucket_name = "indexhub-demo"
    json_file_name = f"users-context/{params.user_id}.json"

    # Define the JSON data to be stored
    json_data = {"persona": params.persona, "company": params.company}
    # Serialize the JSON data
    serialized_data = json.dumps(json_data)

    # Store the serialized JSON data in the S3 bucket
    s3.put_object(Bucket=bucket_name, Key=json_file_name, Body=serialized_data)
    return {"msg": "OK"}
