"""Alembic entrypoint; connection may be injected by isolated integration tests."""

import os

from alembic import context
from app.persistence.database import create_database_engine
from app.persistence.models import Base

config = context.config
target_metadata = Base.metadata


def database_url():
    value = os.environ.get("MENUTO_DATABASE_URL")
    if not value:
        raise RuntimeError("Set MENUTO_DATABASE_URL to an explicit PostgreSQL database")
    return value


def migrate(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = config.attributes.get("connection")
    if connection is not None:
        migrate(connection)
    else:
        engine = create_database_engine(database_url())
        with engine.connect() as connection:
            migrate(connection)
        engine.dispose()
