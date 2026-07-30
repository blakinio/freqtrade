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
from ai_platform.portal.simulator.costs import ExecutionCostModel
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.schema import MarketTick, ScenarioManifest


def _manifest(*, cost_model: ExecutionCostModel | None = None) -> ScenarioManifest:
    return ScenarioManifest(
        scenario_id="costs-001",
        tenant_id="tenant-simulator",
        bot_id="bot-simulator",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount="2",
        environment=Environment.TEST,
        initial_equity="1000",
        entry_tick=MarketTick(
            occurred_at=datetime(2026, 7, 30, 10, 0, tzinfo=UTC),
            pair="BTC/USDT",
            price="100",
        ),
        exit_tick=MarketTick(
            occurred_at=datetime(2026, 7, 30, 10, 5, tzinfo=UTC),
            pair="BTC/USDT",
            price="110",
        ),
        cost_model=cost_model or ExecutionCostModel(),
    )


def _run(manifest: ScenarioManifest):
    context = CorrelationContext(
        request_id=UUID("00000000-0000-4000-8000-000000000001"),
        correlation_id=UUID("00000000-0000-4000-8000-000000000002"),
    )
    trade_intent = SimpleNamespace(
        tenant_id=manifest.tenant_id,
        bot_id=manifest.bot_id,
        pair=manifest.pair,
        environment=manifest.environment,
        side=manifest.side,
        amount=manifest.amount,
    )
    intent = SimpleNamespace(
        trade_intent=trade_intent,
        execution_intent_id=UUID("00000000-0000-4000-8000-000000000003"),
    )
    simulator = DeterministicExchangeSimulator(manifest)
    simulator.submit_approved_intent(intent, context)
    outcome = simulator.close_position()
    return outcome, simulator.evidence()


def test_versioned_fee_and_slippage_model_is_explicit_in_evidence() -> None:
    outcome, evidence = _run(
        _manifest(
            cost_model=ExecutionCostModel(
                entry_fee_rate="0.001",
                exit_fee_rate="0.001",
                entry_slippage_bps="10",
                exit_slippage_bps="10",
            )
        )
    )

    assert evidence.costs.model_version == "sim-cost-v1"
    assert evidence.costs.entry_fill_price == Decimal("100.100")
    assert evidence.costs.exit_fill_price == Decimal("109.890")
    assert evidence.costs.entry_fee == Decimal("0.200200")
    assert evidence.costs.exit_fee == Decimal("0.219780")
    assert outcome.fees == Decimal("0.419980")
    assert evidence.gross_pnl == Decimal("19.580")
    assert outcome.realized_pnl == evidence.realized_pnl == Decimal("19.160020")


def test_zero_cost_defaults_preserve_existing_scenario_result() -> None:
    outcome, evidence = _run(_manifest())

    assert outcome.fees == 0
    assert evidence.funding_cash_flow == 0
    assert outcome.realized_pnl == Decimal("20")
    assert evidence.exit_reason == "scenario_exit"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entry_fee_rate", "-0.001"),
        ("exit_fee_rate", "1.001"),
        ("entry_slippage_bps", "-1"),
        ("exit_slippage_bps", "10000"),
    ],
)
def test_invalid_cost_configuration_fails_closed(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        ExecutionCostModel(**{field: value})
