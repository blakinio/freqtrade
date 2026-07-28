from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from typing import Literal, Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.exchange_connections import CredentialReference
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


class CredentialPurpose(StrEnum):
    RUNTIME_API = "RUNTIME_API"
    RUNTIME_PROVISIONING = "RUNTIME_PROVISIONING"


class CredentialLeaseRequest(ContractModel):
    tenant_id: NonEmptyStr
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    runtime_id: NonEmptyStr
    environment: Environment
    execution_mode: ExecutionMode
    purpose: CredentialPurpose
    requested_at: UtcDateTime
    correlation: CorrelationContext

    @model_validator(mode="after")
    def validate_dry_run_only(self) -> Self:
        if self.execution_mode != ExecutionMode.DRY_RUN:
            raise ValueError("credential broker permits dry-run execution only")
        return self


class CredentialLeaseEvidence(ContractModel):
    lease_id: NonEmptyStr
    tenant_id: NonEmptyStr
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    runtime_id: NonEmptyStr
    purpose: CredentialPurpose
    vault_version: PositiveInt
    issued_at: UtcDateTime
    expires_at: UtcDateTime
    rotated_at: UtcDateTime
    withdrawals_disabled: Literal[True] = True
    dry_run_only: Literal[True] = True
    evidence_ref: NonEmptyStr

    @model_validator(mode="after")
    def validate_times(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("credential lease expiry must be after issue time")
        if self.rotated_at > self.issued_at:
            raise ValueError("credential rotation timestamp cannot be in the future")
        return self


class VaultCredentialMetadata(ContractModel):
    tenant_id: NonEmptyStr
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    version: PositiveInt
    rotated_at: UtcDateTime
    revoked: bool
    withdrawals_enabled: bool
    dry_run_only: bool
    destroyed: bool = False
    deletion_time: UtcDateTime | None = None

    def rotation_due(self, *, inspected_at: UtcDateTime, maximum_age: timedelta) -> bool:
        if maximum_age <= timedelta(0):
            raise ValueError("maximum credential age must be positive")
        return inspected_at - self.rotated_at >= maximum_age
