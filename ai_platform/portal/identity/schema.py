from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.identity import RoleName


class PrincipalStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class IdentityPrincipal(ContractModel):
    principal_id: NonEmptyStr
    issuer: NonEmptyStr
    subject: NonEmptyStr
    display_name: NonEmptyStr
    email: str | None = None
    status: PrincipalStatus
    created_at: UtcDateTime
    updated_at: UtcDateTime


class TenantMembership(ContractModel):
    membership_id: NonEmptyStr
    principal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    roles: tuple[RoleName, ...]
    status: MembershipStatus
    membership_version: int = Field(ge=1)
    valid_from: UtcDateTime
    valid_until: UtcDateTime | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_roles_and_validity(self) -> Self:
        values = [role.value for role in self.roles]
        if not values:
            raise ValueError("membership must contain at least one role")
        if values != sorted(set(values)):
            raise ValueError("membership roles must be unique and deterministically sorted")
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("membership valid_until must be after valid_from")
        return self


class PortalSessionView(ContractModel):
    principal_id: NonEmptyStr
    membership_id: NonEmptyStr
    tenant_id: NonEmptyStr
    roles: tuple[RoleName, ...]
    membership_version: int = Field(ge=1)
    mfa_satisfied: bool
    authentication_time: UtcDateTime
    created_at: UtcDateTime
    last_seen_at: UtcDateTime
    idle_expires_at: UtcDateTime
    absolute_expires_at: UtcDateTime


class SessionRevocationRecord(ContractModel):
    revocation_id: NonEmptyStr
    principal_id: NonEmptyStr
    session_id_hash: str | None = None
    idp_session_id: str | None = None
    actor_id: NonEmptyStr
    reason: NonEmptyStr
    occurred_at: UtcDateTime
    correlation_id: str | None = None


class OidcIdentity(ContractModel):
    issuer: NonEmptyStr
    subject: NonEmptyStr
    display_name: NonEmptyStr
    email: str | None = None
    idp_session_id: str | None = None
    authentication_time: UtcDateTime
    mfa_satisfied: bool
    authentication_methods: tuple[str, ...] = ()


class BeginLoginResult(ContractModel):
    authorization_url: NonEmptyStr
    expires_at: UtcDateTime


class CompletedLogin(ContractModel):
    return_to: NonEmptyStr
    session: PortalSessionView
    session_token: NonEmptyStr
    csrf_token: NonEmptyStr


class MembershipCreate(ContractModel):
    principal_id: NonEmptyStr
    tenant_id: NonEmptyStr
    roles: tuple[RoleName, ...]
    valid_until: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_roles(self) -> Self:
        values = [role.value for role in self.roles]
        if not values or values != sorted(set(values)):
            raise ValueError("roles must be non-empty, unique and deterministically sorted")
        return self


class MembershipRolesUpdate(ContractModel):
    roles: tuple[RoleName, ...]

    @model_validator(mode="after")
    def validate_roles(self) -> Self:
        values = [role.value for role in self.roles]
        if not values or values != sorted(set(values)):
            raise ValueError("roles must be non-empty, unique and deterministically sorted")
        return self


class BackchannelLogoutResult(ContractModel):
    revoked_sessions: int = Field(ge=0)
    processed_at: UtcDateTime


class IdentityAuditEvent(ContractModel):
    event_id: NonEmptyStr
    action: NonEmptyStr
    actor_id: NonEmptyStr
    principal_id: str | None = None
    tenant_id: str | None = None
    membership_id: str | None = None
    result: NonEmptyStr
    reason: str | None = None
    occurred_at: UtcDateTime
    correlation_id: str | None = None


def ensure_utc(value: datetime) -> datetime:
    """Runtime helper used by storage conversion code."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value
