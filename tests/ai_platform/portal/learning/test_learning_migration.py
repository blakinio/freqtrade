from pathlib import Path


MIGRATION = Path("ai_platform/portal/learning/migrations/0001_learning_loop.sql")


def test_learning_migration_preserves_hypotheses_experiments_and_candidates() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "portal_learning_hypotheses" in sql
    assert "portal_learning_experiments" in sql
    assert "portal_learning_candidates" in sql
    assert "hypothesis_json TEXT NOT NULL" in sql
    assert "experiment_json TEXT NOT NULL" in sql
    assert "candidate_json TEXT NOT NULL" in sql
