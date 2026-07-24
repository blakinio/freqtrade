from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from ai_platform.portal.control_plane.database import build_engine, create_schema


MIGRATION = Path(
    "ai_platform/portal/operations/migrations/0002_private_runtime_reconciliation.sql"
)


def test_development_schema_includes_runtime_trade_and_source_status_tables() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)

    assert {
        "portal_operational_trades",
        "portal_operational_source_status",
    }.issubset(set(inspect(engine).get_table_names()))


def test_runtime_reconciliation_migration_is_tenant_scoped_and_secret_free() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "PRIMARY KEY (tenant_id, trade_id)" in sql
    assert "PRIMARY KEY (tenant_id, bot_id, source_runtime_id, kind)" in sql
    for forbidden in ("api_key", "api_secret", "password", "token", "credential"):
        assert forbidden not in sql.lower()
