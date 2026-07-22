from pathlib import Path


MIGRATION = Path("ai_platform/portal/intelligence/migrations/0001_trade_intelligence.sql")


def test_trade_intelligence_migration_declares_durable_evidence_tables() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "portal_decision_snapshots" in sql
    assert "portal_trade_outcomes" in sql
    assert "portal_trade_analyses" in sql
    assert "snapshot_json TEXT NOT NULL" in sql
    assert "outcome_json TEXT NOT NULL" in sql
    assert "analysis_json TEXT NOT NULL" in sql
