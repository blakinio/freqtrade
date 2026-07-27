from __future__ import annotations

from abc import abstractmethod
from enum import StrEnum
from typing import Protocol

from ai_platform.portal.contracts.bot_management.exchange_connections import CredentialReference
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime


class CredentialReferenceState(StrEnum):
    CURRENT = "CURRENT"
    UNAVAILABLE = "UNAVAILABLE"
    REVOKED = "REVOKED"
    ROTATION_REQUIRED = "ROTATION_REQUIRED"


class CredentialReferenceInspection(ContractModel):
    tenant_id: NonEmptyStr
    credential_ref: CredentialReference
    state: CredentialReferenceState
    inspected_at: UtcDateTime
    evidence_ref: NonEmptyStr


class CredentialReferenceStatusPort(Protocol):
    """Secret-free PI-07 seam; implementations may inspect only an opaque reference."""

    @abstractmethod
    def inspect_reference(
        self,
        *,
        tenant_id: str,
        credential_ref: str,
    ) -> CredentialReferenceInspection: ...
