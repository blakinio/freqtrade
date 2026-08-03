from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


SessionFactory = Callable[[], Session]
SQLITE_BUSY_TIMEOUT_SECONDS = 30.0


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        enabled = cursor.execute("PRAGMA foreign_keys").fetchone()
        if enabled is None or enabled[0] != 1:
            raise RuntimeError("SQLite foreign-key enforcement could not be enabled")
    finally:
        cursor.close()


def _build_sqlite_engine(database_url: str, **kwargs: Any) -> Engine:
    engine = create_engine(database_url, **kwargs)
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def build_engine(database_url: str) -> Engine:
    if database_url == "sqlite+pysqlite:///:memory:":
        return _build_sqlite_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if database_url.startswith("sqlite"):
        return _build_sqlite_engine(
            database_url,
            connect_args={"timeout": SQLITE_BUSY_TIMEOUT_SECONDS},
            pool_pre_ping=True,
        )
    return create_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    """Compatibility entry point for tests and local tools.

    Schema construction is always delegated to the authoritative revision runner;
    no runtime path may construct a parallel schema with ``metadata.create_all``.
    """

    from ai_platform.portal.database.schema import migrate_database

    migrate_database(engine)
