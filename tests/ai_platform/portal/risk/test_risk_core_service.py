from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.audit import AuditAction, AuditResult
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.events import EventType
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RejectedExecutionIntent,
    RiskDecisionOutcome,
    TradeSide,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.risk.database import create_risk_schema
from ai_platform.portal.risk.repository import RiskRepository
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.portal.risk.service import (
    DAILY_LOSS_LIMIT_EXCEEDED,
    DRAWDOWN_LIMIT_EXCEEDED,
    GROSS_EXPOSURE_LIMIT_EXCEEDED,
    KILL_SWITCH_ACTIVE,
    OPEN_POSITION_LIMIT_EXCEEDED,
    ORDER_NOTIONAL_LIMIT_EXCEEDED,
    RISK_APPROVED,
    RUNTIME_UNHEALTHY,
    RiskConflictError,
    RiskPolicyNotFoundError,
    RiskService,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 22, 20, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_risk_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str, *permissions: Permission) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _limits(**updates: object) -> RiskPolicyLimits:
    values: dict[str, object] = {
        "max_order_notional": Decimal("1000"),
        "max_projected_gross_exposure": Decimal("5000"),
        "max_projected_open_positions": 5,
        "max_daily_loss": Decimal("500"),
        "max_drawdown": Decimal("0.20"),
        "require_healthy_runtime": True,
    }
    values.update(updates)
    return RiskPolicyLimits(**values)


def _snapshot(**updates: object) -> RiskEvaluationSnapshot:
    values: dict[str, object] = {
        "intent_notional": Decimal("100"),
        "projected_gross_exposure": Decimal("1000"),
        "projected_open_positions": 1,
        "daily_loss": Decimal("10"),
        "current_drawdown": Decimal("0.01"),
        "runtime_health": RuntimeHealthState.HEALTHY,
    }
    values.update(updates)
    return RiskEvaluationSnapshot(**values)


def _register_default(service: RiskService, tenant_id: str = "tenant-a") -> RequestContext:
    context = _context(tenant_id, Permission.RISK_MANAGE, Permission.TRADE_MANUAL_EXECUTE)
    service.register_policy(context, "risk-v1", _limits())
    return context


def _evaluate(
    service: RiskService,
    context: RequestContext,
    snapshot: RiskEvaluationSnapshot,
):
    return service.evaluate_manual_intent(
        context,
        bot_id="bot-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("0.01"),
        environment=Environment.TEST,
        risk_policy_version_id="risk-v1",
        snapshot=snapshot,
    )


def test_policy_registration_is_immutable_and_audited(session_factory: SessionFactory) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.RISK_MANAGE)
    original = service.register_policy(context, "risk-v1", _limits())

    with pytest.raises(RiskConflictError, match="already exists"):
        service.register_policy(
            context,
            "risk-v1",
            _limits(max_order_notional=Decimal("2000")),
        )

    assert service.get_policy(context, "risk-v1") == original
    with session_factory() as session:
        audits = BotRepository().list_audit_events(session, "tenant-a", "risk_policy", "risk-v1")
    assert [event.action for event in audits] == [AuditAction.RISK_POLICY_CHANGED]


def test_policy_and_kill_switch_are_tenant_scoped(session_factory: SessionFactory) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    tenant_a = _register_default(service, "tenant-a")
    tenant_b = _context("tenant-b", Permission.RISK_MANAGE)
    service.activate_kill_switch(tenant_a, Environment.TEST, "INCIDENT")

    with pytest.raises(RiskPolicyNotFoundError):
        service.get_policy(tenant_b, "risk-v1")
    assert service.get_kill_switch(tenant_b, Environment.TEST) is None


def test_risk_permissions_fail_closed(session_factory: SessionFactory) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    no_permissions = _context("tenant-a")

    with pytest.raises(PermissionDeniedError):
        service.register_policy(no_permissions, "risk-v1", _limits())

    manager = _context("tenant-a", Permission.RISK_MANAGE)
    service.register_policy(manager, "risk-v1", _limits())
    with pytest.raises(PermissionDeniedError):
        _evaluate(service, manager, _snapshot())

    trader = _context("tenant-a", Permission.TRADE_MANUAL_EXECUTE)
    with pytest.raises(PermissionDeniedError):
        service.activate_kill_switch(trader, Environment.TEST, "NOT_ALLOWED")


def test_passing_limits_produce_canonical_approved_execution_intent(
    session_factory: SessionFactory,
) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    context = _register_default(service)

    result = _evaluate(service, context, _snapshot())

    assert isinstance(result, ApprovedExecutionIntent)
    assert result.risk_decision.decision is RiskDecisionOutcome.APPROVED
    assert result.risk_decision.reason_codes == (RISK_APPROVED,)
    assert len(result.risk_decision.evaluated_limits) == 7
    assert all(item.passed for item in result.risk_decision.evaluated_limits)
    assert result.context.correlation_id == context.correlation_id

    intent_id = str(result.trade_intent.trade_intent_id)
    with session_factory() as session:
        audits = BotRepository().list_audit_events(
            session,
            "tenant-a",
            "trade_intent",
            intent_id,
        )
        events = BotRepository().list_outbox_events(
            session,
            "tenant-a",
            "trade_intent",
            intent_id,
        )
    assert len(audits) == 1
    assert audits[0].action is AuditAction.MANUAL_TRADE_INTENT
    assert audits[0].result is AuditResult.SUCCEEDED
    assert {event.event_type for event in events} == {
        EventType.TRADE_INTENT_CREATED,
        EventType.RISK_APPROVED,
    }


@pytest.mark.parametrize(
    ("snapshot", "reason_code"),
    [
        (_snapshot(intent_notional=Decimal("1000.01")), ORDER_NOTIONAL_LIMIT_EXCEEDED),
        (
            _snapshot(projected_gross_exposure=Decimal("5000.01")),
            GROSS_EXPOSURE_LIMIT_EXCEEDED,
        ),
        (_snapshot(projected_open_positions=6), OPEN_POSITION_LIMIT_EXCEEDED),
        (_snapshot(daily_loss=Decimal("500.01")), DAILY_LOSS_LIMIT_EXCEEDED),
        (_snapshot(current_drawdown=Decimal("0.21")), DRAWDOWN_LIMIT_EXCEEDED),
        (_snapshot(runtime_health=RuntimeHealthState.DEGRADED), RUNTIME_UNHEALTHY),
    ],
)
def test_each_deterministic_limit_fails_closed(
    session_factory: SessionFactory,
    snapshot: RiskEvaluationSnapshot,
    reason_code: str,
) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    context = _register_default(service)

    result = _evaluate(service, context, snapshot)

    assert isinstance(result, RejectedExecutionIntent)
    assert result.risk_decision.decision is RiskDecisionOutcome.REJECTED
    assert reason_code in result.risk_decision.reason_codes
    assert any(not item.passed for item in result.risk_decision.evaluated_limits)


def test_active_kill_switch_always_rejects_and_release_restores_evaluation(
    session_factory: SessionFactory,
) -> None:
    service = RiskService(session_factory, clock=lambda: NOW)
    context = _register_default(service)
    service.activate_kill_switch(context, Environment.TEST, "INCIDENT")

    rejected = _evaluate(service, context, _snapshot())
    assert isinstance(rejected, RejectedExecutionIntent)
    assert rejected.risk_decision.reason_codes[0] == KILL_SWITCH_ACTIVE

    released = service.release_kill_switch(context, Environment.TEST, "INCIDENT_RESOLVED")
    assert released.active is False
    approved = _evaluate(service, context, _snapshot())
    assert isinstance(approved, ApprovedExecutionIntent)


class _FailingOutboxRepository(RiskRepository):
    def add_outbox_event(self, session, event) -> None:
        raise RuntimeError("simulated outbox failure")


def test_outbox_failure_rolls_back_intent_decision_and_audit(
    session_factory: SessionFactory,
) -> None:
    normal_service = RiskService(session_factory, clock=lambda: NOW)
    context = _register_default(normal_service)
    repository = _FailingOutboxRepository()
    failing_service = RiskService(session_factory, repository=repository, clock=lambda: NOW)

    with pytest.raises(RuntimeError, match="simulated outbox failure"):
        _evaluate(failing_service, context, _snapshot())

    with session_factory() as session:
        decisions = repository.list_risk_decisions(session, "tenant-a")
        audits = BotRepository().list_audit_events(session, "tenant-a", "trade_intent")
        events = BotRepository().list_outbox_events(session, "tenant-a", "trade_intent")
    assert decisions == ()
    assert audits == ()
    assert events == ()
