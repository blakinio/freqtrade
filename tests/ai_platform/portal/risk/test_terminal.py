from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import OrderRecord, OrderState, RuntimeHealthState
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent, TradeSide
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory, build_engine, build_session_factory
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.risk.database import create_risk_schema
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.portal.risk.service import RiskService
from ai_platform.portal.risk.terminal import TerminalExecutionState, TerminalService


NOW = datetime(2026, 7, 22, 20, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_risk_schema(engine)
    return build_session_factory(engine)


def _context() -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(
            Permission.BOT_CREATE,
            Permission.BOT_READ,
            Permission.RISK_MANAGE,
            Permission.TRADE_MANUAL_EXECUTE,
        ),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _seed(session_factory: SessionFactory, context: RequestContext) -> None:
    ControlPlaneService(session_factory, clock=lambda: NOW).create_bot(
        context,
        "bot-1",
        "Terminal bot",
        BotSpec(
            tenant_id="tenant-a",
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation="1000",
            capital_currency="USDT",
            runtime_version="freqtrade-2026.7",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
    )
    RiskService(session_factory, clock=lambda: NOW).register_policy(
        context,
        "risk-v1",
        RiskPolicyLimits(
            max_order_notional="1000",
            max_projected_gross_exposure="5000",
            max_projected_open_positions=5,
            max_daily_loss="500",
            max_drawdown="0.20",
            require_healthy_runtime=True,
        ),
    )


class StaticSnapshotProvider:
    def __init__(self, intent_notional: str = "100") -> None:
        self.intent_notional = intent_notional

    def build_snapshot(self, context, bot, *, pair, side, amount) -> RiskEvaluationSnapshot:
        del context, bot, pair, side, amount
        return RiskEvaluationSnapshot(
            intent_notional=self.intent_notional,
            projected_gross_exposure="500",
            projected_open_positions=1,
            daily_loss="0",
            current_drawdown="0.01",
            runtime_health=RuntimeHealthState.HEALTHY,
        )


class RecordingSubmitter:
    def __init__(self) -> None:
        self.calls = 0

    def submit_approved_intent(self, intent: ApprovedExecutionIntent, context) -> OrderRecord:
        del context
        self.calls += 1
        return OrderRecord(
            tenant_id=intent.tenant_id,
            bot_id=intent.trade_intent.bot_id,
            order_id="order-1",
            execution_intent_id=str(intent.execution_intent_id),
            pair=intent.trade_intent.pair,
            side=intent.trade_intent.side,
            state=OrderState.SUBMITTED,
            amount=intent.trade_intent.amount,
            created_at=NOW,
        )


def test_terminal_uses_pinned_policy_and_fails_closed_when_submission_is_unavailable(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    _seed(session_factory, context)
    service = TerminalService(session_factory, snapshot_provider=StaticSnapshotProvider())

    result = service.submit_manual_intent(
        context,
        bot_id="bot-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("0.01"),
    )

    assert result.risk_decision.risk_policy_version == "risk-v1"
    assert result.execution_state is TerminalExecutionState.BLOCKED
    assert result.execution_reason_code == "ORDER_SUBMISSION_NOT_IMPLEMENTED"
    assert result.order is None


def test_rejected_intent_never_reaches_execution_submitter(session_factory: SessionFactory) -> None:
    context = _context()
    _seed(session_factory, context)
    submitter = RecordingSubmitter()
    service = TerminalService(
        session_factory,
        snapshot_provider=StaticSnapshotProvider(intent_notional="1500"),
        execution_submitter=submitter,
    )

    result = service.submit_manual_intent(
        context,
        bot_id="bot-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("0.01"),
    )

    assert result.execution_state is TerminalExecutionState.REJECTED
    assert result.execution_reason_code == "ORDER_NOTIONAL_LIMIT_EXCEEDED"
    assert submitter.calls == 0


def test_terminal_api_accepts_only_intent_fields_and_uses_server_side_snapshot(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    _seed(session_factory, context)
    submitter = RecordingSubmitter()
    terminal = TerminalService(
        session_factory,
        snapshot_provider=StaticSnapshotProvider(),
        execution_submitter=submitter,
    )
    client = TestClient(create_app(session_factory, lambda: context, terminal))

    injected = client.post(
        "/v1/terminal/intents",
        json={
            "bot_id": "bot-1",
            "pair": "BTC/USDT",
            "side": "BUY",
            "amount": "0.01",
            "snapshot": {"runtime_health": "HEALTHY"},
        },
    )
    response = client.post(
        "/v1/terminal/intents",
        json={"bot_id": "bot-1", "pair": "BTC/USDT", "side": "BUY", "amount": "0.01"},
    )

    assert injected.status_code == 422
    assert response.status_code == 200
    assert response.json()["execution_state"] == "SUBMITTED"
    assert response.json()["order"]["order_id"] == "order-1"
    assert submitter.calls == 1


def test_terminal_api_fails_closed_without_trusted_snapshot_provider(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    _seed(session_factory, context)
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.post(
        "/v1/terminal/intents",
        json={"bot_id": "bot-1", "pair": "BTC/USDT", "side": "BUY", "amount": "0.01"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "RISK_SNAPSHOT_UNAVAILABLE"
