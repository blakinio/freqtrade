from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import cast

from ai_platform.wickhunter.contracts import (
    BotMode,
    LiquidationSourceState,
    RiskOutcome,
    ShadowDecisionEvidence,
    ShadowStatus,
    SourceHealth,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import (
    RuntimeHealth,
    ShadowRuntime,
    ShadowRuntimePolicy,
    ShadowRuntimeTick,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


OBSERVED_MS = 2_000_000
MODEL_HASH = "c" * 64
PARAMETER_HASH = "b" * 64
DATASET_HASH = "d" * 64
CODE_SHA = "a" * 40


def _universe() -> DynamicUniverseSnapshot:
    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version="wickhunter-dynamic-universe-policy-v1",
        selected_at_ms=OBSERVED_MS - 1_000,
        decisions=(
            UniverseInstrumentDecision(
                canonical_instrument_id="binance:perpetual:BTCUSDT",
                canonical_symbol="BTCUSDT",
                included=True,
                reason_codes=("eligible",),
            ),
        ),
    )


def _request(universe: DynamicUniverseSnapshot) -> ShadowDecisionRequest:
    return cast(
        ShadowDecisionRequest,
        SimpleNamespace(
            bot_instance="wickhunter-shadow-1",
            mode=BotMode.SHADOW,
            universe=universe,
            market=SimpleNamespace(
                symbol="BTCUSDT",
                decision_timestamp_ms=OBSERVED_MS - 100,
            ),
            hypothesis=StrategyHypothesis.REVERSAL,
        ),
    )


def _tiny_allowed_evidence() -> ShadowDecisionEvidence:
    candidate = SimpleNamespace(
        candidate_id="3" * 64,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=OBSERVED_MS - 100,
        reason_codes=("reversal_long",),
    )
    score = SimpleNamespace(score_id="4" * 64)
    intent = SimpleNamespace(
        trade_intent_id="1" * 64,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=OBSERVED_MS - 100,
        decision_price=Decimal("100000000"),
        requested_base_risk_ratio=Decimal("0.0000000000001"),
        requested_leverage=Decimal("1"),
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        dca_plan=SimpleNamespace(maximum_total_risk_ratio=Decimal("0.0000000000001")),
        model_version="wickhunter-lightgbm-v1",
        model_hash=MODEL_HASH,
        parameter_version="wickhunter-parameters-v1",
        parameter_hash=PARAMETER_HASH,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
    )
    risk = SimpleNamespace(
        risk_decision_id="5" * 64,
        outcome=RiskOutcome.ALLOW,
        reason_codes=("RISK_APPROVED",),
    )
    return cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id="2" * 64,
            status=ShadowStatus.SIMULATED_ALLOWED,
            candidate=candidate,
            score=score,
            trade_intent=intent,
            risk_decision=risk,
        ),
    )


def test_allowed_decision_with_unrepresentable_quantity_does_not_fail_runtime() -> None:
    universe = _universe()
    runtime = ShadowRuntime(
        bot_instance="wickhunter-shadow-1",
        mode=BotMode.SHADOW,
        policy=ShadowRuntimePolicy(
            policy_version="wickhunter-shadow-runtime-policy-v1",
            simulated_initial_equity_quote=Decimal("10000"),
            maximum_universe_age_ms=60_000,
            maximum_source_age_ms=30_000,
            minimum_healthy_sources=1,
            maximum_open_positions=3,
            maximum_drawdown_ratio=Decimal("0.20"),
            decision_history_limit=10,
        ),
        decision_evaluator=lambda _request: _tiny_allowed_evidence(),
    )
    result = runtime.step(
        ShadowRuntimeTick(
            observed_at_ms=OBSERVED_MS,
            universe=universe,
            decision_requests=(_request(universe),),
            mark_prices=(("BTCUSDT", Decimal("100000000")),),
            source_states=(
                LiquidationSourceState(
                    source="binance-usdm",
                    health=SourceHealth.HEALTHY,
                    coverage_available=True,
                    last_received_at_ms=OBSERVED_MS - 1_000,
                    observed_at_ms=OBSERVED_MS - 500,
                ),
            ),
            validation_state="accepted_candidate_only",
            retraining_state="idle",
        )
    )

    assert result.state.generation == 1
    assert result.state.positions == ()
    assert result.snapshot.health is RuntimeHealth.HEALTHY
    assert result.snapshot.decisions[0].status is ShadowStatus.SIMULATED_ALLOWED
    assert "runtime_position_quantity_not_positive" in result.snapshot.decisions[0].reason_codes
