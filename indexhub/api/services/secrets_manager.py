# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import json
import os
from typing import Mapping

import boto3
from botocore.exceptions import ClientError


ENVIRONMENT = "dev" if os.environ["DEBUG"].lower() != "true" else "prod"


def get_aws_secret(tag: str, secret_type: str, user_id: str):

    secret_name = f"{ENVIRONMENT}/{secret_type}/{user_id.replace('|', '_')}@{tag}"
    region_name = "ap-northeast-2"

    # Create a Secrets Manager client
    session = boto3.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def create_aws_secret(
    tag: str, secret_type: str, user_id: str, secret: Mapping[str, str]
):

    secret_name = f"{ENVIRONMENT}/{secret_type}/{user_id.replace('|', '_')}@{tag}"
    region_name = "ap-northeast-2"

    # Create a Secrets Manager client
    session = boto3.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret),
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response
