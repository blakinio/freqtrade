from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from typing import Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.configuration import BotManagementConfiguration
from ai_platform.portal.contracts.bot_management.policies import (
    DcaPolicyVersion,
    EntryPolicyVersion,
    ExitPolicyVersion,
    GridPolicyVersion,
    MarketPolicyVersion,
    PositionSizingPolicyVersion,
    RuntimePolicyVersion,
    SignalPolicyVersion,
)
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from ai_platform.portal.contracts.common import (
    ContractModel,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


class BotBuilderReasonCode(StrEnum):
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    DRAFT_ALREADY_EXISTS = "DRAFT_ALREADY_EXISTS"
    DRAFT_NOT_FOUND = "DRAFT_NOT_FOUND"
    DRAFT_REVISION_CONFLICT = "DRAFT_REVISION_CONFLICT"
    CONFIGURATION_REVISION_CONFLICT = "CONFIGURATION_REVISION_CONFLICT"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"
    COMPATIBILITY_REJECTED = "COMPATIBILITY_REJECTED"


class DraftReadinessStatus(StrEnum):
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"
    INCOMPATIBLE = "INCOMPATIBLE"
    READY = "READY"


class DraftField(StrEnum):
    CATALOG_REF = "catalog_ref"
    TEMPLATE_REF = "template_ref"
    STRATEGY_VERSION = "strategy_version"
    EXCHANGE_CONNECTION_REF = "exchange_connection_ref"
    EXCHANGE_PROFILE_VERSION = "exchange_profile_version"
    MARKET_POLICY = "market_policy"
    ENTRY_POLICY = "entry_policy"
    POSITION_SIZING_POLICY = "position_sizing_policy"
    EXIT_POLICY = "exit_policy"
    RISK_POLICY_VERSION = "risk_policy_version"
    RUNTIME_POLICY = "runtime_policy"
    ENVIRONMENT = "environment"
    EXECUTION_MODE = "execution_mode"


class BotBuilderAccessContext(ContractModel):
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    capabilities: tuple[BotManagementCapability, ...]

    @model_validator(mode="after")
    def validate_capabilities(self) -> Self:
        values = [item.value for item in self.capabilities]
        if len(values) != len(set(values)):
            raise ValueError("capabilities must not contain duplicates")
        if values != sorted(values):
            raise ValueError("capabilities must use deterministic sorted order")
        return self


class BotConfigurationDraftPayload(ContractModel):
    catalog_ref: CatalogVersionRef | None = None
    template_ref: CatalogVersionRef | None = None
    strategy_version: NonEmptyStr | None = None
    model_version: NonEmptyStr | None = None
    exchange_connection_ref: NonEmptyStr | None = None
    exchange_profile_version: NonEmptyStr | None = None
    market_policy: MarketPolicyVersion | None = None
    entry_policy: EntryPolicyVersion | None = None
    position_sizing_policy: PositionSizingPolicyVersion | None = None
    dca_policy: DcaPolicyVersion | None = None
    exit_policy: ExitPolicyVersion | None = None
    risk_policy_version: NonEmptyStr | None = None
    signal_policy: SignalPolicyVersion | None = None
    grid_policy: GridPolicyVersion | None = None
    runtime_policy: RuntimePolicyVersion | None = None
    environment: Environment | None = None
    execution_mode: ExecutionMode | None = None


class CreateBotConfigurationDraft(ContractModel):
    draft_id: NonEmptyStr
    bot_id: NonEmptyStr
    payload: BotConfigurationDraftPayload


class ReviseBotConfigurationDraft(ContractModel):
    draft_id: NonEmptyStr
    expected_revision: PositiveInt
    payload: BotConfigurationDraftPayload


class DraftRevisionRef(ContractModel):
    tenant_id: NonEmptyStr
    draft_id: NonEmptyStr
    revision: PositiveInt


class BotConfigurationDraftRevision(ContractModel):
    draft_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    revision: PositiveInt
    supersedes_revision: PositiveInt | None = None
    payload: BotConfigurationDraftPayload
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime

    @property
    def draft_ref(self) -> DraftRevisionRef:
        return DraftRevisionRef(
            tenant_id=self.tenant_id,
            draft_id=self.draft_id,
            revision=self.revision,
        )

    @model_validator(mode="after")
    def validate_revision_lineage(self) -> Self:
        if self.revision == 1 and self.supersedes_revision is not None:
            raise ValueError("first draft revision must not supersede another revision")
        if self.revision > 1 and self.supersedes_revision != self.revision - 1:
            raise ValueError("draft revision must supersede the immediately preceding revision")
        return self


class BotConfigurationDraftPreview(ContractModel):
    draft_ref: DraftRevisionRef
    status: DraftReadinessStatus
    missing_fields: tuple[DraftField, ...] = ()
    validation_errors: tuple[NonEmptyStr, ...] = ()
    compatibility_decision: BotCompatibilityDecision | None = None

    @model_validator(mode="after")
    def validate_preview(self) -> Self:
        self._validate_collection_order()
        self._validate_stage_payload()
        return self

    def _validate_collection_order(self) -> None:
        missing = [item.value for item in self.missing_fields]
        if len(missing) != len(set(missing)) or missing != sorted(missing):
            raise ValueError("missing_fields must use deterministic unique sorted order")
        if len(self.validation_errors) != len(set(self.validation_errors)):
            raise ValueError("validation_errors must not contain duplicates")
        if list(self.validation_errors) != sorted(self.validation_errors):
            raise ValueError("validation_errors must use deterministic sorted order")

    def _validate_stage_payload(self) -> None:
        if self.status == DraftReadinessStatus.INCOMPLETE:
            if not self.missing_fields:
                raise ValueError("incomplete preview requires missing fields")
            if self.compatibility_decision is not None or self.validation_errors:
                raise ValueError("incomplete preview must not contain later-stage results")
            return
        if self.missing_fields:
            raise ValueError("only incomplete preview may contain missing fields")
        if self.status == DraftReadinessStatus.INVALID:
            if not self.validation_errors:
                raise ValueError("invalid preview requires validation errors")
            return
        if self.validation_errors:
            raise ValueError("only invalid preview may contain validation errors")
        self._validate_decision_status()

    def _validate_decision_status(self) -> None:
        decision = self.compatibility_decision
        if self.status == DraftReadinessStatus.INCOMPATIBLE:
            if decision is None or decision.status != CompatibilityStatus.REJECTED:
                raise ValueError("incompatible preview requires a rejected compatibility decision")
        if self.status == DraftReadinessStatus.READY:
            if decision is None or decision.status != CompatibilityStatus.COMPATIBLE:
                raise ValueError("ready preview requires a compatible decision")


class FinalizeBotConfigurationDraft(ContractModel):
    draft_ref: DraftRevisionRef
    expected_configuration_revision: PositiveInt | None = None


class FinalizedBotConfiguration(ContractModel):
    draft_ref: DraftRevisionRef
    configuration: BotManagementConfiguration
    compatibility_decision: BotCompatibilityDecision
    configuration_sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_finalization(self) -> Self:
        configuration = self.configuration
        decision = self.compatibility_decision
        selection = decision.selection
        checks = (
            (
                configuration.tenant_id == self.draft_ref.tenant_id,
                "configuration tenant must match draft tenant",
            ),
            (
                decision.tenant_id == configuration.tenant_id,
                "compatibility decision tenant must match configuration tenant",
            ),
            (
                decision.status == CompatibilityStatus.COMPATIBLE,
                "finalized configuration requires a compatible decision",
            ),
            (
                configuration.compatibility_decision_ref == decision.decision_id,
                "configuration must bind the exact compatibility decision",
            ),
            (
                configuration.template_ref == selection.template_ref,
                "configuration template must match compatibility selection",
            ),
            (
                configuration.strategy_version == selection.strategy_version,
                "configuration strategy must match compatibility selection",
            ),
            (
                configuration.model_version == selection.model_version,
                "configuration model must match compatibility selection",
            ),
            (
                configuration.market_policy.market_type == selection.market_type,
                "configuration market type must match compatibility selection",
            ),
            (
                configuration.market_policy.direction == selection.direction,
                "configuration direction must match compatibility selection",
            ),
            (
                configuration.execution_mode == selection.execution_mode,
                "configuration execution mode must match compatibility selection",
            ),
            (
                configuration.runtime_policy.runtime_version == selection.runtime_version,
                "configuration runtime must match compatibility selection",
            ),
            (
                configuration.risk_policy_version == selection.risk_policy_version,
                "configuration risk policy must match compatibility selection",
            ),
        )
        for matches, message in checks:
            if not matches:
                raise ValueError(message)
        expected_digest = sha256(configuration.canonical_json().encode()).hexdigest()
        if self.configuration_sha256 != expected_digest:
            raise ValueError("configuration digest must match canonical configuration")
        return self
