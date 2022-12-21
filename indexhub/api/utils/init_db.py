from sqlmodel import SQLModel, create_engine

database_url = "postgresql://localhost:5432"
engine = create_engine(database_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
