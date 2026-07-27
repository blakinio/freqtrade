from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, StringConstraints, model_validator

from ai_platform.portal.contracts.bot_management.policies import (
    FractionDecimal,
    PositiveDecimal,
    SignalAuthority,
    SignalCommand,
)
from ai_platform.portal.contracts.common import (
    ContractModel,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)


SignalAuthenticationReference = Annotated[
    str,
    StringConstraints(pattern=r"^signalref_[A-Za-z0-9_-]{8,128}$"),
]
EndpointSlug = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_-]{12,128}$"),
]


class SignalAuthenticationMode(StrEnum):
    HMAC_SHA256 = "hmac_sha256"
    ED25519 = "ed25519"
    MUTUAL_TLS = "mutual_tls"


class SignalValidationStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    REPLAYED = "REPLAYED"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"


class SignalValidationReasonCode(StrEnum):
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    BOT_REVISION_STALE = "BOT_REVISION_STALE"
    COMMAND_UNSUPPORTED = "COMMAND_UNSUPPORTED"
    ENDPOINT_DISABLED = "ENDPOINT_DISABLED"
    ENVELOPE_EXPIRED = "ENVELOPE_EXPIRED"
    IDEMPOTENCY_DUPLICATE = "IDEMPOTENCY_DUPLICATE"
    NONCE_REPLAYED = "NONCE_REPLAYED"
    PAYLOAD_INVALID = "PAYLOAD_INVALID"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    TENANT_MISMATCH = "TENANT_MISMATCH"


class SignalMappingStatus(StrEnum):
    ADVISORY_RECORDED = "ADVISORY_RECORDED"
    COMMAND_MAPPED = "COMMAND_MAPPED"
    REJECTED = "REJECTED"


class SignalSchemaVersion(ContractModel):
    schema_id: NonEmptyStr
    revision: PositiveInt
    supported_commands: Annotated[tuple[SignalCommand, ...], Field(min_length=1)]
    required_field_names: tuple[NonEmptyStr, ...]

    @model_validator(mode="after")
    def validate_schema(self) -> Self:
        for field_name, values in (
            ("supported_commands", tuple(item.value for item in self.supported_commands)),
            ("required_field_names", self.required_field_names),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
            if list(values) != sorted(values):
                raise ValueError(f"{field_name} must use deterministic sorted order")
        forbidden = {
            "api_key",
            "secret",
            "passphrase",
            "token",
            "private_endpoint",
            "secret_store_path",
        }
        if forbidden & set(self.required_field_names):
            raise ValueError("signal schema must not require secret-bearing fields")
        return self


class SignalEndpointMetadata(ContractModel):
    endpoint_id: NonEmptyStr
    tenant_id: NonEmptyStr
    revision: PositiveInt
    display_name: NonEmptyStr
    endpoint_slug: EndpointSlug
    authentication_mode: SignalAuthenticationMode
    authentication_ref: SignalAuthenticationReference
    signal_schema_ref: NonEmptyStr
    supported_commands: Annotated[tuple[SignalCommand, ...], Field(min_length=1)]
    authority: SignalAuthority
    replay_window_seconds: PositiveInt
    enabled: bool
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_endpoint(self) -> Self:
        commands = [command.value for command in self.supported_commands]
        if len(commands) != len(set(commands)):
            raise ValueError("supported signal commands must be unique")
        if commands != sorted(commands):
            raise ValueError("supported signal commands must use deterministic sorted order")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be before created_at")
        return self


class SignalReplayEnvelope(ContractModel):
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    nonce_hash: Sha256Hex
    issued_at: UtcDateTime
    expires_at: UtcDateTime

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("signal expiry must be after issue time")
        return self


class SignalEnvelope(ContractModel):
    replay: SignalReplayEnvelope
    signal_schema_ref: NonEmptyStr
    authentication_evidence_ref: NonEmptyStr
    bot_id: NonEmptyStr
    config_revision: PositiveInt
    command: SignalCommand
    pair: NonEmptyStr | None = None
    position_id: NonEmptyStr | None = None
    position_revision: PositiveInt | None = None
    price: PositiveDecimal | None = None
    quantity: PositiveDecimal | None = None
    close_fraction: FractionDecimal | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
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
                raise ValueError("position signal requires exact position identity and revision")
        elif self.position_id is not None or self.position_revision is not None:
            raise ValueError("non-position signal must not target a position")
        if self.command == SignalCommand.PARTIAL_CLOSE:
            supplied = sum(value is not None for value in (self.quantity, self.close_fraction))
            if supplied != 1:
                raise ValueError("partial-close signal requires one quantity or fraction")
        elif self.close_fraction is not None:
            raise ValueError("close_fraction is valid only for partial-close signal")
        if self.command in lifecycle_actions:
            if any(value is not None for value in (self.pair, self.price, self.quantity)):
                raise ValueError("lifecycle or close-all signal must not contain trade sizing")
        if self.command in {SignalCommand.OPEN, SignalCommand.DCA} and self.pair is None:
            raise ValueError("open or DCA signal requires a pair")
        return self


class SignalValidationResult(ContractModel):
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    endpoint_id: NonEmptyStr
    status: SignalValidationStatus
    reason_codes: tuple[SignalValidationReasonCode, ...] = ()
    validated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)):
            raise ValueError("signal validation reason codes must be unique")
        if reasons != sorted(reasons):
            raise ValueError("signal validation reason codes must use sorted order")
        if self.status == SignalValidationStatus.VALID and self.reason_codes:
            raise ValueError("valid signal must not contain rejection reason codes")
        if self.status != SignalValidationStatus.VALID and not self.reason_codes:
            raise ValueError("non-valid signal requires at least one reason code")
        return self


class SignalCommandMappingResult(ContractModel):
    signal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    status: SignalMappingStatus
    authority: SignalAuthority
    mapped_command_id: NonEmptyStr | None = None
    reason_codes: tuple[SignalValidationReasonCode, ...] = ()
    mapped_at: UtcDateTime

    @model_validator(mode="after")
    def validate_mapping(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("mapping reason codes must be unique and sorted")
        if self.status == SignalMappingStatus.COMMAND_MAPPED:
            if self.mapped_command_id is None or self.reason_codes:
                raise ValueError("mapped command requires a command id and no rejection reason")
        elif self.mapped_command_id is not None:
            raise ValueError("non-mapped signal must not contain a command id")
        if self.status == SignalMappingStatus.ADVISORY_RECORDED:
            if self.authority != SignalAuthority.ADVISORY_ONLY:
                raise ValueError("advisory result must use advisory-only authority")
        if self.status == SignalMappingStatus.REJECTED and not self.reason_codes:
            raise ValueError("rejected mapping requires at least one reason code")
        return self
