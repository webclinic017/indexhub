import os
from typing import Optional

from indexhub.api import models  # noqa
from sqlmodel import SQLModel, create_engine


def get_psql_conn_uri(
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    dbname: Optional[str] = None,
):
    username = username or os.environ["PSQL_USERNAME"]
    password = password or os.environ["PSQL_PASSWORD"]
    host = host or os.environ["PSQL_HOST"]
    port = port or os.environ["PSQL_PORT"]
    dbname = dbname or os.environ["PSQL_NAME"]
    sslmode = os.environ.get("PSQL_SSLMODE", "require")
    uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    return uri


engine = create_engine(get_psql_conn_uri(), echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
