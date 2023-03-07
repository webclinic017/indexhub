import enum
from datetime import datetime
from typing import List, Optional

from indexhub.api.models._status import StatusTypes
from indexhub.api.models.user import User  # noqa
from sqlmodel import Field, SQLModel


class SourceTags(str, enum.Enum):
    S3 = "S3"
    XERO = "XERO"


class Source(SQLModel, table=True):
    """Metadata schemas:
    S3 - (s3_bucket: str, s3_path: str)
    """

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
    target_cols: List[str]
    msg: Optional[str] = None
