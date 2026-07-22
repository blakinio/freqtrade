from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission


class BotNotFoundError(LookupError):
    pass


class ControlPlaneConflictError(RuntimeError):
    pass


Clock = Callable[[], datetime]


class ControlPlaneService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: BotRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_bot(
        self,
        context: RequestContext,
        bot_id: str,
        name: str,
        spec: BotSpec,
    ) -> BotInstance:
        require_permission(context.permissions, Permission.BOT_CREATE)
        self._require_tenant(context, spec.tenant_id)
        if spec.config_revision != 1:
            raise ValueError("initial bot config_revision must be 1")

        occurred_at = self._clock()
        bot = BotInstance(
            bot_id=bot_id,
            tenant_id=context.tenant_id,
            name=name,
            spec=spec,
            desired_state=BotDesiredState.CREATED,
            observed_state=BotObservedState.CREATED,
        )
        revision = self._revision_from_spec(context, bot_id, spec, occurred_at)
        audit = self._audit_event(
            context,
            bot_id,
            AuditAction.BOT_CREATED,
            occurred_at,
            details={"config_revision": spec.config_revision},
        )
        event = self._domain_event(
            context,
            bot_id,
            EventType.BOT_CREATED,
            occurred_at,
            payload={"config_revision": spec.config_revision},
        )

        try:
            with self._session_factory() as session, session.begin():
                if self._repository.get_bot(session, context.tenant_id, bot_id) is not None:
                    raise ControlPlaneConflictError("bot already exists")
                self._repository.add_bot(session, bot)
                self._repository.add_revision(session, revision)
                self._repository.add_audit_event(session, audit)
                self._repository.add_outbox_event(session, event)
        except IntegrityError as exc:
            raise ControlPlaneConflictError("bot or revision identity already exists") from exc
        return bot

    def get_bot(self, context: RequestContext, bot_id: str) -> BotInstance:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            bot = self._repository.get_bot(session, context.tenant_id, bot_id)
        if bot is None:
            raise BotNotFoundError("bot not found")
        return bot

    def list_bots(self, context: RequestContext) -> tuple[BotInstance, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_bots(session, context.tenant_id)

    def revise_bot(
        self,
        context: RequestContext,
        bot_id: str,
        spec: BotSpec,
    ) -> BotInstance:
        # P1 has no separate bot.configure permission. Creating a new immutable
        # configuration identity therefore uses the existing bot.create capability.
        require_permission(context.permissions, Permission.BOT_CREATE)
        self._require_tenant(context, spec.tenant_id)
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                current = self._repository.get_bot(session, context.tenant_id, bot_id)
                if current is None:
                    raise BotNotFoundError("bot not found")
                next_revision = current.spec.config_revision + 1
                if spec.config_revision != next_revision:
                    raise ControlPlaneConflictError(
                        f"config_revision must be the next immutable revision: {next_revision}"
                    )

                revision = self._revision_from_spec(context, bot_id, spec, occurred_at)
                self._repository.add_revision(session, revision)
                updated = self._repository.set_current_revision(
                    session,
                    context.tenant_id,
                    bot_id,
                    spec,
                )
                if updated is None:
                    raise BotNotFoundError("bot not found")
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        bot_id,
                        AuditAction.BOT_CONFIG_REVISED,
                        occurred_at,
                        details={"config_revision": spec.config_revision},
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        bot_id,
                        EventType.BOT_CONFIG_REVISED,
                        occurred_at,
                        payload={"config_revision": spec.config_revision},
                    ),
                )
        except IntegrityError as exc:
            raise ControlPlaneConflictError("config revision identity already exists") from exc
        return updated

    def set_desired_state(
        self,
        context: RequestContext,
        bot_id: str,
        desired_state: BotDesiredState,
    ) -> BotInstance:
        permission, audit_action, event_type = self._desired_state_policy(desired_state)
        require_permission(context.permissions, permission)
        occurred_at = self._clock()

        with self._session_factory() as session, session.begin():
            current = self._repository.get_bot(session, context.tenant_id, bot_id)
            if current is None:
                raise BotNotFoundError("bot not found")
            updated = self._repository.set_desired_state(
                session,
                context.tenant_id,
                bot_id,
                desired_state,
            )
            if updated is None:
                raise BotNotFoundError("bot not found")
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    bot_id,
                    audit_action,
                    occurred_at,
                    details={"desired_state": desired_state.value},
                ),
            )
            self._repository.add_outbox_event(
                session,
                self._domain_event(
                    context,
                    bot_id,
                    event_type,
                    occurred_at,
                    payload={"desired_state": desired_state.value},
                ),
            )
        return updated

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if tenant_id != context.tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")

    @staticmethod
    def _revision_from_spec(
        context: RequestContext,
        bot_id: str,
        spec: BotSpec,
        created_at: datetime,
    ) -> BotConfigRevision:
        return BotConfigRevision(
            revision_id=str(uuid4()),
            tenant_id=context.tenant_id,
            bot_id=bot_id,
            revision=spec.config_revision,
            strategy_version=spec.strategy_version,
            model_version=spec.model_version,
            risk_policy_version=spec.risk_policy_version,
            exchange_connection_ref=spec.exchange_connection_ref,
            pair_universe=spec.pair_universe,
            timeframe=spec.timeframe,
            capital_allocation=spec.capital_allocation,
            capital_currency=spec.capital_currency,
            runtime_version=spec.runtime_version,
            environment=spec.environment,
            execution_mode=spec.execution_mode,
            created_by_actor_id=context.actor_id,
            created_at=created_at,
        )

    @staticmethod
    def _audit_event(
        context: RequestContext,
        bot_id: str,
        action: AuditAction,
        occurred_at: datetime,
        details: dict[str, str | int],
    ) -> AuditEvent:
        return AuditEvent(
            audit_id=uuid4(),
            occurred_at=occurred_at,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            resource_type="bot",
            resource_id=bot_id,
            action=action,
            result=AuditResult.SUCCEEDED,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            details=details,
        )

    @staticmethod
    def _domain_event(
        context: RequestContext,
        bot_id: str,
        event_type: EventType,
        occurred_at: datetime,
        payload: dict[str, str | int],
    ) -> EventEnvelope:
        return EventEnvelope(
            event_id=uuid4(),
            event_type=event_type,
            event_version=1,
            occurred_at=occurred_at,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            aggregate_type="bot",
            aggregate_id=bot_id,
            payload=payload,
        )

    @staticmethod
    def _desired_state_policy(
        desired_state: BotDesiredState,
    ) -> tuple[Permission, AuditAction, EventType]:
        policies = {
            BotDesiredState.RUNNING: (
                Permission.BOT_START,
                AuditAction.BOT_START_REQUESTED,
                EventType.BOT_START_REQUESTED,
            ),
            BotDesiredState.PAUSED: (
                Permission.BOT_PAUSE,
                AuditAction.BOT_PAUSE_REQUESTED,
                EventType.BOT_PAUSE_REQUESTED,
            ),
            BotDesiredState.STOPPED: (
                Permission.BOT_STOP,
                AuditAction.BOT_STOP_REQUESTED,
                EventType.BOT_STOP_REQUESTED,
            ),
        }
        try:
            return policies[desired_state]
        except KeyError as exc:
            raise ValueError("desired state command must be RUNNING, PAUSED or STOPPED") from exc
