import os
from sqlmodel import SQLModel, create_engine
from indexhub.api import models  # noqa


DATABASE_URI = (
    f"postgresql://{os.getenv('POSTGRES_USERNAME')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DATABASE')}"
)
engine = create_engine(DATABASE_URI, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
