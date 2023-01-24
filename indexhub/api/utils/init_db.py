import os

from sqlmodel import SQLModel, create_engine

database_url = f"postgresql://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DATABASE')}"
engine = create_engine(database_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
