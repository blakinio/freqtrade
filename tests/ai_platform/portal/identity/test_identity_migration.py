from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from ai_platform.portal.control_plane.database import build_engine, create_schema


def test_identity_models_are_in_shared_development_schema() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)

    tables = set(inspect(engine).get_table_names())

    assert {
        "portal_identity_principals",
        "portal_tenant_memberships",
        "portal_identity_sessions",
        "portal_oidc_login_flows",
        "portal_session_revocations",
        "portal_identity_audit_events",
    } <= tables


def test_identity_migration_contains_no_secret_value_columns() -> None:
    migration = Path(
        "ai_platform/portal/identity/migrations/0001_identity_lifecycle.sql"
    ).read_text(encoding="utf-8")
    lowered = migration.lower()

    for forbidden in (
        "access_token",
        "refresh_token",
        "id_token",
        "client_secret",
        "session_token",
        "csrf_token text",
        "password",
    ):
        assert forbidden not in lowered
    assert "session_id_hash" in lowered
    assert "csrf_token_hash" in lowered
