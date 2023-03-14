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


def TARGET_COL_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def LEVEL_COLS_SCHEMA(col_names):
    return {"title": "", "subtitle": "", "values": col_names}


def POLICY_SCHEMAS(entity_cols, feature_cols):
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
                "target_col": TARGET_COL_SCHEMA(feature_cols),
                "level_cols": LEVEL_COLS_SCHEMA(entity_cols),
            },
            "sources": [
                {"name": "panel", "title": "", "subtitle": ""},
                {"name": "benchmark", "title": "", "subtitle": ""},
            ],
        }
    }
