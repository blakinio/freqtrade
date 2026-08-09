from __future__ import annotations

from pathlib import Path

import pytest

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import OIDC_LOGOUT_REPLAY_TABLE_NAME, migrate_database
from ai_platform.portal.database.transfer import (
    PortalStateTransferError,
    _manifest_tables,
    _source_authority,
    transfer_portal_state,
)


def _sqlite_engine(tmp_path: Path, name: str):
    return build_engine(f"sqlite+pysqlite:///{tmp_path / name}")


def test_versioned_current_sqlite_is_accepted_as_transfer_source(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "current.db")
    try:
        migrate_database(engine)

        authority, status, source_tables = _source_authority(engine)

        assert authority == "versioned_current"
        assert status["status"] == "ready"
        assert "portal_bots" in source_tables
    finally:
        engine.dispose()


def test_structurally_current_unversioned_sqlite_is_accepted_for_recovery(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "unversioned-current.db")
    try:
        with engine.begin() as connection:
            for table in _manifest_tables():
                table.create(connection, checkfirst=False)

        authority, status, _source_tables = _source_authority(engine)

        assert authority == "unversioned_structural_current"
        assert status["status"] == "not_ready"
        assert status["applied_revisions"] == []
        assert status["differences"] == {
            "missing_tables": [],
            "unexpected_tables": [],
            "changed_tables": {},
        }
    finally:
        engine.dispose()


def test_pre_logout_replay_sqlite_shape_is_accepted_for_recovery(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "pre-replay.db")
    try:
        with engine.begin() as connection:
            for table in _manifest_tables():
                if table.name != OIDC_LOGOUT_REPLAY_TABLE_NAME:
                    table.create(connection, checkfirst=False)

        authority, status, _source_tables = _source_authority(engine)

        assert authority == "structural_pre_logout_replay"
        assert status["differences"]["missing_tables"] == [OIDC_LOGOUT_REPLAY_TABLE_NAME]
    finally:
        engine.dispose()


def test_divergent_legacy_sqlite_fails_closed(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "divergent.db")
    try:
        with engine.begin() as connection:
            next(table for table in _manifest_tables() if table.name == "portal_bots").create(
                connection,
                checkfirst=False,
            )

        with pytest.raises(PortalStateTransferError, match="divergent"):
            _source_authority(engine)
    finally:
        engine.dispose()


def test_transfer_requires_postgresql_target(tmp_path: Path) -> None:
    source = _sqlite_engine(tmp_path, "source.db")
    target = _sqlite_engine(tmp_path, "target.db")
    try:
        migrate_database(source)
        migrate_database(target)

        with pytest.raises(PortalStateTransferError, match="target must be PostgreSQL"):
            transfer_portal_state(source, target)
    finally:
        source.dispose()
        target.dispose()
