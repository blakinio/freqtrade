from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import PositiveInt
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from typing import Any, cast

from ai_platform.portal.contracts.bots import BotDesiredState, BotInstance
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import BotRow
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import (
    BotNotFoundError,
    ControlPlaneConflictError,
    ControlPlaneService,
)
from ai_platform.portal.lifecycle.models import LifecycleCommandRow
from ai_platform.portal.security.authorization import require_permission


class LifecycleCommandStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    STALE = "STALE"
    DEAD_LETTER = "DEAD_LETTER"


class LifecycleCommand(ContractModel):
    command_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    desired_state: BotDesiredState
    generation_id: NonEmptyStr
    expected_state_version: PositiveInt
    accepted_state_version: PositiveInt
    status: LifecycleCommandStatus
    attempt_count: int
    last_error_code: NonEmptyStr | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime
    completed_at: UtcDateTime | None = None


class LifecycleCommandService:
    """Transactional desired-state ingress for the product runtime worker.

    Durable command identity, desired state, audit and outbox event are committed in one
    database transaction. Runtime effects happen only in LifecycleOutboxWorker.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        *,
        repository: BotRepository | None = None,
        clock: callable | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._core = ControlPlaneService(session_factory, repository=self._repository, clock=self._clock)

    def request(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        desired_state: BotDesiredState,
        idempotency_key: str,
        expected_state_version: int,
        expected_current_state: BotDesiredState,
    ) -> tuple[BotInstance, LifecycleCommand, bool]:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if expected_state_version <= 0:
            raise ValueError("expected_state_version must be positive")
        permission, audit_action, event_type = self._core._desired_state_policy(desired_state)
        require_permission(context.permissions, permission)
        now = self._clock()
        semantic_digest = self._digest(
            {
                "tenant_id": context.tenant_id,
                "bot_id": bot_id,
                "desired_state": desired_state.value,
                "expected_state_version": expected_state_version,
                "expected_current_state": expected_current_state.value,
            }
        )

        try:
            with self._session_factory() as session, session.begin():
                existing = session.scalar(
                    select(LifecycleCommandRow).where(
                        LifecycleCommandRow.tenant_id == context.tenant_id,
                        LifecycleCommandRow.bot_id == bot_id,
                        LifecycleCommandRow.idempotency_key == idempotency_key,
                    )
                )
                if existing is not None:
                    if existing.semantic_request_digest != semantic_digest:
                        raise ControlPlaneConflictError(
                            "idempotency key was already used for a different lifecycle request"
                        )
                    bot = self._repository.get_bot(session, context.tenant_id, bot_id)
                    if bot is None:
                        raise ControlPlaneConflictError(
                            "lifecycle command points to missing bot durable state"
                        )
                    return bot, self._from_row(existing), True

                current = self._repository.get_bot(session, context.tenant_id, bot_id)
                if current is None:
                    raise BotNotFoundError("bot not found")
                if current.state_version != expected_state_version:
                    raise ControlPlaneConflictError(
                        f"stale expected_state_version: expected {current.state_version}"
                    )
                if current.desired_state is not expected_current_state:
                    raise ControlPlaneConflictError(
                        f"stale expected_current_state: expected {current.desired_state.value}"
                    )
                generation_id = (
                    current.desired_runtime_generation_id
                    if desired_state is BotDesiredState.RUNNING
                    else current.observed_runtime_generation_id
                    or current.desired_runtime_generation_id
                )
                if generation_id is None:
                    raise ControlPlaneConflictError(
                        "bot has no RuntimeGeneration bound to this lifecycle command"
                    )
                command_id = str(uuid4())
                result = cast(
                    CursorResult[Any],
                    session.execute(
                        update(BotRow)
                        .where(
                            BotRow.tenant_id == context.tenant_id,
                            BotRow.bot_id == bot_id,
                            BotRow.state_version == expected_state_version,
                            BotRow.desired_state == expected_current_state.value,
                        )
                        .values(
                            desired_state=desired_state.value,
                            state_version=expected_state_version + 1,
                        )
                    ),
                )
                if result.rowcount != 1:
                    raise ControlPlaneConflictError("lifecycle state changed concurrently")
                updated = self._repository.get_bot(session, context.tenant_id, bot_id)
                if updated is None:
                    raise BotNotFoundError("bot not found")
                row = LifecycleCommandRow(
                    command_id=command_id,
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    idempotency_key=idempotency_key,
                    desired_state=desired_state.value,
                    generation_id=generation_id,
                    expected_state_version=expected_state_version,
                    expected_current_state=expected_current_state.value,
                    accepted_state_version=updated.state_version,
                    semantic_request_digest=semantic_digest,
                    status=LifecycleCommandStatus.PENDING.value,
                    attempt_count=0,
                    created_at=now,
                    updated_at=now,
                    completed_at=None,
                )
                session.add(row)
                details = {
                    "desired_state": desired_state.value,
                    "command_id": command_id,
                    "generation_id": generation_id,
                    "expected_state_version": expected_state_version,
                    "accepted_state_version": updated.state_version,
                    "idempotency_key_digest": self._digest(idempotency_key),
                }
                self._repository.add_audit_event(
                    session,
                    self._core._audit_event(
                        context, bot_id, audit_action, now, details=details
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._core._domain_event(
                        context, bot_id, event_type, now, payload=details
                    ),
                )
                session.flush()
                return updated, self._from_row(row), False
        except IntegrityError as exc:
            with self._session_factory() as session:
                existing = session.scalar(
                    select(LifecycleCommandRow).where(
                        LifecycleCommandRow.tenant_id == context.tenant_id,
                        LifecycleCommandRow.bot_id == bot_id,
                        LifecycleCommandRow.idempotency_key == idempotency_key,
                    )
                )
                if existing is not None and existing.semantic_request_digest == semantic_digest:
                    bot = self._repository.get_bot(session, context.tenant_id, bot_id)
                    if bot is not None:
                        return bot, self._from_row(existing), True
            raise ControlPlaneConflictError("lifecycle command identity conflict") from exc

    def get(self, context: RequestContext, bot_id: str, command_id: str) -> LifecycleCommand:
        require_permission(context.permissions, self._core._desired_state_policy(BotDesiredState.STOPPED)[0])
        with self._session_factory() as session:
            row = session.get(LifecycleCommandRow, command_id)
            if row is None or row.tenant_id != context.tenant_id or row.bot_id != bot_id:
                raise BotNotFoundError("lifecycle command not found")
            return self._from_row(row)

    @staticmethod
    def _digest(value: object) -> str:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _from_row(row: LifecycleCommandRow) -> LifecycleCommand:
        return LifecycleCommand(
            command_id=row.command_id,
            tenant_id=row.tenant_id,
            bot_id=row.bot_id,
            idempotency_key=row.idempotency_key,
            desired_state=row.desired_state,
            generation_id=row.generation_id,
            expected_state_version=row.expected_state_version,
            accepted_state_version=row.accepted_state_version,
            status=row.status,
            attempt_count=row.attempt_count,
            last_error_code=row.last_error_code,
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
        )
