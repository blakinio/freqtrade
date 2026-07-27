from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, PositiveInt, StringConstraints, model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import (
    FractionDecimal,
    PositiveDecimal,
    SignalAuthority,
    SignalCommand,
)
from ai_platform.portal.contracts.bot_management.signals import (
    SignalAuthenticationMode,
    SignalAuthenticationReference,
)
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor


OpaqueSignatureEvidenceRef = Annotated[
    str,
    StringConstraints(pattern=r"^sigev_[A-Za-z0-9_-]{8,128}$"),
]


BoundedSignalAgeSeconds = Annotated[int, Field(ge=1, le=86400)]
BoundedFutureSkewSeconds = Annotated[int, Field(ge=0, le=300)]


class SignalControlReasonCode(StrEnum):
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHENTICATION_PROVIDER_UNAVAILABLE = "AUTHENTICATION_PROVIDER_UNAVAILABLE"
    BOT_REVISION_STALE = "BOT_REVISION_STALE"
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    COMMAND_UNSUPPORTED = "COMMAND_UNSUPPORTED"
    CONFIGURATION_REVISION_STALE = "CONFIGURATION_REVISION_STALE"
    ENDPOINT_ALREADY_EXISTS = "ENDPOINT_ALREADY_EXISTS"
    ENDPOINT_DISABLED = "ENDPOINT_DISABLED"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND"
    ENDPOINT_REVISION_CONFLICT = "ENDPOINT_REVISION_CONFLICT"
    ENDPOINT_REVISION_STALE = "ENDPOINT_REVISION_STALE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    IDEMPOTENCY_DUPLICATE = "IDEMPOTENCY_DUPLICATE"
    NONCE_MISSING = "NONCE_MISSING"
    NONCE_REPLAYED = "NONCE_REPLAYED"
    PAYLOAD_INVALID = "PAYLOAD_INVALID"
    RUNTIME_REVISION_STALE = "RUNTIME_REVISION_STALE"
    SIGNAL_REPLAYED = "SIGNAL_REPLAYED"
    SCHEMA_UNSUPPORTED = "SCHEMA_UNSUPPORTED"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    TIMESTAMP_EXPIRED = "TIMESTAMP_EXPIRED"
    TIMESTAMP_FUTURE = "TIMESTAMP_FUTURE"


class SignatureVerificationStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


class SignalValidationStatus(StrEnum):
    VALID = "VALID"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    REPLAYED = "REPLAYED"


class SignalProcessingMode(StrEnum):
    ACCEPT = "ACCEPT"
    PREVIEW = "PREVIEW"


class SignalMappingStatus(StrEnum):
    ADVISORY_RECORDED = "ADVISORY_RECORDED"
    COMMAND_INTENT_CREATED = "COMMAND_INTENT_CREATED"
    REJECTED = "REJECTED"


class MappedCommandVocabulary(StrEnum):
    BM00_SIGNAL = "BM00_SIGNAL"
    BM03_LIFECYCLE = "BM03_LIFECYCLE"
    BM03_POSITION = "BM03_POSITION"


class MappedCommandFamily(StrEnum):
    TRADE_INTENT = "TRADE_INTENT"
    LIFECYCLE = "LIFECYCLE"
    POSITION = "POSITION"


class SignalControlContext(ContractModel):
    tenant_id: NonEmptyStr
    actor: Actor
    environment: Environment
    capabilities: tuple[BotManagementCapability, ...]
    correlation: CorrelationContext

    @model_validator(mode="after")
    def validate_context(self) -> Self:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("signal context actor must belong to the context tenant")
        values = [capability.value for capability in self.capabilities]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("signal context capabilities must be unique and sorted")
        return self


class CreateSignalEndpoint(ContractModel):
    endpoint_id: NonEmptyStr
    display_name: NonEmptyStr
    endpoint_slug: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{12,128}$")]
    authentication_mode: SignalAuthenticationMode
    authentication_ref: SignalAuthenticationReference
    schema_id: NonEmptyStr
    schema_revision: PositiveInt
    supported_commands: Annotated[tuple[SignalCommand, ...], Field(min_length=1)]
    authority: SignalAuthority
    max_past_age_seconds: BoundedSignalAgeSeconds
    max_future_skew_seconds: BoundedFutureSkewSeconds
    replay_window_seconds: BoundedSignalAgeSeconds
    require_nonce: bool = True
    enabled: bool = True

    @model_validator(mode="after")
    def validate_endpoint_request(self) -> Self:
        values = [command.value for command in self.supported_commands]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("supported_commands must be unique and sorted")
        if self.replay_window_seconds > self.max_past_age_seconds:
            raise ValueError("replay window must not exceed maximum past signal age")
        return self


class ReviseSignalEndpoint(CreateSignalEndpoint):
    expected_revision: PositiveInt


class SignalEndpointRevision(ContractModel):
    endpoint_id: NonEmptyStr
    tenant_id: NonEmptyStr
    revision: PositiveInt
    supersedes_revision: PositiveInt | None = None
    display_name: NonEmptyStr
    endpoint_slug: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{12,128}$")]
    authentication_mode: SignalAuthenticationMode
    authentication_ref: SignalAuthenticationReference
    schema_id: NonEmptyStr
    schema_revision: PositiveInt
    supported_commands: Annotated[tuple[SignalCommand, ...], Field(min_length=1)]
    authority: SignalAuthority
    max_past_age_seconds: BoundedSignalAgeSeconds
    max_future_skew_seconds: BoundedFutureSkewSeconds
    replay_window_seconds: BoundedSignalAgeSeconds
    require_nonce: bool
    enabled: bool
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_revision(self) -> Self:
        if self.revision == 1 and self.supersedes_revision is not None:
            raise ValueError("first endpoint revision must not supersede another revision")
        if self.revision > 1 and self.supersedes_revision != self.revision - 1:
            raise ValueError("endpoint revision must supersede the immediately prior revision")
        values = [command.value for command in self.supported_commands]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("supported_commands must be unique and sorted")
        if self.replay_window_seconds > self.max_past_age_seconds:
            raise ValueError("replay window must not exceed maximum past signal age")
        return self


class SignalPayloadSchemaDefinition(ContractModel):
    schema_id: NonEmptyStr
    revision: PositiveInt
    supported_commands: tuple[SignalCommand, ...]
    field_names: tuple[NonEmptyStr, ...]

    @model_validator(mode="after")
    def validate_definition(self) -> Self:
        for name, values in (
            ("supported_commands", tuple(item.value for item in self.supported_commands)),
            ("field_names", self.field_names),
        ):
            if len(values) != len(set(values)) or list(values) != sorted(values):
                raise ValueError(f"{name} must be unique and sorted")
        return self


class SignalPayloadV1(ContractModel):
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    issued_at: UtcDateTime
    nonce: NonEmptyStr | None = None
    idempotency_key: NonEmptyStr
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt
    command: SignalCommand
    pair: NonEmptyStr | None = None
    position_id: NonEmptyStr | None = None
    position_revision: PositiveInt | None = None
    price: PositiveDecimal | None = None
    quantity: PositiveDecimal | None = None
    close_fraction: FractionDecimal | None = None

    @model_validator(mode="after")
    def validate_command_payload(self) -> Self:
        position_actions = {
            SignalCommand.CLOSE_POSITION,
            SignalCommand.PARTIAL_CLOSE,
            SignalCommand.TAKE_PROFIT,
        }
        lifecycle_actions = {
            SignalCommand.ENABLE_BOT,
            SignalCommand.PAUSE_BOT,
            SignalCommand.STOP_BOT,
            SignalCommand.CLOSE_ALL,
        }
        if self.command in position_actions:
            if self.position_id is None or self.position_revision is None:
                raise ValueError("position command requires exact position identity and revision")
        elif self.position_id is not None or self.position_revision is not None:
            raise ValueError("non-position command must not target a position")
        if self.command == SignalCommand.PARTIAL_CLOSE:
            supplied = sum(value is not None for value in (self.quantity, self.close_fraction))
            if supplied != 1:
                raise ValueError("partial close requires exactly one quantity or fraction")
        elif self.close_fraction is not None:
            raise ValueError("close_fraction is valid only for partial close")
        if self.command in lifecycle_actions:
            if any(value is not None for value in (self.pair, self.price, self.quantity)):
                raise ValueError("lifecycle and close-all commands must not contain trade sizing")
        if self.command in {SignalCommand.OPEN, SignalCommand.DCA} and self.pair is None:
            raise ValueError("open and DCA commands require a pair")
        return self


SIGNAL_PAYLOAD_SCHEMA_V1 = SignalPayloadSchemaDefinition(
    schema_id="signal.v1",
    revision=1,
    supported_commands=tuple(sorted(SignalCommand, key=lambda item: item.value)),
    field_names=tuple(
        sorted(
            {
                "bot_id",
                "bot_revision",
                "close_fraction",
                "command",
                "config_revision",
                "endpoint_id",
                "idempotency_key",
                "issued_at",
                "nonce",
                "pair",
                "position_id",
                "position_revision",
                "price",
                "quantity",
                "runtime_id",
                "runtime_revision",
                "signal_id",
                "tenant_id",
            }
        )
    ),
)


class AuthoritativeSignalTargetState(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt
    observed_at: UtcDateTime


class SignatureVerificationDecision(ContractModel):
    status: SignatureVerificationStatus
    evidence_ref: OpaqueSignatureEvidenceRef | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        if self.status == SignatureVerificationStatus.UNAVAILABLE and self.evidence_ref is not None:
            raise ValueError("unavailable verification must not expose provider evidence")
        if self.status != SignatureVerificationStatus.UNAVAILABLE and self.evidence_ref is None:
            raise ValueError("completed verification requires opaque evidence")
        return self


class SignalValidationEvidence(ContractModel):
    validation_id: Sha256Hex
    signal_id: NonEmptyStr
    scope_tenant_id: NonEmptyStr
    attempted_tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    endpoint_revision: PositiveInt
    schema_id: NonEmptyStr
    schema_revision: PositiveInt
    payload_sha256: Sha256Hex
    nonce_sha256: Sha256Hex | None = None
    authentication_evidence_ref: OpaqueSignatureEvidenceRef | None = None
    status: SignalValidationStatus
    reason_codes: tuple[SignalControlReasonCode, ...] = ()
    validated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("validation reasons must be unique and sorted")
        if self.status == SignalValidationStatus.VALID and self.reason_codes:
            raise ValueError("valid evidence must not contain rejection reasons")
        if self.status != SignalValidationStatus.VALID and not self.reason_codes:
            raise ValueError("non-valid evidence requires rejection reasons")
        return self


class SignalCommandIntent(ContractModel):
    intent_id: Sha256Hex
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    endpoint_revision: PositiveInt
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt
    vocabulary: MappedCommandVocabulary
    family: MappedCommandFamily
    action: NonEmptyStr
    source_command: SignalCommand
    required_capability: BotManagementCapability | None = None
    idempotency_key: NonEmptyStr
    pair: NonEmptyStr | None = None
    position_id: NonEmptyStr | None = None
    position_revision: PositiveInt | None = None
    price: PositiveDecimal | None = None
    quantity: PositiveDecimal | None = None
    close_fraction: FractionDecimal | None = None
    requires_risk_approval: bool = True
    preview_only: bool
    execution_performed: bool = False
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_intent(self) -> Self:
        if self.execution_performed:
            raise ValueError("signal command intent must never claim execution")
        if not self.requires_risk_approval:
            raise ValueError("signal command intent must preserve deterministic risk approval")
        return self


class SignalMappingEvidence(ContractModel):
    mapping_id: Sha256Hex
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    endpoint_revision: PositiveInt
    status: SignalMappingStatus
    authority: SignalAuthority
    command_intent_id: Sha256Hex | None = None
    vocabulary: MappedCommandVocabulary | None = None
    mapped_action: NonEmptyStr | None = None
    reason_codes: tuple[SignalControlReasonCode, ...] = ()
    mapped_at: UtcDateTime

    @model_validator(mode="after")
    def validate_mapping(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("mapping reasons must be unique and sorted")
        if self.status == SignalMappingStatus.COMMAND_INTENT_CREATED:
            if (
                self.command_intent_id is None
                or self.vocabulary is None
                or self.mapped_action is None
            ):
                raise ValueError("command mapping requires complete intent evidence")
            if self.reason_codes:
                raise ValueError("successful command mapping must not contain reasons")
        elif self.command_intent_id is not None:
            raise ValueError("non-command mapping must not reference a command intent")
        if self.status == SignalMappingStatus.ADVISORY_RECORDED:
            if self.authority != SignalAuthority.ADVISORY_ONLY:
                raise ValueError("advisory mapping requires advisory-only authority")
            if self.reason_codes:
                raise ValueError("advisory mapping must not contain rejection reasons")
        if self.status == SignalMappingStatus.REJECTED and not self.reason_codes:
            raise ValueError("rejected mapping requires reasons")
        return self


class SignalAuditRecord(ContractModel):
    audit_id: UUID
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    processing_id: Sha256Hex
    result: SignalValidationStatus
    reason_codes: tuple[SignalControlReasonCode, ...]
    occurred_at: UtcDateTime

    @model_validator(mode="after")
    def validate_audit(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("audit reasons must be unique and sorted")
        if self.result == SignalValidationStatus.VALID and self.reason_codes:
            raise ValueError("valid audit record must not contain reasons")
        return self


class SignalProcessingResult(ContractModel):
    processing_id: Sha256Hex
    mode: SignalProcessingMode
    validation: SignalValidationEvidence
    mapping: SignalMappingEvidence
    audit: SignalAuditRecord
    command_intent: SignalCommandIntent | None = None
    persisted: bool
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.execution_performed:
            raise ValueError("signal processing must never claim execution")
        if self.mode == SignalProcessingMode.PREVIEW and self.persisted:
            raise ValueError("preview results must not be persisted")
        if self.audit.processing_id != self.processing_id:
            raise ValueError("audit record must reference the processing result")
        if self.audit.result != self.validation.status:
            raise ValueError("audit result must match validation status")
        if self.audit.reason_codes != self.validation.reason_codes:
            raise ValueError("audit reasons must match validation reasons")
        if self.mapping.status == SignalMappingStatus.COMMAND_INTENT_CREATED:
            if self.command_intent is None:
                raise ValueError("command mapping result requires the command intent")
            if self.command_intent.intent_id != self.mapping.command_intent_id:
                raise ValueError("mapping must reference the exact command intent")
        elif self.command_intent is not None:
            raise ValueError("non-command mapping must not contain a command intent")
        return self


class SignalProcessingRequest(ContractModel):
    endpoint_id: NonEmptyStr
    endpoint_revision: PositiveInt
    schema_id: NonEmptyStr
    schema_revision: PositiveInt
    payload: dict[str, object]
