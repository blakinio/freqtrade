from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RejectedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    RiskPolicyLifecycleState,
    RiskPolicyVersion,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.risk.repository import RiskRepository
from ai_platform.portal.risk.schema import (
    KillSwitchState,
    RiskEvaluationSnapshot,
    RiskPolicyDefinition,
    RiskPolicyLimits,
)
from ai_platform.portal.security.authorization import require_permission


class RiskPolicyNotFoundError(LookupError):
    pass


class RiskConflictError(RuntimeError):
    pass


Clock = Callable[[], datetime]
RiskEvaluationResult = ApprovedExecutionIntent | RejectedExecutionIntent

RISK_APPROVED = "RISK_APPROVED"
KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
ORDER_NOTIONAL_LIMIT_EXCEEDED = "ORDER_NOTIONAL_LIMIT_EXCEEDED"
GROSS_EXPOSURE_LIMIT_EXCEEDED = "GROSS_EXPOSURE_LIMIT_EXCEEDED"
OPEN_POSITION_LIMIT_EXCEEDED = "OPEN_POSITION_LIMIT_EXCEEDED"
DAILY_LOSS_LIMIT_EXCEEDED = "DAILY_LOSS_LIMIT_EXCEEDED"
DRAWDOWN_LIMIT_EXCEEDED = "DRAWDOWN_LIMIT_EXCEEDED"
RUNTIME_UNHEALTHY = "RUNTIME_UNHEALTHY"


class RiskService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: RiskRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or RiskRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def register_policy(
        self,
        context: RequestContext,
        risk_policy_version_id: str,
        limits: RiskPolicyLimits,
    ) -> RiskPolicyDefinition:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        occurred_at = self._clock()
        policy_hash = hashlib.sha256(limits.canonical_json().encode()).hexdigest()
        definition = RiskPolicyDefinition(
            version=RiskPolicyVersion(
                risk_policy_version_id=risk_policy_version_id,
                tenant_id=context.tenant_id,
                policy_hash=policy_hash,
                state=RiskPolicyLifecycleState.PROMOTED,
                created_by_actor_id=context.actor_id,
                created_at=occurred_at,
            ),
            limits=limits,
        )
        audit = self._audit_event(
            context,
            resource_type="risk_policy",
            resource_id=risk_policy_version_id,
            action=AuditAction.RISK_POLICY_CHANGED,
            result=AuditResult.SUCCEEDED,
            occurred_at=occurred_at,
            reason_code=None,
            details={"policy_hash": policy_hash, "state": RiskPolicyLifecycleState.PROMOTED.value},
        )
        try:
            with self._session_factory() as session, session.begin():
                if (
                    self._repository.get_policy(
                        session,
                        context.tenant_id,
                        risk_policy_version_id,
                    )
                    is not None
                ):
                    raise RiskConflictError("risk policy version identity already exists")
                self._repository.add_policy(session, definition)
                self._repository.add_audit_event(session, audit)
        except IntegrityError as exc:
            raise RiskConflictError("risk policy version identity already exists") from exc
        return definition

    def get_policy(
        self,
        context: RequestContext,
        risk_policy_version_id: str,
    ) -> RiskPolicyDefinition:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        with self._session_factory() as session:
            definition = self._repository.get_policy(
                session,
                context.tenant_id,
                risk_policy_version_id,
            )
        if definition is None:
            raise RiskPolicyNotFoundError("risk policy version not found")
        return definition

    def list_policies(self, context: RequestContext) -> tuple[RiskPolicyDefinition, ...]:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        with self._session_factory() as session:
            return self._repository.list_policies(session, context.tenant_id)

    def activate_kill_switch(
        self,
        context: RequestContext,
        environment: Environment,
        reason_code: str,
    ) -> KillSwitchState:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        occurred_at = self._clock()
        with self._session_factory() as session, session.begin():
            current = self._repository.get_kill_switch(session, context.tenant_id, environment)
            if current is not None and current.active:
                raise RiskConflictError("kill switch is already active")
            state = KillSwitchState(
                tenant_id=context.tenant_id,
                environment=environment,
                active=True,
                reason_code=reason_code,
                updated_by_actor_id=context.actor_id,
                updated_at=occurred_at,
            )
            self._repository.set_kill_switch(session, state)
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    resource_type="kill_switch",
                    resource_id=environment.value,
                    action=AuditAction.KILL_SWITCH_ACTIVATED,
                    result=AuditResult.SUCCEEDED,
                    occurred_at=occurred_at,
                    reason_code=reason_code,
                    details={"environment": environment.value},
                ),
            )
        return state

    def release_kill_switch(
        self,
        context: RequestContext,
        environment: Environment,
        reason_code: str,
    ) -> KillSwitchState:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        occurred_at = self._clock()
        with self._session_factory() as session, session.begin():
            current = self._repository.get_kill_switch(session, context.tenant_id, environment)
            if current is None or not current.active:
                raise RiskConflictError("kill switch is not active")
            state = KillSwitchState(
                tenant_id=context.tenant_id,
                environment=environment,
                active=False,
                reason_code=None,
                updated_by_actor_id=context.actor_id,
                updated_at=occurred_at,
            )
            self._repository.set_kill_switch(session, state)
            self._repository.add_audit_event(
                session,
                self._audit_event(
                    context,
                    resource_type="kill_switch",
                    resource_id=environment.value,
                    action=AuditAction.KILL_SWITCH_RELEASED,
                    result=AuditResult.SUCCEEDED,
                    occurred_at=occurred_at,
                    reason_code=reason_code,
                    details={"environment": environment.value},
                ),
            )
        return state

    def get_kill_switch(
        self,
        context: RequestContext,
        environment: Environment,
    ) -> KillSwitchState | None:
        require_permission(context.permissions, Permission.RISK_MANAGE)
        with self._session_factory() as session:
            return self._repository.get_kill_switch(session, context.tenant_id, environment)

    def evaluate_manual_intent(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        pair: str,
        side: TradeSide,
        amount: Decimal,
        environment: Environment,
        risk_policy_version_id: str,
        snapshot: RiskEvaluationSnapshot,
    ) -> RiskEvaluationResult:
        require_permission(context.permissions, Permission.TRADE_MANUAL_EXECUTE)
        occurred_at = self._clock()
        try:
            with self._session_factory() as session, session.begin():
                definition = self._repository.get_policy(
                    session,
                    context.tenant_id,
                    risk_policy_version_id,
                )
                if definition is None:
                    raise RiskPolicyNotFoundError("risk policy version not found")
                if definition.version.state is not RiskPolicyLifecycleState.PROMOTED:
                    raise RiskConflictError("risk policy version is not promoted")
                kill_switch = self._repository.get_kill_switch(
                    session,
                    context.tenant_id,
                    environment,
                )
                intent = TradeIntent(
                    trade_intent_id=uuid4(),
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    prediction_id=None,
                    source_actor_id=context.actor_id,
                    pair=pair,
                    side=side,
                    amount=amount,
                    environment=environment,
                    created_at=occurred_at,
                    context=context.correlation_context(),
                )
                outcome, reason_codes, evaluations = self._evaluate(
                    definition.limits,
                    snapshot,
                    kill_switch_active=kill_switch is not None and kill_switch.active,
                )
                decision = RiskDecision(
                    risk_decision_id=uuid4(),
                    tenant_id=context.tenant_id,
                    trade_intent_id=intent.trade_intent_id,
                    risk_policy_version=risk_policy_version_id,
                    decision=outcome,
                    reason_codes=reason_codes,
                    evaluated_limits=evaluations,
                    occurred_at=occurred_at,
                    context=context.correlation_context(),
                )
                if outcome is RiskDecisionOutcome.APPROVED:
                    result: RiskEvaluationResult = ApprovedExecutionIntent(
                        execution_intent_id=uuid4(),
                        tenant_id=context.tenant_id,
                        trade_intent=intent,
                        risk_decision=decision,
                        created_at=occurred_at,
                        context=context.correlation_context(),
                    )
                    audit_result = AuditResult.SUCCEEDED
                    event_type = EventType.RISK_APPROVED
                else:
                    result = RejectedExecutionIntent(
                        rejection_id=uuid4(),
                        tenant_id=context.tenant_id,
                        trade_intent=intent,
                        risk_decision=decision,
                        created_at=occurred_at,
                        context=context.correlation_context(),
                    )
                    audit_result = AuditResult.DENIED
                    event_type = EventType.RISK_REJECTED

                self._repository.add_trade_intent(session, intent)
                self._repository.add_risk_decision(session, decision)
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        resource_type="trade_intent",
                        resource_id=str(intent.trade_intent_id),
                        action=AuditAction.MANUAL_TRADE_INTENT,
                        result=audit_result,
                        occurred_at=occurred_at,
                        reason_code=reason_codes[0],
                        details={
                            "bot_id": bot_id,
                            "pair": pair,
                            "side": side.value,
                            "risk_policy_version": risk_policy_version_id,
                            "decision": outcome.value,
                        },
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        intent,
                        EventType.TRADE_INTENT_CREATED,
                        occurred_at,
                        payload={
                            "bot_id": bot_id,
                            "pair": pair,
                            "side": side.value,
                            "risk_policy_version": risk_policy_version_id,
                        },
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        intent,
                        event_type,
                        occurred_at,
                        payload={
                            "decision": outcome.value,
                            "reason_codes": list(reason_codes),
                            "risk_policy_version": risk_policy_version_id,
                        },
                    ),
                )
        except IntegrityError as exc:
            raise RiskConflictError("risk evaluation persistence conflict") from exc
        return result

    @staticmethod
    def _evaluate(
        limits: RiskPolicyLimits,
        snapshot: RiskEvaluationSnapshot,
        *,
        kill_switch_active: bool,
    ) -> tuple[
        RiskDecisionOutcome,
        tuple[str, ...],
        tuple[RiskLimitEvaluation, ...],
    ]:
        checks = (
            (
                "kill_switch",
                "inactive",
                "active" if kill_switch_active else "inactive",
                not kill_switch_active,
                KILL_SWITCH_ACTIVE,
            ),
            (
                "max_order_notional",
                str(limits.max_order_notional),
                str(snapshot.intent_notional),
                snapshot.intent_notional <= limits.max_order_notional,
                ORDER_NOTIONAL_LIMIT_EXCEEDED,
            ),
            (
                "max_projected_gross_exposure",
                str(limits.max_projected_gross_exposure),
                str(snapshot.projected_gross_exposure),
                snapshot.projected_gross_exposure <= limits.max_projected_gross_exposure,
                GROSS_EXPOSURE_LIMIT_EXCEEDED,
            ),
            (
                "max_projected_open_positions",
                str(limits.max_projected_open_positions),
                str(snapshot.projected_open_positions),
                snapshot.projected_open_positions <= limits.max_projected_open_positions,
                OPEN_POSITION_LIMIT_EXCEEDED,
            ),
            (
                "max_daily_loss",
                str(limits.max_daily_loss),
                str(snapshot.daily_loss),
                snapshot.daily_loss <= limits.max_daily_loss,
                DAILY_LOSS_LIMIT_EXCEEDED,
            ),
            (
                "max_drawdown",
                str(limits.max_drawdown),
                str(snapshot.current_drawdown),
                snapshot.current_drawdown <= limits.max_drawdown,
                DRAWDOWN_LIMIT_EXCEEDED,
            ),
            (
                "runtime_health",
                RuntimeHealthState.HEALTHY.value if limits.require_healthy_runtime else "ANY",
                snapshot.runtime_health.value,
                not limits.require_healthy_runtime
                or snapshot.runtime_health is RuntimeHealthState.HEALTHY,
                RUNTIME_UNHEALTHY,
            ),
        )
        evaluations = tuple(
            RiskLimitEvaluation(
                limit_name=name,
                configured_value=configured,
                observed_value=observed,
                passed=passed,
            )
            for name, configured, observed, passed, _reason_code in checks
        )
        failures = tuple(reason_code for *_values, passed, reason_code in checks if not passed)
        if failures:
            return RiskDecisionOutcome.REJECTED, failures, evaluations
        return RiskDecisionOutcome.APPROVED, (RISK_APPROVED,), evaluations

    @staticmethod
    def _audit_event(
        context: RequestContext,
        *,
        resource_type: str,
        resource_id: str,
        action: AuditAction,
        result: AuditResult,
        occurred_at: datetime,
        reason_code: str | None,
        details: dict[str, JsonValue],
    ) -> AuditEvent:
        return AuditEvent(
            audit_id=uuid4(),
            occurred_at=occurred_at,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            reason_code=reason_code,
            details=details,
        )

    @staticmethod
    def _domain_event(
        context: RequestContext,
        intent: TradeIntent,
        event_type: EventType,
        occurred_at: datetime,
        payload: dict[str, JsonValue],
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
            aggregate_type="trade_intent",
            aggregate_id=str(intent.trade_intent_id),
            payload=payload,
        )
