from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import Table, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import (
    EXPECTED_SCHEMA_REVISION,
    MIGRATION_TABLE_NAME,
    assert_schema_ready,
    migrate_database,
)


POSTGRES_URL = os.environ.get("PORTAL_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PORTAL_TEST_POSTGRES_URL is required for PostgreSQL schema tests",
)


@pytest.fixture(autouse=True)
def clean_postgres_schema() -> Iterator[None]:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    engine.dispose()
    yield
    engine = build_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    engine.dispose()


def _concurrent_migrate() -> str:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    try:
        report = migrate_database(engine)
        return str(report["applied_revisions"][-1]["revision_id"])
    finally:
        engine.dispose()


def _insert_duplicate_command() -> str:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO portal_bot_commands (
                        scope_tenant_id, command_id, idempotency_key,
                        command_kind, command_digest, command_json, created_at
                    ) VALUES (
                        'tenant-a', 'command-shared', 'idempotency-shared',
                        'start', 'digest-shared', '{}', CURRENT_TIMESTAMP
                    )
                    """
                )
            )
        return "inserted"
    except IntegrityError:
        return "duplicate"
    finally:
        engine.dispose()


def test_concurrent_postgresql_migrations_converge_on_ordered_revision_chain() -> None:
    with ThreadPoolExecutor(max_workers=4) as executor:
        revisions = tuple(executor.map(lambda _index: _concurrent_migrate(), range(4)))
    assert revisions == (EXPECTED_SCHEMA_REVISION,) * 4

    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text(f"SELECT COUNT(*) FROM {MIGRATION_TABLE_NAME}")
                ).scalar_one()
                == 4
            )
        assert assert_schema_ready(engine)["status"] == "ready"
    finally:
        engine.dispose()


def test_concurrent_duplicate_mutations_have_exactly_one_winner() -> None:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    try:
        migrate_database(engine)
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = tuple(executor.map(lambda _index: _insert_duplicate_command(), range(2)))
        assert sorted(outcomes) == ["duplicate", "inserted"]
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM portal_bot_commands
                        WHERE scope_tenant_id = 'tenant-a'
                          AND command_id = 'command-shared'
                        """
                    )
                ).scalar_one()
                == 1
            )
    finally:
        engine.dispose()


def test_postgresql_ddl_failure_rolls_back_entire_revision(monkeypatch) -> None:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    original_create = Table.create

    def fail_on_portal_bots(self, bind, *args, **kwargs):
        if self.name == "portal_bots":
            raise RuntimeError("synthetic migration failure")
        return original_create(self, bind, *args, **kwargs)

    monkeypatch.setattr(Table, "create", fail_on_portal_bots)
    try:
        with pytest.raises(RuntimeError, match="synthetic migration failure"):
            migrate_database(engine)
        with engine.connect() as connection:
            assert inspect(connection).get_table_names() == []
    finally:
        engine.dispose()


def test_postgresql_restart_preserves_exact_revision() -> None:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    migrate_database(engine)
    engine.dispose()

    restarted_engine = build_engine(POSTGRES_URL)
    try:
        report = assert_schema_ready(restarted_engine)
        assert report["status"] == "ready"
        assert report["expected_revision"]["dialect_name"] == "postgresql"
    finally:
        restarted_engine.dispose()


def test_connection_loss_fails_current_operation_and_readiness_recovers() -> None:
    assert POSTGRES_URL is not None
    victim_engine = build_engine(POSTGRES_URL)
    killer_engine = build_engine(POSTGRES_URL)
    try:
        migrate_database(victim_engine)
        with victim_engine.connect() as victim:
            victim_pid = victim.execute(text("SELECT pg_backend_pid()")).scalar_one()
            with killer_engine.begin() as killer:
                assert killer.execute(
                    text("SELECT pg_terminate_backend(:pid)"),
                    {"pid": victim_pid},
                ).scalar_one()
            with pytest.raises(DBAPIError) as exc_info:
                victim.execute(text("SELECT 1"))
            assert exc_info.value.connection_invalidated
        assert assert_schema_ready(victim_engine)["status"] == "ready"
    finally:
        killer_engine.dispose()
        victim_engine.dispose()


def test_audit_and_outbox_write_are_atomic_on_postgresql() -> None:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    migrate_database(engine)
    audit_id = str(uuid4())
    event_id = str(uuid4())
    with pytest.raises(RuntimeError, match="synthetic application rollback"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO portal_audit_events (
                        audit_id, tenant_id, actor_id, resource_type,
                        resource_id, action, result, occurred_at, event_json
                    ) VALUES (
                        :audit_id, 'tenant-a', 'actor-a', 'bot', 'bot-a',
                        'bot.updated', 'success', CURRENT_TIMESTAMP, '{}'
                    )
                    """
                ),
                {"audit_id": audit_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO portal_outbox_events (
                        event_id, tenant_id, event_type, aggregate_type,
                        aggregate_id, occurred_at, event_json, published_at
                    ) VALUES (
                        :event_id, 'tenant-a', 'bot.updated', 'bot', 'bot-a',
                        CURRENT_TIMESTAMP, '{}', NULL
                    )
                    """
                ),
                {"event_id": event_id},
            )
            raise RuntimeError("synthetic application rollback")
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM portal_audit_events WHERE audit_id = :audit_id"),
                {"audit_id": audit_id},
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM portal_outbox_events WHERE event_id = :event_id"),
                {"event_id": event_id},
            ).scalar_one()
            == 0
        )
    engine.dispose()
