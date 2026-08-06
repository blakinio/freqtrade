from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from ai_platform.portal.identity import service_base
from ai_platform.portal.identity.oidc import OidcLogoutIdentity, OidcProtocolError
from ai_platform.portal.identity.repository import (
    IdentityNotFoundError,
    IdentityReplayConflictError,
    IdentityReplayStateError,
    IdentityRepository,
    session_view,
)
from ai_platform.portal.identity.schema import (
    BackchannelLogoutResult,
    CompletedLogin,
    PrincipalStatus,
)
from ai_platform.portal.security.authorization import permissions_for_roles


AuthenticatedSession = service_base.AuthenticatedSession
CSRF_COOKIE_NAME = service_base.CSRF_COOKIE_NAME
CSRF_HEADER_NAME = service_base.CSRF_HEADER_NAME
IdentityAuthenticationError = service_base.IdentityAuthenticationError
IdentityAuthorizationError = service_base.IdentityAuthorizationError
IdentityPolicy = service_base.IdentityPolicy
IdentityProviderError = service_base.IdentityProviderError
SESSION_COOKIE_NAME = service_base.SESSION_COOKIE_NAME


class IdentityService(service_base.IdentityService):
    """Identity service with attributable, replay-safe OIDC lifecycles."""

    def complete_login(self, *, code: str, state: str) -> CompletedLogin:
        if not code or not state:
            raise IdentityAuthenticationError("OIDC callback requires code and state")
        now = self._now()
        claim_id = self._crypto.hash_token(state)

        with self._session_factory() as session:
            repository = IdentityRepository(session)
            try:
                flow = repository.consume_login_flow(claim_id, now)
            except IdentityNotFoundError as exc:
                self._audit(
                    repository,
                    action="identity.login_state_rejected",
                    actor_id="system:oidc_callback",
                    result="denied",
                    reason="invalid_or_replayed",
                    now=now,
                    correlation_id=claim_id,
                )
                session.commit()
                raise IdentityAuthenticationError(str(exc)) from exc
            verifier_ciphertext = flow.verifier_ciphertext
            nonce = flow.nonce
            requested_tenant_id = flow.requested_tenant_id
            return_to = flow.return_to
            self._audit(
                repository,
                action="identity.login_state_claimed",
                actor_id="system:oidc_callback",
                result="success",
                reason="claimed",
                now=now,
                correlation_id=claim_id,
            )
            session.commit()

        verifier = self._crypto.decrypt(verifier_ciphertext)
        try:
            identity = self._oidc.exchange_code(
                code=code,
                code_verifier=verifier,
                expected_nonce=nonce,
            )
        except Exception:
            self._record_login_denial(
                claim_id=claim_id,
                now=now,
                reason="provider_exchange_failed",
            )
            raise
        if identity.issuer.rstrip("/") != self._oidc.issuer.rstrip("/"):
            self._record_login_denial(
                claim_id=claim_id,
                now=now,
                reason="issuer_mismatch",
            )
            raise IdentityAuthenticationError("OIDC issuer mismatch")

        with self._session_factory() as session:
            repository = IdentityRepository(session)
            try:
                principal = repository.get_principal_by_external_identity(
                    identity.issuer,
                    identity.subject,
                )
                if principal is None:
                    principal = repository.create_principal(
                        principal_id=str(uuid4()),
                        issuer=identity.issuer,
                        subject=identity.subject,
                        display_name=identity.display_name,
                        email=identity.email,
                        now=now,
                    )
                    self._audit(
                        repository,
                        action="identity.principal_created",
                        actor_id=principal.principal_id,
                        principal_id=principal.principal_id,
                        result="success",
                        now=now,
                        correlation_id=claim_id,
                    )
                else:
                    repository.update_principal_attributes(
                        principal,
                        display_name=identity.display_name,
                        email=identity.email,
                        now=now,
                    )
                if principal.status != PrincipalStatus.ACTIVE.value:
                    raise IdentityAuthenticationError("portal principal is disabled")

                memberships = repository.list_memberships_for_principal(
                    principal.principal_id,
                    now,
                )
                membership = self._select_membership(
                    memberships,
                    requested_tenant_id=requested_tenant_id,
                )
                permissions = permissions_for_roles(self._role_names(membership))
                privileged = self._requires_mfa(permissions)
                if privileged and not identity.mfa_satisfied:
                    raise IdentityAuthenticationError("MFA is required for this membership")

                session_token = self._crypto.random_token()
                csrf_token = self._crypto.random_token()
                idle_timeout, absolute_timeout = self._session_timeouts(privileged)
                session_row = repository.create_session(
                    session_id_hash=self._crypto.hash_token(session_token),
                    csrf_token_hash=self._crypto.hash_token(csrf_token),
                    principal_id=principal.principal_id,
                    membership_id=membership.membership_id,
                    membership_version=membership.membership_version,
                    idp_session_id=identity.idp_session_id,
                    authentication_time=identity.authentication_time,
                    mfa_satisfied=identity.mfa_satisfied,
                    created_at=now,
                    idle_expires_at=now + idle_timeout,
                    absolute_expires_at=now + absolute_timeout,
                )
                self._audit(
                    repository,
                    action="identity.login_succeeded",
                    actor_id=principal.principal_id,
                    principal_id=principal.principal_id,
                    tenant_id=membership.tenant_id,
                    membership_id=membership.membership_id,
                    result="success",
                    now=now,
                    correlation_id=claim_id,
                )
                session.commit()
                return CompletedLogin(
                    return_to=return_to,
                    session=session_view(session_row, membership),
                    session_token=session_token,
                    csrf_token=csrf_token,
                )
            except IdentityAuthenticationError as exc:
                session.rollback()
                self._record_login_denial(
                    claim_id=claim_id,
                    now=now,
                    reason=self._login_denial_reason(exc),
                )
                raise

    def handle_backchannel_logout(self, logout_token: str) -> BackchannelLogoutResult:
        now = self._now()
        try:
            identity = self._oidc.validate_backchannel_logout(logout_token)
            _validate_logout_identity(identity)
        except OidcProtocolError as exc:
            self._record_logout_event(
                action="identity.backchannel_logout_rejected",
                result="denied",
                reason=_logout_rejection_reason(exc),
                now=now,
                correlation_id=None,
            )
            raise

        replay_key_hash = _logout_replay_key(identity)
        request_fingerprint = _logout_request_fingerprint(identity)

        with self._session_factory() as session:
            repository = IdentityRepository(session)
            purged = repository.purge_expired_logout_replays(now)
            if purged:
                self._audit(
                    repository,
                    action="identity.backchannel_logout_replay_expired",
                    actor_id="system:oidc_logout",
                    principal_id=None,
                    result="success",
                    reason=f"purged:{purged}",
                    now=now,
                )
            try:
                claim = repository.claim_logout_replay(
                    replay_key_hash=replay_key_hash,
                    issuer=identity.issuer,
                    client_id=identity.client_id,
                    jti=identity.jti,
                    request_fingerprint=request_fingerprint,
                    token_type=identity.token_type,
                    signing_key_id=identity.signing_key_id,
                    signing_algorithm=identity.signing_algorithm,
                    issued_at=identity.issued_at,
                    token_expires_at=identity.expires_at,
                    retention_until=identity.retention_until,
                    now=now,
                )
            except (IdentityReplayConflictError, IdentityReplayStateError) as exc:
                self._audit(
                    repository,
                    action="identity.backchannel_logout_conflict",
                    actor_id="system:oidc_logout",
                    principal_id=None,
                    result="denied",
                    reason=(
                        "semantic_conflict"
                        if isinstance(exc, IdentityReplayConflictError)
                        else "nonterminal_state"
                    ),
                    now=now,
                    correlation_id=replay_key_hash[:36],
                )
                session.commit()
                raise

            if not claim.owner:
                row = claim.row
                if row.revoked_sessions is None:
                    raise RuntimeError("terminal logout replay result is incomplete")
                result = BackchannelLogoutResult(
                    revoked_sessions=row.revoked_sessions,
                    processed_at=_utc(row.processed_at),
                )
                session.commit()
                return result

            count = repository.revoke_sessions_for_idp_identity(
                issuer=identity.issuer,
                subject=identity.subject,
                idp_session_id=identity.idp_session_id,
                now=now,
            )
            self._audit(
                repository,
                action="identity.backchannel_logout",
                actor_id=_logout_actor_id(identity.issuer),
                principal_id=None,
                result="success",
                reason=f"revoked:{count}",
                now=now,
                correlation_id=replay_key_hash[:36],
            )
            repository.complete_logout_replay(
                claim.row,
                revoked_sessions=count,
                processed_at=now,
                completed_at=now,
            )
            session.commit()
            return BackchannelLogoutResult(revoked_sessions=count, processed_at=now)

    def _record_login_denial(
        self,
        *,
        claim_id: str,
        now: datetime,
        reason: str,
    ) -> None:
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            self._audit(
                repository,
                action="identity.login_denied",
                actor_id="system:oidc_callback",
                result="denied",
                reason=reason,
                now=now,
                correlation_id=claim_id,
            )
            session.commit()

    def _record_logout_event(
        self,
        *,
        action: str,
        result: str,
        reason: str,
        now: datetime,
        correlation_id: str | None,
    ) -> None:
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            self._audit(
                repository,
                action=action,
                actor_id="system:oidc_logout",
                principal_id=None,
                result=result,
                reason=reason,
                now=now,
                correlation_id=correlation_id,
            )
            session.commit()

    @staticmethod
    def _login_denial_reason(exc: service_base.IdentityAuthenticationError) -> str:
        message = str(exc)
        if message == "portal principal is disabled":
            return "principal_disabled"
        if message == "MFA is required for this membership":
            return "mfa_required"
        if message == "tenant selection is required":
            return "tenant_selection_required"
        if message in {
            "requested tenant membership is unavailable",
            "no active portal membership",
        }:
            return "membership_unavailable"
        return "identity_resolution_failed"


def _canonical_digest(payload: dict[str, str | None]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _logout_replay_key(identity: OidcLogoutIdentity) -> str:
    return _canonical_digest(
        {
            "issuer": identity.issuer,
            "client_id": identity.client_id,
            "jti": identity.jti,
        }
    )


def _logout_request_fingerprint(identity: OidcLogoutIdentity) -> str:
    return _canonical_digest(
        {
            "issuer": identity.issuer,
            "client_id": identity.client_id,
            "jti": identity.jti,
            "issued_at": _utc(identity.issued_at).isoformat(),
            "expires_at": _utc(identity.expires_at).isoformat(),
            "retention_until": _utc(identity.retention_until).isoformat(),
            "token_type": identity.token_type,
            "signing_key_id": identity.signing_key_id,
            "signing_algorithm": identity.signing_algorithm,
            "subject": identity.subject,
            "idp_session_id": identity.idp_session_id,
        }
    )


def _validate_logout_identity(identity: OidcLogoutIdentity) -> None:
    for label, value, maximum in (
        ("issuer", identity.issuer, 1024),
        ("client_id", identity.client_id, 255),
        ("jti", identity.jti, 255),
        ("token_type", identity.token_type, 32),
        ("signing_key_id", identity.signing_key_id, 255),
        ("signing_algorithm", identity.signing_algorithm, 32),
    ):
        if not value or len(value) > maximum:
            raise OidcProtocolError(f"logout identity {label} is invalid")
    if identity.subject is None and identity.idp_session_id is None:
        raise OidcProtocolError("logout identity requires subject or sid")
    issued_at = _utc(identity.issued_at)
    expires_at = _utc(identity.expires_at)
    retention_until = _utc(identity.retention_until)
    if expires_at <= issued_at or retention_until <= expires_at:
        raise OidcProtocolError("logout identity time window is invalid")


def _logout_rejection_reason(exc: OidcProtocolError) -> str:
    message = str(exc).lower()
    if "expired" in message or "older than" in message:
        return "expired_or_stale"
    if "future" in message or "lifetime" in message or "time window" in message:
        return "invalid_time_window"
    if "typ" in message:
        return "invalid_token_type"
    if "jti" in message:
        return "invalid_jti"
    if "signature" in message or "signing" in message or "jwt validation" in message:
        return "invalid_signature"
    return "invalid_protocol"


def _logout_actor_id(issuer: str) -> str:
    return f"idp:{hashlib.sha256(issuer.encode()).hexdigest()}"


def _utc(value: datetime | None) -> datetime:
    if value is None:
        raise RuntimeError("terminal logout replay result is incomplete")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "SESSION_COOKIE_NAME",
    "CSRF_COOKIE_NAME",
    "CSRF_HEADER_NAME",
    "IdentityAuthenticationError",
    "IdentityAuthorizationError",
    "IdentityProviderError",
    "IdentityPolicy",
    "AuthenticatedSession",
    "IdentityService",
]
