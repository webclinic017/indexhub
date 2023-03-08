import enum
from datetime import datetime
from typing import List, Optional

from indexhub.api.models._status import StatusTypes
from indexhub.api.models.user import User  # noqa
from sqlmodel import Field, SQLModel


class SourceTags(str, enum.Enum):
    S3 = "S3"
    XERO = "XERO"


SUPPORTED_FILE_EXT = {"title": "", "subtitle": "", "values": ["csv", "xlsx", "parquet"]}


SOURCE_SCHEMAS = {
    "s3": {
        "description": "",
        "variables": {
            "s3_bucket": {
                "title": "",
                "subtitle": "",
            },
            "s3_path": {
                "title": "",
                "subtitle": "",
            },
            "file_ext": SUPPORTED_FILE_EXT,
        },
    }
}


class Source(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    tag: SourceTags
    name: str
    status: StatusTypes
    created_at: datetime
    updated_at: datetime
    # Source specific variables
    metadata: str
    freq: str
    datetime_fmt: str
    entity_cols: List[str]
    time_col: str
    feature_cols: List[str]
    msg: Optional[str] = None
