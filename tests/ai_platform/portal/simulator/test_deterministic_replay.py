from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.simulator.costs import ExecutionCostModel
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.funding import FundingEvent
from ai_platform.portal.simulator.schema import MarketTick, ScenarioManifest


def _manifest(seed: int) -> ScenarioManifest:
    return ScenarioManifest(
        scenario_id="replay-001",
        tenant_id="tenant-replay",
        bot_id="bot-replay",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount="1.5",
        environment=Environment.TEST,
        initial_equity="1000",
        entry_tick=MarketTick(
            occurred_at=datetime(2026, 7, 30, 11, 0, tzinfo=UTC),
            pair="BTC/USDT",
            price="100",
        ),
        exit_tick=MarketTick(
            occurred_at=datetime(2026, 7, 30, 11, 5, tzinfo=UTC),
            pair="BTC/USDT",
            price="105",
        ),
        seed=seed,
        cost_model=ExecutionCostModel(
            entry_fee_rate="0.001",
            exit_fee_rate="0.001",
            entry_slippage_bps="5",
            exit_slippage_bps="5",
        ),
        funding_events=(
            FundingEvent(
                occurred_at=datetime(2026, 7, 30, 11, 3, tzinfo=UTC),
                rate="0.0001",
            ),
        ),
    )


def _run(manifest: ScenarioManifest):
    context = CorrelationContext(
        request_id=UUID("20000000-0000-4000-8000-000000000001"),
        correlation_id=UUID("20000000-0000-4000-8000-000000000002"),
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
        execution_intent_id=UUID("20000000-0000-4000-8000-000000000003"),
    )
    simulator = DeterministicExchangeSimulator(manifest)
    simulator.submit_approved_intent(intent, context)
    simulator.close_position()
    return simulator.evidence()


def test_same_manifest_and_seed_produce_byte_stable_evidence_and_hash() -> None:
    first = _run(_manifest(seed=42))
    second = _run(_manifest(seed=42))

    assert first.canonical_json().encode() == second.canonical_json().encode()
    assert first.canonical_sha256() == second.canonical_sha256()
    assert len(first.canonical_sha256()) == 64
    assert first.order_id == second.order_id
    assert first.trade_id == second.trade_id
    assert first.outcome_id == second.outcome_id


def test_seed_change_changes_deterministic_identity_and_evidence_hash() -> None:
    first = _run(_manifest(seed=42))
    second = _run(_manifest(seed=43))

    assert first.order_id != second.order_id
    assert first.trade_id != second.trade_id
    assert first.outcome_id != second.outcome_id
    assert first.canonical_sha256() != second.canonical_sha256()


def test_simulator_has_no_sleep_or_network_execution_dependency() -> None:
    paths = (
        "ai_platform/portal/simulator/exchange.py",
        "ai_platform/portal/simulator/costs.py",
        "ai_platform/portal/simulator/latency.py",
        "ai_platform/portal/simulator/funding.py",
        "ai_platform/portal/simulator/gap_stop.py",
    )
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)

    assert "sleep(" not in source
    assert "requests." not in source
    assert "httpx." not in source
    assert "ccxt." not in source
    assert "submit_order" not in source
