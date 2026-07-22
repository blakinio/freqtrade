from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.models import OutboxEventRow
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.events.outbox import EventTransport, OutboxPublisher


NOW = datetime(2026, 7, 22, 13, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
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


def _seed(session_factory: SessionFactory, event: EventEnvelope) -> None:
    with session_factory() as session, session.begin():
        BotRepository().add_outbox_event(session, event)


class _RecordingTransport(EventTransport):
    def __init__(self) -> None:
        self.deliveries: list[tuple[str, EventEnvelope]] = []

    def publish(self, subject: str, event: EventEnvelope) -> None:
        self.deliveries.append((subject, event))


class _RecordThenFailTransport(_RecordingTransport):
    def publish(self, subject: str, event: EventEnvelope) -> None:
        super().publish(subject, event)
        raise RuntimeError("transport unavailable")


def test_successful_publish_marks_outbox_only_after_transport_send(
    session_factory: SessionFactory,
) -> None:
    event = _event()
    _seed(session_factory, event)
    transport = _RecordingTransport()
    publisher = OutboxPublisher(session_factory, transport, clock=lambda: NOW)

    assert publisher.publish_batch() == 1

    assert transport.deliveries == [("portal.v1.bot.created", event)]
    delivered = transport.deliveries[0][1]
    assert delivered.request_id == event.request_id
    assert delivered.correlation_id == event.correlation_id
    assert delivered.causation_id == event.causation_id
    with session_factory() as session:
        row = session.get(OutboxEventRow, str(event.event_id))
        assert row is not None
        assert row.published_at is not None


def test_failed_publish_remains_unpublished_and_can_be_delivered_again(
    session_factory: SessionFactory,
) -> None:
    event = _event()
    _seed(session_factory, event)
    failing = _RecordThenFailTransport()

    with pytest.raises(RuntimeError, match="transport unavailable"):
        OutboxPublisher(session_factory, failing, clock=lambda: NOW).publish_batch()

    with session_factory() as session:
        row = session.get(OutboxEventRow, str(event.event_id))
        assert row is not None
        assert row.published_at is None

    succeeding = _RecordingTransport()
    assert OutboxPublisher(session_factory, succeeding, clock=lambda: NOW).publish_batch() == 1
    assert [item[1].event_id for item in failing.deliveries + succeeding.deliveries] == [
        event.event_id,
        event.event_id,
    ]


def test_publish_batch_respects_positive_limit(session_factory: SessionFactory) -> None:
    _seed(session_factory, _event())
    _seed(session_factory, _event())
    transport = _RecordingTransport()
    publisher = OutboxPublisher(session_factory, transport, clock=lambda: NOW)

    assert publisher.publish_batch(limit=1) == 1
    assert len(transport.deliveries) == 1

    with pytest.raises(ValueError, match="positive"):
        publisher.publish_batch(limit=0)
