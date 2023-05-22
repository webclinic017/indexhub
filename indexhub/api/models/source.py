from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    user_id: str = Field(default=None, foreign_key="user.id")
    tag: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    dataset_type: str
    # Connection fields
    # object_path: str
    # bucket_name: str
    # file_ext: str
    conn_fields: str
    # Data fields
    # entity_cols: List[str]
    # time_col: str
    # target_col: str
    # feature_cols: List[str]
    # agg_method: str
    # impute_method: Union[str, int]
    # freq: str
    # datetime_fmt: str
    data_fields: str
    output_path: Optional[str] = None
    msg: Optional[str] = None
