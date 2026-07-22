from pathlib import Path


def test_model_control_migration_declares_immutable_versions_slots_and_history() -> None:
    migration = Path(
        "ai_platform/portal/model_control/migrations/0001_model_control.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE portal_model_versions" in migration
    assert "PRIMARY KEY (tenant_id, model_version_id)" in migration
    assert "CREATE TABLE portal_model_promotion_slots" in migration
    assert "PRIMARY KEY (tenant_id, model_family_id, environment)" in migration
    assert "FOREIGN KEY (tenant_id, current_model_version_id)" in migration
    assert "REFERENCES portal_model_versions (tenant_id, model_version_id)" in migration
    assert "CREATE TABLE portal_model_promotion_history" in migration
    assert "transition_id TEXT PRIMARY KEY" in migration
    assert "from_model_version_id TEXT NULL" in migration
    assert "to_model_version_id TEXT NOT NULL" in migration
