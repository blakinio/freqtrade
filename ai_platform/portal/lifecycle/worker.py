from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, or_, select, update
from sqlalchemy.engine import CursorResult
from typing import Any, cast

from ai_platform.portal.contracts.bots import BotDesiredState, BotObservedState
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.execution import ExecutionAdapter, RuntimeStatus
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import (
    BotRow,
    OutboxEventRow,
    RuntimeGenerationObservationRow,
    RuntimeGenerationRow,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.events.models import EventInboxRow
from ai_platform.portal.lifecycle.models import LifecycleCommandRow, OutboxDeliveryRow
from ai_platform.portal.lifecycle.service import LifecycleCommandStatus


CONSUMER_NAME = "portal.lifecycle.runtime.v1"
LIFECYCLE_EVENT_TYPES = frozenset(
    {
        EventType.BOT_START_REQUESTED.value,
        EventType.BOT_PAUSE_REQUESTED.value,
        EventType.BOT_STOP_REQUESTED.value,
    }
)


class LifecycleWorkerError(RuntimeError):
    pass


class StaleLifecycleCommand(LifecycleWorkerError):
    pass


class LifecycleOutboxWorker:
    """Restart-safe product worker for desired-state runtime effects.

    The worker owns no container-engine capability. It invokes only the private
    ExecutionAdapter, which in the production composition is backed by the Runtime
    Supervisor boundary. Supervisor command identities are deterministic from the
    durable event correlation context, so a crash after a runtime effect can replay
    safely without duplicating the underlying lifecycle command.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        execution: ExecutionAdapter,
        *,
        clock: Callable[[], datetime] | None = None,
        max_attempts: int = 5,
        base_retry_delay: timedelta = timedelta(seconds=1),
        processing_lease: timedelta = timedelta(seconds=30),
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if base_retry_delay <= timedelta(0) or processing_lease <= timedelta(0):
            raise ValueError("retry and processing lease durations must be positive")
        self._session_factory = session_factory
        self._execution = execution
        self._repository = BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._max_attempts = max_attempts
        self._base_retry_delay = base_retry_delay
        self._processing_lease = processing_lease

    def run_once(self, *, batch_size: int = 32) -> int:
        if not 1 <= batch_size <= 256:
            raise ValueError("batch_size must be between 1 and 256")
        now = self._clock()
        with self._session_factory() as session:
            rows = session.scalars(
                select(OutboxEventRow)
                .outerjoin(OutboxDeliveryRow, OutboxDeliveryRow.event_id == OutboxEventRow.event_id)
                .where(
                    OutboxEventRow.published_at.is_(None),
                    OutboxEventRow.event_type.in_(LIFECYCLE_EVENT_TYPES),
                    or_(
                        OutboxDeliveryRow.event_id.is_(None),
                        (
                            OutboxDeliveryRow.dead_lettered_at.is_(None)
                            & or_(
                                OutboxDeliveryRow.next_attempt_at.is_(None),
                                OutboxDeliveryRow.next_attempt_at <= now,
                            )
                        ),
                    ),
                )
                .order_by(OutboxEventRow.occurred_at, OutboxEventRow.event_id)
                .limit(batch_size)
            ).all()
            event_ids = tuple(row.event_id for row in rows)

        processed = 0
        for event_id in event_ids:
            if self._process_event(event_id):
                processed += 1
        return processed

    def _process_event(self, event_id: str) -> bool:
        envelope = self._load_event(event_id)
        if envelope is None:
            return False
        command_id = self._required_payload_str(envelope, "command_id")
        if not self._claim(command_id):
            return False
        try:
            status = self._execute(envelope, command_id)
        except StaleLifecycleCommand as exc:
            self._terminal_stale(event_id, command_id, self._error_code(exc))
            return True
        except Exception as exc:
            self._retry_or_dead_letter(event_id, command_id, self._error_code(exc))
            return True
        self._reconcile_success(event_id, envelope, command_id, status)
        return True

    def _load_event(self, event_id: str) -> EventEnvelope | None:
        with self._session_factory() as session:
            if session.get(EventInboxRow, (CONSUMER_NAME, event_id)) is not None:
                return None
            row = session.get(OutboxEventRow, event_id)
            if row is None or row.published_at is not None or row.event_type not in LIFECYCLE_EVENT_TYPES:
                return None
            return EventEnvelope.model_validate_json(row.event_json)

    def _claim(self, command_id: str) -> bool:
        now = self._clock()
        stale_processing = now - self._processing_lease
        with self._session_factory() as session, session.begin():
            command = session.get(LifecycleCommandRow, command_id)
            if command is None:
                raise LifecycleWorkerError("LIFECYCLE_COMMAND_NOT_FOUND")
            if command.status in {
                LifecycleCommandStatus.SUCCEEDED.value,
                LifecycleCommandStatus.STALE.value,
                LifecycleCommandStatus.DEAD_LETTER.value,
            }:
                return False
            claimable = command.status in {
                LifecycleCommandStatus.PENDING.value,
                LifecycleCommandStatus.FAILED.value,
            } or (
                command.status == LifecycleCommandStatus.PROCESSING.value
                and command.updated_at <= stale_processing
            )
            if not claimable:
                return False
            previous_status = command.status
            previous_updated_at = command.updated_at
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(LifecycleCommandRow)
                    .where(
                        LifecycleCommandRow.command_id == command_id,
                        LifecycleCommandRow.status == previous_status,
                        LifecycleCommandRow.updated_at == previous_updated_at,
                    )
                    .values(
                        status=LifecycleCommandStatus.PROCESSING.value,
                        attempt_count=command.attempt_count + 1,
                        updated_at=now,
                        last_error_code=None,
                    )
                ),
            )
            return result.rowcount == 1

    def _execute(self, envelope: EventEnvelope, command_id: str) -> RuntimeStatus:
        with self._session_factory() as session:
            command = session.get(LifecycleCommandRow, command_id)
            if command is None:
                raise LifecycleWorkerError("LIFECYCLE_COMMAND_NOT_FOUND")
            bot = self._repository.get_bot(session, command.tenant_id, command.bot_id)
            generation = session.get(RuntimeGenerationRow, command.generation_id)
        if bot is None or generation is None:
            raise StaleLifecycleCommand("LIFECYCLE_AUTHORITY_MISSING")
        if envelope.tenant_id != command.tenant_id or envelope.aggregate_id != command.bot_id:
            raise StaleLifecycleCommand("LIFECYCLE_EVENT_SCOPE_MISMATCH")
        expected_event = self._event_for_desired_state(BotDesiredState(command.desired_state))
        if envelope.event_type is not expected_event:
            raise StaleLifecycleCommand("LIFECYCLE_EVENT_TYPE_MISMATCH")
        if bot.desired_state.value != command.desired_state:
            raise StaleLifecycleCommand("LIFECYCLE_DESIRED_STATE_SUPERSEDED")
        if bot.state_version != command.accepted_state_version:
            raise StaleLifecycleCommand("LIFECYCLE_STATE_VERSION_SUPERSEDED")
        if generation.tenant_id != command.tenant_id or generation.bot_id != command.bot_id:
            raise StaleLifecycleCommand("LIFECYCLE_GENERATION_SCOPE_MISMATCH")
        if command.desired_state == BotDesiredState.RUNNING.value:
            if bot.desired_runtime_generation_id != command.generation_id:
                raise StaleLifecycleCommand("LIFECYCLE_GENERATION_SUPERSEDED")
        elif command.generation_id not in {
            bot.observed_runtime_generation_id,
            bot.desired_runtime_generation_id,
        }:
            raise StaleLifecycleCommand("LIFECYCLE_GENERATION_SUPERSEDED")

        context = CorrelationContext(
            request_id=envelope.request_id,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
        )
        desired = BotDesiredState(command.desired_state)
        if desired is BotDesiredState.RUNNING:
            provisioned = self._execution.provision_bot(bot, context)
            if provisioned.observed_state is BotObservedState.ERROR:
                raise LifecycleWorkerError("RUNTIME_PROVISION_FAILED")
            status = self._execution.start_bot(bot, context)
            if status.observed_state is not BotObservedState.RUNNING:
                raise LifecycleWorkerError("RUNTIME_START_NOT_RECONCILED")
            return status
        if desired is BotDesiredState.PAUSED:
            status = self._execution.pause_bot(bot.tenant_id, bot.bot_id, context)
            if status.observed_state is not BotObservedState.PAUSED:
                raise LifecycleWorkerError("RUNTIME_PAUSE_NOT_RECONCILED")
            return status
        if desired is BotDesiredState.STOPPED:
            status = self._execution.stop_bot(bot.tenant_id, bot.bot_id, context)
            if status.observed_state is not BotObservedState.STOPPED:
                raise LifecycleWorkerError("RUNTIME_STOP_NOT_RECONCILED")
            return status
        raise StaleLifecycleCommand("UNSUPPORTED_LIFECYCLE_DESIRED_STATE")

    def _reconcile_success(
        self,
        event_id: str,
        envelope: EventEnvelope,
        command_id: str,
        status: RuntimeStatus,
    ) -> None:
        now = self._clock()
        with self._session_factory() as session, session.begin():
            command = session.get(LifecycleCommandRow, command_id)
            event = session.get(OutboxEventRow, event_id)
            generation = session.get(RuntimeGenerationRow, command.generation_id) if command else None
            if command is None or event is None or generation is None:
                raise LifecycleWorkerError("LIFECYCLE_DURABLE_STATE_DISAPPEARED")
            if command.status != LifecycleCommandStatus.PROCESSING.value:
                return
            bot_row = session.get(BotRow, (command.tenant_id, command.bot_id))
            if bot_row is None:
                raise LifecycleWorkerError("LIFECYCLE_BOT_DISAPPEARED")
            bot_row.observed_state = status.observed_state.value
            bot_row.observed_runtime_generation_id = command.generation_id
            epoch = int(
                session.scalar(
                    select(func.max(RuntimeGenerationObservationRow.reconciliation_epoch)).where(
                        RuntimeGenerationObservationRow.generation_id == command.generation_id
                    )
                )
                or 0
            ) + 1
            evidence_hash = self._evidence_hash(
                event_id=event_id,
                command_id=command_id,
                runtime_id=status.runtime_id,
                observed_state=status.observed_state.value,
                generation_spec_digest=generation.generation_spec_digest,
            )
            session.add(
                RuntimeGenerationObservationRow(
                    observation_id=str(uuid4()),
                    generation_id=command.generation_id,
                    runtime_instance_id=status.runtime_id,
                    reconciliation_epoch=epoch,
                    reconciliation_attempt=command.attempt_count,
                    observed_state=status.observed_state.value,
                    observed_generation_spec_digest=generation.generation_spec_digest,
                    observed_image_digest=generation.runtime_image_digest,
                    observed_config_digest=generation.normalized_runtime_config_digest,
                    source_sequence=None,
                    source_version="lifecycle-worker-v1",
                    source_observed_at=status.observed_at,
                    reconciled_at=now,
                    identity_status="VERIFIED",
                    freshness_status="CURRENT",
                    completeness_status="COMPLETE",
                    evidence_hash=evidence_hash,
                    reason_code=None,
                )
            )
            command.status = LifecycleCommandStatus.SUCCEEDED.value
            command.updated_at = now
            command.completed_at = now
            command.last_error_code = None
            event.published_at = now
            self._record_inbox(session, envelope, now)
            delivery = session.get(OutboxDeliveryRow, event_id)
            if delivery is not None:
                delivery.next_attempt_at = None
                delivery.last_error_code = None
                delivery.updated_at = now

    def _terminal_stale(self, event_id: str, command_id: str, error_code: str) -> None:
        now = self._clock()
        with self._session_factory() as session, session.begin():
            command = session.get(LifecycleCommandRow, command_id)
            event = session.get(OutboxEventRow, event_id)
            if command is None or event is None:
                return
            command.status = LifecycleCommandStatus.STALE.value
            command.last_error_code = error_code
            command.updated_at = now
            command.completed_at = now
            event.published_at = now
            try:
                envelope = EventEnvelope.model_validate_json(event.event_json)
                self._record_inbox(session, envelope, now)
            except Exception:
                pass

    def _retry_or_dead_letter(self, event_id: str, command_id: str, error_code: str) -> None:
        now = self._clock()
        with self._session_factory() as session, session.begin():
            command = session.get(LifecycleCommandRow, command_id)
            if command is None:
                return
            delivery = session.get(OutboxDeliveryRow, event_id)
            if delivery is None:
                delivery = OutboxDeliveryRow(
                    event_id=event_id,
                    attempt_count=0,
                    next_attempt_at=None,
                    last_error_code=None,
                    dead_lettered_at=None,
                    updated_at=now,
                )
                session.add(delivery)
            delivery.attempt_count = command.attempt_count
            delivery.last_error_code = error_code
            delivery.updated_at = now
            command.last_error_code = error_code
            command.updated_at = now
            if command.attempt_count >= self._max_attempts:
                command.status = LifecycleCommandStatus.DEAD_LETTER.value
                command.completed_at = now
                delivery.dead_lettered_at = now
                delivery.next_attempt_at = None
            else:
                command.status = LifecycleCommandStatus.FAILED.value
                delay = self._base_retry_delay * (2 ** max(command.attempt_count - 1, 0))
                delivery.next_attempt_at = now + delay

    @staticmethod
    def _record_inbox(session: Any, envelope: EventEnvelope, processed_at: datetime) -> None:
        if session.get(EventInboxRow, (CONSUMER_NAME, str(envelope.event_id))) is None:
            session.add(
                EventInboxRow(
                    consumer_name=CONSUMER_NAME,
                    event_id=str(envelope.event_id),
                    tenant_id=envelope.tenant_id,
                    event_type=envelope.event_type.value,
                    correlation_id=str(envelope.correlation_id),
                    processed_at=processed_at,
                )
            )

    @staticmethod
    def _required_payload_str(envelope: EventEnvelope, key: str) -> str:
        value = envelope.payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise LifecycleWorkerError(f"MISSING_{key.upper()}")
        return value

    @staticmethod
    def _event_for_desired_state(desired_state: BotDesiredState) -> EventType:
        if desired_state is BotDesiredState.RUNNING:
            return EventType.BOT_START_REQUESTED
        if desired_state is BotDesiredState.PAUSED:
            return EventType.BOT_PAUSE_REQUESTED
        if desired_state is BotDesiredState.STOPPED:
            return EventType.BOT_STOP_REQUESTED
        raise StaleLifecycleCommand("UNSUPPORTED_LIFECYCLE_DESIRED_STATE")

    @staticmethod
    def _error_code(exc: Exception) -> str:
        text = str(exc).strip().upper().replace(" ", "_")
        if text and len(text) <= 64 and all(char.isalnum() or char == "_" for char in text):
            return text
        return exc.__class__.__name__.upper()[:64]

    @staticmethod
    def _evidence_hash(**payload: str) -> str:
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
