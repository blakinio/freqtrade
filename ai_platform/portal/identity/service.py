from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import Request

from ai_platform.portal.contracts.identity import ActorType, Permission, RoleName
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.identity.crypto import IdentityCrypto
from ai_platform.portal.identity.models import (
    IdentityPrincipalRow,
    PortalSessionRow,
    TenantMembershipRow,
)
from ai_platform.portal.identity.oidc import OidcClientProtocol, pkce_challenge
from ai_platform.portal.identity.repository import (
    IdentityNotFoundError,
    IdentityRepository,
    membership_from_row,
    principal_from_row,
    session_view,
)
from ai_platform.portal.identity.schema import (
    BackchannelLogoutResult,
    BeginLoginResult,
    CompletedLogin,
    IdentityAuditEvent,
    IdentityPrincipal,
    MembershipCreate,
    MembershipRolesUpdate,
    MembershipStatus,
    PortalSessionView,
    PrincipalStatus,
    TenantMembership,
)
from ai_platform.portal.security.authorization import (
    permissions_for_roles,
    require_permission,
)


SESSION_COOKIE_NAME = "__Host-portal_session"
CSRF_COOKIE_NAME = "__Host-portal_csrf"
CSRF_HEADER_NAME = "x-csrf-token"


class IdentityAuthenticationError(PermissionError):
    pass


class IdentityAuthorizationError(PermissionError):
    pass


class IdentityProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class IdentityPolicy:
    standard_idle_timeout: timedelta = timedelta(minutes=30)
    standard_absolute_timeout: timedelta = timedelta(hours=12)
    privileged_idle_timeout: timedelta = timedelta(minutes=15)
    privileged_absolute_timeout: timedelta = timedelta(hours=4)
    step_up_max_age: timedelta = timedelta(minutes=5)
    login_flow_timeout: timedelta = timedelta(minutes=10)
    allowed_return_prefixes: tuple[str, ...] = ("/",)


@dataclass(frozen=True)
class AuthenticatedSession:
    context: RequestContext
    view: PortalSessionView
    row: PortalSessionRow
    membership: TenantMembershipRow


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class IdentityService:
    def __init__(
        self,
        session_factory: SessionFactory,
        oidc_client: OidcClientProtocol,
        crypto: IdentityCrypto,
        *,
        policy: IdentityPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._session_factory = session_factory
        self._oidc = oidc_client
        self._crypto = crypto
        self._policy = policy or IdentityPolicy()
        self._clock = clock or (lambda: datetime.now(UTC))

    @property
    def issuer(self) -> str:
        return self._oidc.issuer

    def begin_login(
        self,
        *,
        requested_tenant_id: str | None,
        return_to: str,
    ) -> BeginLoginResult:
        now = self._now()
        safe_return_to = self._safe_return_to(return_to)
        state = self._crypto.random_token()
        nonce = self._crypto.random_token()
        verifier = self._crypto.random_token(48)
        expires_at = now + self._policy.login_flow_timeout
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            repository.store_login_flow(
                state_hash=self._crypto.hash_token(state),
                nonce=nonce,
                verifier_ciphertext=self._crypto.encrypt(verifier),
                requested_tenant_id=requested_tenant_id,
                return_to=safe_return_to,
                created_at=now,
                expires_at=expires_at,
            )
            session.commit()
        return BeginLoginResult(
            authorization_url=self._oidc.authorization_url(
                state=state,
                nonce=nonce,
                code_challenge=pkce_challenge(verifier),
            ),
            expires_at=expires_at,
        )

    def complete_login(self, *, code: str, state: str) -> CompletedLogin:
        if not code or not state:
            raise IdentityAuthenticationError("OIDC callback requires code and state")
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            try:
                flow = repository.consume_login_flow(self._crypto.hash_token(state), now)
            except IdentityNotFoundError as exc:
                raise IdentityAuthenticationError(str(exc)) from exc
            verifier = self._crypto.decrypt(flow.verifier_ciphertext)
            identity = self._oidc.exchange_code(
                code=code,
                code_verifier=verifier,
                expected_nonce=flow.nonce,
            )
            if identity.issuer.rstrip("/") != self._oidc.issuer.rstrip("/"):
                raise IdentityAuthenticationError("OIDC issuer mismatch")
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

            memberships = repository.list_memberships_for_principal(principal.principal_id, now)
            membership = self._select_membership(
                memberships,
                requested_tenant_id=flow.requested_tenant_id,
            )
            permissions = permissions_for_roles(self._role_names(membership))
            privileged = self._requires_mfa(permissions)
            if privileged and not identity.mfa_satisfied:
                self._audit(
                    repository,
                    action="identity.login_denied",
                    actor_id=principal.principal_id,
                    principal_id=principal.principal_id,
                    tenant_id=membership.tenant_id,
                    membership_id=membership.membership_id,
                    result="denied",
                    reason="mfa_required",
                    now=now,
                )
                session.commit()
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
            )
            session.commit()
            return CompletedLogin(
                return_to=flow.return_to,
                session=session_view(session_row, membership),
                session_token=session_token,
                csrf_token=csrf_token,
            )

    def resolve_request(self, request: Request) -> RequestContext:
        return self.authenticate(request).context

    def authenticate(self, request: Request, *, touch: bool = True) -> AuthenticatedSession:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_token:
            raise IdentityAuthenticationError("portal session is missing")
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            try:
                authenticated = self._authenticate_with_repository(
                    repository,
                    session_token=session_token,
                    now=now,
                    touch=touch,
                )
            except IdentityAuthenticationError:
                session.commit()
                raise
            session.commit()
            return authenticated

    def enforce_csrf(self, request: Request) -> None:
        if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
            return
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_token:
            raise IdentityAuthenticationError("portal session is missing")
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            authenticated = self._authenticate_with_repository(
                repository,
                session_token=session_token,
                now=now,
                touch=False,
            )
            if not csrf_cookie or not csrf_header:
                raise IdentityAuthorizationError("CSRF token is missing")
            if csrf_cookie != csrf_header:
                raise IdentityAuthorizationError("CSRF token mismatch")
            if not self._crypto.verify_token_hash(
                csrf_header,
                authenticated.row.csrf_token_hash,
            ):
                raise IdentityAuthorizationError("CSRF token is invalid")

    def current_session(self, request: Request) -> PortalSessionView:
        return self.authenticate(request).view

    def logout_current(self, request: Request, *, reason: str = "user_logout") -> bool:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_token:
            return False
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            row = repository.get_session(self._crypto.hash_token(session_token))
            if row is None:
                return False
            revoked = repository.revoke_session(
                row,
                actor_id=row.principal_id,
                reason=reason,
                now=now,
                correlation_id=None,
            )
            if revoked:
                self._audit(
                    repository,
                    action="identity.session_revoked",
                    actor_id=row.principal_id,
                    principal_id=row.principal_id,
                    result="success",
                    reason=reason,
                    now=now,
                )
            session.commit()
            return revoked

    def logout_all(self, request: Request) -> int:
        authenticated = self.authenticate(request, touch=False)
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            count = repository.revoke_sessions_for_principal(
                principal_id=authenticated.context.actor_id,
                actor_id=authenticated.context.actor_id,
                reason="user_logout_all",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            self._audit(
                repository,
                action="identity.logout_all",
                actor_id=authenticated.context.actor_id,
                principal_id=authenticated.context.actor_id,
                tenant_id=authenticated.context.tenant_id,
                membership_id=authenticated.view.membership_id,
                result="success",
                reason=f"revoked:{count}",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            session.commit()
            return count

    def handle_backchannel_logout(self, logout_token: str) -> BackchannelLogoutResult:
        identity = self._oidc.validate_backchannel_logout(logout_token)
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            count = repository.revoke_sessions_for_idp_identity(
                issuer=identity.issuer,
                subject=identity.subject,
                idp_session_id=identity.idp_session_id,
                now=now,
            )
            self._audit(
                repository,
                action="identity.backchannel_logout",
                actor_id=f"idp:{identity.issuer}",
                principal_id=None,
                result="success",
                reason=f"revoked:{count}",
                now=now,
            )
            session.commit()
        return BackchannelLogoutResult(revoked_sessions=count, processed_at=now)

    def bootstrap_principal(
        self,
        *,
        issuer: str,
        subject: str,
        display_name: str,
        email: str | None,
    ) -> IdentityPrincipal:
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            row = repository.create_principal(
                principal_id=str(uuid4()),
                issuer=issuer,
                subject=subject,
                display_name=display_name,
                email=email,
                now=now,
            )
            self._audit(
                repository,
                action="identity.principal_bootstrapped",
                actor_id="system:bootstrap",
                principal_id=row.principal_id,
                result="success",
                now=now,
            )
            session.commit()
            return principal_from_row(row)

    def bootstrap_membership(
        self,
        *,
        principal_id: str,
        tenant_id: str,
        roles: tuple[RoleName, ...],
        valid_until: datetime | None = None,
    ) -> TenantMembership:
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            if repository.get_principal(principal_id) is None:
                raise IdentityNotFoundError("principal not found")
            row = repository.create_membership(
                membership_id=str(uuid4()),
                principal_id=principal_id,
                tenant_id=tenant_id,
                roles=roles,
                valid_from=now,
                valid_until=valid_until,
                now=now,
            )
            self._audit(
                repository,
                action="identity.membership_bootstrapped",
                actor_id="system:bootstrap",
                principal_id=principal_id,
                tenant_id=tenant_id,
                membership_id=row.membership_id,
                result="success",
                now=now,
            )
            session.commit()
            return membership_from_row(row)

    def create_membership(
        self,
        request: Request,
        membership: MembershipCreate,
    ) -> TenantMembership:
        authenticated = self._require_admin_step_up(request)
        if membership.tenant_id != authenticated.context.tenant_id:
            raise IdentityAuthorizationError("tenant scope mismatch")
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            principal = repository.get_principal(membership.principal_id)
            if principal is None:
                raise IdentityNotFoundError("principal not found")
            row = repository.create_membership(
                membership_id=str(uuid4()),
                principal_id=membership.principal_id,
                tenant_id=membership.tenant_id,
                roles=membership.roles,
                valid_from=now,
                valid_until=membership.valid_until,
                now=now,
            )
            self._audit(
                repository,
                action="identity.membership_created",
                actor_id=authenticated.context.actor_id,
                principal_id=membership.principal_id,
                tenant_id=membership.tenant_id,
                membership_id=row.membership_id,
                result="success",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            session.commit()
            return membership_from_row(row)

    def update_membership_roles(
        self,
        request: Request,
        membership_id: str,
        update: MembershipRolesUpdate,
    ) -> TenantMembership:
        authenticated = self._require_admin_step_up(request)
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            row = self._tenant_membership(
                repository,
                membership_id,
                authenticated.context.tenant_id,
            )
            repository.update_membership_roles(row, update.roles, now)
            revoked = repository.revoke_sessions_for_membership(
                membership_id=row.membership_id,
                actor_id=authenticated.context.actor_id,
                reason="membership_roles_changed",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            self._audit(
                repository,
                action="identity.membership_roles_changed",
                actor_id=authenticated.context.actor_id,
                principal_id=row.principal_id,
                tenant_id=row.tenant_id,
                membership_id=row.membership_id,
                result="success",
                reason=f"revoked:{revoked}",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            session.commit()
            return membership_from_row(row)

    def disable_membership(self, request: Request, membership_id: str) -> TenantMembership:
        authenticated = self._require_admin_step_up(request)
        now = self._now()
        with self._session_factory() as session:
            repository = IdentityRepository(session)
            row = self._tenant_membership(
                repository,
                membership_id,
                authenticated.context.tenant_id,
            )
            repository.disable_membership(row, now)
            revoked = repository.revoke_sessions_for_membership(
                membership_id=row.membership_id,
                actor_id=authenticated.context.actor_id,
                reason="membership_disabled",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            self._audit(
                repository,
                action="identity.membership_disabled",
                actor_id=authenticated.context.actor_id,
                principal_id=row.principal_id,
                tenant_id=row.tenant_id,
                membership_id=row.membership_id,
                result="success",
                reason=f"revoked:{revoked}",
                now=now,
                correlation_id=str(authenticated.context.correlation_id),
            )
            session.commit()
            return membership_from_row(row)

    def _authenticate_with_repository(
        self,
        repository: IdentityRepository,
        *,
        session_token: str,
        now: datetime,
        touch: bool,
    ) -> AuthenticatedSession:
        row = repository.get_session(self._crypto.hash_token(session_token))
        if row is None:
            raise IdentityAuthenticationError("portal session is invalid")
        if row.revoked_at is not None:
            raise IdentityAuthenticationError("portal session is revoked")
        if _utc(row.idle_expires_at) <= now or _utc(row.absolute_expires_at) <= now:
            repository.revoke_session(
                row,
                actor_id="system:session",
                reason="session_expired",
                now=now,
                correlation_id=None,
            )
            raise IdentityAuthenticationError("portal session is expired")
        principal = repository.get_principal(row.principal_id)
        if principal is None or principal.status != PrincipalStatus.ACTIVE.value:
            raise IdentityAuthenticationError("portal principal is unavailable")
        membership = repository.get_membership(row.membership_id)
        if membership is None:
            raise IdentityAuthenticationError("portal membership is unavailable")
        if membership.status != MembershipStatus.ACTIVE.value:
            raise IdentityAuthenticationError("portal membership is disabled")
        if _utc(membership.valid_from) > now or (
            membership.valid_until is not None and _utc(membership.valid_until) <= now
        ):
            raise IdentityAuthenticationError("portal membership is outside its validity window")
        if membership.membership_version != row.membership_version:
            repository.revoke_session(
                row,
                actor_id="system:membership",
                reason="membership_version_changed",
                now=now,
                correlation_id=None,
            )
            raise IdentityAuthenticationError("portal membership changed")
        roles = self._role_names(membership)
        permissions = permissions_for_roles(roles)
        if self._requires_mfa(permissions) and not row.mfa_satisfied:
            raise IdentityAuthenticationError("MFA is required for this session")
        privileged = self._requires_mfa(permissions)
        idle_timeout, _ = self._session_timeouts(privileged)
        if touch:
            repository.touch_session(row, now=now, idle_expires_at=now + idle_timeout)
        context = RequestContext(
            tenant_id=membership.tenant_id,
            actor_id=principal.principal_id,
            actor_type=ActorType.USER,
            permissions=tuple(sorted(permissions, key=lambda item: item.value)),
            request_id=uuid4(),
            correlation_id=uuid4(),
        )
        return AuthenticatedSession(
            context=context,
            view=session_view(row, membership),
            row=row,
            membership=membership,
        )

    def _require_admin_step_up(self, request: Request) -> AuthenticatedSession:
        authenticated = self.authenticate(request, touch=False)
        try:
            require_permission(authenticated.context.permissions, Permission.ADMIN_MANAGE)
        except PermissionError as exc:
            raise IdentityAuthorizationError(str(exc)) from exc
        if not authenticated.row.mfa_satisfied:
            raise IdentityAuthorizationError("MFA is required")
        if self._now() - _utc(authenticated.row.authentication_time) > self._policy.step_up_max_age:
            raise IdentityAuthorizationError("fresh authentication is required")
        return authenticated

    def _tenant_membership(
        self,
        repository: IdentityRepository,
        membership_id: str,
        tenant_id: str,
    ) -> TenantMembershipRow:
        row = repository.get_membership(membership_id)
        if row is None or row.tenant_id != tenant_id:
            raise IdentityNotFoundError("membership not found")
        return row

    @staticmethod
    def _role_names(membership: TenantMembershipRow) -> tuple[RoleName, ...]:
        import json

        return tuple(RoleName(value) for value in json.loads(membership.roles_json))

    @staticmethod
    def _requires_mfa(permissions: frozenset[Permission]) -> bool:
        read_only = {
            Permission.BOT_READ,
            Permission.MODEL_READ,
        }
        return bool(set(permissions) - read_only)

    def _session_timeouts(self, privileged: bool) -> tuple[timedelta, timedelta]:
        if privileged:
            return (
                self._policy.privileged_idle_timeout,
                self._policy.privileged_absolute_timeout,
            )
        return (
            self._policy.standard_idle_timeout,
            self._policy.standard_absolute_timeout,
        )

    def _select_membership(
        self,
        memberships: tuple[TenantMembershipRow, ...],
        *,
        requested_tenant_id: str | None,
    ) -> TenantMembershipRow:
        if requested_tenant_id is not None:
            selected = next(
                (item for item in memberships if item.tenant_id == requested_tenant_id),
                None,
            )
            if selected is None:
                raise IdentityAuthenticationError("requested tenant membership is unavailable")
            return selected
        if len(memberships) == 1:
            return memberships[0]
        if not memberships:
            raise IdentityAuthenticationError("no active portal membership")
        raise IdentityAuthenticationError("tenant selection is required")

    def _safe_return_to(self, return_to: str) -> str:
        if not return_to.startswith("/") or return_to.startswith("//"):
            raise ValueError("return_to must be an application-relative path")
        if not any(return_to.startswith(prefix) for prefix in self._policy.allowed_return_prefixes):
            raise ValueError("return_to is not allowed")
        return return_to

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("identity clock must return a timezone-aware timestamp")
        return value.astimezone(UTC)

    @staticmethod
    def _audit(
        repository: IdentityRepository,
        *,
        action: str,
        actor_id: str,
        result: str,
        now: datetime,
        principal_id: str | None = None,
        tenant_id: str | None = None,
        membership_id: str | None = None,
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        repository.add_audit_event(
            IdentityAuditEvent(
                event_id=str(uuid4()),
                action=action,
                actor_id=actor_id,
                principal_id=principal_id,
                tenant_id=tenant_id,
                membership_id=membership_id,
                result=result,
                reason=reason,
                occurred_at=now,
                correlation_id=correlation_id,
            )
        )
