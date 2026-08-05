from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Select, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.identity.models import (
    IdentityAuditEventRow,
    IdentityPrincipalRow,
    OidcLoginFlowRow,
    OidcLogoutReplayRow,
    PortalSessionRow,
    SessionRevocationRow,
    TenantMembershipRow,
)
from ai_platform.portal.identity.schema import (
    IdentityAuditEvent,
    IdentityPrincipal,
    MembershipStatus,
    PortalSessionView,
    PrincipalStatus,
    SessionRevocationRecord,
    TenantMembership,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class IdentityConflictError(RuntimeError):
    pass


class IdentityNotFoundError(LookupError):
    pass


class IdentityReplayConflictError(RuntimeError):
    pass


class IdentityReplayStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class LogoutReplayClaim:
    row: OidcLogoutReplayRow
    owner: bool


def _roles_json(roles: Sequence[RoleName]) -> str:
    return json.dumps([role.value for role in roles], separators=(",", ":"), sort_keys=True)


def _roles(value: str) -> tuple[RoleName, ...]:
    return tuple(RoleName(item) for item in json.loads(value))


def principal_from_row(row: IdentityPrincipalRow) -> IdentityPrincipal:
    return IdentityPrincipal(
        principal_id=row.principal_id,
        issuer=row.issuer,
        subject=row.subject,
        display_name=row.display_name,
        email=row.email,
        status=PrincipalStatus(row.status),
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
    )


def membership_from_row(row: TenantMembershipRow) -> TenantMembership:
    return TenantMembership(
        membership_id=row.membership_id,
        principal_id=row.principal_id,
        tenant_id=row.tenant_id,
        roles=_roles(row.roles_json),
        status=MembershipStatus(row.status),
        membership_version=row.membership_version,
        valid_from=_utc(row.valid_from),
        valid_until=_utc(row.valid_until) if row.valid_until is not None else None,
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
    )


class IdentityRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_principal(self, principal_id: str) -> IdentityPrincipalRow | None:
        return self.session.get(IdentityPrincipalRow, principal_id)

    def get_principal_by_external_identity(
        self,
        issuer: str,
        subject: str,
    ) -> IdentityPrincipalRow | None:
        return self.session.scalar(
            select(IdentityPrincipalRow).where(
                IdentityPrincipalRow.issuer == issuer,
                IdentityPrincipalRow.subject == subject,
            )
        )

    def create_principal(
        self,
        *,
        principal_id: str,
        issuer: str,
        subject: str,
        display_name: str,
        email: str | None,
        now: datetime,
    ) -> IdentityPrincipalRow:
        if self.get_principal_by_external_identity(issuer, subject) is not None:
            raise IdentityConflictError("external identity is already mapped")
        row = IdentityPrincipalRow(
            principal_id=principal_id,
            issuer=issuer,
            subject=subject,
            display_name=display_name,
            email=email,
            status=PrincipalStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def update_principal_attributes(
        self,
        row: IdentityPrincipalRow,
        *,
        display_name: str,
        email: str | None,
        now: datetime,
    ) -> None:
        row.display_name = display_name
        row.email = email
        row.updated_at = now
        self.session.flush()

    def create_membership(
        self,
        *,
        membership_id: str,
        principal_id: str,
        tenant_id: str,
        roles: tuple[RoleName, ...],
        valid_from: datetime,
        valid_until: datetime | None,
        now: datetime,
    ) -> TenantMembershipRow:
        existing = self.session.scalar(
            select(TenantMembershipRow).where(
                TenantMembershipRow.principal_id == principal_id,
                TenantMembershipRow.tenant_id == tenant_id,
            )
        )
        if existing is not None:
            raise IdentityConflictError("principal already has a membership in this tenant")
        row = TenantMembershipRow(
            membership_id=membership_id,
            principal_id=principal_id,
            tenant_id=tenant_id,
            roles_json=_roles_json(roles),
            status=MembershipStatus.ACTIVE.value,
            membership_version=1,
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_membership(self, membership_id: str) -> TenantMembershipRow | None:
        return self.session.get(TenantMembershipRow, membership_id)

    def list_memberships_for_principal(
        self,
        principal_id: str,
        now: datetime,
    ) -> tuple[TenantMembershipRow, ...]:
        query: Select[tuple[TenantMembershipRow]] = (
            select(TenantMembershipRow)
            .where(
                TenantMembershipRow.principal_id == principal_id,
                TenantMembershipRow.status == MembershipStatus.ACTIVE.value,
                TenantMembershipRow.valid_from <= now,
            )
            .order_by(TenantMembershipRow.tenant_id)
        )
        rows = self.session.scalars(query).all()
        return tuple(row for row in rows if row.valid_until is None or row.valid_until > now)

    def update_membership_roles(
        self,
        row: TenantMembershipRow,
        roles: tuple[RoleName, ...],
        now: datetime,
    ) -> None:
        row.roles_json = _roles_json(roles)
        row.membership_version += 1
        row.updated_at = now
        self.session.flush()

    def disable_membership(self, row: TenantMembershipRow, now: datetime) -> None:
        row.status = MembershipStatus.DISABLED.value
        row.membership_version += 1
        row.updated_at = now
        self.session.flush()

    def store_login_flow(
        self,
        *,
        state_hash: str,
        nonce: str,
        verifier_ciphertext: str,
        requested_tenant_id: str | None,
        return_to: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> None:
        self.session.add(
            OidcLoginFlowRow(
                state_hash=state_hash,
                nonce=nonce,
                verifier_ciphertext=verifier_ciphertext,
                requested_tenant_id=requested_tenant_id,
                return_to=return_to,
                created_at=created_at,
                expires_at=expires_at,
                consumed_at=None,
            )
        )
        self.session.flush()

    def consume_login_flow(self, state_hash: str, now: datetime) -> OidcLoginFlowRow:
        statement = (
            update(OidcLoginFlowRow)
            .where(
                OidcLoginFlowRow.state_hash == state_hash,
                OidcLoginFlowRow.consumed_at.is_(None),
                OidcLoginFlowRow.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(OidcLoginFlowRow)
            .execution_options(synchronize_session=False)
        )
        row = self.session.scalars(statement).one_or_none()
        if row is None:
            raise IdentityNotFoundError("OIDC login state is invalid or expired")
        return row

    def claim_logout_replay(
        self,
        *,
        replay_key_hash: str,
        issuer: str,
        client_id: str,
        jti: str,
        request_fingerprint: str,
        token_type: str,
        signing_key_id: str,
        signing_algorithm: str,
        issued_at: datetime,
        token_expires_at: datetime,
        retention_until: datetime,
        now: datetime,
    ) -> LogoutReplayClaim:
        candidate = OidcLogoutReplayRow(
            replay_key_hash=replay_key_hash,
            issuer=issuer,
            client_id=client_id,
            jti=jti,
            request_fingerprint=request_fingerprint,
            token_type=token_type,
            signing_key_id=signing_key_id,
            signing_algorithm=signing_algorithm,
            issued_at=issued_at,
            token_expires_at=token_expires_at,
            retention_until=retention_until,
            status="processing",
            revoked_sessions=None,
            processed_at=None,
            created_at=now,
            completed_at=None,
        )
        try:
            with self.session.begin_nested():
                self.session.add(candidate)
                self.session.flush()
        except IntegrityError:
            existing = self.session.scalar(
                select(OidcLogoutReplayRow)
                .where(OidcLogoutReplayRow.replay_key_hash == replay_key_hash)
                .execution_options(populate_existing=True)
            )
            if existing is None:
                raise IdentityReplayStateError("logout replay owner could not be resolved")
            exact_key = (existing.issuer, existing.client_id, existing.jti) == (
                issuer,
                client_id,
                jti,
            )
            if not exact_key or existing.request_fingerprint != request_fingerprint:
                raise IdentityReplayConflictError("logout replay key has conflicting semantics")
            if (
                existing.status != "completed"
                or existing.revoked_sessions is None
                or existing.processed_at is None
                or existing.completed_at is None
            ):
                raise IdentityReplayStateError("logout replay result is not terminal")
            return LogoutReplayClaim(row=existing, owner=False)
        return LogoutReplayClaim(row=candidate, owner=True)

    def complete_logout_replay(
        self,
        row: OidcLogoutReplayRow,
        *,
        revoked_sessions: int,
        processed_at: datetime,
        completed_at: datetime,
    ) -> None:
        if row.status != "processing":
            raise IdentityReplayStateError("logout replay reservation is not processing")
        row.status = "completed"
        row.revoked_sessions = revoked_sessions
        row.processed_at = processed_at
        row.completed_at = completed_at
        self.session.flush()

    def purge_expired_logout_replays(self, now: datetime) -> int:
        statement = (
            delete(OidcLogoutReplayRow)
            .where(
                OidcLogoutReplayRow.status == "completed",
                OidcLogoutReplayRow.retention_until <= now,
            )
            .returning(OidcLogoutReplayRow.replay_key_hash)
        )
        return len(self.session.scalars(statement).all())

    def create_session(
        self,
        *,
        session_id_hash: str,
        csrf_token_hash: str,
        principal_id: str,
        membership_id: str,
        membership_version: int,
        idp_session_id: str | None,
        authentication_time: datetime,
        mfa_satisfied: bool,
        created_at: datetime,
        idle_expires_at: datetime,
        absolute_expires_at: datetime,
    ) -> PortalSessionRow:
        row = PortalSessionRow(
            session_id_hash=session_id_hash,
            csrf_token_hash=csrf_token_hash,
            principal_id=principal_id,
            membership_id=membership_id,
            membership_version=membership_version,
            idp_session_id=idp_session_id,
            authentication_time=authentication_time,
            mfa_satisfied=mfa_satisfied,
            created_at=created_at,
            last_seen_at=created_at,
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
            revoked_at=None,
            revocation_reason=None,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_session(self, session_id_hash: str) -> PortalSessionRow | None:
        return self.session.get(OidcLogoutReplayRow, session_id_hash) if False else self.session.get(PortalSessionRow, session_id_hash)

    def touch_session(
        self,
        row: PortalSessionRow,
        *,
        now: datetime,
        idle_expires_at: datetime,
    ) -> None:
        row.last_seen_at = now
        row.idle_expires_at = min(idle_expires_at, _utc(row.absolute_expires_at))
        self.session.flush()

    def revoke_session(
        self,
        row: PortalSessionRow,
        *,
        actor_id: str,
        reason: str,
        now: datetime,
        correlation_id: str | None,
    ) -> bool:
        if row.revoked_at is not None:
            return False
        row.revoked_at = now
        row.revocation_reason = reason
        self.session.add(
            SessionRevocationRow(
                revocation_id=_new_id(),
                principal_id=row.principal_id,
                session_id_hash=row.session_id_hash,
                idp_session_id=row.idp_session_id,
                actor_id=actor_id,
                reason=reason,
                occurred_at=now,
                correlation_id=correlation_id,
            )
        )
        self.session.flush()
        return True

    def revoke_sessions_for_principal(
        self,
        *,
        principal_id: str,
        actor_id: str,
        reason: str,
        now: datetime,
        correlation_id: str | None,
    ) -> int:
        rows = self.session.scalars(
            select(PortalSessionRow).where(
                PortalSessionRow.principal_id == principal_id,
                PortalSessionRow.revoked_at.is_(None),
            )
        ).all()
        return sum(
            self.revoke_session(
                row,
                actor_id=actor_id,
                reason=reason,
                now=now,
                correlation_id=correlation_id,
            )
            for row in rows
        )

    def revoke_sessions_for_membership(
        self,
        *,
        membership_id: str,
        actor_id: str,
        reason: str,
        now: datetime,
        correlation_id: str | None,
    ) -> int:
        rows = self.session.scalars(
            select(PortalSessionRow).where(
                PortalSessionRow.membership_id == membership_id,
                PortalSessionRow.revoked_at.is_(None),
            )
        ).all()
        return sum(
            self.revoke_session(
                row,
                actor_id=actor_id,
                reason=reason,
                now=now,
                correlation_id=correlation_id,
            )
            for row in rows
        )

    def revoke_sessions_for_idp_identity(
        self,
        *,
        issuer: str,
        subject: str | None,
        idp_session_id: str | None,
        now: datetime,
    ) -> int:
        if subject is None and idp_session_id is None:
            return 0
        query = (
            select(PortalSessionRow)
            .join(
                IdentityPrincipalRow,
                IdentityPrincipalRow.principal_id == PortalSessionRow.principal_id,
            )
            .where(
                IdentityPrincipalRow.issuer == issuer,
                PortalSessionRow.revoked_at.is_(None),
            )
        )
        if subject is not None:
            query = query.where(IdentityPrincipalRow.subject == subject)
        if idp_session_id is not None:
            query = query.where(PortalSessionRow.idp_session_id == idp_session_id)
        rows = self.session.scalars(query).all()
        actor_id = f"idp:{issuer}"
        return sum(
            self.revoke_session(
                row,
                actor_id=actor_id,
                reason="idp_backchannel_logout",
                now=now,
                correlation_id=None,
            )
            for row in rows
        )

    def add_audit_event(self, event: IdentityAuditEvent) -> None:
        self.session.add(
            IdentityAuditEventRow(
                event_id=event.event_id,
                action=event.action,
                actor_id=event.actor_id,
                principal_id=event.principal_id,
                tenant_id=event.tenant_id,
                membership_id=event.membership_id,
                result=event.result,
                reason=event.reason,
                occurred_at=event.occurred_at,
                correlation_id=event.correlation_id,
            )
        )
        self.session.flush()

    def list_audit_events(self, principal_id: str) -> tuple[IdentityAuditEvent, ...]:
        rows = self.session.scalars(
            select(IdentityAuditEventRow)
            .where(IdentityAuditEventRow.principal_id == principal_id)
            .order_by(IdentityAuditEventRow.occurred_at, IdentityAuditEventRow.event_id)
        ).all()
        return tuple(
            IdentityAuditEvent(
                event_id=row.event_id,
                action=row.action,
                actor_id=row.actor_id,
                principal_id=row.principal_id,
                tenant_id=row.tenant_id,
                membership_id=row.membership_id,
                result=row.result,
                reason=row.reason,
                occurred_at=_utc(row.occurred_at),
                correlation_id=row.correlation_id,
            )
            for row in rows
        )


def session_view(
    session: PortalSessionRow,
    membership: TenantMembershipRow,
) -> PortalSessionView:
    return PortalSessionView(
        principal_id=session.principal_id,
        membership_id=membership.membership_id,
        tenant_id=membership.tenant_id,
        roles=_roles(membership.roles_json),
        membership_version=membership.membership_version,
        mfa_satisfied=session.mfa_satisfied,
        authentication_time=_utc(session.authentication_time),
        created_at=_utc(session.created_at),
        last_seen_at=_utc(session.last_seen_at),
        idle_expires_at=_utc(session.idle_expires_at),
        absolute_expires_at=_utc(session.absolute_expires_at),
    )


def revocation_from_row(row: SessionRevocationRow) -> SessionRevocationRecord:
    return SessionRevocationRecord(
        revocation_id=row.revocation_id,
        principal_id=row.principal_id,
        session_id_hash=row.session_id_hash,
        idp_session_id=row.idp_session_id,
        actor_id=row.actor_id,
        reason=row.reason,
        occurred_at=_utc(row.occurred_at),
        correlation_id=row.correlation_id,
    )


def _new_id() -> str:
    from uuid import uuid4

    return str(uuid4())
