from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.funding import FundingEvent
from ai_platform.portal.simulator.gap_stop import GapStopModel
from ai_platform.portal.simulator.latency import LatencyModel, SimulationLatencyError
from ai_platform.portal.simulator.schema import MarketTick, ScenarioManifest


def _time(minute: int, second: int = 0) -> datetime:
    return datetime(2026, 7, 30, 10, minute, second, tzinfo=UTC)


def _manifest(
    *,
    side: TradeSide = TradeSide.BUY,
    entry_price: str = "100",
    exit_price: str = "110",
    latency_model: LatencyModel | None = None,
    gap_stop_model: GapStopModel | None = None,
    funding_events: tuple[FundingEvent, ...] = (),
    market_ticks: tuple[MarketTick, ...] = (),
) -> ScenarioManifest:
    return ScenarioManifest(
        scenario_id=f"fidelity-{side.value.lower()}",
        tenant_id="tenant-simulator",
        bot_id="bot-simulator",
        pair="BTC/USDT",
        side=side,
        amount="1",
        environment=Environment.TEST,
        initial_equity="1000",
        entry_tick=MarketTick(occurred_at=_time(0), pair="BTC/USDT", price=entry_price),
        exit_tick=MarketTick(occurred_at=_time(5), pair="BTC/USDT", price=exit_price),
        latency_model=latency_model or LatencyModel(),
        gap_stop_model=gap_stop_model or GapStopModel(),
        funding_events=funding_events,
        market_ticks=market_ticks,
    )


def _simulator(manifest: ScenarioManifest) -> DeterministicExchangeSimulator:
    context = CorrelationContext(
        request_id=UUID("10000000-0000-4000-8000-000000000001"),
        correlation_id=UUID("10000000-0000-4000-8000-000000000002"),
    )
    intent = SimpleNamespace(
        trade_intent=SimpleNamespace(
            tenant_id=manifest.tenant_id,
            bot_id=manifest.bot_id,
            pair=manifest.pair,
            environment=manifest.environment,
            side=manifest.side,
            amount=manifest.amount,
        ),
        execution_intent_id=UUID("10000000-0000-4000-8000-000000000003"),
    )
    simulator = DeterministicExchangeSimulator(manifest)
    simulator.submit_approved_intent(intent, context)
    return simulator


def test_latency_uses_first_tick_at_or_after_scenario_ready_time() -> None:
    manifest = _manifest(
        latency_model=LatencyModel(entry_delay_ms=500, exit_delay_ms=500),
        market_ticks=(
            MarketTick(occurred_at=_time(0, 1), pair="BTC/USDT", price="101"),
            MarketTick(occurred_at=_time(5, 1), pair="BTC/USDT", price="109"),
        ),
    )

    simulator = _simulator(manifest)
    outcome = simulator.close_position()
    evidence = simulator.evidence()

    assert outcome.opened_at == _time(0, 1)
    assert outcome.closed_at == _time(5, 1)
    assert evidence.entry_latency.ready_at == datetime(2026, 7, 30, 10, 0, 0, 500_000, tzinfo=UTC)
    assert evidence.entry_latency.delay_ms == 500
    assert evidence.costs.entry_market_price == Decimal("101")
    assert evidence.costs.exit_market_price == Decimal("109")


def test_latency_fails_closed_when_no_tick_exists_after_ready_time() -> None:
    simulator = _simulator(_manifest(latency_model=LatencyModel(exit_delay_ms=1)))

    with pytest.raises(SimulationLatencyError, match="latency-ready time"):
        simulator.close_position()


def test_positive_funding_is_paid_by_long_and_received_by_short() -> None:
    event = FundingEvent(occurred_at=_time(3), rate="0.01")

    long_simulator = _simulator(_manifest(funding_events=(event,)))
    assert long_simulator.close_position().realized_pnl == Decimal("9")
    assert long_simulator.evidence().funding_cash_flow == Decimal("-1")

    short_simulator = _simulator(
        _manifest(
            side=TradeSide.SELL,
            entry_price="100",
            exit_price="90",
            funding_events=(event,),
        )
    )
    assert short_simulator.close_position().realized_pnl == Decimal("11")
    assert short_simulator.evidence().funding_cash_flow == Decimal("1")


def test_gap_through_stop_fills_at_observed_adverse_price() -> None:
    simulator = _simulator(
        _manifest(
            gap_stop_model=GapStopModel(stop_price="95"),
            market_ticks=(
                MarketTick(occurred_at=_time(1), pair="BTC/USDT", price="99"),
                MarketTick(occurred_at=_time(2), pair="BTC/USDT", price="90"),
            ),
        )
    )

    outcome = simulator.close_position()
    evidence = simulator.evidence()

    assert outcome.exit_reason == "gap_through_stop"
    assert outcome.closed_at == _time(2)
    assert evidence.stop_resolution.triggered is True
    assert evidence.stop_resolution.observed_price == Decimal("90")
    assert evidence.costs.exit_market_price == Decimal("90")
    assert outcome.realized_pnl == Decimal("-10")


@pytest.mark.parametrize(
    ("side", "exit_price"),
    [(TradeSide.BUY, "110"), (TradeSide.SELL, "90")],
)
def test_invalid_stop_placement_fails_closed(
    side: TradeSide,
    exit_price: str,
) -> None:
    with pytest.raises(ValidationError, match="stop price"):
        _manifest(
            side=side,
            exit_price=exit_price,
            gap_stop_model=GapStopModel(stop_price="100"),
        )
