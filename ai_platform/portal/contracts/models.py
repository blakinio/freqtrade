from __future__ import annotations

import json
from enum import StrEnum
from typing import Self

from pydantic import field_validator, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime


class ModelLifecycleState(StrEnum):
    EXPERIMENTAL = "EXPERIMENTAL"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    PROMOTED = "PROMOTED"
    DRY_RUN = "DRY_RUN"
    SHADOW = "SHADOW"
    LIVE_SMALL = "LIVE_SMALL"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


class TrainingWindow(ContractModel):
    start_at: UtcDateTime
    end_at: UtcDateTime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end_at <= self.start_at:
            raise ValueError("training window end_at must be after start_at")
        return self


class ModelFamily(ContractModel):
    model_family_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: NonEmptyStr
    framework: NonEmptyStr


class FeatureSchemaVersion(ContractModel):
    feature_schema_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    feature_names: tuple[NonEmptyStr, ...]
    schema_hash: Sha256Hex
    code_revision: NonEmptyStr

    @model_validator(mode="after")
    def validate_features(self) -> Self:
        if not self.feature_names:
            raise ValueError("feature schema must contain at least one feature")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature schema contains duplicate feature names")
        return self


class DatasetVersion(ContractModel):
    dataset_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    source_manifest_hash: Sha256Hex
    integrity_hash: Sha256Hex
    training_window: TrainingWindow
    created_at: UtcDateTime


class TrainingPipelineVersion(ContractModel):
    training_pipeline_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    code_revision: NonEmptyStr
    pipeline_hash: Sha256Hex


class ExperimentReference(ContractModel):
    experiment_id: NonEmptyStr
    tenant_id: NonEmptyStr
    run_id: NonEmptyStr


class ModelParameter(ContractModel):
    name: NonEmptyStr
    value_json: NonEmptyStr

    @field_validator("value_json")
    @classmethod
    def validate_json_value(cls, value: str) -> str:
        parsed = json.loads(value)
        canonical = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if value != canonical:
            raise ValueError("model parameter value_json must use canonical JSON encoding")
        return value


class ModelVersion(ContractModel):
    model_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    model_family_id: NonEmptyStr
    artifact_id: NonEmptyStr
    artifact_sha256: Sha256Hex
    feature_schema_version_id: NonEmptyStr
    dataset_version_id: NonEmptyStr
    training_window: TrainingWindow
    training_pipeline_version_id: NonEmptyStr
    parameters: tuple[ModelParameter, ...]
    git_revision: NonEmptyStr
    created_at: UtcDateTime
    lifecycle_state: ModelLifecycleState
    experiment_reference: ExperimentReference | None = None

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        parameter_names = [parameter.name for parameter in self.parameters]
        if len(set(parameter_names)) != len(parameter_names):
            raise ValueError("model parameters must have unique names")
        if self.experiment_reference and self.experiment_reference.tenant_id != self.tenant_id:
            raise ValueError("experiment reference must belong to the same tenant")
        return self
