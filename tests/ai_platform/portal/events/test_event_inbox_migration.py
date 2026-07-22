from pathlib import Path


def test_event_inbox_migration_declares_durable_consumer_identity() -> None:
    migration = Path("ai_platform/portal/events/migrations/0001_event_inbox.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE TABLE portal_event_inbox" in migration
    assert "PRIMARY KEY (consumer_name, event_id)" in migration
    assert "tenant_id TEXT NOT NULL" in migration
    assert "correlation_id TEXT NOT NULL" in migration
    assert "processed_at TIMESTAMPTZ NOT NULL" in migration
