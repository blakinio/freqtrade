from __future__ import annotations

import pytest

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.control_plane.migration_authority import (
    MIGRATION_PATHS,
    SchemaIntegrityError,
    expected_revision,
    migration_manifest,
    schema_status,
    split_sql_statements,
)


def test_manifest_is_complete_ordered_and_checksum_bound() -> None:
    manifest = migration_manifest()

    assert len(manifest) == len(MIGRATION_PATHS) == 18
    assert [migration.position for migration in manifest] == list(range(1, 19))
    assert all(len(migration.sha256) == 64 for migration in manifest)
    assert expected_revision().startswith("18:")


def test_sql_splitter_preserves_postgresql_dollar_quoted_block() -> None:
    raw = """
    BEGIN;
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM example WHERE value = ';') THEN
            RAISE EXCEPTION 'blocked; still one statement';
        END IF;
    END
    $$;
    CREATE TABLE example (value TEXT);
    COMMIT;
    """

    statements = split_sql_statements(raw)

    assert len(statements) == 2
    assert statements[0].startswith("DO $$")
    assert "blocked; still one statement" in statements[0]
    assert statements[1] == "CREATE TABLE example (value TEXT)"


def test_public_schema_authority_rejects_sqlite() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        with pytest.raises(SchemaIntegrityError, match="requires PostgreSQL"):
            schema_status(engine)
    finally:
        engine.dispose()
