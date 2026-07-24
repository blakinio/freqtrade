from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.bots import (
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import OrderState, TradeState
from ai_platform.portal.execution.adapter import FreqtradeExecutionAdapter
from ai_platform.portal.execution.errors import (
    RuntimeNotProvisionedError,
    RuntimeReadIsolationError,
    RuntimeReadProtocolError,
    RuntimeReadTimeoutError,
    RuntimeReadUnavailableError,
    UnsupportedExecutionOperationError,
)
from ai_platform.portal.execution.private_read import (
    HttpPrivateRuntimeTransport,
    PrivateRuntimeCollector,
    PrivateRuntimePage,
    RuntimeReadFreshness,
    RuntimeReadKind,
    RuntimeReadReconciliationStatus,
    RuntimeReadRequest,
)
from ai_platform.portal.execution.runtime import (
    DriverRuntimeState,
    ResolvedRuntimeArtifacts,
    RuntimeContainerSpec,
)
from ai_platform.portal.execution.workspace import RuntimeWorkspaceStore


NOW = datetime(2026, 7, 24, 6, 0, tzinfo=UTC)
TENANT = "tenant-a"
BOT = "bot-a"
RUNTIME = "runtime-a"


def _position(source_id: str = "position-1", amount: str = "0.1") -> dict[str, Any]:
    return {
        "source_position_id": source_id,
        "pair": "BTC/USDT",
        "side": "BUY",
        "amount": amount,
        "opened_at": (NOW - timedelta(minutes=10)).isoformat(),
        "source_updated_at": NOW.isoformat(),
    }


def _order(source_id: str = "order-1") -> dict[str, Any]:
    return {
        "source_order_id": source_id,
        "source_trade_id": "trade-1",
        "execution_intent_id": "intent-1",
        "pair": "BTC/USDT",
        "side": "BUY",
        "state": "FILLED",
        "amount": "0.1",
        "created_at": (NOW - timedelta(minutes=10)).isoformat(),
        "source_updated_at": NOW.isoformat(),
    }


def _trade(source_id: str = "trade-1") -> dict[str, Any]:
    return {
        "source_trade_id": source_id,
        "pair": "BTC/USDT",
        "side": "BUY",
        "state": "CLOSED",
        "amount": "0.1",
        "opened_at": (NOW - timedelta(minutes=10)).isoformat(),
        "closed_at": (NOW - timedelta(minutes=1)).isoformat(),
        "realized_pnl": "4.2",
        "fees": "0.1",
        "exit_reason": "roi",
        "source_updated_at": NOW.isoformat(),
    }


def _page(
    kind: RuntimeReadKind,
    records: tuple[dict[str, Any], ...],
    *,
    cursor: str | None = None,
    complete: bool = True,
    tenant_id: str = TENANT,
    bot_id: str = BOT,
    runtime_id: str = RUNTIME,
    source_observed_at: datetime = NOW,
) -> PrivateRuntimePage:
    return PrivateRuntimePage(
        tenant_id=tenant_id,
        bot_id=bot_id,
        source_runtime_id=runtime_id,
        kind=kind,
        source_observed_at=source_observed_at,
        records=records,
        next_cursor=cursor,
        complete=complete,
    )


class _Transport:
    def __init__(self, responses: dict[tuple[RuntimeReadKind, str | None], object]) -> None:
        self.responses = responses
        self.calls: list[RuntimeReadRequest] = []

    def fetch_page(self, request: RuntimeReadRequest) -> PrivateRuntimePage:
        self.calls.append(request)
        response = self.responses[(request.kind, request.cursor)]
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, PrivateRuntimePage):
            raise TypeError("fake transport response must be a private runtime page")
        return response


class _SequenceTransport:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def fetch_page(self, request: RuntimeReadRequest) -> PrivateRuntimePage:
        del request
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, PrivateRuntimePage):
            raise TypeError("fake transport response must be a private runtime page")
        return response


def test_collector_handles_pagination_and_identical_duplicates_idempotently() -> None:
    transport = _Transport(
        {
            (RuntimeReadKind.OPEN_POSITIONS, None): _page(
                RuntimeReadKind.OPEN_POSITIONS,
                (_position("position-1"),),
                cursor="page-2",
                complete=False,
            ),
            (RuntimeReadKind.OPEN_POSITIONS, "page-2"): _page(
                RuntimeReadKind.OPEN_POSITIONS,
                (_position("position-1"), _position("position-2")),
            ),
        }
    )
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW, sleeper=lambda _: None)

    result = collector.collect_positions(TENANT, BOT, RUNTIME)

    assert result.status.complete is True
    assert result.status.freshness is RuntimeReadFreshness.CURRENT
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.SYNCED
    assert [record.source_position_id for record in result.records] == [
        "position-1",
        "position-2",
    ]
    assert len(transport.calls) == 2


def test_collector_retries_timeout_then_maps_source_unavailable() -> None:
    transport = _SequenceTransport(
        [RuntimeReadTimeoutError(), RuntimeReadTimeoutError(), RuntimeReadTimeoutError()]
    )
    collector = PrivateRuntimeCollector(
        transport,
        clock=lambda: NOW,
        sleeper=lambda _: None,
        max_retries=2,
    )

    result = collector.collect_orders(TENANT, BOT, RUNTIME)

    assert transport.calls == 3
    assert result.records == ()
    assert result.status.freshness is RuntimeReadFreshness.SOURCE_UNAVAILABLE
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE
    assert result.status.reason_code == "RUNTIME_READ_TIMEOUT"


def test_collector_does_not_retry_authentication_failure() -> None:
    from ai_platform.portal.execution.errors import RuntimeReadAuthenticationError

    transport = _SequenceTransport([RuntimeReadAuthenticationError()])
    collector = PrivateRuntimeCollector(
        transport,
        clock=lambda: NOW,
        sleeper=lambda _: None,
        max_retries=3,
    )

    result = collector.collect_trades(TENANT, BOT, RUNTIME)

    assert transport.calls == 1
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE
    assert result.status.reason_code == "RUNTIME_READ_AUTHENTICATION_FAILED"


def test_collector_marks_stale_complete_source_pending() -> None:
    transport = _Transport(
        {
            (RuntimeReadKind.TRADES, None): _page(
                RuntimeReadKind.TRADES,
                (_trade(),),
                source_observed_at=NOW - timedelta(minutes=3),
            )
        }
    )
    collector = PrivateRuntimeCollector(
        transport,
        clock=lambda: NOW,
        stale_after_seconds=120,
    )

    result = collector.collect_trades(TENANT, BOT, RUNTIME)

    assert result.status.complete is True
    assert result.status.freshness is RuntimeReadFreshness.STALE
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.PENDING
    assert result.status.reason_code == "RUNTIME_READ_SOURCE_STALE"


def test_partial_page_failure_never_reports_synced() -> None:
    transport = _Transport(
        {
            (RuntimeReadKind.ORDERS, None): _page(
                RuntimeReadKind.ORDERS,
                (_order("order-1"),),
                cursor="page-2",
                complete=False,
            ),
            (RuntimeReadKind.ORDERS, "page-2"): RuntimeReadTimeoutError(),
        }
    )
    collector = PrivateRuntimeCollector(
        transport,
        clock=lambda: NOW,
        sleeper=lambda _: None,
        max_retries=0,
    )

    result = collector.collect_orders(TENANT, BOT, RUNTIME)

    assert len(result.records) == 1
    assert result.status.complete is False
    assert result.status.freshness is RuntimeReadFreshness.PARTIAL
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.PENDING
    assert result.status.reason_code == "RUNTIME_READ_TIMEOUT"


def test_conflicting_duplicate_is_mismatch() -> None:
    transport = _Transport(
        {
            (RuntimeReadKind.OPEN_POSITIONS, None): _page(
                RuntimeReadKind.OPEN_POSITIONS,
                (_position(amount="0.1"), _position(amount="0.2")),
            )
        }
    )
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW)

    result = collector.collect_positions(TENANT, BOT, RUNTIME)

    assert len(result.records) == 1
    assert result.status.reconciliation_status is RuntimeReadReconciliationStatus.MISMATCH
    assert result.status.reason_code == "RUNTIME_READ_DUPLICATE_MISMATCH"


@pytest.mark.parametrize(
    ("tenant_id", "runtime_id"),
    [("tenant-b", RUNTIME), (TENANT, "runtime-b")],
)
def test_cross_tenant_or_runtime_page_fails_closed(
    tenant_id: str,
    runtime_id: str,
) -> None:
    transport = _Transport(
        {
            (RuntimeReadKind.OPEN_POSITIONS, None): _page(
                RuntimeReadKind.OPEN_POSITIONS,
                (_position(),),
                tenant_id=tenant_id,
                runtime_id=runtime_id,
            )
        }
    )
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW)

    with pytest.raises(RuntimeReadIsolationError):
        collector.collect_positions(TENANT, BOT, RUNTIME)


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback

    def read(self, amount: int = -1) -> bytes:
        return self.payload[:amount] if amount >= 0 else self.payload


def _request() -> RuntimeReadRequest:
    return RuntimeReadRequest(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        kind=RuntimeReadKind.ORDERS,
        page_size=100,
        timeout_seconds=5,
    )


def test_http_transport_redacts_secret_payload_and_error_details() -> None:
    def opener(_request: object, timeout: int) -> _Response:
        assert timeout == 5
        return _Response(
            {
                "schema_version": 1,
                "tenant_id": TENANT,
                "bot_id": BOT,
                "source_runtime_id": RUNTIME,
                "kind": "ORDERS",
                "source_observed_at": NOW.isoformat(),
                "records": [{**_order(), "api_key": "do-not-serialize"}],
                "next_cursor": None,
                "complete": True,
            }
        )

    transport = HttpPrivateRuntimeTransport(
        lambda _runtime, _kind: "https://private-runtime.invalid/read",
        lambda _runtime: {"Authorization": "Bearer private-token"},
        opener=opener,
    )

    with pytest.raises(RuntimeReadProtocolError) as exc_info:
        transport.fetch_page(_request())

    serialized_error = str(exc_info.value)
    assert serialized_error == "RUNTIME_READ_INVALID_PAYLOAD"
    assert "private-runtime.invalid" not in serialized_error
    assert "private-token" not in serialized_error
    assert "do-not-serialize" not in serialized_error


def test_http_transport_maps_authentication_without_leaking_endpoint() -> None:
    def opener(_request: object, timeout: int) -> _Response:
        del timeout
        raise HTTPError(
            "https://private-runtime.invalid/read",
            401,
            "Unauthorized private-token",
            hdrs=None,
            fp=None,
        )

    transport = HttpPrivateRuntimeTransport(
        lambda _runtime, _kind: "https://private-runtime.invalid/read",
        lambda _runtime: {"Authorization": "Bearer private-token"},
        opener=opener,
    )

    from ai_platform.portal.execution.errors import RuntimeReadAuthenticationError

    with pytest.raises(RuntimeReadAuthenticationError) as exc_info:
        transport.fetch_page(_request())
    assert str(exc_info.value) == "RUNTIME_READ_AUTHENTICATION_FAILED"


class _Resolver:
    def resolve(self, bot: BotInstance) -> ResolvedRuntimeArtifacts:
        del bot
        return ResolvedRuntimeArtifacts(
            image="freqtradeorg/freqtrade:stable",
            strategy_name="PortalStrategy",
            base_config={"exchange": {"name": "binance"}},
        )


class _Driver:
    def __init__(self) -> None:
        self.states: dict[str, DriverRuntimeState] = {}

    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:
        return self.states.setdefault(spec.runtime_id, DriverRuntimeState.CREATED)

    def start(self, runtime_id: str) -> DriverRuntimeState:
        self.states[runtime_id] = DriverRuntimeState.RUNNING
        return self.states[runtime_id]

    def pause(self, runtime_id: str) -> DriverRuntimeState:
        self.states[runtime_id] = DriverRuntimeState.PAUSED
        return self.states[runtime_id]

    def stop(self, runtime_id: str) -> DriverRuntimeState:
        self.states[runtime_id] = DriverRuntimeState.STOPPED
        return self.states[runtime_id]

    def inspect(self, runtime_id: str) -> DriverRuntimeState:
        return self.states.get(runtime_id, DriverRuntimeState.MISSING)


def _bot(tenant_id: str = TENANT) -> BotInstance:
    return BotInstance(
        bot_id=BOT,
        tenant_id=tenant_id,
        name="Runtime read bot",
        spec=BotSpec(
            tenant_id=tenant_id,
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
        desired_state=BotDesiredState.CREATED,
        observed_state=BotObservedState.CREATED,
    )


def _context() -> CorrelationContext:
    return CorrelationContext(
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _adapter(
    tmp_path: Path,
    collector: PrivateRuntimeCollector | None,
) -> tuple[FreqtradeExecutionAdapter, _Driver, str]:
    driver = _Driver()
    store = RuntimeWorkspaceStore(tmp_path)
    adapter = FreqtradeExecutionAdapter(
        driver,
        _Resolver(),
        store,
        clock=lambda: NOW,
        private_read_collector=collector,
    )
    status = adapter.provision_bot(_bot(), _context())
    return adapter, driver, status.runtime_id


def _all_read_transport(runtime_id: str) -> _Transport:
    return _Transport(
        {
            (RuntimeReadKind.OPEN_POSITIONS, None): _page(
                RuntimeReadKind.OPEN_POSITIONS,
                (_position(),),
                runtime_id=runtime_id,
            ),
            (RuntimeReadKind.ORDERS, None): _page(
                RuntimeReadKind.ORDERS,
                (_order(),),
                runtime_id=runtime_id,
            ),
            (RuntimeReadKind.TRADES, None): _page(
                RuntimeReadKind.TRADES,
                (_trade(),),
                runtime_id=runtime_id,
            ),
        }
    )


def test_adapter_read_success_and_submission_remains_fail_closed(tmp_path: Path) -> None:
    provisional, driver, runtime_id = _adapter(tmp_path, None)
    transport = _all_read_transport(runtime_id)
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW)
    adapter = FreqtradeExecutionAdapter(
        driver,
        _Resolver(),
        RuntimeWorkspaceStore(tmp_path),
        clock=lambda: NOW,
        private_read_collector=collector,
    )
    driver.states[runtime_id] = DriverRuntimeState.RUNNING

    positions = adapter.get_open_positions(TENANT, BOT, _context())
    orders = adapter.get_orders(TENANT, BOT, _context())
    trades = adapter.get_trades(TENANT, BOT, _context())

    assert positions[0].position_id == "position-1"
    assert orders[0].order_id == "order-1"
    assert orders[0].state is OrderState.FILLED
    assert trades[0].trade_id == "trade-1"
    assert trades[0].state is TradeState.CLOSED
    with pytest.raises(UnsupportedExecutionOperationError) as exc_info:
        adapter.submit_approved_intent(
            object(),  # type: ignore[arg-type]
            _context(),
        )
    assert exc_info.value.reason_code == "ORDER_SUBMISSION_NOT_IMPLEMENTED"
    del provisional


def test_adapter_missing_collector_and_stopped_runtime_fail_closed(tmp_path: Path) -> None:
    adapter, driver, runtime_id = _adapter(tmp_path, None)

    with pytest.raises(RuntimeReadUnavailableError, match="COLLECTOR_NOT_CONFIGURED"):
        adapter.get_open_positions(TENANT, BOT, _context())

    transport = _all_read_transport(runtime_id)
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW)
    adapter_with_collector = FreqtradeExecutionAdapter(
        driver,
        _Resolver(),
        RuntimeWorkspaceStore(tmp_path),
        clock=lambda: NOW,
        private_read_collector=collector,
    )
    driver.states[runtime_id] = DriverRuntimeState.STOPPED
    with pytest.raises(RuntimeReadUnavailableError, match="RUNTIME_STOPPED"):
        adapter_with_collector.get_trades(TENANT, BOT, _context())
    assert transport.calls == []


def test_adapter_cross_tenant_read_is_denied_before_transport(tmp_path: Path) -> None:
    _adapter_instance, driver, runtime_id = _adapter(tmp_path, None)
    transport = _all_read_transport(runtime_id)
    collector = PrivateRuntimeCollector(transport, clock=lambda: NOW)
    adapter = FreqtradeExecutionAdapter(
        driver,
        _Resolver(),
        RuntimeWorkspaceStore(tmp_path),
        clock=lambda: NOW,
        private_read_collector=collector,
    )
    driver.states[runtime_id] = DriverRuntimeState.RUNNING

    with pytest.raises(RuntimeNotProvisionedError):
        adapter.get_orders("tenant-b", BOT, _context())
    assert transport.calls == []
