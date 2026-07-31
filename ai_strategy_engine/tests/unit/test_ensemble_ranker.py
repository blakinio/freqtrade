from dataclasses import replace
from decimal import Decimal
from typing import Literal

from strategy_engine.ai.ensemble_ranker import (
    CandidateEvidence,
    RankingManifest,
    RankingPolicy,
    rank_candidates,
)

MetricsScope = Literal["oos_trading", "training_only"]


def candidate(
    candidate_id: str,
    *,
    profit: str = "0.30",
    stability: str = "0.80",
    correlation: str = "0.20",
    drawdown: str = "0.10",
    calibration: str = "0.05",
    validation_passed: bool = True,
    immutable: bool = True,
    metrics_scope: MetricsScope = "oos_trading",
    oos_timerange: str = "20260501-20260630",
    protected_holdout_used: bool = False,
) -> CandidateEvidence:
    return CandidateEvidence(
        candidate_id=candidate_id,
        model_version_id=f"model-{candidate_id}",
        experiment_id=f"experiment-{candidate_id}",
        experiment_result_hash="a" * 64,
        validation_report_hash="d" * 64,
        feature_registry_identity="registry-v1",
        config_identity="config-v1",
        data_identity="data-v1",
        routing_evidence_hash="b" * 64,
        oos_timerange=oos_timerange,
        oos_profit=Decimal(profit),
        oos_stability=Decimal(stability),
        max_abs_correlation=Decimal(correlation),
        drawdown_contribution=Decimal(drawdown),
        calibration_error=Decimal(calibration),
        trade_count=50,
        validation_passed=validation_passed,
        evidence_immutable=immutable,
        research_only=True,
        order_submission_performed=False,
        metrics_scope=metrics_scope,
        protected_holdout_used=protected_holdout_used,
    )


def manifest(candidates: tuple[CandidateEvidence, ...]) -> RankingManifest:
    return RankingManifest(
        manifest_id="ranking-v1",
        feature_registry_identity="registry-v1",
        config_identity="config-v1",
        data_identity="data-v1",
        routing_evidence_hash="b" * 64,
        candidates=candidates,
    )


def test_ranking_exposes_every_penalty_without_selection_or_promotion() -> None:
    result = rank_candidates(
        manifest((candidate("a"), candidate("b", profit="0.20", correlation="0.90"))),
        RankingPolicy(policy_id="rank-v1"),
    )

    first = result.rankings[0]
    assert first.candidate_id == "a"
    assert first.eligible is True
    assert first.oos_profit_component == Decimal("0.300000")
    assert first.correlation_penalty == Decimal("0.040000")
    assert first.instability_penalty == Decimal("0.040000")
    assert first.drawdown_penalty == Decimal("0.025000")
    assert first.calibration_penalty == Decimal("0.007500")
    assert first.score == Decimal("0.187500")
    assert result.proposed_candidates == ("a", "b")
    assert result.selected_model is None
    assert result.promotion_authorized is False
    assert result.execution_authorized is False
    assert result.risk_core_bypassed is False
    assert result.active_model_mutated is False


def test_same_manifest_ranking_is_input_order_independent() -> None:
    first = rank_candidates(
        manifest((candidate("a"), candidate("b"))),
        RankingPolicy(policy_id="rank-v1"),
    )
    second = rank_candidates(
        manifest((candidate("b"), candidate("a"))),
        RankingPolicy(policy_id="rank-v1"),
    )

    assert first == second


def test_invalid_metric_ranges_fail_closed() -> None:
    row = rank_candidates(
        manifest(
            (
                candidate(
                    "bad",
                    stability="1.1",
                    correlation="-0.1",
                    drawdown="1.2",
                    calibration="1.01",
                ),
            )
        ),
        RankingPolicy(policy_id="rank-v1"),
    ).rankings[0]

    assert row.eligible is False
    assert row.score is None
    assert "OOS_STABILITY_MISSING_OR_INVALID" in row.reason_codes
    assert "CORRELATION_MISSING_OR_INVALID" in row.reason_codes
    assert "DRAWDOWN_CONTRIBUTION_MISSING_OR_INVALID" in row.reason_codes
    assert "CALIBRATION_MISSING_OR_INVALID" in row.reason_codes


def test_training_only_mutable_or_unvalidated_evidence_is_ineligible() -> None:
    row = rank_candidates(
        manifest(
            (
                candidate(
                    "bad",
                    validation_passed=False,
                    immutable=False,
                    metrics_scope="training_only",
                ),
            )
        ),
        RankingPolicy(policy_id="rank-v1"),
    ).rankings[0]

    assert row.eligible is False
    assert "VALIDATION_REQUIRED" in row.reason_codes
    assert "IMMUTABLE_EVIDENCE_REQUIRED" in row.reason_codes
    assert "OOS_TRADING_METRICS_REQUIRED" in row.reason_codes


def test_metric_boundaries_are_valid_and_penalties_remain_visible() -> None:
    row = rank_candidates(
        manifest(
            (
                candidate(
                    "edge",
                    profit="0",
                    stability="0",
                    correlation="1",
                    drawdown="1",
                    calibration="1",
                ),
            )
        ),
        RankingPolicy(policy_id="rank-v1"),
    ).rankings[0]

    assert row.eligible is True
    assert row.correlation_penalty == Decimal("0.200000")
    assert row.instability_penalty == Decimal("0.200000")
    assert row.drawdown_penalty == Decimal("0.250000")
    assert row.calibration_penalty == Decimal("0.150000")


def test_protected_holdout_and_selected_model_guards_fail_closed() -> None:
    guarded = replace(
        manifest(
            (
                candidate(
                    "a",
                    protected_holdout_used=True,
                    oos_timerange="20260801-20260930",
                ),
            )
        ),
        protected_holdout_used=True,
        selected_model="candidate-a",
    )
    result = rank_candidates(guarded, RankingPolicy(policy_id="rank-v1"))

    row = result.rankings[0]
    assert row.eligible is False
    assert "PROTECTED_HOLDOUT_FORBIDDEN" in row.reason_codes
    assert "PROTECTED_HOLDOUT_TIMERANGE_FORBIDDEN" in row.reason_codes
    assert "SELECTED_MODEL_MUST_REMAIN_NULL" in row.reason_codes
    assert result.proposed_candidates == ()
    assert result.selected_model is None


def test_duplicate_candidate_identity_is_ambiguous_and_fail_closed() -> None:
    result = rank_candidates(
        manifest((candidate("same"), candidate("same", profit="0.50"))),
        RankingPolicy(policy_id="rank-v1"),
    )

    assert all(row.eligible is False for row in result.rankings)
    assert all("AMBIGUOUS_CANDIDATE_ID" in row.reason_codes for row in result.rankings)
