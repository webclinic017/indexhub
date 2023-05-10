"""Postgresql fixtures for different "states" of the IndexHub webapp:
"""

import json
import os
from datetime import datetime
from typing import Optional

from pytest_postgresql import factories
from sqlmodel import Session, select

from indexhub.api.models import Objective, Source, User


def load_database(dbname: str, host: str, port: int, user: str, password: str):
    def _create_db_and_tables():
        from indexhub.api.db import create_db_and_tables

        create_db_and_tables()

    os.environ["PSQL_DBNAME"] = dbname
    os.environ["PSQL_HOST"] = host
    os.environ["PSQL_PORT"] = port
    os.environ["PSQL_USERNAME"] = user
    os.environ["PSQL_PASSWORD"] = password
    _create_db_and_tables()


# Shared template database
database = factories.postgresql_proc(
    load=[load_database],
)

# NEW USER STATES

# Clean state (no users)
clean_db = factories.postgresql("database")

# New user
def new_user():
    from indexhub.api.db import engine

    with Session(engine) as session:
        user = User(
            id="test_auth0_id",
            name="John Smith",
            nickname="John",
            email="",
            email_verified=True,
        )
        session.add(user)
        session.commit()


new_user_db = factories.postgresql("database", load=[new_user()])

# User with storage
def new_storage(tag: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(User).where(User.name == "John Smith")
        user = session.exec(query).one()
        user.storage_tag = tag
        user.storage_bucket_name = "indexhub-demo"
        user.storage_created_at = datetime.utcnow()


new_s3_storage_db = factories.postgresql("database", load=[new_storage("s3")])

# SOURCE CREATION / UPDATE STATES
# User creates new source with state=RUNNING
def _add_data_lake_source(tag: str, file_ext: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(User).where(User.name == "John Smith")
        user = session.exec(query).one()
        user_id = user.id
        source = Source(
            user_id=user_id,
            tag=tag,
            name="Tourism",
            status="RUNNING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            variables=json.dumps(
                {
                    "bucket_name": "indexhub-demo",
                    "object_path": "tourism",
                    "file_ext": file_ext,
                }
            ),
            freq="M",
            datetime_fmt="dd/mm/yyyy",
            time_col="time_col",
            output_path="tourism",
            feature_cols=["country", "trips_in_000s"],
            entity_cols=["territory", "state"],
        )
        session.add(source)
        session.commit()


def new_source(tag: str, file_ext: Optional[str] = None):
    if tag in ["s3", "azure"]:
        _add_data_lake_source(tag, file_ext=file_ext)
    else:
        raise ValueError(f"Tag {tag} not supported")


new_s3_csv_source_db = factories.postgresql("database", load=[new_source("s3", "csv")])

new_s3_xlsx_source_db = factories.postgresql(
    "database", load=[new_source("s3", "xlsx")]
)


def update_source_status(status: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(Source).where(Source.name == "Tourism")
        source = session.exec(query).first()
        source.status = status

        session.add(source)
        session.commit()


# User with connected source (panel)
connected_source_db = factories.postgresql(
    "database",
    load=[
        update_source_status("SUCCESSFUL"),
    ],
)

# User with source that failed to connect
failed_source_db = factories.postgresql(
    "database",
    load=[
        update_source_status("FAILED"),
    ],
)

# User with source being updated
updating_source_db = factories.postgresql(
    "database",
    load=[
        update_source_status("RUNNING"),
    ],
)

# OBJECTIVE CREATION / UPDATE STATES


def new_objective(has_baseline: bool = False):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(User).where(User.name == "John Smith")
        user = session.exec(query).one()
        user_id = user.id

        query = select(Source).where(Source.name == "Tourism")
        source = session.exec(query).first()
        source_id = source.id

        fields = {
            "direction": "over",
            "risks": "low volatility",
            "target_col": ["trips_in_000s"],
            "level_cols": ["territory", "state"],
            "panel": source_id,
        }

        if has_baseline:
            fields["baseline"] = source.id

        objective = Objective(
            user_id=user_id,
            tag="forecast",
            name="Tourism Forecast",
            status="RUNNING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            fields=json.dumps(fields),
        )
        session.add(objective)
        session.commit()


# User creates new "forecast" objective with panel source only
new_forecast_objective_db = factories.postgresql(
    "database",
    load=[
        new_objective(),
    ],
)

# User creates new "forecast" objective with panel and baseline sources
new_forecast_with_baseline_objective_db = factories.postgresql(
    "database",
    load=[
        new_objective(has_baseline=True),
    ],
)


def update_objective_status(status: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(Objective).where(Source.name == "Tourism Forecast")
        objective = session.exec(query).first()
        objective.status = status

        session.add(objective)
        session.commit()


# User with new completed "forecast" objective
completed_forecast_objective_db = factories.postgresql(
    "database",
    load=[
        update_objective_status(status="successful"),
    ],
)

# User with failed "forecast" objective
failed_forecast_objective_db = factories.postgresql(
    "database",
    load=[
        update_objective_status(status="failed"),
    ],
)

# User with "forecast" objective being updated
updating_forecast_objective_db = factories.postgresql(
    "database",
    load=[
        update_objective_status(status="running"),
    ],
)
