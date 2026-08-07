from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateScore,
    DataFreshnessEvidence,
    DcaPlan,
    DriftState,
    ModelPromotionState,
    RiskOutcome,
    ScoreKind,
    SourceHealth,
    TradeDirection,
    WickHunterTradeIntent,
)
from ai_platform.wickhunter.risk import (
    WickHunterRiskContext,
    WickHunterRiskLimits,
    evaluate_trade_intent,
)


DECISION_MS = 1_800_000_000_000
SCORE_ID = "1" * 64
CANDIDATE_ID = "2" * 64
FEATURE_HASH = "3" * 64
MODEL_HASH = "4" * 64
INTENT_ID = "5" * 64
DATASET_HASH = "6" * 64
PARAMETER_HASH = "7" * 64


def _score() -> CandidateScore:
    return CandidateScore(
        score_id=SCORE_ID,
        kind=ScoreKind.SUPERVISED_MODEL,
        candidate_id=CANDIDATE_ID,
        feature_hash=FEATURE_HASH,
        confidence=Decimal("0.90"),
        expected_return_after_costs=Decimal("0.01"),
        bounded_risk_multiplier=Decimal("0.50"),
        model_version="wickhunter-lightgbm-candidate-v1",
        model_hash=MODEL_HASH,
        promotion_state=ModelPromotionState.CANDIDATE,
        scored_at_ms=DECISION_MS,
    )


def _intent(mode: BotMode) -> WickHunterTradeIntent:
    return WickHunterTradeIntent(
        schema_version="wickhunter-trade-intent-v1",
        trade_intent_id=INTENT_ID,
        candidate_id=CANDIDATE_ID,
        score_id=SCORE_ID,
        bot_instance="wickhunter-paper-v1",
        strategy_version="wickhunter-strategy-v1",
        model_version="wickhunter-lightgbm-candidate-v1",
        parameter_version="wickhunter-production-h180s-v1",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=DECISION_MS,
        decision_price=Decimal("100"),
        candidate_reason=("candidate_for_paper_validation",),
        liquidation_evidence_ids=("public-liquidation-evidence",),
        feature_hash=FEATURE_HASH,
        confidence=Decimal("0.90"),
        requested_base_risk_ratio=Decimal("0.001"),
        requested_leverage=Decimal("1"),
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        dca_plan=DcaPlan(
            enabled=False,
            maximum_levels=0,
            spacing_ratio=Decimal("0.005"),
            maximum_total_risk_ratio=Decimal("0.001"),
        ),
        expiration_timestamp_ms=DECISION_MS + 60_000,
        freshness=DataFreshnessEvidence(
            liquidation_age_ms=1_000,
            candle_age_ms=1_000,
            open_interest_age_ms=1_000,
            funding_age_ms=1_000,
            source_health=(
                ("binance-usdm", SourceHealth.HEALTHY),
                ("bybit-linear", SourceHealth.HEALTHY),
            ),
        ),
        dataset_hash=DATASET_HASH,
        model_hash=MODEL_HASH,
        code_sha="a" * 40,
        parameter_hash=PARAMETER_HASH,
        mode=mode,
    )


def _context(*, authorized: bool) -> WickHunterRiskContext:
    return WickHunterRiskContext(
        evaluated_at_ms=DECISION_MS + 1_000,
        global_kill_switch_active=False,
        circuit_breaker_active=False,
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        projected_concurrent_positions=1,
        projected_symbol_exposure_ratio=Decimal("0.001"),
        projected_correlated_exposure_ratio=Decimal("0.001"),
        projected_directional_exposure_ratio=Decimal("0.001"),
        daily_loss_ratio=Decimal("0"),
        drawdown_ratio=Decimal("0"),
        consecutive_losses=0,
        consecutive_loss_cooldown_until_ms=None,
        symbol_cooldown_until_ms=None,
        setup_still_valid=True,
        dca_adverse_condition_met=True,
        dca_timing_condition_met=True,
        spread_bps=Decimal("1"),
        quote_volume_usd=Decimal("100000000"),
        candidate_paper_validation_authorized=authorized,
    )


def _limits() -> WickHunterRiskLimits:
    return WickHunterRiskLimits(
        risk_policy_version="wickhunter-paper-validation-risk-v1",
        maximum_base_risk_ratio=Decimal("0.01"),
        maximum_effective_exposure_ratio=Decimal("0.10"),
        maximum_leverage=Decimal("2"),
        maximum_dca_count=0,
        maximum_total_dca_risk_ratio=Decimal("0.01"),
        maximum_concurrent_positions=10,
        maximum_symbol_exposure_ratio=Decimal("0.10"),
        maximum_correlated_exposure_ratio=Decimal("0.20"),
        maximum_directional_exposure_ratio=Decimal("0.20"),
        maximum_daily_loss_ratio=Decimal("0.05"),
        maximum_drawdown_ratio=Decimal("0.20"),
        maximum_consecutive_losses=5,
        maximum_liquidation_age_ms=30_000,
        maximum_candle_age_ms=120_000,
        maximum_open_interest_age_ms=60_000,
        maximum_funding_age_ms=60_000,
        maximum_spread_bps=Decimal("10"),
        minimum_quote_volume_usd=Decimal("1000000"),
        minimum_confidence=Decimal("0.50"),
    )


@pytest.mark.parametrize("mode", (BotMode.SHADOW, BotMode.PAPER))
def test_candidate_model_is_allowed_only_for_explicit_simulation_modes(mode: BotMode) -> None:
    decision = evaluate_trade_intent(
        intent=_intent(mode),
        score=_score(),
        context=_context(authorized=True),
        limits=_limits(),
    )

    assert decision.outcome is RiskOutcome.ALLOW
    assert decision.reason_codes == ("RISK_APPROVED",)


def test_candidate_model_remains_rejected_without_explicit_gate() -> None:
    decision = evaluate_trade_intent(
        intent=_intent(BotMode.PAPER),
        score=_score(),
        context=_context(authorized=False),
        limits=_limits(),
    )

    assert decision.outcome is RiskOutcome.REJECT
    assert "MODEL_NOT_APPROVED" in decision.reason_codes


def test_candidate_gate_cannot_authorize_research_mode() -> None:
    decision = evaluate_trade_intent(
        intent=_intent(BotMode.RESEARCH),
        score=_score(),
        context=_context(authorized=True),
        limits=_limits(),
    )

    assert decision.outcome is RiskOutcome.REJECT
    assert "MODEL_NOT_APPROVED" in decision.reason_codes


def test_zero_effective_exposure_is_rejected_before_runtime_position_sizing() -> None:
    intent = _intent(BotMode.PAPER)
    zero_exposure_intent = replace(
        intent,
        requested_base_risk_ratio=Decimal("0"),
        dca_plan=replace(intent.dca_plan, maximum_total_risk_ratio=Decimal("0")),
    )

    decision = evaluate_trade_intent(
        intent=zero_exposure_intent,
        score=_score(),
        context=_context(authorized=True),
        limits=_limits(),
    )

    assert decision.outcome is RiskOutcome.REJECT
    assert decision.reason_codes == ("EFFECTIVE_EXPOSURE_NOT_POSITIVE",)
