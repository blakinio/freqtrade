from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.control_plane.database import build_engine


def _assert_sqlite_foreign_keys(engine) -> None:
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_sqlite_memory_engine_enforces_foreign_keys() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        _assert_sqlite_foreign_keys(engine)
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE parent (id TEXT PRIMARY KEY)"))
            connection.execute(
                text(
                    "CREATE TABLE child ("
                    "id TEXT PRIMARY KEY, "
                    "parent_id TEXT NOT NULL REFERENCES parent(id) ON DELETE RESTRICT"
                    ")"
                )
            )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text("INSERT INTO child (id, parent_id) VALUES ('child', 'missing')")
                )
    finally:
        engine.dispose()


def test_sqlite_file_engine_enables_foreign_keys_for_new_connections(
    tmp_path: Path,
) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'portal.db'}")
    try:
        _assert_sqlite_foreign_keys(engine)
        engine.dispose()
        _assert_sqlite_foreign_keys(engine)
    finally:
        engine.dispose()
