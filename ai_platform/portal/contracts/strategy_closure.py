from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, JsonValue, PositiveInt, field_validator, model_validator

from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.product.schema import StrategyCatalogEntry, StrategyLifecycleState

_SENSITIVE_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "credential",
    "private_key",
    "api_key",
    "vault_path",
    "private_endpoint",
)


def _reject_sensitive_metadata(value: JsonValue, path: str = "metadata") -> JsonValue:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                raise ValueError(f"sensitive metadata key is forbidden: {path}.{key}")
            _reject_sensitive_metadata(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_metadata(child, f"{path}[{index}]")
    return value


class ClosureContractModel(ContractModel):
    contract_version: Literal["v2"] = "v2"


class ResearchAuthority(StrEnum):
    RESEARCH_ONLY = "research_only"


class StrategyCapability(StrEnum):
    STRATEGY_READ = "strategy.read"
    STRATEGY_RESEARCH = "strategy.research"
    EXPERIMENT_SUBMIT = "experiment.submit"
    STRATEGY_APPROVE = "strategy.approve"
    STRATEGY_DEPLOY_DRY_RUN = "strategy.deploy_dry_run"
    STRATEGY_ROLLBACK_DRY_RUN = "strategy.rollback_dry_run"


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StrategyDeploymentMode(StrEnum):
    SIMULATED = "SIMULATED"
    DRY_RUN = "DRY_RUN"
    SHADOW = "SHADOW"


class StrategyDeploymentState(StrEnum):
    REQUESTED = "REQUESTED"
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class PublicContractProvenance(ClosureContractModel):
    producer: NonEmptyStr
    artifact_id: NonEmptyStr
    created_at: UtcDateTime
    source_refs: tuple[NonEmptyStr, ...] = ()
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    _exclude_secrets = field_validator("metadata")(_reject_sensitive_metadata)


class ClosureRequestContext(ClosureContractModel):
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    actor_type: ActorType
    resource_type: NonEmptyStr
    resource_id: NonEmptyStr
    environment: Environment
    execution_mode: ExecutionMode
    correlation: CorrelationContext
    provenance: PublicContractProvenance
    authority: Literal[ResearchAuthority.RESEARCH_ONLY] = ResearchAuthority.RESEARCH_ONLY


class CapabilityRequirement(ClosureContractModel):
    capability: StrategyCapability
    authorization_decision_ref: NonEmptyStr
    enforced: Literal[True] = True


class SignalWizardFeatureSelection(ClosureContractModel):
    feature_id: NonEmptyStr
    timeframe: NonEmptyStr
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    enabled: bool = True

    _exclude_parameter_secrets = field_validator("parameters")(_reject_sensitive_metadata)


class SignalWizardParameterConstraint(ClosureContractModel):
    parameter: NonEmptyStr
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: tuple[JsonValue, ...] = ()
    reason_code: NonEmptyStr

    @model_validator(mode="after")
    def validate_constraint(self) -> Self:
        if self.minimum is None and self.maximum is None and not self.allowed_values:
            raise ValueError("constraint requires a bound or allowed_values")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("constraint minimum cannot exceed maximum")
        return self


class SignalWizardLeakageWarning(ClosureContractModel):
    reason_code: NonEmptyStr
    field_path: NonEmptyStr
    message: NonEmptyStr
    blocking: bool


class SignalWizardPreviewCommand(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    strategy_id: NonEmptyStr
    base_strategy_version: NonEmptyStr | None = None
    feature_selections: tuple[SignalWizardFeatureSelection, ...]
    parameter_constraints: tuple[SignalWizardParameterConstraint, ...] = ()
    condition_ast: dict[str, JsonValue]
    requested_strategy_schema_version: Literal["2.0.0"] = "2.0.0"
    capability: CapabilityRequirement

    @model_validator(mode="after")
    def validate_preview_command(self) -> Self:
        if not self.feature_selections:
            raise ValueError("preview requires at least one feature selection")
        feature_ids = [selection.feature_id for selection in self.feature_selections]
        if len(set(feature_ids)) != len(feature_ids):
            raise ValueError("feature selections must be unique")
        if self.capability.capability != StrategyCapability.STRATEGY_RESEARCH:
            raise ValueError("preview requires strategy.research capability")
        _reject_sensitive_metadata(self.condition_ast, "condition_ast")
        return self


class SignalWizardPreviewResult(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    strategy_definition: dict[str, JsonValue]
    leakage_warnings: tuple[SignalWizardLeakageWarning, ...] = ()
    reason_codes: tuple[NonEmptyStr, ...] = ()
    preview_hash: Sha256Hex
    execution_authority: Literal[False] = False
    promotion_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_preview_result(self) -> Self:
        if self.strategy_definition.get("schema_version") != "2.0.0":
            raise ValueError("preview result requires StrategyDefinition schema_version 2.0.0")
        _reject_sensitive_metadata(self.strategy_definition, "strategy_definition")
        return self


class SignalWizardSubmitCommand(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    preview_hash: Sha256Hex
    experiment_name: NonEmptyStr
    expected_strategy_version: NonEmptyStr
    capability: CapabilityRequirement

    @model_validator(mode="after")
    def validate_submit_command(self) -> Self:
        if self.capability.capability != StrategyCapability.EXPERIMENT_SUBMIT:
            raise ValueError("submit requires experiment.submit capability")
        return self


class SignalWizardSubmitResult(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    experiment_id: NonEmptyStr
    accepted: bool
    reason_codes: tuple[NonEmptyStr, ...] = ()
    execution_authority: Literal[False] = False
    promotion_authority: Literal[False] = False


class StrategyVersionHistoryEntry(ClosureContractModel):
    tenant_id: NonEmptyStr
    strategy_version: NonEmptyStr
    revision: PositiveInt
    lifecycle_state: StrategyLifecycleState
    immutable_hash: Sha256Hex
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime
    provenance: PublicContractProvenance


class StrategyApprovalRecord(ClosureContractModel):
    tenant_id: NonEmptyStr
    strategy_version: NonEmptyStr
    approval_id: NonEmptyStr
    decision: ApprovalDecision
    required_capability: Literal[StrategyCapability.STRATEGY_APPROVE] = (
        StrategyCapability.STRATEGY_APPROVE
    )
    decided_by_actor_id: NonEmptyStr | None = None
    decided_at: UtcDateTime | None = None
    reason_codes: tuple[NonEmptyStr, ...] = ()
    provenance: PublicContractProvenance

    @model_validator(mode="after")
    def validate_decision_evidence(self) -> Self:
        has_actor = self.decided_by_actor_id is not None
        has_timestamp = self.decided_at is not None
        if self.decision == ApprovalDecision.PENDING and (has_actor or has_timestamp):
            raise ValueError("pending approval cannot contain decision evidence")
        if self.decision != ApprovalDecision.PENDING and not (has_actor and has_timestamp):
            raise ValueError("completed approval requires actor and timestamp")
        return self


class StrategyDeploymentRecord(ClosureContractModel):
    tenant_id: NonEmptyStr
    deployment_id: NonEmptyStr
    strategy_version: NonEmptyStr
    environment: Environment
    mode: StrategyDeploymentMode
    state: StrategyDeploymentState
    deployed_by_actor_id: NonEmptyStr
    deployed_at: UtcDateTime
    provenance: PublicContractProvenance
    live_capital_authority: Literal[False] = False


class StrategyCatalogDetail(ClosureContractModel):
    tenant_id: NonEmptyStr
    entry: StrategyCatalogEntry
    history: tuple[StrategyVersionHistoryEntry, ...]
    approvals: tuple[StrategyApprovalRecord, ...] = ()
    deployments: tuple[StrategyDeploymentRecord, ...] = ()
    rollback_targets: tuple[NonEmptyStr, ...] = ()
    provenance: PublicContractProvenance
    required_capabilities: tuple[StrategyCapability, ...]

    @model_validator(mode="after")
    def validate_tenant_and_versions(self) -> Self:
        if not self.history:
            raise ValueError("strategy catalog detail requires version history")
        if any(item.tenant_id != self.tenant_id for item in self.history):
            raise ValueError("strategy catalog detail contains cross-tenant history")
        if any(item.tenant_id != self.tenant_id for item in self.approvals):
            raise ValueError("strategy catalog detail contains cross-tenant approvals")
        if any(item.tenant_id != self.tenant_id for item in self.deployments):
            raise ValueError("strategy catalog detail contains cross-tenant deployments")
        versions = {item.strategy_version for item in self.history}
        if self.entry.strategy_version not in versions:
            raise ValueError("catalog entry version must exist in history")
        if any(target not in versions for target in self.rollback_targets):
            raise ValueError("rollback target must exist in history")
        if len(set(self.required_capabilities)) != len(self.required_capabilities):
            raise ValueError("required_capabilities must be unique")
        return self


class StrategyApprovalCommand(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    strategy_version: NonEmptyStr
    decision: Literal[ApprovalDecision.APPROVED, ApprovalDecision.REJECTED]
    reason_codes: tuple[NonEmptyStr, ...]
    capability: CapabilityRequirement

    @model_validator(mode="after")
    def validate_capability(self) -> Self:
        if self.capability.capability != StrategyCapability.STRATEGY_APPROVE:
            raise ValueError("approval requires strategy.approve capability")
        return self


class StrategyDeploymentCommand(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    strategy_version: NonEmptyStr
    mode: StrategyDeploymentMode
    capability: CapabilityRequirement
    approval_evidence_ref: NonEmptyStr

    @model_validator(mode="after")
    def validate_capability(self) -> Self:
        if self.capability.capability != StrategyCapability.STRATEGY_DEPLOY_DRY_RUN:
            raise ValueError("deployment requires strategy.deploy_dry_run capability")
        return self


class StrategyRollbackCommand(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    from_strategy_version: NonEmptyStr
    to_strategy_version: NonEmptyStr
    reason: NonEmptyStr
    capability: CapabilityRequirement

    @model_validator(mode="after")
    def validate_rollback(self) -> Self:
        if self.from_strategy_version == self.to_strategy_version:
            raise ValueError("rollback target must differ from current strategy version")
        if self.capability.capability != StrategyCapability.STRATEGY_ROLLBACK_DRY_RUN:
            raise ValueError("rollback requires strategy.rollback_dry_run capability")
        return self


class StrategyMutationResult(ClosureContractModel):
    context: ClosureRequestContext
    idempotency_key: NonEmptyStr
    strategy_version: NonEmptyStr
    accepted: bool
    lifecycle_state: StrategyLifecycleState
    reason_codes: tuple[NonEmptyStr, ...] = ()
    execution_authority: Literal[False] = False
    live_capital_authority: Literal[False] = False


__all__ = [
    "ApprovalDecision",
    "CapabilityRequirement",
    "ClosureContractModel",
    "ClosureRequestContext",
    "PublicContractProvenance",
    "ResearchAuthority",
    "SignalWizardFeatureSelection",
    "SignalWizardLeakageWarning",
    "SignalWizardParameterConstraint",
    "SignalWizardPreviewCommand",
    "SignalWizardPreviewResult",
    "SignalWizardSubmitCommand",
    "SignalWizardSubmitResult",
    "StrategyApprovalCommand",
    "StrategyApprovalRecord",
    "StrategyCatalogDetail",
    "StrategyDeploymentCommand",
    "StrategyDeploymentMode",
    "StrategyDeploymentRecord",
    "StrategyDeploymentState",
    "StrategyMutationResult",
    "StrategyRollbackCommand",
    "StrategyCapability",
    "StrategyLifecycleState",
    "StrategyVersionHistoryEntry",
]
