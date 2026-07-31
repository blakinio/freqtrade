from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs
from uuid import NAMESPACE_URL, uuid5

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    Base,
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.identity.models import TenantMembershipRow
from ai_platform.portal.identity.oidc import OidcProviderUnavailable
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig, build_identity_service
from ai_platform.portal.identity.schema import (
    BackchannelLogoutResult,
    MembershipStatus,
    PortalSessionView,
    PrincipalStatus,
)
from ai_platform.portal.identity.service import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    IdentityAuthenticationError,
    IdentityAuthorizationError,
    IdentityService,
)

_SECURE_SESSION_COOKIE = "__Host-portal_session"
_SECURE_CSRF_COOKIE = "__Host-portal_csrf"
_LOCAL_SESSION_COOKIE = "portal_session"
_LOCAL_CSRF_COOKIE = "portal_csrf"

Scope = dict[str, Any]
Message = dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
AsgiApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class LogoutAllResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked_sessions: int


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked: bool


class LocalHttpCookieAdapter:
    """Translate secure production cookie names only in the explicit local-test mode."""

    def __init__(self, app: AsgiApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        adapted_scope = dict(scope)
        adapted_scope["headers"] = [
            (name, _rewrite_request_cookie(value) if name.lower() == b"cookie" else value)
            for name, value in scope.get("headers", [])
        ]

        async def adapted_send(message: Message) -> None:
            if message.get("type") == "http.response.start":
                message = dict(message)
                message["headers"] = [
                    (
                        name,
                        _rewrite_response_cookie(value)
                        if name.lower() == b"set-cookie"
                        else value,
                    )
                    for name, value in message.get("headers", [])
                ]
            await send(message)

        await self.app(adapted_scope, receive, adapted_send)


def _rewrite_request_cookie(value: bytes) -> bytes:
    text = value.decode("latin-1")
    items: list[str] = []
    for item in text.split(";"):
        stripped = item.strip()
        if stripped.startswith(f"{_LOCAL_SESSION_COOKIE}="):
            stripped = f"{_SECURE_SESSION_COOKIE}={stripped.split('=', 1)[1]}"
        elif stripped.startswith(f"{_LOCAL_CSRF_COOKIE}="):
            stripped = f"{_SECURE_CSRF_COOKIE}={stripped.split('=', 1)[1]}"
        items.append(stripped)
    return "; ".join(items).encode("latin-1")


def _rewrite_response_cookie(value: bytes) -> bytes:
    text = value.decode("latin-1")
    if text.startswith(f"{_SECURE_SESSION_COOKIE}="):
        text = f"{_LOCAL_SESSION_COOKIE}={text.split('=', 1)[1]}"
    elif text.startswith(f"{_SECURE_CSRF_COOKIE}="):
        text = f"{_LOCAL_CSRF_COOKIE}={text.split('=', 1)[1]}"
    parts = [part for part in text.split("; ") if part.lower() != "secure"]
    return "; ".join(parts).encode("latin-1")


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required local-test setting is missing: {name}")
    return value


def _ensure_local_owner_membership(
    session_factory: SessionFactory,
    config: IdentityRuntimeConfig,
) -> None:
    subject = _required("PORTAL_IDENTITY_BOOTSTRAP_SUBJECT")
    display_name = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_DISPLAY_NAME", "Local Portal Owner")
    email = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_EMAIL") or None
    tenant_id = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_TENANT_ID", "tenant-local")
    now = datetime.now(UTC)
    with session_factory() as session:
        repository = IdentityRepository(session)
        principal = repository.get_principal_by_external_identity(config.issuer, subject)
        if principal is None:
            principal = repository.create_principal(
                principal_id=str(uuid5(NAMESPACE_URL, f"{config.issuer}|{subject}")),
                issuer=config.issuer,
                subject=subject,
                display_name=display_name,
                email=email,
                now=now,
            )
        elif principal.status != PrincipalStatus.ACTIVE.value:
            raise RuntimeError("local owner principal exists but is disabled")
        membership = session.scalar(
            select(TenantMembershipRow).where(
                TenantMembershipRow.principal_id == principal.principal_id,
                TenantMembershipRow.tenant_id == tenant_id,
            )
        )
        if membership is None:
            repository.create_membership(
                membership_id=str(
                    uuid5(NAMESPACE_URL, f"{config.issuer}|{subject}|{tenant_id}|membership")
                ),
                principal_id=principal.principal_id,
                tenant_id=tenant_id,
                roles=(RoleName.ADMIN,),
                valid_from=now,
                valid_until=None,
                now=now,
            )
        else:
            if membership.status != MembershipStatus.ACTIVE.value:
                raise RuntimeError("local owner membership exists but is disabled")
            roles = set(json.loads(membership.roles_json))
            if roles != {RoleName.ADMIN.value}:
                raise RuntimeError("local owner membership roles differ from the frozen contract")
        session.commit()


def _register_identity_routes(app: FastAPI, service: IdentityService) -> None:  # noqa: C901
    @app.exception_handler(IdentityAuthenticationError)
    async def authentication_error_handler(
        _request: Request,
        exc: IdentityAuthenticationError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})

    @app.exception_handler(IdentityAuthorizationError)
    async def authorization_error_handler(
        _request: Request,
        exc: IdentityAuthorizationError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

    @app.exception_handler(OidcProviderUnavailable)
    async def provider_error_handler(
        _request: Request,
        _exc: OidcProviderUnavailable,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "OIDC provider is unavailable"},
        )

    @app.middleware("http")
    async def csrf_middleware(request: Request, call_next):
        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and (
            request.url.path != "/v1/identity/backchannel-logout"
        ):
            try:
                service.enforce_csrf(request)
            except IdentityAuthenticationError as exc:
                return JSONResponse(status_code=401, content={"detail": str(exc)})
            except IdentityAuthorizationError as exc:
                return JSONResponse(status_code=403, content={"detail": str(exc)})
        return await call_next(request)

    @app.get("/v1/identity/login")
    def login(tenant_id: str | None = None, return_to: str = "/") -> RedirectResponse:
        result = service.begin_login(requested_tenant_id=tenant_id, return_to=return_to)
        response = RedirectResponse(result.authorization_url, status_code=307)
        response.headers["cache-control"] = "no-store"
        return response

    @app.get("/v1/identity/callback")
    def callback(code: str, state: str) -> RedirectResponse:
        completed = service.complete_login(code=code, state=state)
        response = RedirectResponse(completed.return_to, status_code=303)
        response.set_cookie(
            SESSION_COOKIE_NAME,
            completed.session_token,
            secure=True,
            httponly=True,
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            CSRF_COOKIE_NAME,
            completed.csrf_token,
            secure=True,
            httponly=False,
            samesite="lax",
            path="/",
        )
        response.headers["cache-control"] = "no-store"
        return response

    @app.get("/v1/identity/session", response_model=PortalSessionView)
    def current_session(request: Request) -> PortalSessionView:
        return service.current_session(request)

    @app.post("/v1/identity/logout", response_model=LogoutResponse)
    def logout(request: Request) -> LogoutResponse:
        return LogoutResponse(revoked=service.logout_current(request))

    @app.post("/v1/identity/logout-all", response_model=LogoutAllResponse)
    def logout_all(request: Request) -> LogoutAllResponse:
        return LogoutAllResponse(revoked_sessions=service.logout_all(request))

    @app.post("/v1/identity/backchannel-logout", response_model=BackchannelLogoutResult)
    async def backchannel_logout(request: Request) -> BackchannelLogoutResult:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            raise IdentityAuthenticationError("back-channel logout requires form encoding")
        values = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
        tokens = values.get("logout_token", [])
        if len(tokens) != 1 or not tokens[0]:
            raise IdentityAuthenticationError("logout_token is required")
        return service.handle_backchannel_logout(tokens[0])


def build_local_test_app() -> FastAPI:
    if os.environ.get("PORTAL_ENVIRONMENT") != "test":
        raise RuntimeError("local-test identity runtime requires PORTAL_ENVIRONMENT=test")
    database_url = _required("PORTAL_DATABASE_URL")
    engine = build_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    config = IdentityRuntimeConfig.from_environment()
    if not config.allow_insecure_local_http:
        raise RuntimeError("local-test identity runtime requires local_http_test transport")
    _ensure_local_owner_membership(session_factory, config)
    identity_service = build_identity_service(session_factory, config)
    app = FastAPI(title="Freqtrade Portal Local Identity Session API")
    _register_identity_routes(app, identity_service)

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {
            "status": "ok",
            "identity_transport": config.transport_mode,
            "identity_fixture": False,
            "live_capital_authorized": False,
        }

    app.add_middleware(LocalHttpCookieAdapter)
    return app


app = build_local_test_app()
