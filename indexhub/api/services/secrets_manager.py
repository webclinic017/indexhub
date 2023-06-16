# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import json
import logging
import os
from datetime import datetime
from typing import Mapping

import boto3
from botocore.exceptions import ClientError

ENV_NAME = os.environ["ENV_NAME"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]


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


def get_aws_secret(tag: str, secret_type: str, user_id: str):
    # Create a Secrets Manager client
    session = boto3.Session()
    client = session.client(
        service_name="secretsmanager", region_name=AWS_DEFAULT_REGION
    )

    try:
        secret_name = f"{ENV_NAME}/{secret_type}/{user_id.replace('|', '_')}@{tag}"
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.exception("❌ Error occured when getting aws secret.")
        raise e

    # Decrypts secret using the associated KMS key.
    secret = response["SecretString"]
    return json.loads(secret)


def create_aws_secret(
    tag: str, secret_type: str, user_id: str, secret: Mapping[str, str]
):
    session = boto3.Session()
    client = session.client(
        service_name="secretsmanager", region_name=AWS_DEFAULT_REGION
    )

    try:
        secret_name = f"{ENV_NAME}/{secret_type}/{user_id.replace('|', '_')}@{tag}"
        response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret),
            Description=f"Created at: {datetime.now():%c}",
        )
        response = client.tag_resource(
            SecretId=secret_name, Tags=[{"Key": "owner", "Value": "user"}]
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.exception("❌ Error occured when creating aws secret.")
        raise e

    return response
