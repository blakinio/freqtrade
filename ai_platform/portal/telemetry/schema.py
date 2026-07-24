from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime


class TelemetryWindowRole(StrEnum):
    REFERENCE = "REFERENCE"
    OBSERVATION = "OBSERVATION"


class TelemetrySourceAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class DriftHealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    ATTENTION = "ATTENTION"
    DEGRADED = "DEGRADED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"


class InferenceTelemetryScope(ContractModel):
    tenant_id: NonEmptyStr
    model_version_id: NonEmptyStr
    feature_schema_version_id: NonEmptyStr
    bot_id: NonEmptyStr
    bot_config_revision: PositiveInt
    bot_config_revision_id: NonEmptyStr
    runtime_id: NonEmptyStr
    source_id: NonEmptyStr


class TelemetryWindow(ContractModel):
    window_id: NonEmptyStr
    start_at: UtcDateTime
    end_at: UtcDateTime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end_at <= self.start_at:
            raise ValueError("telemetry window end_at must be after start_at")
        return self


class ReasonCount(ContractModel):
    reason_code: NonEmptyStr
    count: int = Field(ge=0)


class DistributionBucket(ContractModel):
    bucket_id: NonEmptyStr
    count: int = Field(ge=0)


class DistributionAggregate(ContractModel):
    distribution_id: NonEmptyStr
    buckets: tuple[DistributionBucket, ...]

    @model_validator(mode="after")
    def validate_buckets(self) -> Self:
        if not self.buckets:
            raise ValueError("distribution must contain at least one bucket")
        bucket_ids = [bucket.bucket_id for bucket in self.buckets]
        if len(set(bucket_ids)) != len(bucket_ids):
            raise ValueError("distribution bucket identities must be unique")
        if self.total_count <= 0:
            raise ValueError("distribution total count must be > 0")
        return self

    @property
    def total_count(self) -> int:
        return sum(bucket.count for bucket in self.buckets)

    @property
    def bucket_ids(self) -> tuple[str, ...]:
        return tuple(bucket.bucket_id for bucket in self.buckets)


class FeatureQualityAggregate(ContractModel):
    feature_name: NonEmptyStr
    present_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    distribution: DistributionAggregate | None = None

    @model_validator(mode="after")
    def validate_distribution(self) -> Self:
        if self.present_count == 0 and self.distribution is not None:
            raise ValueError("feature distribution is not allowed when present_count is zero")
        if self.present_count > 0 and self.distribution is None:
            raise ValueError("feature distribution is required when present_count is positive")
        if self.distribution is not None and self.distribution.total_count != self.present_count:
            raise ValueError("feature distribution total must equal present_count")
        return self

    @property
    def total_count(self) -> int:
        return self.present_count + self.missing_count + self.invalid_count


class InferenceTelemetryEnvelope(ContractModel):
    schema_version: int = 1
    telemetry_id: UUID
    scope: InferenceTelemetryScope
    role: TelemetryWindowRole
    window: TelemetryWindow
    generated_at: UtcDateTime
    accepted_predictions: int = Field(ge=0)
    rejected_predictions: int = Field(ge=0)
    rejection_reasons: tuple[ReasonCount, ...] = ()
    feature_quality: tuple[FeatureQualityAggregate, ...]
    prediction_distribution: DistributionAggregate
    sampling_rate: Decimal = Field(gt=Decimal("0"), le=Decimal("1"))
    aggregate_only: bool = True
    protected_holdout_included: bool = False

    @model_validator(mode="after")
    def validate_envelope(self) -> Self:
        self._validate_contract_flags()
        prediction_count = self._validate_prediction_counts()
        self._validate_rejection_reasons()
        self._validate_feature_quality(prediction_count)
        return self

    def _validate_contract_flags(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not self.aggregate_only:
            raise ValueError("PI-03 accepts aggregate-only telemetry")
        if self.protected_holdout_included:
            raise ValueError("protected final holdout telemetry is forbidden")
        if self.generated_at < self.window.end_at:
            raise ValueError("generated_at must be at or after telemetry window end_at")

    def _validate_prediction_counts(self) -> int:
        prediction_count = self.prediction_count
        if prediction_count <= 0:
            raise ValueError("telemetry window must contain at least one prediction")
        if self.prediction_distribution.total_count != prediction_count:
            raise ValueError("prediction distribution total must equal prediction count")
        return prediction_count

    def _validate_rejection_reasons(self) -> None:
        reason_codes = [reason.reason_code for reason in self.rejection_reasons]
        if len(set(reason_codes)) != len(reason_codes):
            raise ValueError("rejection reason codes must be unique")
        if sum(reason.count for reason in self.rejection_reasons) != self.rejected_predictions:
            raise ValueError("rejection reason counts must equal rejected_predictions")

    def _validate_feature_quality(self, prediction_count: int) -> None:
        if not self.feature_quality:
            raise ValueError("feature_quality must contain at least one feature aggregate")
        feature_names = [feature.feature_name for feature in self.feature_quality]
        if len(set(feature_names)) != len(feature_names):
            raise ValueError("feature aggregates must use unique feature names")
        for feature in self.feature_quality:
            if feature.total_count != prediction_count:
                raise ValueError("each feature aggregate total must equal prediction count")

    @property
    def prediction_count(self) -> int:
        return self.accepted_predictions + self.rejected_predictions


class InferenceTelemetrySourceStatus(ContractModel):
    schema_version: int = 1
    scope: InferenceTelemetryScope
    availability: TelemetrySourceAvailability
    checked_at: UtcDateTime
    reason_code: NonEmptyStr

    @model_validator(mode="after")
    def validate_schema_version(self) -> Self:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        return self


class DriftPolicy(ContractModel):
    policy_version: NonEmptyStr
    method: NonEmptyStr
    minimum_samples: PositiveInt
    attention_threshold: Decimal = Field(gt=Decimal("0"))
    degraded_threshold: Decimal = Field(gt=Decimal("0"))
    feature_quality_attention_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    feature_quality_degraded_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    smoothing_epsilon: Decimal = Field(gt=Decimal("0"), lt=Decimal("1"))

    @model_validator(mode="after")
    def validate_threshold_order(self) -> Self:
        if self.degraded_threshold <= self.attention_threshold:
            raise ValueError("degraded_threshold must be greater than attention_threshold")
        if self.feature_quality_degraded_rate <= self.feature_quality_attention_rate:
            raise ValueError("feature_quality_degraded_rate must be greater than attention rate")
        return self


class DriftAssessment(ContractModel):
    assessment_id: NonEmptyStr
    scope: InferenceTelemetryScope
    reference_telemetry_id: UUID
    reference_window_id: NonEmptyStr
    observation_telemetry_id: UUID
    observation_window_id: NonEmptyStr
    assessed_at: UtcDateTime
    policy: DriftPolicy
    status: DriftHealthStatus
    reason_code: NonEmptyStr
    reference_sample_count: int = Field(ge=0)
    observation_sample_count: int = Field(ge=0)
    accepted_predictions: int = Field(ge=0)
    rejected_predictions: int = Field(ge=0)
    rejection_reasons: tuple[ReasonCount, ...]
    prediction_drift_score: Decimal | None = Field(default=None, ge=Decimal("0"))
    max_feature_drift_score: Decimal | None = Field(default=None, ge=Decimal("0"))
    worst_feature_name: NonEmptyStr | None = None
    max_feature_quality_issue_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )


class ModelHealthRecord(ContractModel):
    health_record_id: NonEmptyStr
    model_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    model_family_id: NonEmptyStr
    lifecycle_state: NonEmptyStr
    created_at: UtcDateTime
    training_window_end: UtcDateTime
    metadata_age_days: int = Field(ge=0)
    drift_status: DriftHealthStatus
    drift_reason: NonEmptyStr
    policy_version: NonEmptyStr | None = None
    reference_window_id: NonEmptyStr | None = None
    observation_window_id: NonEmptyStr | None = None
    reference_sample_count: int = Field(default=0, ge=0)
    observation_sample_count: int = Field(default=0, ge=0)
    accepted_predictions: int = Field(default=0, ge=0)
    rejected_predictions: int = Field(default=0, ge=0)
    rejection_reasons: tuple[ReasonCount, ...] = ()
    prediction_drift_score: Decimal | None = Field(default=None, ge=Decimal("0"))
    max_feature_drift_score: Decimal | None = Field(default=None, ge=Decimal("0"))
    worst_feature_name: NonEmptyStr | None = None
    max_feature_quality_issue_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )
    feature_schema_version_id: NonEmptyStr | None = None
    bot_id: NonEmptyStr | None = None
    bot_config_revision_id: NonEmptyStr | None = None
    runtime_id: NonEmptyStr | None = None
    source_id: NonEmptyStr | None = None
    source_availability: TelemetrySourceAvailability = TelemetrySourceAvailability.UNAVAILABLE
    source_checked_at: UtcDateTime | None = None
