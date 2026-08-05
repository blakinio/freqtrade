from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.control_plane.database import Base, build_engine
from ai_platform.portal.database.model_registry import load_portal_models
from ai_platform.portal.database.schema import (
    EXPECTED_SCHEMA_REVISION,
    INITIAL_SCHEMA_REVISION,
    MIGRATION_TABLE_NAME,
    OIDC_LOGOUT_REPLAY_TABLE_NAME,
    SchemaReadinessError,
    UnversionedSchemaError,
    assert_schema_ready,
    migrate_database,
    scan_database_integrity,
)


def test_model_registry_preserves_canonical_module_identity() -> None:
    manifest = load_portal_models()
    table = Base.metadata.tables["portal_execution_submissions"]

    module = importlib.import_module("ai_platform.portal.execution_submission.models")

    assert module.ExecutionSubmissionRow.__table__ is table
    assert load_portal_models() == manifest


def test_fresh_sqlite_migration_is_exact_and_idempotent() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        first = migrate_database(engine)
        second = migrate_database(engine)
        assert first["status"] == "ready"
        assert second["status"] == "ready"
        assert first["expected_revision"]["revision_id"] == EXPECTED_SCHEMA_REVISION
        assert [revision["revision_id"] for revision in first["applied_revisions"]] == [
            INITIAL_SCHEMA_REVISION,
            EXPECTED_SCHEMA_REVISION,
        ]
        assert first["sqlite_foreign_keys"] is True
        assert scan_database_integrity(engine)["status"] == "clean"
    finally:
        engine.dispose()


def test_exact_revision_one_upgrades_atomically_to_revision_two(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'upgrade.db'}")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            connection.exec_driver_sql(f"DROP TABLE {OIDC_LOGOUT_REPLAY_TABLE_NAME}")
            connection.execute(text(f"DELETE FROM {MIGRATION_TABLE_NAME} WHERE sequence = 2"))

        upgraded = migrate_database(engine)

        assert upgraded["status"] == "ready"
        assert [revision["revision_id"] for revision in upgraded["applied_revisions"]] == [
            INITIAL_SCHEMA_REVISION,
            EXPECTED_SCHEMA_REVISION,
        ]
        assert OIDC_LOGOUT_REPLAY_TABLE_NAME not in upgraded["differences"]["missing_tables"]
    finally:
        engine.dispose()


def test_hard_tenant_relationships_reject_orphans_and_identity_mismatch() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        migrate_database(engine)
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO portal_bot_config_revisions (
                            tenant_id, bot_id, revision, revision_id,
                            revision_json, created_by_actor_id, created_at
                        ) VALUES (
                            'tenant-a', 'missing-bot', 1, 'revision-1',
                            '{}', 'actor-1', '2026-08-03T00:00:00+00:00'
                        )
                        """
                    )
                )
        with engine.begin() as connection:
            for principal_id in ("principal-a", "principal-b"):
                connection.execute(
                    text(
                        """
                        INSERT INTO portal_identity_principals (
                            principal_id, issuer, subject, display_name, email,
                            status, created_at, updated_at
                        ) VALUES (
                            :principal_id, 'https://issuer.example', :principal_id,
                            :principal_id, NULL, 'active',
                            '2026-08-03T00:00:00+00:00',
                            '2026-08-03T00:00:00+00:00'
                        )
                        """
                    ),
                    {"principal_id": principal_id},
                )
            connection.execute(
                text(
                    """
                    INSERT INTO portal_tenant_memberships (
                        membership_id, principal_id, tenant_id, roles_json,
                        status, membership_version, valid_from, valid_until,
                        created_at, updated_at
                    ) VALUES (
                        'membership-b', 'principal-b', 'tenant-b', '["admin"]',
                        'active', 1, '2026-08-03T00:00:00+00:00', NULL,
                        '2026-08-03T00:00:00+00:00',
                        '2026-08-03T00:00:00+00:00'
                    )
                    """
                )
            )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO portal_identity_sessions (
                            session_id_hash, csrf_token_hash, principal_id,
                            membership_id, membership_version, idp_session_id,
                            authentication_time, mfa_satisfied, created_at,
                            last_seen_at, idle_expires_at, absolute_expires_at,
                            revoked_at, revocation_reason
                        ) VALUES (
                            'session-hash', 'csrf-hash', 'principal-a',
                            'membership-b', 1, NULL,
                            '2026-08-03T00:00:00+00:00', 1,
                            '2026-08-03T00:00:00+00:00',
                            '2026-08-03T00:00:00+00:00',
                            '2026-08-03T01:00:00+00:00',
                            '2026-08-04T00:00:00+00:00', NULL, NULL
                        )
                        """
                    )
                )
    finally:
        engine.dispose()


def test_trade_intent_uniqueness_is_tenant_scoped() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            for tenant_id in ("tenant-a", "tenant-b"):
                connection.execute(
                    text(
                        """
                        INSERT INTO portal_decision_snapshots (
                            tenant_id, snapshot_id, bot_id, trade_intent_id,
                            decision_at, snapshot_json
                        ) VALUES (
                            :tenant_id, :snapshot_id, 'bot-1', 'intent-shared',
                            '2026-08-03T00:00:00+00:00', '{}'
                        )
                        """
                    ),
                    {"tenant_id": tenant_id, "snapshot_id": f"snapshot-{tenant_id}"},
                )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO portal_decision_snapshots (
                            tenant_id, snapshot_id, bot_id, trade_intent_id,
                            decision_at, snapshot_json
                        ) VALUES (
                            'tenant-a', 'snapshot-duplicate', 'bot-1',
                            'intent-shared', '2026-08-03T00:00:00+00:00', '{}'
                        )
                        """
                    )
                )
    finally:
        engine.dispose()


def test_unversioned_existing_schema_fails_closed(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'unversioned.db'}")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE portal_legacy_data ("
                    "tenant_id TEXT NOT NULL, evidence_json TEXT NOT NULL)"
                )
            )
        with pytest.raises(UnversionedSchemaError) as exc_info:
            migrate_database(engine)
        assert exc_info.value.report["status"] == "unversioned_schema"
        assert exc_info.value.report["policy"] == (
            "backup_scan_quarantine_rebuild_restore_validate"
        )
        assert "portal_legacy_data" in exc_info.value.report["existing_portal_tables"]
    finally:
        engine.dispose()


def test_unknown_revision_and_schema_drift_fail_readiness() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"UPDATE {MIGRATION_TABLE_NAME} "
                    "SET revision_id = 'unknown-revision' WHERE sequence = 2"
                )
            )
        with pytest.raises(SchemaReadinessError):
            assert_schema_ready(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"UPDATE {MIGRATION_TABLE_NAME} "
                    "SET revision_id = :revision_id WHERE sequence = 2"
                ),
                {"revision_id": EXPECTED_SCHEMA_REVISION},
            )
            connection.execute(text("DROP INDEX ix_portal_bots_tenant"))
        with pytest.raises(SchemaReadinessError) as exc_info:
            assert_schema_ready(engine)
        assert "portal_bots" in exc_info.value.report["differences"]["changed_tables"]
    finally:
        engine.dispose()
