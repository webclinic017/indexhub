from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Integration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    ticker: str  # Case sensitive ticker handle. e.g. for EconDB CPI: "CPI". Will be used as key to `extractor()`
    tag: str  # e.g. s3
    name: str  # e.g. "Consumer Price Index".
    provider: str  # Namespace, such as "econdb", "oecd" etc
    created_at: datetime
    updated_at: Optional[datetime]
    status: str  # e.g. SUCCESS
    description: Optional[str]  # optional
    # Fields
    # entity_col: str # e.g. iso_country_code. TODO: Support multiple as a list
    # freq: str # Same as all other freq variables
    # agg_method: str  # Same as functime
    # impute_method: str # Same as functime
    fields: str
    # Outputs
    # object_path: str # Read path from cloud storage
    # bucket_name: str
    # file_ext: str
    outputs: str
    msg: str
