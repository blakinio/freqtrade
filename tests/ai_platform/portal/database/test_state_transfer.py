from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import OIDC_LOGOUT_REPLAY_TABLE_NAME, migrate_database
from ai_platform.portal.database.transfer import (
    PUBLIC_OIDC_V1_AUTHORITY,
    PUBLIC_OIDC_V1_SUPPORTED_TARGET_REVISION,
    PUBLIC_OIDC_V1_UNVERSIONED_TABLES,
    PortalStateTransferError,
    _assert_transfer_target_revision,
    _manifest_tables,
    _missing_table_is_transferable,
    _source_authority,
    transfer_portal_state,
)


def _sqlite_engine(tmp_path: Path, name: str):
    return build_engine(f"sqlite+pysqlite:///{tmp_path / name}")


def _create_manifest_subset(engine, table_names: frozenset[str]) -> None:
    with engine.begin() as connection:
        for table in _manifest_tables():
            if table.name in table_names:
                table.create(connection, checkfirst=False)


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


def test_deployed_public_oidc_v1_unversioned_sqlite_is_exactly_recognized(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)

        authority, status, source_tables = _source_authority(engine)

        assert authority == PUBLIC_OIDC_V1_AUTHORITY
        assert source_tables == PUBLIC_OIDC_V1_UNVERSIONED_TABLES
        assert status["status"] == "not_ready"
        assert status["applied_revisions"] == []
        assert status["differences"]["unexpected_tables"] == []
        assert status["differences"]["changed_tables"] == {}
        assert status["differences"]["missing_tables"]
        assert all(
            _missing_table_is_transferable(PUBLIC_OIDC_V1_AUTHORITY, table_name)
            for table_name in status["differences"]["missing_tables"]
        )
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_profile_rejects_missing_historical_table(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-missing.db")
    try:
        profile = PUBLIC_OIDC_V1_UNVERSIONED_TABLES - {"portal_identity_sessions"}
        _create_manifest_subset(engine, frozenset(profile))

        with pytest.raises(PortalStateTransferError, match="divergent"):
            _source_authority(engine)
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_profile_rejects_unexpected_portal_table(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-unexpected.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE portal_unknown_legacy_table (id INTEGER PRIMARY KEY)"))

        with pytest.raises(PortalStateTransferError, match="divergent"):
            _source_authority(engine)
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_profile_rejects_changed_existing_table(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-changed.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE portal_bots ADD COLUMN unexpected_legacy_column TEXT"))

        with pytest.raises(PortalStateTransferError, match="divergent"):
            _source_authority(engine)
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_transfer_is_frozen_to_reviewed_target_revision() -> None:
    _assert_transfer_target_revision(
        PUBLIC_OIDC_V1_AUTHORITY,
        {"expected_revision": {"revision_id": PUBLIC_OIDC_V1_SUPPORTED_TARGET_REVISION}},
    )

    with pytest.raises(PortalStateTransferError, match="explicit revalidation"):
        _assert_transfer_target_revision(
            PUBLIC_OIDC_V1_AUTHORITY,
            {"expected_revision": {"revision_id": "future_revision"}},
        )


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
