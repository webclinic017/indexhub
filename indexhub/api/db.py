import os
from sqlmodel import SQLModel, create_engine
from indexhub.api import models  # noqa



def get_psql_conn_uri():
    username = os.environ["PSQL_USERNAME"]
    password = os.environ["PSQL_PASSWORD"]
    host = os.environ["PSQL_HOST"]
    port = os.environ["PSQL_PORT"]
    dbname = os.environ["PSQL_NAME"]
    sslmode = os.environ.get("PSQL_SSLMODE", "require")
    uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    return uri


engine = create_engine(get_psql_conn_uri(), echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
