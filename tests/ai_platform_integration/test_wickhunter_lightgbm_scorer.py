from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.wickhunter.baseline_strategy import EvaluationCase, EvaluationStatus
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    LiquidationFeatureVector,
    ModelPromotionState,
    SourceLiquidationAggregate,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import (
    LABEL_SCHEMA_VERSION,
    CandidateLabel,
    LabelOutcome,
)
from ai_platform.wickhunter.lightgbm_scorer import (
    LightGBMAdvisoryScorer,
    LightGBMScorerError,
    LightGBMTrainingPolicy,
    _fit_calibration,
    evaluate_lightgbm_against_baseline,
    train_lightgbm_scorer,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
    WickHunterParameters,
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


def _parameters() -> WickHunterParameters:
    return replace(
        INITIAL_COMPATIBILITY_PRIOR,
        parameter_version="wickhunter-lightgbm-test-v1",
        maximum_holding_ms=HORIZON_MS,
    )


def _metric(name: str, value: str, decision_ms: int) -> AvailableMetric:
    return AvailableMetric(
        name=name,
        value=Decimal(value),
        available_at_ms=decision_ms,
        source="test",
    )


def _feature(decision_ms: int, *, suffix: str, positive_long: bool) -> LiquidationFeatureVector:
    long_value = Decimal("800")
    short_value = Decimal("200")
    total = long_value + short_value
    trend = "-0.02" if positive_long else "-0.03"
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
        maximum_event_notional_usd=long_value,
        maximum_event_percentile=Decimal("0.90"),
        maximum_event_zscore=Decimal("2.5"),
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
                maximum_event_notional_usd=long_value,
                maximum_ingest_latency_ms=100,
                latest_received_at_ms=decision_ms - 1_000,
            ),
        ),
        market_metrics=(
            _metric("quote_volume_24h_usd", "100000000", decision_ms),
            _metric("trend_return_ratio", trend, decision_ms),
            _metric("volatility_ratio", "0.02", decision_ms),
            _metric("vwap", "101", decision_ms),
            _metric("vwma", "101", decision_ms),
            _metric("wick_ratio", "0.01", decision_ms),
        ),
        feature_available_at_ms=decision_ms,
        input_event_ids=(f"binance:event-{suffix}",),
        history_id=f"history-{suffix}",
        history_sha256=canonical_sha256({"history": suffix}),
    )


def _label(
    *,
    row_sha: str,
    split_name: str,
    feature: LiquidationFeatureVector,
    side: TradeDirection,
    net_return: Decimal,
) -> CandidateLabel:
    positive = net_return > 0
    label_id = canonical_sha256(
        {
            "row_sha": row_sha,
            "split_name": split_name,
            "feature_hash": feature.feature_hash,
            "side": side.value,
            "net_return": net_return,
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
        split_name=split_name,
        symbol=feature.symbol,
        side=side,
        decision_timestamp_ms=feature.decision_timestamp_ms,
        label_end_ms=feature.decision_timestamp_ms + HORIZON_MS,
        outcome=LabelOutcome.TAKE_PROFIT if positive else LabelOutcome.STOP_LOSS,
        entry_timestamp_ms=feature.decision_timestamp_ms,
        entry_aggregate_trade_id=1,
        entry_trade_sha256=canonical_sha256({"entry": label_id}),
        raw_entry_price=Decimal("100"),
        executed_entry_price=Decimal("100.1"),
        exit_timestamp_ms=feature.decision_timestamp_ms + 1_000,
        exit_aggregate_trade_id=2,
        exit_trade_sha256=canonical_sha256({"exit": label_id}),
        raw_exit_price=Decimal("106") if positive else Decimal("94"),
        executed_exit_price=Decimal("105.894") if positive else Decimal("94.094"),
        gross_return_ratio=net_return + Decimal("0.002"),
        net_return_ratio=net_return,
        maximum_favorable_excursion_ratio=Decimal("0.06"),
        maximum_adverse_excursion_ratio=Decimal("0.01"),
        time_to_outcome_ms=1_000,
        fee_ratio=Decimal("0.001"),
        slippage_ratio=Decimal("0.001"),
        take_profit_ratio=Decimal("0.085"),
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


def _case(index: int, split_name: str, *, positive_long: bool) -> EvaluationCase:
    feature = _feature(
        START + (index * 400_000),
        suffix=f"{split_name}-{index}",
        positive_long=positive_long,
    )
    row_sha = canonical_sha256(
        {"split_name": split_name, "index": index, "feature_hash": feature.feature_hash}
    )
    long_return = Decimal("0.05") if positive_long else Decimal("-0.03")
    short_return = Decimal("-0.03") if positive_long else Decimal("0.05")
    return EvaluationCase(
        dataset_row_sha256=row_sha,
        split_name=split_name,
        feature=feature,
        labels=(
            _label(
                row_sha=row_sha,
                split_name=split_name,
                feature=feature,
                side=TradeDirection.LONG,
                net_return=long_return,
            ),
            _label(
                row_sha=row_sha,
                split_name=split_name,
                feature=feature,
                side=TradeDirection.SHORT,
                net_return=short_return,
            ),
        ),
    )


def _cases() -> tuple[EvaluationCase, ...]:
    return (
        _case(1, "train", positive_long=True),
        _case(2, "train", positive_long=False),
        _case(3, "train", positive_long=True),
        _case(4, "train", positive_long=False),
        _case(5, "calibration", positive_long=True),
        _case(6, "calibration", positive_long=False),
        _case(7, "validation", positive_long=True),
        _case(8, "validation", positive_long=False),
    )


def test_training_is_reproducible_and_registry_is_advisory_only() -> None:
    policy = LightGBMTrainingPolicy(num_boost_round=8, calibration_bins=4)

    first = train_lightgbm_scorer(
        cases=_cases(),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=policy,
    )
    second = train_lightgbm_scorer(
        cases=tuple(reversed(_cases())),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=policy,
    )

    assert first == second
    assert first.model_hash == second.model_hash
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.positive_example_count > 0
    assert first.negative_example_count > 0
    registry = first.as_registry_record()
    assert registry["promotion_state"] == ModelPromotionState.CANDIDATE.value
    assert registry["advisory_only"] is True
    assert registry["automatic_promotion_enabled"] is False
    assert registry["execution_enabled"] is False
    assert registry["live_capital_authorized"] is False
    assert registry["orders_submitted"] == 0


def test_candidate_score_is_stable_calibrated_and_bound_to_model() -> None:
    artifact = train_lightgbm_scorer(
        cases=_cases(),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=LightGBMTrainingPolicy(num_boost_round=8, calibration_bins=4),
    )
    case = next(item for item in _cases() if item.split_name == "validation")
    candidate = generate_candidate(
        features=case.feature,
        parameters=_parameters(),
        hypothesis=StrategyHypothesis.REVERSAL,
        memory=SignalMemory(),
    )
    scorer = LightGBMAdvisoryScorer(artifact)

    first = scorer.score(
        candidate=candidate,
        features=case.feature,
        parameters=_parameters(),
    )
    second = scorer.score(
        candidate=candidate,
        features=case.feature,
        parameters=_parameters(),
    )

    assert first == second
    assert first.model_hash == artifact.model_hash
    assert first.model_version == artifact.model_version
    assert first.promotion_state is ModelPromotionState.CANDIDATE
    assert Decimal("0") <= first.confidence <= Decimal("1")
    assert first.expected_return_after_costs is not None
    assert Decimal("0") <= first.bounded_risk_multiplier <= Decimal("1")


def test_comparison_uses_wh03_interface_and_explicit_no_trade_threshold() -> None:
    policy = LightGBMTrainingPolicy(
        num_boost_round=8,
        calibration_bins=4,
        no_trade_confidence=Decimal("0.99"),
    )
    artifact = train_lightgbm_scorer(
        cases=_cases(),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=policy,
    )

    report = evaluate_lightgbm_against_baseline(
        artifact=artifact,
        cases=_cases(),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
    )

    assert report.baseline_overall.decision_count == report.model_overall.decision_count
    assert report.model_overall.ignored_count > 0
    assert any(
        decision.status is EvaluationStatus.IGNORED
        and "model_confidence_below_threshold" in decision.reason_codes
        for decision in report.decisions
    )
    assert report.model_promoted is False
    assert report.profitability_claimed is False
    assert report.execution_enabled is False
    assert report.live_capital_authorized is False
    assert report.orders_submitted == 0


def test_protected_holdout_and_parameter_mismatch_fail_closed() -> None:
    protected = _case(9, "holdout", positive_long=True)
    with pytest.raises(LightGBMScorerError, match="protected holdout"):
        train_lightgbm_scorer(
            cases=(*_cases(), protected),
            parameters=_parameters(),
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
            policy=LightGBMTrainingPolicy(num_boost_round=4, calibration_bins=4),
        )

    artifact = train_lightgbm_scorer(
        cases=_cases(),
        parameters=_parameters(),
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=LightGBMTrainingPolicy(num_boost_round=4, calibration_bins=4),
    )
    mismatched = replace(_parameters(), parameter_version="different-model-input")
    with pytest.raises(LightGBMScorerError, match="parameters do not match"):
        evaluate_lightgbm_against_baseline(
            artifact=artifact,
            cases=_cases(),
            parameters=mismatched,
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        )


def test_empty_calibration_bins_do_not_invent_confidence() -> None:
    curve = _fit_calibration((0.01, 0.02), (0, 0), bins=10)

    assert curve.probabilities == (Decimal("0.250000000000"),) * 10


def test_leading_empty_calibration_bins_remain_unsupported() -> None:
    curve = _fit_calibration((0.75,), (1,), bins=10)

    assert curve.probabilities[:7] == (Decimal("0"),) * 7
    assert curve.probabilities[7:] == (Decimal("0.666666666667"),) * 3
