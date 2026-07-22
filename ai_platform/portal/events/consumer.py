from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.events.models import EventInboxRow


EventHandler = Callable[[Session, EventEnvelope], None]
Clock = Callable[[], datetime]


class ConsumeResult(StrEnum):
    PROCESSED = "PROCESSED"
    DUPLICATE = "DUPLICATE"


class IdempotentEventConsumer:
    """Reference consumer with transactional inbox and handler side effects."""

    def __init__(
        self,
        session_factory: SessionFactory,
        consumer_name: str,
        handler: EventHandler,
        clock: Clock | None = None,
    ) -> None:
        if not consumer_name.strip():
            raise ValueError("consumer_name must not be empty")
        self._session_factory = session_factory
        self._consumer_name = consumer_name
        self._handler = handler
        self._clock = clock or (lambda: datetime.now(UTC))

    def consume(self, event: EventEnvelope) -> ConsumeResult:
        session = self._session_factory()
        handler_started = False
        try:
            with session.begin():
                marker = EventInboxRow(
                    consumer_name=self._consumer_name,
                    event_id=str(event.event_id),
                    tenant_id=event.tenant_id,
                    event_type=event.event_type.value,
                    correlation_id=str(event.correlation_id),
                    processed_at=self._clock(),
                )
                session.add(marker)
                session.flush()
                handler_started = True
                self._handler(session, event)
            return ConsumeResult.PROCESSED
        except IntegrityError:
            session.rollback()
            if handler_started:
                raise
            return ConsumeResult.DUPLICATE
        finally:
            session.close()
