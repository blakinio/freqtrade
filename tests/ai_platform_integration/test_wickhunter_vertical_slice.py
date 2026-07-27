from __future__ import annotations

import inspect
from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.market_data.contracts import Exchange, InstrumentSnapshot, MarketType
from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
)
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    BotMode,
    CandidateAction,
    DriftState,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    ModelPromotionState,
    RiskOutcome,
    ShadowStatus,
    SourceHealth,
    StrategyHypothesis,
)
from ai_platform.wickhunter.features import build_liquidation_features
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
    validate_parameters,
)
from ai_platform.wickhunter.risk import (
    WickHunterRiskContext,
    WickHunterRiskLimits,
    evaluate_trade_intent,
)
from ai_platform.wickhunter.scoring import (
    DeterministicBaselineScorer,
    validated_external_model_score,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest, evaluate_shadow_decision
from ai_platform.wickhunter.strategy import (
    CooldownRecord,
    SignalMemory,
    generate_candidate,
)
from ai_platform.wickhunter.universe import (
    DynamicUniversePolicy,
    LiquidationCoverage,
    UniverseQualitySnapshot,
    select_dynamic_universe,
)


DECISION_MS = 2_000_000
CANDLE_CLOSE_MS = 1_940_000
DATASET_HASH = "d" * 64
CODE_SHA = "a" * 40


def _instrument(symbol: str, *, active: bool = True) -> InstrumentSnapshot:
    return InstrumentSnapshot(
        schema_version=1,
        exchange=Exchange.BYBIT,
        market_type=MarketType.PERPETUAL,
        native_instrument_id=symbol,
        canonical_instrument_id=f"bybit:perpetual:{symbol}",
        native_symbol=symbol,
        canonical_symbol=symbol,
        base_asset=symbol.removesuffix("USDT"),
        quote_asset="USDT",
        settlement_asset="USDT",
        contract_type=MarketType.PERPETUAL,
        contract_value=Decimal("1"),
        contract_value_unit="base",
        tick_size=Decimal("0.01"),
        quantity_step=Decimal("0.001"),
        active=active,
        listed_at_ms=1,
        expires_at_ms=None,
        source_snapshot_id=f"snapshot-{symbol}",
        source_snapshot_sha256="b" * 64,
    )


def _quality(
    symbol: str,
    *,
    quote_volume: Decimal = Decimal("50000000"),
    spread_bps: Decimal | None = Decimal("5"),
    source_health: SourceHealth = SourceHealth.HEALTHY,
    source_received_at_ms: int | None = DECISION_MS - 1_000,
    risk_blocked: bool = False,
) -> UniverseQualitySnapshot:
    return UniverseQualitySnapshot(
        canonical_instrument_id=f"bybit:perpetual:{symbol}",
        measured_at_ms=DECISION_MS - 1_000,
        quote_volume_24h_usd=quote_volume,
        spread_bps=spread_bps,
        candle_history_rows=1_000,
        feature_history_rows=500,
        latest_candle_available_at_ms=CANDLE_CLOSE_MS,
        liquidation_coverage=(
            LiquidationCoverage(
                source="binance-usdm",
                health=source_health,
                last_received_at_ms=source_received_at_ms,
            ),
            LiquidationCoverage(
                source="bybit-linear",
                health=source_health,
                last_received_at_ms=source_received_at_ms,
            ),
        ),
        symbol_risk_blocked=risk_blocked,
    )


def _universe(*, inactive_sol: bool = False):
    instruments = (
        _instrument("BTCUSDT"),
        _instrument("SOLUSDT", active=not inactive_sol),
        _instrument("XRPUSDT"),
    )
    qualities = tuple(_quality(item.canonical_symbol) for item in instruments)
    policy = DynamicUniversePolicy(
        policy_version="wickhunter-dynamic-universe-policy-v1",
        required_market_type=MarketType.PERPETUAL,
        required_quote_asset="USDT",
        minimum_quote_volume_24h_usd=Decimal("10000000"),
        maximum_spread_bps=Decimal("10"),
        minimum_candle_history_rows=100,
        minimum_feature_history_rows=50,
        minimum_healthy_liquidation_sources=1,
        maximum_quality_age_ms=60_000,
        maximum_candle_age_ms=120_000,
        maximum_liquidation_age_ms=30_000,
    )
    return select_dynamic_universe(
        instruments=instruments,
        quality_snapshots=qualities,
        policy=policy,
        decision_timestamp_ms=DECISION_MS,
    )


def _events(
    *,
    dominant_side: LiquidatedPositionSide = LiquidatedPositionSide.LONG,
    symbol: str = "BTCUSDT",
) -> tuple[LiquidationEvent, ...]:
    other_side = (
        LiquidatedPositionSide.SHORT
        if dominant_side is LiquidatedPositionSide.LONG
        else LiquidatedPositionSide.LONG
    )
    return (
        LiquidationEvent(
            schema_version=1,
            source="bybit-linear",
            source_event_id="bybit-1",
            symbol=symbol,
            liquidated_position_side=dominant_side,
            occurred_at_ms=DECISION_MS - 6_000,
            received_at_ms=DECISION_MS - 5_500,
            price=Decimal("99"),
            quantity=Decimal("600"),
            notional_usd=Decimal("60000"),
            raw_side="Sell",
        ),
        LiquidationEvent(
            schema_version=1,
            source="binance-usdm",
            source_event_id="binance-1",
            symbol=symbol,
            liquidated_position_side=dominant_side,
            occurred_at_ms=DECISION_MS - 5_000,
            received_at_ms=DECISION_MS - 4_000,
            price=Decimal("99"),
            quantity=Decimal("300"),
            notional_usd=Decimal("30000"),
            raw_side="SELL",
        ),
        LiquidationEvent(
            schema_version=1,
            source="bybit-linear",
            source_event_id="bybit-2",
            symbol=symbol,
            liquidated_position_side=other_side,
            occurred_at_ms=DECISION_MS - 4_000,
            received_at_ms=DECISION_MS - 3_500,
            price=Decimal("99"),
            quantity=Decimal("100"),
            notional_usd=Decimal("10000"),
            raw_side="Buy",
        ),
    )


def _market(
    *,
    price: Decimal = Decimal("99"),
    trend: Decimal = Decimal("-0.02"),
    future_metric: bool = False,
) -> MarketContextSnapshot:
    available = DECISION_MS + 1 if future_metric else CANDLE_CLOSE_MS
    metrics = (
        AvailableMetric(
            "atr_ratio", Decimal("0.02"), available, "completed_candle:5m"
        ),
        AvailableMetric(
            "market_wide_liquidation_intensity",
            Decimal("1.5"),
            DECISION_MS - 1_000,
            "liquidation-aggregate",
        ),
        AvailableMetric(
            "open_interest_usd", Decimal("100000000"), DECISION_MS - 1_000, "oi"
        ),
        AvailableMetric(
            "funding_rate", Decimal("0.0001"), DECISION_MS - 1_000, "funding"
        ),
        AvailableMetric(
            "quote_volume_24h_usd", Decimal("50000000"), DECISION_MS - 1_000, "ticker"
        ),
        AvailableMetric("spread_bps", Decimal("5"), DECISION_MS - 1_000, "book"),
        AvailableMetric(
            "trend_return_ratio", trend, available, "completed_candle:5m"
        ),
        AvailableMetric(
            "volatility_ratio", Decimal("0.03"), available, "completed_candle:5m"
        ),
        AvailableMetric("vwap", Decimal("100"), available, "completed_candle:5m"),
        AvailableMetric("vwma", Decimal("100"), available, "completed_candle:5m"),
        AvailableMetric(
            "wick_ratio", Decimal("0.01"), available, "completed_candle:5m"
        ),
    )
    return MarketContextSnapshot(
        symbol="BTCUSDT",
        decision_timestamp_ms=DECISION_MS,
        decision_price=price,
        completed_candle_close_ms=CANDLE_CLOSE_MS,
        metrics=metrics,
    )


def _history() -> LiquidationHistorySnapshot:
    return LiquidationHistorySnapshot(
        symbol="BTCUSDT",
        event_notionals_usd=tuple(Decimal(value) for value in range(1_000, 11_000, 1_000)),
        burst_window_notionals_usd=tuple(
            Decimal(value) for value in range(5_000, 55_000, 5_000)
        ),
        previous_burst_received_at_ms=DECISION_MS - 120_000,
        available_at_ms=DECISION_MS - 1_000,
        history_id="liquidation-history-btc-v1",
        history_sha256="c" * 64,
    )


def _source_states(
    *, health: SourceHealth = SourceHealth.HEALTHY
) -> tuple[LiquidationSourceState, ...]:
    return (
        LiquidationSourceState(
            source="binance-usdm",
            health=health,
            coverage_available=health is SourceHealth.HEALTHY,
            last_received_at_ms=DECISION_MS - 4_000,
            observed_at_ms=DECISION_MS - 500,
        ),
        LiquidationSourceState(
            source="bybit-linear",
            health=health,
            coverage_available=health is SourceHealth.HEALTHY,
            last_received_at_ms=DECISION_MS - 3_500,
            observed_at_ms=DECISION_MS - 500,
        ),
    )


def _features(*, short_dominant: bool = False, price: Decimal = Decimal("99"), trend=None):
    return build_liquidation_features(
        events=_events(
            dominant_side=(
                LiquidatedPositionSide.SHORT
                if short_dominant
                else LiquidatedPositionSide.LONG
            )
        ),
        market=_market(
            price=price,
            trend=(
                Decimal("0.02")
                if trend is None and short_dominant
                else Decimal("-0.02")
                if trend is None
                else trend
            ),
        ),
        history=_history(),
        source_states=_source_states(),
        burst_window_ms=INITIAL_COMPATIBILITY_PRIOR.burst_window_ms,
    )


def _risk_limits(**overrides) -> WickHunterRiskLimits:
    values = dict(
        risk_policy_version="wickhunter-shadow-risk-v1",
        maximum_base_risk_ratio=Decimal("0.01"),
        maximum_effective_exposure_ratio=Decimal("0.20"),
        maximum_leverage=Decimal("15"),
        maximum_dca_count=5,
        maximum_total_dca_risk_ratio=Decimal("0.03"),
        maximum_concurrent_positions=10,
        maximum_symbol_exposure_ratio=Decimal("0.20"),
        maximum_correlated_exposure_ratio=Decimal("0.40"),
        maximum_directional_exposure_ratio=Decimal("0.60"),
        maximum_daily_loss_ratio=Decimal("0.05"),
        maximum_drawdown_ratio=Decimal("0.15"),
        maximum_consecutive_losses=5,
        maximum_liquidation_age_ms=30_000,
        maximum_candle_age_ms=120_000,
        maximum_open_interest_age_ms=60_000,
        maximum_funding_age_ms=60_000,
        maximum_spread_bps=Decimal("10"),
        minimum_quote_volume_usd=Decimal("10000000"),
        minimum_confidence=Decimal("0.55"),
    )
    values.update(overrides)
    return WickHunterRiskLimits(**values)


def _risk_context(**overrides) -> WickHunterRiskContext:
    values = dict(
        evaluated_at_ms=DECISION_MS,
        global_kill_switch_active=False,
        circuit_breaker_active=False,
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        projected_concurrent_positions=1,
        projected_symbol_exposure_ratio=Decimal("0.10"),
        projected_correlated_exposure_ratio=Decimal("0.20"),
        projected_directional_exposure_ratio=Decimal("0.30"),
        daily_loss_ratio=Decimal("0.01"),
        drawdown_ratio=Decimal("0.02"),
        consecutive_losses=0,
        consecutive_loss_cooldown_until_ms=None,
        symbol_cooldown_until_ms=None,
        setup_still_valid=True,
        dca_adverse_condition_met=True,
        dca_timing_condition_met=True,
        spread_bps=Decimal("5"),
        quote_volume_usd=Decimal("50000000"),
    )
    values.update(overrides)
    return WickHunterRiskContext(**values)


def _request(**overrides) -> ShadowDecisionRequest:
    values = dict(
        bot_instance="wickhunter-shadow-1",
        mode=BotMode.SHADOW,
        events=_events(),
        market=_market(),
        history=_history(),
        source_states=_source_states(),
        universe=_universe(),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        hypothesis=StrategyHypothesis.REVERSAL,
        scorer=DeterministicBaselineScorer(),
        signal_memory=SignalMemory(),
        risk_limits=_risk_limits(),
        risk_context=_risk_context(),
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
    )
    values.update(overrides)
    return ShadowDecisionRequest(**values)


def test_feature_generation_is_deterministic_and_source_labelled() -> None:
    first = _features()
    second = _features()
    assert first == second
    assert first.feature_hash == second.feature_hash
    assert [item.source for item in first.source_aggregates] == [
        "binance-usdm",
        "bybit-linear",
    ]
    assert first.event_count == 3
    assert first.total_notional_usd == Decimal("100000")


def test_feature_pipeline_retains_long_short_and_latency_evidence() -> None:
    features = _features()
    assert features.liquidated_long_notional_usd == Decimal("90000")
    assert features.liquidated_short_notional_usd == Decimal("10000")
    assert features.long_short_imbalance == Decimal("-0.8")
    assert features.ingest_latency_ms == 1_000
    assert features.maximum_event_percentile == Decimal("1")


def test_as_of_join_rejects_future_liquidation_event() -> None:
    future = replace(_events()[0], received_at_ms=DECISION_MS + 1)
    with pytest.raises(ValueError, match="received after decision"):
        build_liquidation_features(
            events=(future, *_events()[1:]),
            market=_market(),
            history=_history(),
            source_states=_source_states(),
            burst_window_ms=60_000,
        )


def test_no_lookahead_rejects_future_candle_metric() -> None:
    with pytest.raises(ValueError, match="not available at decision time"):
        build_liquidation_features(
            events=_events(),
            market=_market(future_metric=True),
            history=_history(),
            source_states=_source_states(),
            burst_window_ms=60_000,
        )


def test_dynamic_universe_selects_multiple_eligible_symbols_without_manual_pair_list() -> None:
    universe = _universe()
    assert universe.selected_symbols == ("BTCUSDT", "SOLUSDT", "XRPUSDT")
    assert universe.includes_symbol("SOLUSDT")


def test_dynamic_universe_removes_inactive_instrument() -> None:
    universe = _universe(inactive_sol=True)
    assert universe.selected_symbols == ("BTCUSDT", "XRPUSDT")
    sol = next(item for item in universe.decisions if item.canonical_symbol == "SOLUSDT")
    assert "instrument_inactive" in sol.reason_codes


def test_dynamic_universe_blocks_stale_liquidation_coverage() -> None:
    instruments = (_instrument("BTCUSDT"),)
    qualities = (
        _quality(
            "BTCUSDT",
            source_health=SourceHealth.STALE,
            source_received_at_ms=DECISION_MS - 120_000,
        ),
    )
    policy = DynamicUniversePolicy(
        policy_version="v1",
        required_market_type=MarketType.PERPETUAL,
        required_quote_asset="USDT",
        minimum_quote_volume_24h_usd=Decimal("10000000"),
        maximum_spread_bps=Decimal("10"),
        minimum_candle_history_rows=100,
        minimum_feature_history_rows=50,
        minimum_healthy_liquidation_sources=1,
        maximum_quality_age_ms=60_000,
        maximum_candle_age_ms=120_000,
        maximum_liquidation_age_ms=30_000,
    )
    universe = select_dynamic_universe(
        instruments=instruments,
        quality_snapshots=qualities,
        policy=policy,
        decision_timestamp_ms=DECISION_MS,
    )
    assert universe.selected_symbols == ()
    assert "insufficient_healthy_liquidation_sources" in universe.decisions[0].reason_codes


def test_reversal_hypothesis_generates_long_after_long_liquidation_exhaustion() -> None:
    candidate = generate_candidate(
        features=_features(),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.REVERSAL,
    )
    assert candidate.action is CandidateAction.ENTER_LONG


def test_reversal_hypothesis_generates_short_after_short_liquidation_exhaustion() -> None:
    candidate = generate_candidate(
        features=_features(short_dominant=True, price=Decimal("101")),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.REVERSAL,
    )
    assert candidate.action is CandidateAction.ENTER_SHORT


def test_continuation_hypothesis_can_short_long_liquidation_cascade() -> None:
    candidate = generate_candidate(
        features=_features(),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.CONTINUATION,
    )
    assert candidate.action is CandidateAction.ENTER_SHORT


def test_continuation_hypothesis_can_long_short_liquidation_cascade() -> None:
    candidate = generate_candidate(
        features=_features(short_dominant=True, price=Decimal("101")),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.CONTINUATION,
    )
    assert candidate.action is CandidateAction.ENTER_LONG


def test_duplicate_signal_evidence_is_ignored() -> None:
    features = _features()
    candidate = generate_candidate(
        features=features,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.REVERSAL,
        memory=SignalMemory(seen_feature_hashes=frozenset({features.feature_hash})),
    )
    assert candidate.action is CandidateAction.IGNORE
    assert candidate.reason_codes == ("duplicate_feature_evidence",)


def test_symbol_side_cooldown_is_enforced() -> None:
    candidate = generate_candidate(
        features=_features(),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.REVERSAL,
        memory=SignalMemory(
            cooldown_records=(
                CooldownRecord(
                    symbol="BTCUSDT",
                    side=generate_candidate(
                        features=_features(),
                        parameters=INITIAL_COMPATIBILITY_PRIOR,
                        hypothesis=StrategyHypothesis.REVERSAL,
                    ).side,
                    hypothesis=StrategyHypothesis.REVERSAL,
                    candidate_at_ms=DECISION_MS - 1_000,
                ),
            )
        ),
    )
    assert candidate.action is CandidateAction.IGNORE
    assert candidate.reason_codes == ("symbol_side_cooldown_active",)


def test_parameter_bounds_reject_leverage_above_hard_ceiling() -> None:
    invalid = replace(INITIAL_COMPATIBILITY_PRIOR, leverage=Decimal("15.1"))
    with pytest.raises(ValueError, match="leverage"):
        validate_parameters(invalid, DEFAULT_RESEARCH_BOUNDS)


def test_parameter_hash_is_reproducible_and_changes_with_versioned_values() -> None:
    same = replace(INITIAL_COMPATIBILITY_PRIOR)
    changed = replace(INITIAL_COMPATIBILITY_PRIOR, take_profit_ratio=Decimal("0.09"))
    assert same.parameter_hash == INITIAL_COMPATIBILITY_PRIOR.parameter_hash
    assert changed.parameter_hash != INITIAL_COMPATIBILITY_PRIOR.parameter_hash


def test_baseline_scorer_is_deterministic_and_bounded() -> None:
    features = _features()
    candidate = generate_candidate(
        features=features,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        hypothesis=StrategyHypothesis.REVERSAL,
    )
    scorer = DeterministicBaselineScorer()
    first = scorer.score(
        candidate=candidate,
        features=features,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
    )
    second = scorer.score(
        candidate=candidate,
        features=features,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
    )
    assert first == second
    assert Decimal("0") <= first.confidence <= Decimal("1")
    assert (
        INITIAL_COMPATIBILITY_PRIOR.minimum_risk_multiplier
        <= first.bounded_risk_multiplier
        <= INITIAL_COMPATIBILITY_PRIOR.maximum_risk_multiplier
    )


def test_first_vertical_slice_reaches_simulated_allowed_shadow_result() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.status is ShadowStatus.SIMULATED_ALLOWED
    assert result.trade_intent is not None
    assert result.risk_decision is not None
    assert result.risk_decision.outcome is RiskOutcome.ALLOW
    assert result.trade_intent.symbol == "BTCUSDT"
    assert result.trade_intent.code_sha == CODE_SHA
    assert result.trade_intent.dataset_hash == DATASET_HASH


def test_replay_shadow_contract_is_deterministic_for_identical_inputs() -> None:
    first = evaluate_shadow_decision(_request())
    second = evaluate_shadow_decision(_request())
    assert first == second
    assert first.shadow_decision_id == second.shadow_decision_id


def test_shadow_runtime_returns_no_candidate_when_symbol_leaves_universe() -> None:
    empty_universe = select_dynamic_universe(
        instruments=(_instrument("BTCUSDT", active=False),),
        quality_snapshots=(_quality("BTCUSDT"),),
        policy=DynamicUniversePolicy(
            policy_version="v1",
            required_market_type=MarketType.PERPETUAL,
            required_quote_asset="USDT",
            minimum_quote_volume_24h_usd=Decimal("10000000"),
            maximum_spread_bps=Decimal("10"),
            minimum_candle_history_rows=100,
            minimum_feature_history_rows=50,
            minimum_healthy_liquidation_sources=1,
            maximum_quality_age_ms=60_000,
            maximum_candle_age_ms=120_000,
            maximum_liquidation_age_ms=30_000,
        ),
        decision_timestamp_ms=DECISION_MS,
    )
    result = evaluate_shadow_decision(_request(universe=empty_universe))
    assert result.status is ShadowStatus.NO_CANDIDATE
    assert result.trade_intent is None


def test_live_mode_is_explicitly_blocked() -> None:
    with pytest.raises(ValueError, match="live mode is not authorized"):
        evaluate_shadow_decision(_request(mode=BotMode.LIVE_BLOCKED))


def test_stale_liquidation_data_fails_closed() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.trade_intent is not None and result.score is not None
    stale_intent = replace(
        result.trade_intent,
        freshness=replace(result.trade_intent.freshness, liquidation_age_ms=120_000),
    )
    decision = evaluate_trade_intent(
        intent=stale_intent,
        score=result.score,
        context=_risk_context(),
        limits=_risk_limits(),
    )
    assert decision.outcome is RiskOutcome.REJECT
    assert "LIQUIDATION_DATA_STALE" in decision.reason_codes


def test_dca_exposure_ceiling_fails_closed() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.trade_intent is not None and result.score is not None
    excessive = replace(
        result.trade_intent,
        dca_plan=replace(
            result.trade_intent.dca_plan,
            maximum_levels=5,
            maximum_total_risk_ratio=Decimal("0.04"),
        ),
    )
    decision = evaluate_trade_intent(
        intent=excessive,
        score=result.score,
        context=_risk_context(),
        limits=_risk_limits(),
    )
    assert "DCA_EXPOSURE_LIMIT_EXCEEDED" in decision.reason_codes


def test_circuit_breaker_fails_closed() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.trade_intent is not None and result.score is not None
    decision = evaluate_trade_intent(
        intent=result.trade_intent,
        score=result.score,
        context=_risk_context(circuit_breaker_active=True),
        limits=_risk_limits(),
    )
    assert decision.outcome is RiskOutcome.REJECT
    assert "CIRCUIT_BREAKER_ACTIVE" in decision.reason_codes


def test_unapproved_model_cannot_replace_baseline_silently() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.candidate is not None and result.trade_intent is not None
    model_score = validated_external_model_score(
        candidate=result.candidate,
        feature_hash=result.trade_intent.feature_hash,
        confidence=Decimal("0.9"),
        expected_return_after_costs=Decimal("0.01"),
        bounded_risk_multiplier=Decimal("0.5"),
        model_version="wickhunter-lightgbm-candidate-v1",
        model_hash="e" * 64,
        promotion_state=ModelPromotionState.CANDIDATE,
        scored_at_ms=DECISION_MS,
    )
    model_intent = replace(
        result.trade_intent,
        score_id=model_score.score_id,
        confidence=model_score.confidence,
        model_version=model_score.model_version,
        model_hash=model_score.model_hash,
    )
    decision = evaluate_trade_intent(
        intent=model_intent,
        score=model_score,
        context=_risk_context(),
        limits=_risk_limits(),
    )
    assert decision.outcome is RiskOutcome.REJECT
    assert "MODEL_NOT_APPROVED" in decision.reason_codes


def test_risk_rejection_reasons_are_stable_unique_and_sorted() -> None:
    result = evaluate_shadow_decision(_request())
    assert result.trade_intent is not None and result.score is not None
    decision = evaluate_trade_intent(
        intent=result.trade_intent,
        score=result.score,
        context=_risk_context(
            global_kill_switch_active=True,
            circuit_breaker_active=True,
            drawdown_ratio=Decimal("0.30"),
        ),
        limits=_risk_limits(),
    )
    assert decision.reason_codes == tuple(sorted(set(decision.reason_codes)))


def test_shadow_package_has_no_direct_order_submission_surface() -> None:
    from ai_platform.wickhunter import shadow

    source = inspect.getsource(shadow)
    forbidden = ("create_order", "submit_order", "submit_approved_intent", "ccxt")
    assert all(token not in source for token in forbidden)
