"""Postgresql fixtures for different "states" of the IndexHub webapp:
"""

import json
import os
from datetime import datetime
from typing import Optional

from indexhub.api.models import Policy, Source, User
from pytest_postgresql import factories
from sqlmodel import Session, select


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


new_s3_storage_db = factories.postgresql(
    "database", load=[new_user(), new_storage("s3")]
)

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


new_s3_csv_source_db = factories.postgresql(
    "database", load=[new_user(), new_storage("s3"), new_source("s3", "csv")]
)

new_s3_xlsx_source_db = factories.postgresql(
    "database", load=[new_user(), new_storage("s3"), new_source("s3", "xlsx")]
)


def update_source_status(status: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(Source).where(Source.name == "Tourism")
        source = session.exec(query).one()
        source.status = status

        session.add(source)
        session.commit()


# User with connected source (panel)
connected_source_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
    ],
)

# User with source that failed to connect
failed_source_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("FAILED"),
    ],
)

# User with source being updated
updating_source_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("RUNNING"),
    ],
)

# POLICY CREATION / UPDATE STATES


def new_policy(has_baseline: bool = False):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(User).where(User.name == "John Smith")
        user = session.exec(query).one()
        user_id = user.id

        query = select(Source).where(Source.name == "Tourism")
        source = session.exec(query).one()
        source_id = source.id

        fields = {
            "direction": "over",
            "risks": "low volatility",
            "target_col": ["trips_in_000s"],
            "level_cols": ["territory", "state"],
            "panel_source_id": source_id,
        }

        if has_baseline:
            fields["baseline_source_id"] = source.id

        policy = Policy(
            user_id=user_id,
            tag="forecast",
            name="Tourism Forecast",
            status="RUNNING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            fields=json.dumps(fields),
        )
        session.add(policy)
        session.commit()


# User creates new "forecast" policy with panel source only
new_forecast_policy_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
        new_policy(),
    ],
)

# User creates new "forecast" policy with panel and baseline sources
new_forecast_with_baseline_policy_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
        new_policy(has_baseline=True),
    ],
)


def update_policy_status(status: str):
    from indexhub.api.db import engine

    with Session(engine) as session:
        query = select(Policy).where(Source.name == "Tourism Forecast")
        policy = session.exec(query).one()
        policy.status = status

        session.add(policy)
        session.commit()


# User with new completed "forecast" policy
completed_forecast_policy_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
        new_policy(has_baseline=True),
        update_policy_status(status="successful"),
    ],
)

# User with failed "forecast" policy
failed_forecast_policy_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
        new_policy(has_baseline=True),
        update_policy_status(status="failed"),
    ],
)

# User with "forecast" policy being updated
updating_forecast_policy_db = factories.postgresql(
    "database",
    load=[
        new_user(),
        new_storage("s3"),
        new_source("s3", "csv"),
        update_source_status("SUCCESSFUL"),
        new_policy(has_baseline=True),
        update_policy_status(status="running"),
    ],
)