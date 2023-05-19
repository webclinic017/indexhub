import os

from sqlmodel import SQLModel, create_engine

from indexhub.api import models  # noqa


PSQL_USERNAME = os.environ["PSQL_USERNAME"]
PSQL_PASSWORD = os.environ["PSQL_PASSWORD"]
PSQL_HOST = os.environ["PSQL_HOST"]
PSQL_PORT = os.environ["PSQL_PORT"]
PSQL_DBNAME = os.environ["PSQL_DBNAME"]
PSQL_SSLMODE = os.environ.get("PSQL_SSLMODE", "require")
PSQL_URI = (
    f"postgresql://{PSQL_USERNAME}:{PSQL_PASSWORD}@"
    f"{PSQL_HOST}:{PSQL_PORT}/{PSQL_DBNAME}?sslmode={PSQL_SSLMODE}"
)

engine = create_engine(PSQL_URI, echo=True)


def create_db_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_tables()
