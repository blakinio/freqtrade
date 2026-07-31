from dataclasses import dataclass
from decimal import Decimal

from strategy_engine.ai.ensemble_ranker import (
    CandidateEvidence,
    RankingManifest,
    RankingPolicy,
    rank_candidates,
)
from strategy_engine.ai.regime_router import (
    DriftEvidence,
    FeatureEvidence,
    RegimeManifest,
    RegimePolicy,
    liquidation_evidence_from_alignment,
    route_regime,
)
from strategy_engine.research.liquidation_alignment import (
    MarketObservation,
    ObservationKind,
    align_liquidation_context,
)


@dataclass(frozen=True, slots=True)
class LiquidationFixture:
    schema_version: int = 1
    source: str = "bybit-linear"
    source_event_id: str = "liq-1"
    symbol: str = "BTCUSDT"
    occurred_at_ms: int = 10_000
    received_at_ms: int = 10_050


def observation(kind: ObservationKind, event_id: str, value: str) -> MarketObservation:
    return MarketObservation(
        schema_version=1,
        data_version="market-v1",
        source="bybit-linear",
        source_event_id=event_id,
        symbol="BTCUSDT",
        kind=kind,
        event_time_ms=9_900,
        received_at_ms=9_910,
        available_at_ms=9_920,
        value=Decimal(value),
    )


def candidate(candidate_id: str, route_hash: str, profit: str) -> CandidateEvidence:
    return CandidateEvidence(
        candidate_id=candidate_id,
        model_version_id=f"model-{candidate_id}-v1",
        experiment_id=f"experiment-{candidate_id}",
        experiment_result_hash=("a" if candidate_id == "a" else "c") * 64,
        validation_report_hash="d" * 64,
        feature_registry_identity="feature-registry-v1",
        config_identity="ranking-config-v1",
        data_identity="oos-data-v1",
        routing_evidence_hash=route_hash,
        oos_timerange="20260501-20260630",
        oos_profit=Decimal(profit),
        oos_stability=Decimal("1.0"),
        max_abs_correlation=Decimal("0.10"),
        drawdown_contribution=Decimal("0.05"),
        calibration_error=Decimal("0.02"),
        trade_count=40,
        validation_passed=True,
        evidence_immutable=True,
        research_only=True,
        order_submission_performed=False,
        metrics_scope="oos_trading",
    )


def test_routing_and_ranking_evidence_is_identity_bound_deterministic_and_non_authoritative() -> (
    None
):
    alignment = align_liquidation_context(
        LiquidationFixture(),
        [
            observation(ObservationKind.OPEN_INTEREST, "oi-1", "100"),
            observation(ObservationKind.FUNDING_RATE, "funding-1", "-0.0001"),
        ],
        expected_sources=["bybit-linear"],
        max_age_ms=1_000,
    )
    liquidation = liquidation_evidence_from_alignment(
        alignment,
        expected_sources=["bybit-linear"],
        severity_score=Decimal("2.5"),
        data_identity="route-data-v1",
    )
    route_manifest = RegimeManifest(
        model_version_id="router-model-v1",
        feature_registry_identity="feature-registry-v1",
        config_identity="router-config-v1",
        data_identity="route-data-v1",
        as_of_ms=10_050,
        evidence_timerange="20260701-20260731",
        approved_feature_ids=("atr.v1", "roc.v1"),
        features=(
            FeatureEvidence(
                "roc.v1",
                "1.0.0",
                Decimal("0.02"),
                10_000,
                "feature-registry-v1",
                "route-data-v1",
                "router-config-v1",
                True,
            ),
            FeatureEvidence(
                "atr.v1",
                "1.0.0",
                Decimal("0.03"),
                10_000,
                "feature-registry-v1",
                "route-data-v1",
                "router-config-v1",
                True,
            ),
        ),
        liquidation=liquidation,
        drift=DriftEvidence(
            "drift-v1",
            Decimal("0.05"),
            10_020,
            "feature-schema-v1",
            "reference-data-v1",
            "route-data-v1",
        ),
    )
    route_first = route_regime(route_manifest, RegimePolicy(policy_id="router-policy-v1"))
    route_second = route_regime(route_manifest, RegimePolicy(policy_id="router-policy-v1"))

    ranking_manifest = RankingManifest(
        manifest_id="ensemble-ranking-v1",
        feature_registry_identity="feature-registry-v1",
        config_identity="ranking-config-v1",
        data_identity="oos-data-v1",
        routing_evidence_hash=route_first.evidence_hash,
        candidates=(
            candidate("b", route_first.evidence_hash, "0.10"),
            candidate("a", route_first.evidence_hash, "0.20"),
        ),
    )
    ranking_first = rank_candidates(ranking_manifest, RankingPolicy(policy_id="rank-policy-v1"))
    ranking_second = rank_candidates(ranking_manifest, RankingPolicy(policy_id="rank-policy-v1"))

    assert route_first == route_second
    assert route_first.ranking_allowed is True
    assert ranking_first == ranking_second
    assert ranking_first.proposed_candidates == ("a", "b")
    assert ranking_first.selected_model is None
    assert ranking_first.promotion_authorized is False
    assert ranking_first.execution_authorized is False
    assert route_first.risk_core_bypassed is False
    assert ranking_first.risk_core_bypassed is False
    assert ranking_first.active_model_mutated is False
