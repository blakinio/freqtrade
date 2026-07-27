from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    CandidateScore,
    LiquidationFeatureVector,
    ModelPromotionState,
    ScoreKind,
    WickHunterCandidate,
)
from ai_platform.wickhunter.parameters import WickHunterParameters


class CandidateScorer(Protocol):
    def score(
        self,
        *,
        candidate: WickHunterCandidate,
        features: LiquidationFeatureVector,
        parameters: WickHunterParameters,
    ) -> CandidateScore: ...


def _clamp(value: Decimal, minimum: Decimal, maximum: Decimal) -> Decimal:
    return max(minimum, min(maximum, value))


class DeterministicBaselineScorer:
    scorer_version = "wickhunter-deterministic-baseline-score-v1"

    def score(
        self,
        *,
        candidate: WickHunterCandidate,
        features: LiquidationFeatureVector,
        parameters: WickHunterParameters,
    ) -> CandidateScore:
        percentile_component = features.maximum_event_percentile
        zscore_component = _clamp(
            features.maximum_event_zscore / Decimal("6"), Decimal(0), Decimal(1)
        )
        burst_component = _clamp(
            features.liquidation_burst_intensity / Decimal("4"), Decimal(0), Decimal(1)
        )
        confidence = (
            percentile_component
            + zscore_component
            + burst_component
            + features.source_coverage_ratio
        ) / Decimal(4)
        confidence = _clamp(confidence, Decimal(0), Decimal(1)).quantize(Decimal("0.000001"))
        bounded_multiplier = _clamp(
            confidence,
            parameters.minimum_risk_multiplier,
            parameters.maximum_risk_multiplier,
        ).quantize(Decimal("0.000001"))
        score_id = canonical_sha256(
            {
                "scorer_version": self.scorer_version,
                "candidate_id": candidate.candidate_id,
                "feature_hash": features.feature_hash,
                "confidence": confidence,
                "bounded_risk_multiplier": bounded_multiplier,
            }
        )
        return CandidateScore(
            score_id=score_id,
            kind=ScoreKind.DETERMINISTIC_BASELINE,
            candidate_id=candidate.candidate_id,
            feature_hash=features.feature_hash,
            confidence=confidence,
            expected_return_after_costs=None,
            bounded_risk_multiplier=bounded_multiplier,
            model_version=None,
            model_hash=None,
            promotion_state=ModelPromotionState.BASELINE,
            scored_at_ms=features.decision_timestamp_ms,
        )


def validated_external_model_score(
    *,
    candidate: WickHunterCandidate,
    feature_hash: str,
    confidence: Decimal,
    expected_return_after_costs: Decimal,
    bounded_risk_multiplier: Decimal,
    model_version: str,
    model_hash: str,
    promotion_state: ModelPromotionState,
    scored_at_ms: int,
) -> CandidateScore:
    score_id = canonical_sha256(
        {
            "candidate_id": candidate.candidate_id,
            "feature_hash": feature_hash,
            "confidence": confidence,
            "expected_return_after_costs": expected_return_after_costs,
            "bounded_risk_multiplier": bounded_risk_multiplier,
            "model_version": model_version,
            "model_hash": model_hash,
            "promotion_state": promotion_state.value,
            "scored_at_ms": scored_at_ms,
        }
    )
    return CandidateScore(
        score_id=score_id,
        kind=ScoreKind.SUPERVISED_MODEL,
        candidate_id=candidate.candidate_id,
        feature_hash=feature_hash,
        confidence=confidence,
        expected_return_after_costs=expected_return_after_costs,
        bounded_risk_multiplier=bounded_risk_multiplier,
        model_version=model_version,
        model_hash=model_hash,
        promotion_state=promotion_state,
        scored_at_ms=scored_at_ms,
    )
