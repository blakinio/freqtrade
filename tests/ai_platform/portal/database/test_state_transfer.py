from __future__ import annotations

import copy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select, text

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import (
    OIDC_LOGOUT_REPLAY_TABLE_NAME,
    _expected_snapshot,
    migrate_database,
    schema_status,
)
from ai_platform.portal.database.transfer import (
    PUBLIC_OIDC_V1_AUTHORITY,
    PUBLIC_OIDC_V1_CHANGED_TABLES,
    PUBLIC_OIDC_V1_MISSING_BOT_COLUMNS,
    PUBLIC_OIDC_V1_MISSING_TABLES,
    PUBLIC_OIDC_V1_SUPPORTED_TARGET_REVISION,
    PUBLIC_OIDC_V1_UNVERSIONED_TABLES,
    PortalStateTransferError,
    _assert_transfer_target_revision,
    _backfill_public_oidc_v1_target,
    _manifest_tables,
    _matches_public_oidc_v1,
    _missing_table_is_transferable,
    _public_oidc_v1_actual_from_current_expected,
    _source_authority,
    _source_rows,
    transfer_portal_state,
)


def _sqlite_engine(tmp_path: Path, name: str):
    return build_engine(f"sqlite+pysqlite:///{tmp_path / name}")


def _create_manifest_subset(engine, table_names: frozenset[str]) -> None:
    with engine.begin() as connection:
        for table in _manifest_tables():
            if table.name in table_names:
                table.create(connection, checkfirst=False)


def _synthetic_public_oidc_v1_status(engine) -> dict:
    status = copy.deepcopy(schema_status(engine))
    expected = _expected_snapshot(engine)
    status["differences"]["changed_tables"] = {
        table_name: {
            "expected": expected[table_name],
            "actual": _public_oidc_v1_actual_from_current_expected(
                table_name,
                expected[table_name],
            ),
        }
        for table_name in PUBLIC_OIDC_V1_CHANGED_TABLES
    }
    return status


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


def test_deployed_public_oidc_v1_delta_is_exactly_frozen(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-shape.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        status = _synthetic_public_oidc_v1_status(engine)

        assert frozenset(status["differences"]["missing_tables"]) == PUBLIC_OIDC_V1_MISSING_TABLES
        assert status["differences"]["unexpected_tables"] == []
        assert frozenset(status["differences"]["changed_tables"]) == PUBLIC_OIDC_V1_CHANGED_TABLES
        assert _matches_public_oidc_v1(status, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        assert all(
            _missing_table_is_transferable(PUBLIC_OIDC_V1_AUTHORITY, table_name)
            for table_name in PUBLIC_OIDC_V1_MISSING_TABLES
        )
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_delta_rejects_extra_structural_change(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-extra-change.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        status = _synthetic_public_oidc_v1_status(engine)
        changed = status["differences"]["changed_tables"]["portal_identity_sessions"]
        changed["actual"]["indexes"] = []

        assert not _matches_public_oidc_v1(status, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
    finally:
        engine.dispose()


def test_deployed_public_oidc_v1_delta_rejects_table_set_changes(tmp_path: Path) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-table-set.db")
    try:
        _create_manifest_subset(engine, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
        status = _synthetic_public_oidc_v1_status(engine)

        assert not _matches_public_oidc_v1(
            status,
            PUBLIC_OIDC_V1_UNVERSIONED_TABLES - {"portal_identity_sessions"},
        )
        status["differences"]["missing_tables"].append("portal_future_table")
        assert not _matches_public_oidc_v1(status, PUBLIC_OIDC_V1_UNVERSIONED_TABLES)
    finally:
        engine.dispose()


def test_public_oidc_v1_source_projection_omits_later_nullable_bot_columns(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-projection.db")
    bot_table = next(table for table in _manifest_tables() if table.name == "portal_bots")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE portal_bots (
                        tenant_id VARCHAR(255) NOT NULL,
                        bot_id VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        spec_json TEXT NOT NULL,
                        desired_state VARCHAR(32) NOT NULL,
                        observed_state VARCHAR(32) NOT NULL,
                        current_revision INTEGER NOT NULL,
                        PRIMARY KEY (tenant_id, bot_id)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO portal_bots (
                        tenant_id, bot_id, name, spec_json,
                        desired_state, observed_state, current_revision
                    ) VALUES (
                        'tenant-test', 'bot-test', 'Bot', '{}',
                        'stopped', 'stopped', 1
                    )
                    """
                )
            )

        with engine.connect() as connection:
            rows = [dict(row) for row in _source_rows(connection, bot_table)]

        assert len(rows) == 1
        assert PUBLIC_OIDC_V1_MISSING_BOT_COLUMNS.isdisjoint(rows[0])
        assert rows[0]["tenant_id"] == "tenant-test"
        assert rows[0]["current_revision"] == 1
    finally:
        engine.dispose()


def test_public_oidc_v1_target_backfill_matches_runtime_generation_migration(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-backfill.db")
    bot_table = next(table for table in _manifest_tables() if table.name == "portal_bots")
    revision_table = next(
        table for table in _manifest_tables() if table.name == "portal_bot_config_revisions"
    )
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            connection.execute(
                bot_table.insert().values(
                    tenant_id="tenant-test",
                    bot_id="bot-test",
                    name="Bot",
                    spec_json="{}",
                    desired_state="stopped",
                    observed_state="stopped",
                    current_revision=2,
                    latest_authored_revision_id=None,
                    desired_revision_id=None,
                    desired_runtime_generation_id=None,
                    observed_runtime_generation_id=None,
                    state_version=None,
                )
            )
            connection.execute(
                revision_table.insert().values(
                    tenant_id="tenant-test",
                    bot_id="bot-test",
                    revision=2,
                    revision_id="revision-2",
                    revision_json="{}",
                    created_by_actor_id="actor-test",
                    created_at=datetime.now(UTC),
                )
            )

            _backfill_public_oidc_v1_target(connection)

            row = connection.execute(
                select(
                    bot_table.c.latest_authored_revision_id,
                    bot_table.c.desired_revision_id,
                    bot_table.c.desired_runtime_generation_id,
                    bot_table.c.observed_runtime_generation_id,
                    bot_table.c.state_version,
                )
            ).one()

        assert row.latest_authored_revision_id == "revision-2"
        assert row.desired_revision_id is None
        assert row.desired_runtime_generation_id is None
        assert row.observed_runtime_generation_id is None
        assert row.state_version == 1
    finally:
        engine.dispose()


def test_public_oidc_v1_target_backfill_rejects_missing_current_revision(
    tmp_path: Path,
) -> None:
    engine = _sqlite_engine(tmp_path, "public-oidc-v1-missing-current-revision.db")
    bot_table = next(table for table in _manifest_tables() if table.name == "portal_bots")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            connection.execute(
                bot_table.insert().values(
                    tenant_id="tenant-test",
                    bot_id="bot-test",
                    name="Bot",
                    spec_json="{}",
                    desired_state="stopped",
                    observed_state="stopped",
                    current_revision=7,
                    latest_authored_revision_id=None,
                    desired_revision_id=None,
                    desired_runtime_generation_id=None,
                    observed_runtime_generation_id=None,
                    state_version=None,
                )
            )

            with pytest.raises(PortalStateTransferError, match="current revision did not resolve"):
                _backfill_public_oidc_v1_target(connection)
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
