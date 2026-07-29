from __future__ import annotations

from typing import Any, Self

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex


class FeatureParameterReadModel(ContractModel):
    name: NonEmptyStr
    kinds: tuple[NonEmptyStr, ...]
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[Any, ...] = ()


class FeatureRegistryFeature(ContractModel):
    feature_id: NonEmptyStr
    status: NonEmptyStr
    approved_for_ai: bool
    research_only: bool
    roles: tuple[NonEmptyStr, ...]
    inputs: tuple[NonEmptyStr, ...]
    dependencies: tuple[NonEmptyStr, ...]
    required_sources: tuple[NonEmptyStr, ...]
    parameters: tuple[FeatureParameterReadModel, ...]
    constraints: tuple[NonEmptyStr, ...]
    warmup: NonEmptyStr
    timestamp_policy: NonEmptyStr
    normalization_policy: NonEmptyStr
    license_origin: NonEmptyStr
    definition_sha256: Sha256Hex
    execution_authority: bool = False

    @model_validator(mode="after")
    def forbid_execution_authority(self) -> Self:
        if self.execution_authority:
            raise ValueError("feature registry metadata cannot grant execution authority")
        return self


class FeatureRegistrySnapshot(ContractModel):
    registry_version: NonEmptyStr
    manifest_sha256: Sha256Hex
    snapshot_sha256: Sha256Hex
    feature_count: int = Field(ge=0)
    features: tuple[FeatureRegistryFeature, ...]
    execution_authority: bool = False

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.feature_count != len(self.features):
            raise ValueError("feature_count must match features")
        if self.execution_authority:
            raise ValueError("feature registry snapshot cannot grant execution authority")
        return self


class FeatureDependencyResolution(ContractModel):
    registry_version: NonEmptyStr
    snapshot_sha256: Sha256Hex
    requested_feature_ids: tuple[NonEmptyStr, ...]
    resolved_feature_ids: tuple[NonEmptyStr, ...]
    execution_authority: bool = False

    @model_validator(mode="after")
    def forbid_execution_authority(self) -> Self:
        if self.execution_authority:
            raise ValueError("dependency resolution cannot grant execution authority")
        return self


class FeatureRegistryReplayRecord(ContractModel):
    sequence: int = Field(ge=0)
    feature_id: NonEmptyStr
    definition_sha256: Sha256Hex


class FeatureRegistryReplay(ContractModel):
    registry_version: NonEmptyStr
    manifest_sha256: Sha256Hex
    snapshot_sha256: Sha256Hex
    replay_sha256: Sha256Hex
    append_only: bool = True
    record_count: int = Field(ge=0)
    records: tuple[FeatureRegistryReplayRecord, ...]
    execution_authority: bool = False

    @model_validator(mode="after")
    def validate_replay(self) -> Self:
        if not self.append_only:
            raise ValueError("feature registry replay must be append-only")
        if self.record_count != len(self.records):
            raise ValueError("record_count must match records")
        if tuple(record.sequence for record in self.records) != tuple(range(self.record_count)):
            raise ValueError("feature registry replay sequence must be contiguous")
        if self.execution_authority:
            raise ValueError("feature registry replay cannot grant execution authority")
        return self
