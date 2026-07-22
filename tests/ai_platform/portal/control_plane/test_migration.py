from pathlib import Path


def test_initial_control_plane_migration_declares_required_tenant_scoped_tables() -> None:
    migration_path = Path("ai_platform/portal/control_plane/migrations/0001_control_plane.sql")
    migration = migration_path.read_text(encoding="utf-8")

    for table in (
        "portal_bots",
        "portal_bot_config_revisions",
        "portal_audit_events",
        "portal_outbox_events",
    ):
        assert f"CREATE TABLE {table}" in migration

    assert "PRIMARY KEY (tenant_id, bot_id)" in migration
    assert "PRIMARY KEY (tenant_id, bot_id, revision)" in migration
    assert "UNIQUE (tenant_id, revision_id)" in migration
    assert "published_at TIMESTAMPTZ NULL" in migration
    assert "ON DELETE RESTRICT" in migration
