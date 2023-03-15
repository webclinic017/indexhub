from typing import List

from indexhub.api.models.source import Source
from indexhub.api.models.user import User

STORAGE_SCHEMAS = {
    "s3": {
        "AWS_ACCESS_KEY_ID": {
            "title": "AWS Access Key ID",
            "subtitle": "Equivalent to the AWS_ACCESS_KEY_ID environment variable.",
        },
        "AWS_SECRET_KEY_ID": {
            "title": "AWS Secret Key ID",
            "subtitle": "Equivalent to the AWS_SECRET_ACCESS_KEY environment variable.",
        },
    },
    # Schema for Azure Blob Storage taken from:
    # https://docs.prefect.io/api-ref/prefect/filesystems/#prefect.filesystems.Azure
    "azure": {
        "AZURE_STORAGE_CONNECTION_STRING": {
            "title": "Azure storage connection string",
            "subtitle": "Equivalent to the AZURE_STORAGE_CONNECTION_STRING environment variable.",
        },
        "AZURE_STORAGE_ACCOUNT_KEY": {
            "title": "Azure storage account key",
            "subtitle": "Equivalent to the AZURE_STORAGE_ACCOUNT_KEY environment variable.",
        },
        "AZURE_TENANT_ID": {
            "title": "Azure storage tenant ID",
            "subtitle": "Equivalent to the AZURE_TENANT_ID environment variable.",
        },
    },
}

SUPPORTED_FILE_EXT = {
    "title": "File extension",
    "subtitle": "",
    "values": ["csv", "xlsx", "parquet"],
}


def SOURCE_SCHEMAS(user: User):
    return {
        "s3": {
            "available": True,
            "is_authenticated": user.has_s3_creds,
            "credentials": STORAGE_SCHEMAS["s3"],
            "description": "",
            "variables": {
                "bucket_name": {
                    "title": "Bucket name",
                    "subtitle": "",
                },
                "object_path": {
                    "title": "Object path",
                    "subtitle": "",
                },
                "file_ext": SUPPORTED_FILE_EXT,
            },
        },
        "azure": {
            "available": False,
            "is_authenticated": user.has_azure_creds,
            "credentials": STORAGE_SCHEMAS["azure"],
            "description": "",
            "variables": {
                "bucket_name": {
                    "title": "Bucket name",
                    "subtitle": "",
                },
                "object_path": {
                    "title": "Object path",
                    "subtitle": "",
                },
                "file_ext": SUPPORTED_FILE_EXT,
            },
        },
    }


def TARGET_COL_SCHEMA(col_names: List[str], depends_on: str = "source_id"):
    schema = {
        "title": "",
        "subtitle": "",
        "values": col_names,
        "depends_on": depends_on,
    }
    return schema


def LEVEL_COLS_SCHEMA(col_names: List[str], depends_on: str = "source_id"):
    schema = {
        "title": "",
        "subtitle": "",
        "values": col_names,
        "depends_on": depends_on,
    }
    return schema


def POLICY_SCHEMAS(sources: List[Source]):
    return {
        "forecast": {
            "description": "Reduce {direction} forecast error for {risks} entitie).",
            "fields": {
                "direction": {
                    "title": "",
                    "subtitle": "",
                    "values": ["over", "under", "overall"],
                },
                "risks": {"title": "", "subtitle": "", "values": ["low volatility"]},
                "target_col": {
                    src.id: TARGET_COL_SCHEMA(
                        col=src.feature_cols, depends_on="panel_source_id"
                    )
                    for src in sources
                },
                "level_cols": {
                    src.id: LEVEL_COLS_SCHEMA(
                        col=src.entity_cols, depends_on="panel_source_id"
                    )
                    for src in sources
                },
                "panel_source_id": {
                    "title": "",
                    "subtitle": "",
                    "values": {src.name: src.id for src in sources},
                },
                "baseline_source_id": {
                    "title": "",
                    "subtitle": "",
                    "values": {src.name: src.id for src in sources},
                },
            },
        }
    }
