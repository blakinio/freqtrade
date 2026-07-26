from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class IdentityPrincipalRow(Base):
    __tablename__ = "portal_identity_principals"

    principal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issuer: Mapped[str] = mapped_column(String(1024), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_portal_identity_issuer_subject"),
        Index("ix_portal_identity_principal_status", "status"),
    )


class TenantMembershipRow(Base):
    __tablename__ = "portal_tenant_memberships"

    membership_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    principal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    roles_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    membership_version: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "principal_id",
            "tenant_id",
            name="uq_portal_membership_principal_tenant",
        ),
        Index("ix_portal_membership_tenant_status", "tenant_id", "status"),
        Index("ix_portal_membership_principal", "principal_id"),
    )


class PortalSessionRow(Base):
    __tablename__ = "portal_identity_sessions"

    session_id_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    principal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    membership_id: Mapped[str] = mapped_column(String(36), nullable=False)
    membership_version: Mapped[int] = mapped_column(Integer, nullable=False)
    idp_session_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    authentication_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mfa_satisfied: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_portal_session_principal_active", "principal_id", "revoked_at"),
        Index("ix_portal_session_membership_active", "membership_id", "revoked_at"),
        Index("ix_portal_session_idp_sid", "idp_session_id"),
    )


class OidcLoginFlowRow(Base):
    __tablename__ = "portal_oidc_login_flows"

    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce: Mapped[str] = mapped_column(String(255), nullable=False)
    verifier_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    requested_tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    return_to: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_portal_oidc_flow_expiry", "expires_at", "consumed_at"),)


class SessionRevocationRow(Base):
    __tablename__ = "portal_session_revocations"

    revocation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    principal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    session_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idp_session_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (Index("ix_portal_revocation_principal_time", "principal_id", "occurred_at"),)


class IdentityAuditEventRow(Base):
    __tablename__ = "portal_identity_audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    principal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    membership_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_portal_identity_audit_principal_time", "principal_id", "occurred_at"),
        Index("ix_portal_identity_audit_tenant_time", "tenant_id", "occurred_at"),
    )
