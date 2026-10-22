"""Explicit database factory. Importing the application never connects or migrates."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.drivername != "postgresql+psycopg":
        raise ValueError("Menuto persistence requires postgresql+psycopg")
    return create_engine(
        parsed,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"options": "-c timezone=UTC", "connect_timeout": 5},
    )


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
