from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import OperationalPosition
from ai_platform.portal.security.authorization import PermissionDeniedError
from ai_platform.portal.valuation.runtime import (
    HttpPrivateRuntimeValuationSource,
    RuntimePositionMark,
    RuntimeValuationRequest,
    RuntimeValuationSourceResult,
    UnavailableRuntimeValuationSource,
    ValuationService,
    ValuationState,
)


NOW = datetime(2026, 7, 24, 18, 0, tzinfo=UTC)
TENANT = "tenant-a"
BOT = "bot-1"
RUNTIME = "runtime-1"


def _context(tenant_id: str = TENANT) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.SERVICE,
        permissions=(Permission.BOT_READ,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _seed(factory: Any, *, side: TradeSide = TradeSide.BUY, currency: str = "USDT") -> None:
    create_context = _context().model_copy(
        update={"permissions": (Permission.BOT_CREATE, Permission.BOT_READ)}
    )
    ControlPlaneService(factory).create_bot(
        create_context,
        BOT,
        "Valuation bot",
        BotSpec(
            tenant_id=TENANT,
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency=currency,
            runtime_version="runtime-v1",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
    )
    position = OperationalPosition(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        position_id="position-1",
        source_position_id="source-position-1",
        pair="BTC/USDT",
        side=side,
        amount=Decimal("2"),
        opened_at=NOW - timedelta(hours=1),
        source_updated_at=NOW,
        observed_at=NOW,
        last_reconciled_at=NOW,
        freshness=RuntimeReadFreshness.CURRENT,
        reconciliation_status=ReconciliationStatus.SYNCED,
    )
    with factory() as session, session.begin():
        OperationalRepository().upsert_position(session, position)


class _Source:
    def __init__(self, result: RuntimeValuationSourceResult) -> None:
        self.result = result
        self.requests: list[RuntimeValuationRequest] = []

    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult:
        self.requests.append(request)
        return self.result


def _mark(
    *,
    rate: str = "110",
    leverage: str = "1",
    quote: str = "USDT",
    side: TradeSide = TradeSide.BUY,
    observed_at: datetime = NOW,
) -> RuntimePositionMark:
    return RuntimePositionMark(
        source_position_id="source-position-1",
        pair="BTC/USDT",
        side=side,
        base_currency="BTC",
        quote_currency=quote,
        entry_rate=Decimal("100"),
        mark_rate=Decimal(rate),
        leverage=Decimal(leverage),
        source_price_id="freqtrade:runtime-1:BTC-USDT:1",
        source_observed_at=observed_at,
    )


def _result(
    *marks: RuntimePositionMark,
    state: ValuationState = ValuationState.CURRENT,
) -> RuntimeValuationSourceResult:
    return RuntimeValuationSourceResult(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        observed_at=NOW,
        state=state,
        marks=marks,
        reason_code=None if state is ValuationState.CURRENT else "VALUATION_SOURCE_UNAVAILABLE",
    )


def test_current_long_and_short_mark_to_entry_are_deterministic() -> None:
    factory = _factory()
    _seed(factory)
    source = _Source(_result(_mark()))

    long_value = ValuationService(factory, source, clock=lambda: NOW).list_valuations(_context())[0]

    assert source.requests[0].source_runtime_id == RUNTIME
    assert long_value.state is ValuationState.CURRENT
    assert long_value.cost_basis == Decimal("200")
    assert long_value.market_value == Decimal("220")
    assert long_value.unrealized_pnl == Decimal("20")
    assert long_value.valuation_currency == "USDT"
    assert long_value.source_price_id == "freqtrade:runtime-1:BTC-USDT:1"

    short_factory = _factory()
    _seed(short_factory, side=TradeSide.SELL)
    short_value = ValuationService(
        short_factory,
        _Source(_result(_mark(rate="90", side=TradeSide.SELL))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]

    assert short_value.unrealized_pnl == Decimal("20")
    assert short_value.method_version == "mark-to-entry-v1"


def test_stale_cross_currency_and_leverage_never_produce_numeric_value() -> None:
    factory = _factory()
    _seed(factory)

    stale = ValuationService(
        factory,
        _Source(_result(_mark(observed_at=NOW - timedelta(minutes=3)))),
        clock=lambda: NOW,
        stale_after_seconds=120,
    ).list_valuations(_context())[0]
    assert stale.state is ValuationState.STALE
    assert stale.unrealized_pnl is None

    cross_currency = ValuationService(
        factory,
        _Source(_result(_mark(quote="EUR"))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert cross_currency.state is ValuationState.UNPRICED
    assert cross_currency.reason_code == "VALUATION_CURRENCY_CONVERSION_UNAVAILABLE"
    assert cross_currency.market_value is None

    leveraged = ValuationService(
        factory,
        _Source(_result(_mark(leverage="2"))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert leveraged.state is ValuationState.UNPRICED
    assert leveraged.reason_code == "VALUATION_LEVERAGE_UNSUPPORTED"
    assert leveraged.unrealized_pnl is None


def test_unconfigured_source_and_cross_tenant_scope_fail_closed() -> None:
    factory = _factory()
    _seed(factory)

    unavailable = ValuationService(
        factory,
        UnavailableRuntimeValuationSource(NOW),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert unavailable.state is ValuationState.SOURCE_UNAVAILABLE
    assert unavailable.unrealized_pnl is None

    mismatched = _result(_mark()).model_copy(update={"tenant_id": "tenant-b"})
    with pytest.raises(PermissionDeniedError, match="scope mismatch"):
        ValuationService(factory, _Source(mismatched), clock=lambda: NOW).list_valuations(
            _context()
        )

    assert (
        ValuationService(factory, _Source(_result(_mark())), clock=lambda: NOW).list_valuations(
            _context("tenant-b")
        )
        == ()
    )


class _Response:
    def __init__(self, payload: object | bytes) -> None:
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback

    def read(self, amount: int = -1) -> bytes:
        return self.payload if amount < 0 else self.payload[:amount]


def _request() -> RuntimeValuationRequest:
    return RuntimeValuationRequest(
        tenant_id=TENANT,
        bot_id=BOT,
        source_runtime_id=RUNTIME,
        timeout_seconds=5,
    )


def _payload() -> dict[str, object]:
    return _result(_mark()).model_dump(mode="json")


def test_http_source_enforces_timeout_body_limit_and_secret_rejection() -> None:
    seen_timeout: list[int] = []

    def opener(_request: object, timeout: int) -> _Response:
        seen_timeout.append(timeout)
        return _Response(_payload())

    source = HttpPrivateRuntimeValuationSource(
        lambda _runtime: "https://private-runtime.invalid/valuation",
        lambda _runtime: {"Authorization": "Bearer hidden"},
        opener=opener,
        clock=lambda: NOW,
    )

    result = source.fetch(_request())

    assert seen_timeout == [5]
    assert result.state is ValuationState.CURRENT
    assert result.marks[0].mark_rate == Decimal("110")

    oversized = HttpPrivateRuntimeValuationSource(
        lambda _runtime: "https://private-runtime.invalid/valuation",
        lambda _runtime: {},
        opener=lambda _request, timeout: _Response(b"x" * 17),
        max_body_bytes=16,
        clock=lambda: NOW,
    ).fetch(_request())
    assert oversized.state is ValuationState.SOURCE_UNAVAILABLE
    assert oversized.reason_code == "VALUATION_SOURCE_PROTOCOL_ERROR"

    secret_payload = _payload()
    secret_payload["api_key"] = "must-not-pass"
    rejected = HttpPrivateRuntimeValuationSource(
        lambda _runtime: "https://private-runtime.invalid/valuation",
        lambda _runtime: {},
        opener=lambda _request, timeout: _Response(secret_payload),
        clock=lambda: NOW,
    ).fetch(_request())
    assert rejected.state is ValuationState.SOURCE_UNAVAILABLE
    assert rejected.reason_code == "VALUATION_SOURCE_PROTOCOL_ERROR"


def test_http_source_maps_auth_failure_without_leaking_details() -> None:
    def opener(_request: object, timeout: int) -> _Response:
        del timeout
        raise HTTPError(
            "https://private-runtime.invalid/valuation",
            401,
            "Bearer hidden",
            hdrs=None,
            fp=None,
        )

    result = HttpPrivateRuntimeValuationSource(
        lambda _runtime: "https://private-runtime.invalid/valuation",
        lambda _runtime: {"Authorization": "Bearer hidden"},
        opener=opener,
        clock=lambda: NOW,
    ).fetch(_request())

    assert result.state is ValuationState.SOURCE_UNAVAILABLE
    assert result.reason_code == "VALUATION_SOURCE_AUTHENTICATION_FAILED"
    serialized = result.canonical_json()
    assert "private-runtime.invalid" not in serialized
    assert "Bearer hidden" not in serialized
