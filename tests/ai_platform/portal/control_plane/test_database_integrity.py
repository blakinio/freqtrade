from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.control_plane.database import build_engine


def test_sqlite_enables_foreign_keys_for_every_connection() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            connection.exec_driver_sql(
                "CREATE TABLE parent (tenant_id TEXT NOT NULL, id TEXT NOT NULL, "
                "PRIMARY KEY (tenant_id, id))"
            )
            connection.exec_driver_sql(
                "CREATE TABLE child (tenant_id TEXT NOT NULL, parent_id TEXT NOT NULL, "
                "FOREIGN KEY (tenant_id, parent_id) "
                "REFERENCES parent (tenant_id, id) ON DELETE RESTRICT)"
            )
            with pytest.raises(IntegrityError):
                connection.exec_driver_sql(
                    "INSERT INTO child (tenant_id, parent_id) VALUES ('tenant-a', 'missing')"
                )
    finally:
        engine.dispose()
