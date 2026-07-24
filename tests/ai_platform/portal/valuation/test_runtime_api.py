from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory, create_schema
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import OperationalPosition
from ai_platform.portal.valuation.runtime import (
    RuntimePositionMark,
    RuntimeValuationRequest,
    RuntimeValuationSourceResult,
    ValuationService,
    ValuationState,
)


NOW = datetime(2026, 7, 24, 18, 0, tzinfo=UTC)


def _context(tenant_id: str) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.SERVICE,
        permissions=(Permission.BOT_READ,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


class _Source:
    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult:
        return RuntimeValuationSourceResult(
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            source_runtime_id=request.source_runtime_id,
            observed_at=NOW,
            state=ValuationState.CURRENT,
            marks=(
                RuntimePositionMark(
                    source_position_id="source-position-1",
                    pair="BTC/USDT",
                    side=TradeSide.BUY,
                    base_currency="BTC",
                    quote_currency="USDT",
                    entry_rate=Decimal("100"),
                    mark_rate=Decimal("110"),
                    source_price_id="freqtrade:runtime-1:BTC-USDT:1",
                    source_observed_at=NOW,
                ),
            ),
        )


def test_valuations_api_returns_attributed_current_value_without_secrets() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = build_session_factory(engine)
    create_context = _context("tenant-a").model_copy(
        update={"permissions": (Permission.BOT_CREATE, Permission.BOT_READ)}
    )
    ControlPlaneService(factory).create_bot(
        create_context,
        "bot-1",
        "Valuation bot",
        BotSpec(
            tenant_id="tenant-a",
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
    with factory() as session, session.begin():
        OperationalRepository().upsert_position(
            session,
            OperationalPosition(
                tenant_id="tenant-a",
                bot_id="bot-1",
                source_runtime_id="runtime-1",
                position_id="position-1",
                source_position_id="source-position-1",
                pair="BTC/USDT",
                side=TradeSide.BUY,
                amount=Decimal("2"),
                opened_at=NOW - timedelta(hours=1),
                source_updated_at=NOW,
                observed_at=NOW,
                last_reconciled_at=NOW,
                freshness=RuntimeReadFreshness.CURRENT,
                reconciliation_status=ReconciliationStatus.SYNCED,
            ),
        )

    holder = {"context": _context("tenant-a")}
    client = TestClient(
        create_app(
            factory,
            lambda: holder["context"],
            valuation_service=ValuationService(factory, _Source(), clock=lambda: NOW),
        )
    )

    response = client.get("/v1/valuations")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["state"] == "CURRENT"
    assert payload[0]["unrealized_pnl"] == "20"
    assert payload[0]["source_price_id"] == "freqtrade:runtime-1:BTC-USDT:1"
    for forbidden in ("authorization", "password", "api_key", "api_secret", "endpoint"):
        assert forbidden not in response.text.lower()

    holder["context"] = _context("tenant-b")
    assert client.get("/v1/valuations").json() == []
