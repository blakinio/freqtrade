from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, localcontext
from hashlib import sha256

from ai_platform.portal.telemetry.schema import (
    DistributionAggregate,
    DriftAssessment,
    DriftHealthStatus,
    DriftPolicy,
    FeatureQualityAggregate,
    InferenceTelemetryEnvelope,
    TelemetryWindowRole,
)


PSI_V1 = DriftPolicy(
    policy_version="psi-v1",
    method="population-stability-index",
    minimum_samples=100,
    attention_threshold=Decimal("0.100000"),
    degraded_threshold=Decimal("0.250000"),
    feature_quality_attention_rate=Decimal("0.010000"),
    feature_quality_degraded_rate=Decimal("0.050000"),
    smoothing_epsilon=Decimal("0.000001"),
)

_SCORE_QUANTUM = Decimal("0.000001")


def population_stability_index(
    reference: DistributionAggregate,
    observation: DistributionAggregate,
    *,
    epsilon: Decimal,
) -> Decimal:
    if reference.bucket_ids != observation.bucket_ids:
        raise ValueError("distribution bucket identities are incompatible")

    reference_total = Decimal(reference.total_count)
    observation_total = Decimal(observation.total_count)
    score = Decimal("0")
    with localcontext() as context:
        context.prec = 28
        for reference_bucket, observation_bucket in zip(
            reference.buckets,
            observation.buckets,
            strict=True,
        ):
            reference_rate = max(Decimal(reference_bucket.count) / reference_total, epsilon)
            observation_rate = max(
                Decimal(observation_bucket.count) / observation_total,
                epsilon,
            )
            score += (observation_rate - reference_rate) * (
                observation_rate / reference_rate
            ).ln()
    return max(score, Decimal("0")).quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def _assessment_id(
    reference: InferenceTelemetryEnvelope,
    observation: InferenceTelemetryEnvelope,
    policy: DriftPolicy,
) -> str:
    canonical = "|".join(
        (
            reference.scope.tenant_id,
            reference.scope.model_version_id,
            reference.scope.bot_id,
            reference.scope.runtime_id,
            reference.scope.bot_config_revision_id,
            str(reference.telemetry_id),
            str(observation.telemetry_id),
            policy.policy_version,
        )
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _quality_issue_rate(feature: FeatureQualityAggregate) -> Decimal:
    return (
        Decimal(feature.missing_count + feature.invalid_count) / Decimal(feature.total_count)
    ).quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def _base_assessment(
    reference: InferenceTelemetryEnvelope,
    observation: InferenceTelemetryEnvelope,
    *,
    policy: DriftPolicy,
    assessed_at: datetime,
    status: DriftHealthStatus,
    reason_code: str,
    prediction_drift_score: Decimal | None = None,
    max_feature_drift_score: Decimal | None = None,
    worst_feature_name: str | None = None,
    max_feature_quality_issue_rate: Decimal | None = None,
) -> DriftAssessment:
    return DriftAssessment(
        assessment_id=_assessment_id(reference, observation, policy),
        scope=observation.scope,
        reference_telemetry_id=reference.telemetry_id,
        reference_window_id=reference.window.window_id,
        observation_telemetry_id=observation.telemetry_id,
        observation_window_id=observation.window.window_id,
        assessed_at=assessed_at,
        policy=policy,
        status=status,
        reason_code=reason_code,
        reference_sample_count=reference.prediction_count,
        observation_sample_count=observation.prediction_count,
        accepted_predictions=observation.accepted_predictions,
        rejected_predictions=observation.rejected_predictions,
        rejection_reasons=observation.rejection_reasons,
        prediction_drift_score=prediction_drift_score,
        max_feature_drift_score=max_feature_drift_score,
        worst_feature_name=worst_feature_name,
        max_feature_quality_issue_rate=max_feature_quality_issue_rate,
    )


def assess_drift(
    reference: InferenceTelemetryEnvelope,
    observation: InferenceTelemetryEnvelope,
    *,
    assessed_at: datetime,
    policy: DriftPolicy = PSI_V1,
) -> DriftAssessment:
    if reference.role is not TelemetryWindowRole.REFERENCE:
        raise ValueError("reference envelope must use REFERENCE role")
    if observation.role is not TelemetryWindowRole.OBSERVATION:
        raise ValueError("observation envelope must use OBSERVATION role")
    if reference.scope != observation.scope:
        raise ValueError("reference and observation scopes must match exactly")

    if (
        reference.prediction_count < policy.minimum_samples
        or observation.prediction_count < policy.minimum_samples
    ):
        return _base_assessment(
            reference,
            observation,
            policy=policy,
            assessed_at=assessed_at,
            status=DriftHealthStatus.INSUFFICIENT_EVIDENCE,
            reason_code="MINIMUM_SAMPLE_COUNT_NOT_MET",
        )

    if reference.prediction_distribution.bucket_ids != (
        observation.prediction_distribution.bucket_ids
    ):
        return _base_assessment(
            reference,
            observation,
            policy=policy,
            assessed_at=assessed_at,
            status=DriftHealthStatus.INSUFFICIENT_EVIDENCE,
            reason_code="PREDICTION_DISTRIBUTION_BUCKETS_INCOMPATIBLE",
        )

    reference_features = {feature.feature_name: feature for feature in reference.feature_quality}
    observation_features = {
        feature.feature_name: feature for feature in observation.feature_quality
    }
    if set(reference_features) != set(observation_features):
        return _base_assessment(
            reference,
            observation,
            policy=policy,
            assessed_at=assessed_at,
            status=DriftHealthStatus.INSUFFICIENT_EVIDENCE,
            reason_code="FEATURE_AGGREGATES_INCOMPATIBLE",
        )

    for feature_name in sorted(reference_features):
        reference_distribution = reference_features[feature_name].distribution
        observation_distribution = observation_features[feature_name].distribution
        if reference_distribution is None or observation_distribution is None:
            return _base_assessment(
                reference,
                observation,
                policy=policy,
                assessed_at=assessed_at,
                status=DriftHealthStatus.INSUFFICIENT_EVIDENCE,
                reason_code="FEATURE_DISTRIBUTION_UNAVAILABLE",
            )
        if reference_distribution.bucket_ids != observation_distribution.bucket_ids:
            return _base_assessment(
                reference,
                observation,
                policy=policy,
                assessed_at=assessed_at,
                status=DriftHealthStatus.INSUFFICIENT_EVIDENCE,
                reason_code="FEATURE_DISTRIBUTION_BUCKETS_INCOMPATIBLE",
            )

    prediction_score = population_stability_index(
        reference.prediction_distribution,
        observation.prediction_distribution,
        epsilon=policy.smoothing_epsilon,
    )
    feature_scores: dict[str, Decimal] = {}
    for feature_name in sorted(reference_features):
        reference_distribution = reference_features[feature_name].distribution
        observation_distribution = observation_features[feature_name].distribution
        assert reference_distribution is not None
        assert observation_distribution is not None
        feature_scores[feature_name] = population_stability_index(
            reference_distribution,
            observation_distribution,
            epsilon=policy.smoothing_epsilon,
        )

    worst_feature_name = max(feature_scores, key=lambda name: (feature_scores[name], name))
    max_feature_score = feature_scores[worst_feature_name]
    max_quality_rate = max(
        _quality_issue_rate(feature) for feature in observation.feature_quality
    )

    if max_quality_rate >= policy.feature_quality_degraded_rate:
        status = DriftHealthStatus.DEGRADED
        reason_code = "FEATURE_QUALITY_DEGRADED"
    elif max(prediction_score, max_feature_score) >= policy.degraded_threshold:
        status = DriftHealthStatus.DEGRADED
        reason_code = "PSI_V1_DEGRADED"
    elif max_quality_rate >= policy.feature_quality_attention_rate:
        status = DriftHealthStatus.ATTENTION
        reason_code = "FEATURE_QUALITY_ATTENTION"
    elif max(prediction_score, max_feature_score) >= policy.attention_threshold:
        status = DriftHealthStatus.ATTENTION
        reason_code = "PSI_V1_ATTENTION"
    else:
        status = DriftHealthStatus.HEALTHY
        reason_code = "PSI_V1_WITHIN_LIMITS"

    return _base_assessment(
        reference,
        observation,
        policy=policy,
        assessed_at=assessed_at,
        status=status,
        reason_code=reason_code,
        prediction_drift_score=prediction_score,
        max_feature_drift_score=max_feature_score,
        worst_feature_name=worst_feature_name,
        max_feature_quality_issue_rate=max_quality_rate,
    )
