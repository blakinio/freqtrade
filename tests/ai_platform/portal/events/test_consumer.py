from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.events.consumer import ConsumeResult, IdempotentEventConsumer
from ai_platform.portal.events.models import EventInboxRow
from ai_platform.portal.events.schema import create_event_schema


NOW = datetime(2026, 7, 22, 13, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_event_schema(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE p4_test_side_effects ("
                "effect_id TEXT PRIMARY KEY, event_id TEXT NOT NULL UNIQUE)"
            )
        )
    return build_session_factory(engine)


def _event() -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type=EventType.BOT_CREATED,
        event_version=1,
        occurred_at=NOW,
        tenant_id="tenant-a",
        actor_id="actor-a",
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
        aggregate_type="bot",
        aggregate_id="bot-1",
        payload={"config_revision": 1},
    )


def _insert_effect(session: Session, event: EventEnvelope) -> None:
    session.execute(
        text(
            "INSERT INTO p4_test_side_effects (effect_id, event_id) VALUES (:effect_id, :event_id)"
        ),
        {"effect_id": str(uuid4()), "event_id": str(event.event_id)},
    )


def test_duplicate_delivery_does_not_run_handler_twice(
    session_factory: SessionFactory,
) -> None:
    event = _event()
    consumer = IdempotentEventConsumer(
        session_factory,
        "trade-mirror",
        _insert_effect,
        clock=lambda: NOW,
    )

    assert consumer.consume(event) is ConsumeResult.PROCESSED
    assert consumer.consume(event) is ConsumeResult.DUPLICATE

    with session_factory() as session:
        effect_count = session.scalar(text("SELECT COUNT(*) FROM p4_test_side_effects"))
        inbox_count = session.scalar(select(func.count()).select_from(EventInboxRow))
        marker = session.get(EventInboxRow, ("trade-mirror", str(event.event_id)))

    assert effect_count == 1
    assert inbox_count == 1
    assert marker is not None
    assert marker.tenant_id == event.tenant_id
    assert marker.correlation_id == str(event.correlation_id)


def test_handler_failure_rolls_back_side_effect_and_inbox_marker(
    session_factory: SessionFactory,
) -> None:
    event = _event()

    def failing_handler(session: Session, current: EventEnvelope) -> None:
        _insert_effect(session, current)
        raise RuntimeError("handler failed")

    failing = IdempotentEventConsumer(
        session_factory,
        "trade-mirror",
        failing_handler,
        clock=lambda: NOW,
    )
    with pytest.raises(RuntimeError, match="handler failed"):
        failing.consume(event)

    with session_factory() as session:
        assert session.scalar(text("SELECT COUNT(*) FROM p4_test_side_effects")) == 0
        assert session.get(EventInboxRow, ("trade-mirror", str(event.event_id))) is None

    succeeding = IdempotentEventConsumer(
        session_factory,
        "trade-mirror",
        _insert_effect,
        clock=lambda: NOW,
    )
    assert succeeding.consume(event) is ConsumeResult.PROCESSED


def test_handler_integrity_error_is_not_misclassified_as_duplicate(
    session_factory: SessionFactory,
) -> None:
    event = _event()

    def integrity_failure(session: Session, current: EventEnvelope) -> None:
        _insert_effect(session, current)
        _insert_effect(session, current)
        session.flush()

    consumer = IdempotentEventConsumer(
        session_factory,
        "trade-mirror",
        integrity_failure,
        clock=lambda: NOW,
    )

    with pytest.raises(IntegrityError):
        consumer.consume(event)

    with session_factory() as session:
        assert session.get(EventInboxRow, ("trade-mirror", str(event.event_id))) is None
        assert session.scalar(text("SELECT COUNT(*) FROM p4_test_side_effects")) == 0


def test_same_event_is_processed_once_per_consumer_name(
    session_factory: SessionFactory,
) -> None:
    event = _event()
    calls: list[str] = []

    def record_consumer(_session: Session, current: EventEnvelope) -> None:
        calls.append(str(current.event_id))

    first = IdempotentEventConsumer(session_factory, "consumer-a", record_consumer)
    second = IdempotentEventConsumer(session_factory, "consumer-b", record_consumer)

    assert first.consume(event) is ConsumeResult.PROCESSED
    assert first.consume(event) is ConsumeResult.DUPLICATE
    assert second.consume(event) is ConsumeResult.PROCESSED
    assert calls == [str(event.event_id), str(event.event_id)]
