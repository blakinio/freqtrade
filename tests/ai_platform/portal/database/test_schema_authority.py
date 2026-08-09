from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.control_plane.database import Base, build_engine
from ai_platform.portal.database.model_registry import load_portal_models
from ai_platform.portal.database.schema import (
    BOT_RUNTIME_STATE_COLUMNS,
    EXPECTED_SCHEMA_REVISION,
    INITIAL_SCHEMA_REVISION,
    MIGRATION_TABLE_NAME,
    OIDC_LOGOUT_REPLAY_TABLE_NAME,
    OIDC_SCHEMA_REVISION,
    RUNTIME_GENERATION_SCHEMA_REVISION,
    RUNTIME_ISOLATION_BINDING_COLUMNS,
    SchemaMigrationError,
    SchemaReadinessError,
    UnversionedSchemaError,
    _canonical_check_sql,
    assert_schema_ready,
    migrate_database,
    scan_database_integrity,
)


def _drop_runtime_isolation_binding_revision(connection) -> None:
    for column_name in RUNTIME_ISOLATION_BINDING_COLUMNS:
        connection.exec_driver_sql(
            f"ALTER TABLE portal_runtime_generations DROP COLUMN {column_name}"
        )
    connection.execute(text(f"DELETE FROM {MIGRATION_TABLE_NAME} WHERE sequence = 4"))


def _drop_runtime_generation_revision(connection) -> None:
    _drop_runtime_isolation_binding_revision(connection)
    for table_name in (
        "portal_command_idempotency",
        "portal_runtime_generation_observations",
        "portal_bot_rollouts",
        "portal_runtime_generations",
    ):
        connection.exec_driver_sql(f"DROP TABLE {table_name}")
    for column_name in BOT_RUNTIME_STATE_COLUMNS:
        connection.exec_driver_sql(f"ALTER TABLE portal_bots DROP COLUMN {column_name}")
    connection.execute(text(f"DELETE FROM {MIGRATION_TABLE_NAME} WHERE sequence = 3"))


def test_postgresql_string_array_check_matches_declared_in_expression() -> None:
    declared = "status IN ('processing', 'completed')"
    reflected = (
        "status::text = ANY (ARRAY['processing'::character varying, "
        "'completed'::character varying]::text[])"
    )

    assert _canonical_check_sql(reflected) == _canonical_check_sql(declared)


def test_postgresql_boolean_check_matches_declared_grouping() -> None:
    declared = (
        "(status = 'processing' AND revoked_sessions IS NULL "
        "AND processed_at IS NULL AND completed_at IS NULL) OR "
        "(status = 'completed' AND revoked_sessions IS NOT NULL "
        "AND processed_at IS NOT NULL AND completed_at IS NOT NULL)"
    )
    reflected = (
        "status::text = 'processing'::text AND revoked_sessions IS NULL "
        "AND processed_at IS NULL AND completed_at IS NULL OR "
        "status::text = 'completed'::text AND revoked_sessions IS NOT NULL "
        "AND processed_at IS NOT NULL AND completed_at IS NOT NULL"
    )

    assert _canonical_check_sql(reflected) == _canonical_check_sql(declared)


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
            OIDC_SCHEMA_REVISION,
            RUNTIME_GENERATION_SCHEMA_REVISION,
            EXPECTED_SCHEMA_REVISION,
        ]
        assert first["sqlite_foreign_keys"] is True
        assert scan_database_integrity(engine)["status"] == "clean"
    finally:
        engine.dispose()


def test_exact_revision_one_upgrades_atomically_through_revision_four(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'upgrade-v1.db'}")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            _drop_runtime_generation_revision(connection)
            connection.exec_driver_sql(f"DROP TABLE {OIDC_LOGOUT_REPLAY_TABLE_NAME}")
            connection.execute(text(f"DELETE FROM {MIGRATION_TABLE_NAME} WHERE sequence = 2"))

        upgraded = migrate_database(engine)

        assert upgraded["status"] == "ready"
        assert [revision["revision_id"] for revision in upgraded["applied_revisions"]] == [
            INITIAL_SCHEMA_REVISION,
            OIDC_SCHEMA_REVISION,
            RUNTIME_GENERATION_SCHEMA_REVISION,
            EXPECTED_SCHEMA_REVISION,
        ]
        assert OIDC_LOGOUT_REPLAY_TABLE_NAME not in upgraded["differences"]["missing_tables"]
    finally:
        engine.dispose()


def test_revision_two_backfills_only_latest_authored_and_state_version(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'upgrade-v2.db'}")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            _drop_runtime_generation_revision(connection)
            connection.execute(
                text(
                    """
                    INSERT INTO portal_bots (
                        tenant_id, bot_id, name, spec_json,
                        desired_state, observed_state, current_revision
                    ) VALUES (
                        'tenant-a', 'bot-legacy', 'Legacy bot', '{}',
                        'STOPPED', 'STOPPED', 2
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO portal_bot_config_revisions (
                        tenant_id, bot_id, revision, revision_id,
                        revision_json, created_by_actor_id, created_at
                    ) VALUES (
                        'tenant-a', 'bot-legacy', 2, 'revision-legacy-2',
                        '{}', 'actor-1', '2026-08-03T00:00:00+00:00'
                    )
                    """
                )
            )

        upgraded = migrate_database(engine)

        assert upgraded["status"] == "ready"
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT latest_authored_revision_id,
                               desired_revision_id,
                               desired_runtime_generation_id,
                               observed_runtime_generation_id,
                               state_version
                          FROM portal_bots
                         WHERE tenant_id = 'tenant-a' AND bot_id = 'bot-legacy'
                        """
                    )
                )
                .mappings()
                .one()
            )
        assert row["latest_authored_revision_id"] == "revision-legacy-2"
        assert row["desired_revision_id"] is None
        assert row["desired_runtime_generation_id"] is None
        assert row["observed_runtime_generation_id"] is None
        assert row["state_version"] == 1
    finally:
        engine.dispose()


def test_revision_three_without_generations_upgrades_to_isolation_binding(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'upgrade-v3-empty.db'}")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            _drop_runtime_isolation_binding_revision(connection)

        upgraded = migrate_database(engine)

        assert upgraded["status"] == "ready"
        assert upgraded["applied_revisions"][-1]["revision_id"] == EXPECTED_SCHEMA_REVISION
        changed = upgraded["differences"]["changed_tables"]
        assert "portal_runtime_generations" not in changed
    finally:
        engine.dispose()


def test_revision_three_with_generation_rows_refuses_identity_fabrication(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'upgrade-v3-populated.db'}")
    try:
        migrate_database(engine)
        with engine.begin() as connection:
            _drop_runtime_isolation_binding_revision(connection)
            connection.execute(
                text(
                    """
                    INSERT INTO portal_bots (
                        tenant_id, bot_id, name, spec_json,
                        desired_state, observed_state, current_revision,
                        latest_authored_revision_id, desired_revision_id,
                        desired_runtime_generation_id, observed_runtime_generation_id,
                        state_version
                    ) VALUES (
                        'tenant-a', 'bot-legacy', 'Legacy bot', '{}',
                        'STOPPED', 'STOPPED', 1,
                        NULL, NULL, NULL, NULL, 1
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO portal_runtime_generations (
                        generation_id, generation_ordinal, tenant_id, bot_id,
                        config_revision_id, config_revision_number,
                        config_revision_digest, normalized_runtime_config_digest,
                        runtime_image_digest, strategy_version, strategy_artifact_digest,
                        model_version, model_artifact_digest, feature_schema_version,
                        risk_policy_version, risk_policy_digest, execution_mode,
                        managed_mode, managed_mode_request_digest,
                        managed_mode_resolution_digest, paper_authorization_digest,
                        exchange_mode, exchange_connection_revision,
                        isolation_profile_version, isolation_profile_digest,
                        gateway_contract_version, generation_spec_version,
                        generation_spec_digest, created_by_actor_id, created_at,
                        request_id, correlation_id, causation_id
                    ) VALUES (
                        'generation-legacy', 1, 'tenant-a', 'bot-legacy',
                        'revision-legacy', 1,
                        :d1, :d2, :d3, 'strategy-v1', :d4,
                        NULL, NULL, NULL,
                        'risk-v1', :d5, 'dry_run',
                        'shadow', :d6, :d7, NULL,
                        'dry-run-public-market-data', NULL,
                        'isolation-v1', :d8,
                        'gateway-v1', 'v1', :d9,
                        'actor-1', '2026-08-08T00:00:00+00:00',
                        'request-1', 'correlation-1', NULL
                    )
                    """
                ),
                {f"d{index}": str(index) * 64 for index in range(1, 10)},
            )

        with pytest.raises(SchemaMigrationError) as exc_info:
            migrate_database(engine)

        assert exc_info.value.report["status"] == "runtime_generation_identity_backfill_forbidden"
        assert exc_info.value.report["runtime_generation_count"] == 1
        assert exc_info.value.report["policy"] == (
            "fail_closed_recreate_generation_from_trusted_material"
        )
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
                    "SET revision_id = 'unknown-revision' WHERE sequence = 4"
                )
            )
        with pytest.raises(SchemaReadinessError):
            assert_schema_ready(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"UPDATE {MIGRATION_TABLE_NAME} "
                    "SET revision_id = :revision_id WHERE sequence = 4"
                ),
                {"revision_id": EXPECTED_SCHEMA_REVISION},
            )
            connection.execute(text("DROP INDEX ix_portal_bots_tenant"))
        with pytest.raises(SchemaReadinessError) as exc_info:
            assert_schema_ready(engine)
        assert "portal_bots" in exc_info.value.report["differences"]["changed_tables"]
    finally:
        engine.dispose()
