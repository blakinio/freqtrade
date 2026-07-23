from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from ai_platform.portal.control_plane.database import build_engine, create_schema


MIGRATION = Path("ai_platform/portal/operations/migrations/0001_operational_read_models.sql")


def test_development_schema_includes_operational_read_model_tables() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)

    assert {
        "portal_operational_orders",
        "portal_operational_positions",
    }.issubset(set(inspect(engine).get_table_names()))


def test_operational_migration_keeps_tenant_in_composite_primary_keys() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "PRIMARY KEY (tenant_id, order_id)" in sql
    assert "PRIMARY KEY (tenant_id, position_id)" in sql
    assert "api_key" not in sql.lower()
    assert "api_secret" not in sql.lower()
