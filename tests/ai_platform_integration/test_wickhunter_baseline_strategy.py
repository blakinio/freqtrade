from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.wickhunter.baseline_strategy import (
    BaselineEvaluationError,
    EvaluationCase,
    EvaluationDimensions,
    EvaluationStatus,
    LiquidityBucket,
    MarketRegime,
    build_evaluation_decision,
    evaluate_deterministic_baselines,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    LiquidationFeatureVector,
    SourceLiquidationAggregate,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import (
    LABEL_SCHEMA_VERSION,
    CandidateLabel,
    LabelOutcome,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
)
from ai_platform.wickhunter.strategy import SignalMemory, generate_candidate


START = 1_000_000
HORIZON_MS = 60_000
POLICY_SHA = "a" * 64
DATASET_SHA = "b" * 64
MARKET_SHA = "c" * 64
SPLIT_SHA = "d" * 64
PRICE_PATH_SHA = "e" * 64
CODE_SHA = "f" * 40


def _parameters():
    return replace(
        INITIAL_COMPATIBILITY_PRIOR,
        parameter_version="wickhunter-baseline-test-v1",
        maximum_holding_ms=HORIZON_MS,
    )


def _metric(name: str, value: str, decision_ms: int) -> AvailableMetric:
    return AvailableMetric(
        name=name,
        value=Decimal(value),
        available_at_ms=decision_ms,
        source="test",
    )


def _feature(
    decision_ms: int,
    *,
    input_suffix: str,
    quote_volume: str = "100000000",
    trend: str = "-0.02",
    long_notional: str = "800",
    short_notional: str = "200",
) -> LiquidationFeatureVector:
    long_value = Decimal(long_notional)
    short_value = Decimal(short_notional)
    total = long_value + short_value
    return LiquidationFeatureVector(
        feature_schema_version="wickhunter-liquidation-features-v1",
        symbol="BTCUSDT",
        decision_timestamp_ms=decision_ms,
        decision_price=Decimal("100"),
        event_count=2,
        total_notional_usd=total,
        liquidated_long_notional_usd=long_value,
        liquidated_short_notional_usd=short_value,
        long_short_imbalance=(short_value - long_value) / total,
        maximum_event_notional_usd=max(long_value, short_value),
        maximum_event_percentile=Decimal("0.90"),
        maximum_event_zscore=Decimal("2"),
        liquidation_burst_intensity=Decimal("3"),
        time_since_previous_burst_ms=60_000,
        ingest_latency_ms=100,
        source_coverage_ratio=Decimal("1"),
        source_aggregates=(
            SourceLiquidationAggregate(
                source="binance",
                event_count=2,
                total_notional_usd=total,
                liquidated_long_notional_usd=long_value,
                liquidated_short_notional_usd=short_value,
                maximum_event_notional_usd=max(long_value, short_value),
                maximum_ingest_latency_ms=100,
                latest_received_at_ms=decision_ms - 1_000,
            ),
        ),
        market_metrics=(
            _metric("quote_volume_24h_usd", quote_volume, decision_ms),
            _metric("trend_return_ratio", trend, decision_ms),
            _metric("volatility_ratio", "0.02", decision_ms),
            _metric("vwap", "101", decision_ms),
            _metric("vwma", "101", decision_ms),
            _metric("wick_ratio", "0.01", decision_ms),
        ),
        feature_available_at_ms=decision_ms,
        input_event_ids=(f"binance:event-{input_suffix}",),
        history_id=f"history-{input_suffix}",
        history_sha256=canonical_sha256({"history": input_suffix}),
    )


def _label(
    *,
    row_sha: str,
    feature: LiquidationFeatureVector,
    side: TradeDirection,
    fee_ratio: Decimal = Decimal("0.001"),
    take_profit_ratio: Decimal = Decimal("0.085"),
) -> CandidateLabel:
    selected_return = Decimal("0.05") if side is TradeDirection.LONG else Decimal("-0.02")
    label_id = canonical_sha256(
        {
            "row_sha": row_sha,
            "feature_hash": feature.feature_hash,
            "side": side.value,
            "fee_ratio": fee_ratio,
            "take_profit_ratio": take_profit_ratio,
        }
    )
    return CandidateLabel(
        schema_version=LABEL_SCHEMA_VERSION,
        label_id=label_id,
        policy_version="wickhunter-replay-policy-test-v1",
        policy_sha256=POLICY_SHA,
        dataset_id="wickhunter-dataset-test",
        dataset_manifest_sha256=DATASET_SHA,
        market_manifest_sha256=MARKET_SHA,
        split_geometry_sha256=SPLIT_SHA,
        dataset_row_sha256=row_sha,
        price_path_manifest_sha256=PRICE_PATH_SHA,
        source_commit_sha=CODE_SHA,
        split_name="train",
        symbol=feature.symbol,
        side=side,
        decision_timestamp_ms=feature.decision_timestamp_ms,
        label_end_ms=feature.decision_timestamp_ms + HORIZON_MS,
        outcome=LabelOutcome.TAKE_PROFIT,
        entry_timestamp_ms=feature.decision_timestamp_ms,
        entry_aggregate_trade_id=1,
        entry_trade_sha256=canonical_sha256({"entry": label_id}),
        raw_entry_price=Decimal("100"),
        executed_entry_price=Decimal("100.1"),
        exit_timestamp_ms=feature.decision_timestamp_ms + 1_000,
        exit_aggregate_trade_id=2,
        exit_trade_sha256=canonical_sha256({"exit": label_id}),
        raw_exit_price=Decimal("106"),
        executed_exit_price=Decimal("105.894"),
        gross_return_ratio=selected_return + Decimal("0.002"),
        net_return_ratio=selected_return,
        maximum_favorable_excursion_ratio=Decimal("0.06"),
        maximum_adverse_excursion_ratio=Decimal("0.01"),
        time_to_outcome_ms=1_000,
        fee_ratio=fee_ratio,
        slippage_ratio=Decimal("0.001"),
        take_profit_ratio=take_profit_ratio,
        stop_loss_ratio=Decimal("0.05"),
        entry_delay_ms=0,
        maximum_entry_delay_ms=2_000,
        protected_holdout_accessed=False,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )


def _case(
    row_character: str,
    feature: LiquidationFeatureVector,
    *,
    fee_ratio: Decimal = Decimal("0.001"),
    take_profit_ratio: Decimal = Decimal("0.085"),
) -> EvaluationCase:
    row_sha = row_character * 64
    return EvaluationCase(
        dataset_row_sha256=row_sha,
        split_name="train",
        feature=feature,
        labels=(
            _label(
                row_sha=row_sha,
                feature=feature,
                side=TradeDirection.LONG,
                fee_ratio=fee_ratio,
                take_profit_ratio=take_profit_ratio,
            ),
            _label(
                row_sha=row_sha,
                feature=feature,
                side=TradeDirection.SHORT,
                fee_ratio=fee_ratio,
                take_profit_ratio=take_profit_ratio,
            ),
        ),
    )


def test_evaluates_reversal_and_continuation_with_exact_wh02_results() -> None:
    feature = _feature(START, input_suffix="one")
    case = _case("1", feature)

    report = evaluate_deterministic_baselines(
        cases=(case,),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )

    assert report.protected_holdout_accessed is False
    assert report.model_promoted is False
    assert report.profitability_claimed is False
    assert report.execution_enabled is False
    assert report.live_capital_authorized is False
    assert report.orders_submitted == 0
    assert report.fee_ratio == Decimal("0.001")
    assert report.slippage_ratio == Decimal("0.001")
    assert report.take_profit_ratio == Decimal("0.085")
    assert report.stop_loss_ratio == Decimal("0.05")
    assert report.label_horizon_ms == HORIZON_MS
    assert report.overall.decision_count == 2
    assert report.overall.selected_count == 2
    assert report.overall.net_return_sum == Decimal("0.03")

    by_hypothesis = {item.dimensions.hypothesis: item for item in report.decisions}
    reversal = by_hypothesis[StrategyHypothesis.REVERSAL]
    continuation = by_hypothesis[StrategyHypothesis.CONTINUATION]
    assert reversal.side is TradeDirection.LONG
    assert continuation.side is TradeDirection.SHORT
    assert reversal.net_return_ratio == case.label_for(TradeDirection.LONG).net_return_ratio
    assert continuation.net_return_ratio == case.label_for(TradeDirection.SHORT).net_return_ratio
    assert reversal.maximum_favorable_excursion_ratio == Decimal("0.06")
    assert reversal.maximum_adverse_excursion_ratio == Decimal("0.01")
    assert reversal.time_to_outcome_ms == 1_000

    slice_keys = {(item.dimension, item.value) for item in report.slices}
    assert ("side", "long") in slice_keys
    assert ("side", "short") in slice_keys
    assert ("symbol", "BTCUSDT") in slice_keys
    assert ("liquidity", "medium") in slice_keys
    assert ("source", "binance") in slice_keys
    assert ("regime", "downtrend") in slice_keys
    assert ("hypothesis", "reversal") in slice_keys
    assert ("hypothesis", "continuation") in slice_keys


def test_duplicate_evidence_and_cooldown_are_explicit() -> None:
    duplicate_feature = _feature(START, input_suffix="duplicate")
    duplicate_report = evaluate_deterministic_baselines(
        cases=(
            _case("1", duplicate_feature),
            _case("2", duplicate_feature),
        ),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )

    duplicate_ignored = [
        item
        for item in duplicate_report.decisions
        if item.status is EvaluationStatus.IGNORED
    ]
    assert len(duplicate_ignored) == 2
    assert {item.reason_codes for item in duplicate_ignored} == {
        ("duplicate_feature_evidence",)
    }

    first = _feature(START, input_suffix="cooldown-one")
    second = _feature(START + 60_000, input_suffix="cooldown-two")
    cooldown_report = evaluate_deterministic_baselines(
        cases=(
            _case("3", first),
            _case("4", second),
        ),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )
    cooldown_ignored = [
        item
        for item in cooldown_report.decisions
        if item.status is EvaluationStatus.IGNORED
    ]
    assert len(cooldown_ignored) == 2
    assert {item.reason_codes for item in cooldown_ignored} == {
        ("symbol_side_cooldown_active",)
    }


def test_input_order_does_not_change_report_identity() -> None:
    first = _case("1", _feature(START, input_suffix="first"))
    second = _case("2", _feature(START + 400_000, input_suffix="second"))

    forward = evaluate_deterministic_baselines(
        cases=(first, second),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )
    reverse = evaluate_deterministic_baselines(
        cases=(second, first),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )

    assert forward == reverse
    assert forward.report_id == reverse.report_id
    assert forward.as_json_dict() == reverse.as_json_dict()


def test_rejects_parameter_or_cost_mismatch() -> None:
    feature = _feature(START, input_suffix="mismatch")

    with pytest.raises(BaselineEvaluationError, match="take_profit_ratio"):
        evaluate_deterministic_baselines(
            cases=(_case("1", feature, take_profit_ratio=Decimal("0.09")),),
            parameters=_parameters(),
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        )

    second = _feature(START + 400_000, input_suffix="second-cost")
    with pytest.raises(BaselineEvaluationError, match="one replay identity"):
        evaluate_deterministic_baselines(
            cases=(
                _case("2", feature),
                _case("3", second, fee_ratio=Decimal("0.002")),
            ),
            parameters=_parameters(),
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        )


def test_shared_evaluation_interface_accepts_advisory_score_identity() -> None:
    feature = _feature(START, input_suffix="model")
    case = _case("1", feature)
    candidate = generate_candidate(
        features=feature,
        parameters=_parameters(),
        hypothesis=StrategyHypothesis.REVERSAL,
        memory=SignalMemory(),
    )
    dimensions = EvaluationDimensions(
        split_name="train",
        symbol=feature.symbol,
        side="long",
        liquidity=LiquidityBucket.MEDIUM,
        source="binance",
        regime=MarketRegime.DOWNTREND,
        hypothesis=StrategyHypothesis.REVERSAL,
    )

    decision = build_evaluation_decision(
        strategy_id="wickhunter-advisory-model-test",
        case=case,
        candidate=candidate,
        dimensions=dimensions,
        score_id="9" * 64,
        model_version="model-test-v1",
    )

    assert decision.score_id == "9" * 64
    assert decision.model_version == "model-test-v1"
    assert decision.model_promoted is False
    assert decision.profitability_claimed is False
