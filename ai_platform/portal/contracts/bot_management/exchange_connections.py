from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, StringConstraints, model_validator

from ai_platform.portal.contracts.bot_management.policies import OrderType, PositiveDecimal
from ai_platform.portal.contracts.bot_management.templates import MarketType
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor


CredentialReference = Annotated[
    str,
    StringConstraints(pattern=r"^credref_[A-Za-z0-9_-]{8,128}$"),
]


class ConnectionVerificationStatus(StrEnum):
    NEVER_VERIFIED = "NEVER_VERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"


class CredentialRotationStatus(StrEnum):
    CURRENT = "CURRENT"
    ROTATION_REQUIRED = "ROTATION_REQUIRED"
    ROTATION_PENDING = "ROTATION_PENDING"
    REVOKED = "REVOKED"


class ConnectionRevocationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOCATION_PENDING = "REVOCATION_PENDING"
    REVOKED = "REVOKED"


class VerificationReasonCode(StrEnum):
    CAPABILITY_PROFILE_MISMATCH = "CAPABILITY_PROFILE_MISMATCH"
    CONNECTION_REVOKED = "CONNECTION_REVOKED"
    CREDENTIAL_REFERENCE_UNAVAILABLE = "CREDENTIAL_REFERENCE_UNAVAILABLE"
    EXCHANGE_UNAVAILABLE = "EXCHANGE_UNAVAILABLE"
    PERMISSION_OBSERVATION_MISSING = "PERMISSION_OBSERVATION_MISSING"
    TRADING_PERMISSION_DISABLED = "TRADING_PERMISSION_DISABLED"
    WITHDRAWAL_PERMISSION_ENABLED = "WITHDRAWAL_PERMISSION_ENABLED"


class ExchangeCapabilityProfile(ContractModel):
    profile_id: NonEmptyStr
    revision: PositiveInt
    exchange_id: NonEmptyStr
    market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    order_types: Annotated[tuple[OrderType, ...], Field(min_length=1)]
    supports_order_replace: bool
    supports_short: bool
    supports_subaccounts: bool
    maximum_leverage: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_capability_profile(self) -> Self:
        for field_name, values in (
            ("market_types", tuple(item.value for item in self.market_types)),
            ("order_types", tuple(item.value for item in self.order_types)),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
            if list(values) != sorted(values):
                raise ValueError(f"{field_name} must use deterministic sorted order")
        if self.maximum_leverage is not None and MarketType.SPOT in self.market_types:
            if len(self.market_types) == 1:
                raise ValueError("spot-only capability profile must not declare leverage")
        return self


class ExchangeConnectionMetadata(ContractModel):
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    metadata_revision: PositiveInt
    display_name: NonEmptyStr
    exchange_id: NonEmptyStr
    exchange_profile_ref: NonEmptyStr
    credential_ref: CredentialReference
    account_label: NonEmptyStr
    subaccount_label: NonEmptyStr | None = None
    enabled_market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    verification_status: ConnectionVerificationStatus
    rotation_status: CredentialRotationStatus
    revocation_status: ConnectionRevocationStatus
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_connection_metadata(self) -> Self:
        market_types = [item.value for item in self.enabled_market_types]
        if len(market_types) != len(set(market_types)):
            raise ValueError("enabled market types must not contain duplicates")
        if market_types != sorted(market_types):
            raise ValueError("enabled market types must use deterministic sorted order")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be before created_at")
        if self.revocation_status == ConnectionRevocationStatus.REVOKED:
            if self.rotation_status != CredentialRotationStatus.REVOKED:
                raise ValueError("revoked connection must also mark credential reference revoked")
        return self


class ExchangePermissionObservation(ContractModel):
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    trading_enabled: bool
    withdrawals_enabled: bool
    observed_at: UtcDateTime
    evidence_ref: NonEmptyStr

    @model_validator(mode="after")
    def validate_permissions(self) -> Self:
        if self.withdrawals_enabled:
            raise ValueError("withdrawal-enabled exchange connections are forbidden")
        return self


class ExchangeConnectionVerificationRequest(ContractModel):
    verification_id: NonEmptyStr
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    metadata_revision: PositiveInt
    actor: Actor
    environment: Environment
    correlation: CorrelationContext
    idempotency_key: NonEmptyStr
    requested_at: UtcDateTime

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("verification actor must belong to the request tenant")
        return self


class ExchangeConnectionVerificationResult(ContractModel):
    verification_id: NonEmptyStr
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    metadata_revision: PositiveInt
    status: ConnectionVerificationStatus
    permission_observation: ExchangePermissionObservation | None = None
    reason_codes: tuple[VerificationReasonCode, ...] = ()
    completed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)):
            raise ValueError("verification reason codes must be unique")
        if reasons != sorted(reasons):
            raise ValueError("verification reason codes must use deterministic sorted order")
        if self.permission_observation is not None:
            if self.permission_observation.tenant_id != self.tenant_id:
                raise ValueError("permission observation tenant mismatch")
            if self.permission_observation.connection_id != self.connection_id:
                raise ValueError("permission observation connection mismatch")
        if self.status == ConnectionVerificationStatus.VERIFIED:
            if self.reason_codes or self.permission_observation is None:
                raise ValueError("verified result requires clean permission observation")
            if not self.permission_observation.trading_enabled:
                raise ValueError("verified connection must have trading permission enabled")
        if self.status == ConnectionVerificationStatus.FAILED and not self.reason_codes:
            raise ValueError("failed verification requires a reason code")
        return self
