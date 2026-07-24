from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    PositionReadResult,
    PrivateOrderRecord,
    PrivatePositionRecord,
    PrivateRuntimeSnapshot,
    PrivateTradeRecord,
    RuntimeReadFreshness,
    RuntimeReadKind,
    RuntimeReadReconciliationStatus,
    RuntimeReadStatus,
    TradeReadResult,
)
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.service import OperationalReadService
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 24, 6, 0, tzinfo=UTC)
TENANT = "tenant-a"
BOT = "bot-1"
RUNTIME = "runtime-a"


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str = TENANT, *permissions: Permission) -> RequestContext:
    selected = permissions or (Permission.BOT_READ,)
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.SERVICE,
        permissions=selected,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _create_bot(session_factory: SessionFactory) -> None:
    context = _context(TENANT, Permission.BOT_CREATE, Permission.BOT_READ)
    ControlPlaneService(session_factory).create_bot(
        context,
        BOT,
        "Runtime evidence bot",
        BotSpec(
            tenant_id=TENANT,
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency="USDT",
            runtime_version="runtime-v1",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
    )


def _status(
    kind: RuntimeReadKind,
    *,
    record_count: int,
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT,
    reconciliation: RuntimeReadReconciliationStatus = RuntimeReadReconciliationStatus.SYNCED,
    complete: bool = True,
    reason_code: str | None = None,
    source_observed_at: datetime | None = NOW,
) -> RuntimeReadStatus:
    return RuntimeReadStatus(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        kind=kind,
        source_observed_at=source_observed_at,
        observed_at=NOW,
        last_reconciled_at=NOW,
        freshness=freshness,
        reconciliation_status=reconciliation,
        complete=complete,
        record_count=record_count,
        reason_code=reason_code,
    )


def _position() -> PrivatePositionRecord:
    return PrivatePositionRecord(
        source_position_id="position-source-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("0.1"),
        opened_at=NOW - timedelta(minutes=10),
        source_updated_at=NOW,
    )


def _order(*, execution_intent_id: str | None = "intent-1") -> PrivateOrderRecord:
    return PrivateOrderRecord(
        source_order_id="order-source-1",
        source_trade_id="trade-source-1",
        execution_intent_id=execution_intent_id,
        pair="BTC/USDT",
        side=TradeSide.BUY,
        state="FILLED",
        amount=Decimal("0.1"),
        created_at=NOW - timedelta(minutes=10),
        source_updated_at=NOW,
    )


def _trade(*, complete_outcome: bool = True) -> PrivateTradeRecord:
    return PrivateTradeRecord(
        source_trade_id="trade-source-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        state="CLOSED",
        amount=Decimal("0.1"),
        opened_at=NOW - timedelta(minutes=10),
        closed_at=NOW - timedelta(minutes=1),
        realized_pnl=Decimal("4.2") if complete_outcome else None,
        fees=Decimal("0.1") if complete_outcome else None,
        exit_reason="roi" if complete_outcome else None,
        source_updated_at=NOW,
    )


def _snapshot(
    *,
    positions: tuple[PrivatePositionRecord, ...] = (_position(),),
    orders: tuple[PrivateOrderRecord, ...] = (_order(),),
    trades: tuple[PrivateTradeRecord, ...] = (_trade(),),
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT,
    reconciliation: RuntimeReadReconciliationStatus = RuntimeReadReconciliationStatus.SYNCED,
    complete: bool = True,
    reason_code: str | None = None,
    source_observed_at: datetime | None = NOW,
) -> PrivateRuntimeSnapshot:
    return PrivateRuntimeSnapshot(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        observed_at=NOW,
        positions=PositionReadResult(
            status=_status(
                RuntimeReadKind.OPEN_POSITIONS,
                record_count=len(positions),
                freshness=freshness,
                reconciliation=reconciliation,
                complete=complete,
                reason_code=reason_code,
                source_observed_at=source_observed_at,
            ),
            records=positions,
        ),
        orders=OrderReadResult(
            status=_status(
                RuntimeReadKind.ORDERS,
                record_count=len(orders),
                freshness=freshness,
                reconciliation=reconciliation,
                complete=complete,
                reason_code=reason_code,
                source_observed_at=source_observed_at,
            ),
            records=orders,
        ),
        trades=TradeReadResult(
            status=_status(
                RuntimeReadKind.TRADES,
                record_count=len(trades),
                freshness=freshness,
                reconciliation=reconciliation,
                complete=complete,
                reason_code=reason_code,
                source_observed_at=source_observed_at,
            ),
            records=trades,
        ),
    )


def test_reconciliation_is_idempotent_and_preserves_source_identity(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)
    context = _context()

    first = service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(),
        expected_runtime_id=RUNTIME,
    )
    second = service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(),
        expected_runtime_id=RUNTIME,
    )

    assert len(first.positions) == len(second.positions) == 1
    assert len(first.orders) == len(second.orders) == 1
    assert len(first.trades) == len(second.trades) == 1
    assert len(second.source_statuses) == 3
    assert first.positions[0].position_id == second.positions[0].position_id
    assert first.positions[0].source_position_id == "position-source-1"
    assert first.orders[0].source_order_id == "order-source-1"
    assert first.trades[0].source_trade_id == "trade-source-1"
    assert first.trades[0].source_updated_at == NOW
    assert all(
        status.reconciliation_status is ReconciliationStatus.SYNCED
        for status in second.source_statuses
    )


def test_source_unavailable_marks_existing_records_without_presenting_them_current(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)
    context = _context()
    service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(),
        expected_runtime_id=RUNTIME,
    )

    unavailable = _snapshot(
        positions=(),
        orders=(),
        trades=(),
        freshness=RuntimeReadFreshness.SOURCE_UNAVAILABLE,
        reconciliation=RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE,
        complete=False,
        reason_code="RUNTIME_READ_TIMEOUT",
        source_observed_at=None,
    )
    evidence = service.reconcile_private_runtime_snapshot(
        context,
        unavailable,
        expected_runtime_id=RUNTIME,
    )

    assert evidence.positions[0].freshness is RuntimeReadFreshness.SOURCE_UNAVAILABLE
    assert evidence.orders[0].reconciliation_status is ReconciliationStatus.SOURCE_UNAVAILABLE
    assert evidence.trades[0].reason_code == "RUNTIME_READ_TIMEOUT"
    assert all(status.complete is False for status in evidence.source_statuses)


def test_stale_and_partial_snapshots_remain_pending_not_synced(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)
    context = _context()

    stale = service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(
            freshness=RuntimeReadFreshness.STALE,
            reconciliation=RuntimeReadReconciliationStatus.PENDING,
            reason_code="RUNTIME_READ_SOURCE_STALE",
            source_observed_at=NOW - timedelta(minutes=5),
        ),
        expected_runtime_id=RUNTIME,
    )
    assert stale.positions[0].freshness is RuntimeReadFreshness.STALE
    assert stale.positions[0].reconciliation_status is ReconciliationStatus.PENDING

    partial = service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(
            positions=(),
            orders=(),
            trades=(),
            freshness=RuntimeReadFreshness.PARTIAL,
            reconciliation=RuntimeReadReconciliationStatus.PENDING,
            complete=False,
            reason_code="RUNTIME_READ_TIMEOUT",
        ),
        expected_runtime_id=RUNTIME,
    )
    assert partial.positions[0].freshness is RuntimeReadFreshness.PARTIAL
    assert partial.positions[0].reconciliation_status is ReconciliationStatus.PENDING


def test_complete_source_removes_absent_open_position_but_marks_missing_history_mismatch(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)
    context = _context()
    service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(),
        expected_runtime_id=RUNTIME,
    )

    evidence = service.reconcile_private_runtime_snapshot(
        context,
        _snapshot(positions=(), orders=(), trades=()),
        expected_runtime_id=RUNTIME,
    )

    assert evidence.positions == ()
    assert evidence.orders[0].reconciliation_status is ReconciliationStatus.MISMATCH
    assert evidence.orders[0].reason_code == "RUNTIME_SOURCE_RECORD_MISSING"
    assert evidence.trades[0].reconciliation_status is ReconciliationStatus.MISMATCH


def test_missing_order_attribution_and_incomplete_trade_outcome_are_mismatches(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)

    evidence = service.reconcile_private_runtime_snapshot(
        _context(),
        _snapshot(
            orders=(_order(execution_intent_id=None),),
            trades=(_trade(complete_outcome=False),),
        ),
        expected_runtime_id=RUNTIME,
    )

    assert evidence.orders[0].execution_intent_id is None
    assert evidence.orders[0].reconciliation_status is ReconciliationStatus.MISMATCH
    assert evidence.orders[0].reason_code == "RUNTIME_ORDER_ATTRIBUTION_MISSING"
    assert evidence.trades[0].reconciliation_status is ReconciliationStatus.MISMATCH
    assert evidence.trades[0].reason_code == "RUNTIME_TRADE_OUTCOME_INCOMPLETE"


def test_cross_tenant_and_cross_runtime_reconciliation_fail_closed(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)

    with pytest.raises(PermissionDeniedError, match="tenant scope"):
        service.reconcile_private_runtime_snapshot(
            _context("tenant-b"),
            _snapshot(),
            expected_runtime_id=RUNTIME,
        )
    with pytest.raises(PermissionDeniedError, match="runtime scope"):
        service.reconcile_private_runtime_snapshot(
            _context(),
            _snapshot(),
            expected_runtime_id="runtime-b",
        )


def test_runtime_evidence_api_exposes_freshness_without_private_transport_details(
    session_factory: SessionFactory,
) -> None:
    _create_bot(session_factory)
    service = OperationalReadService(session_factory)
    holder = {"context": _context()}
    service.reconcile_private_runtime_snapshot(
        holder["context"],
        _snapshot(),
        expected_runtime_id=RUNTIME,
    )
    client = TestClient(
        create_app(
            session_factory,
            lambda: holder["context"],
            operational_read_service=service,
        )
    )

    response = client.get("/v1/runtime-evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["positions"][0]["freshness"] == "CURRENT"
    assert payload["source_statuses"][0]["reconciliation_status"] == "SYNCED"
    serialized = response.text.lower()
    for forbidden in (
        "authorization",
        "api_key",
        "api_secret",
        "credential",
        "private_endpoint",
        "runtime_url",
        "password",
        "token",
    ):
        assert forbidden not in serialized

    holder["context"] = _context("tenant-b")
    other_tenant = client.get("/v1/runtime-evidence")
    assert other_tenant.status_code == 200
    assert other_tenant.json() == {
        "positions": [],
        "orders": [],
        "trades": [],
        "source_statuses": [],
    }

    openapi = json_text = str(client.get("/openapi.json").json()).lower()
    assert "/v1/runtime-evidence" in openapi
    assert "private_endpoint" not in json_text
    assert "authorization" not in json_text
