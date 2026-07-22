from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import OutboxEventRow


Clock = Callable[[], datetime]


class EventTransport(Protocol):
    def publish(self, subject: str, event: EventEnvelope) -> None: ...


def event_subject(event: EventEnvelope) -> str:
    return f"portal.v{event.event_version}.{event.event_type.value}"


class OutboxRepository:
    def lock_next_unpublished(self, session: Session) -> OutboxEventRow | None:
        statement = (
            select(OutboxEventRow)
            .where(OutboxEventRow.published_at.is_(None))
            .order_by(OutboxEventRow.occurred_at, OutboxEventRow.event_id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return session.scalars(statement).first()

    @staticmethod
    def mark_published(row: OutboxEventRow, published_at: datetime) -> None:
        row.published_at = published_at


class OutboxPublisher:
    """At-least-once publisher for P2 transactional outbox rows."""

    def __init__(
        self,
        session_factory: SessionFactory,
        transport: EventTransport,
        repository: OutboxRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._transport = transport
        self._repository = repository or OutboxRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def publish_batch(self, limit: int = 100) -> int:
        if limit < 1:
            raise ValueError("limit must be positive")

        published = 0
        for _ in range(limit):
            if not self._publish_next():
                break
            published += 1
        return published

    def _publish_next(self) -> bool:
        with self._session_factory() as session, session.begin():
            row = self._repository.lock_next_unpublished(session)
            if row is None:
                return False
            event = EventEnvelope.model_validate_json(row.event_json)
            self._transport.publish(event_subject(event), event)
            self._repository.mark_published(row, self._clock())
        return True
