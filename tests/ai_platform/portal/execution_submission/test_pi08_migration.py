from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from ai_platform.portal.control_plane.database import build_engine, create_schema


MIGRATION = Path(
    "ai_platform/portal/execution_submission/migrations/0001_private_dry_run_submission.sql"
)


def test_development_schema_includes_execution_submission_table() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    inspector = inspect(engine)

    assert "portal_execution_submissions" in inspector.get_table_names()
    unique_sets = {
        tuple(sorted(item["column_names"]))
        for item in inspector.get_unique_constraints("portal_execution_submissions")
    }
    assert ("idempotency_key", "tenant_id") in unique_sets
    assert ("command_id", "tenant_id") in unique_sets
    assert ("execution_intent_id", "tenant_id") in unique_sets


def test_migration_is_tenant_scoped_and_secret_free() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "PRIMARY KEY (tenant_id, attempt_id)" in sql
    assert "UNIQUE (tenant_id, idempotency_key)" in sql
    assert "UNIQUE (tenant_id, command_id)" in sql
    assert "UNIQUE (tenant_id, execution_intent_id)" in sql
    for forbidden in (
        "api_key",
        "api_secret",
        "passphrase",
        "password",
        "private_endpoint",
        "vault_path",
    ):
        assert forbidden not in sql.lower()
