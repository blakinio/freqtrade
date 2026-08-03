from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from ai_platform.portal.identity.repository import (
    IdentityNotFoundError,
    IdentityRepository,
    session_view,
)
from ai_platform.portal.identity.schema import CompletedLogin, PrincipalStatus
from ai_platform.portal.identity.service_base import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    AuthenticatedSession,
    IdentityAuthenticationError,
    IdentityAuthorizationError,
    IdentityPolicy,
    IdentityProviderError,
    IdentityService as _IdentityService,
)
from ai_platform.portal.security.authorization import permissions_for_roles


class IdentityService(_IdentityService):
    """Identity service with an attributable, fail-closed OIDC callback lifecycle."""

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

    @staticmethod
    def _login_denial_reason(exc: IdentityAuthenticationError) -> str:
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
