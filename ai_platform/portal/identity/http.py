from __future__ import annotations

from typing import cast
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict

from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import IdentityContextProvider
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.identity.repository import IdentityConflictError, IdentityNotFoundError
from ai_platform.portal.identity.schema import (
    BackchannelLogoutResult,
    MembershipCreate,
    MembershipRolesUpdate,
    PortalSessionView,
    TenantMembership,
)
from ai_platform.portal.identity.service import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    IdentityAuthenticationError,
    IdentityAuthorizationError,
    IdentityService,
)


class LogoutAllResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked_sessions: int


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked: bool


def create_identity_enabled_app(
    session_factory: SessionFactory,
    identity_service: IdentityService,
    **control_plane_dependencies: object,
) -> FastAPI:
    provider = cast(IdentityContextProvider, identity_service.resolve_request)
    app = create_app(
        session_factory,
        identity_context_provider=provider,
        **control_plane_dependencies,
    )
    register_identity_routes(app, identity_service)
    install_csrf_middleware(app, identity_service)
    return app


def install_csrf_middleware(app: FastAPI, service: IdentityService) -> None:
    exempt_paths = {"/v1/identity/backchannel-logout"}

    @app.middleware("http")
    async def csrf_middleware(request: Request, call_next):
        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.url.path not in exempt_paths:
                try:
                    service.enforce_csrf(request)
                except IdentityAuthenticationError as exc:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": str(exc)},
                    )
                except IdentityAuthorizationError as exc:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": str(exc)},
                    )
        return await call_next(request)


def register_identity_routes(app: FastAPI, service: IdentityService) -> None:
    @app.exception_handler(IdentityAuthenticationError)
    async def authentication_error_handler(
        _request: Request,
        exc: IdentityAuthenticationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IdentityAuthorizationError)
    async def authorization_error_handler(
        _request: Request,
        exc: IdentityAuthorizationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def identity_validation_error_handler(
        _request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IdentityNotFoundError)
    async def identity_not_found_handler(
        _request: Request,
        exc: IdentityNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IdentityConflictError)
    async def identity_conflict_handler(
        _request: Request,
        exc: IdentityConflictError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.get("/v1/identity/login")
    def login(
        tenant_id: str | None = None,
        return_to: str = "/",
    ) -> RedirectResponse:
        result = service.begin_login(
            requested_tenant_id=tenant_id,
            return_to=return_to,
        )
        response = RedirectResponse(
            result.authorization_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
        response.headers["cache-control"] = "no-store"
        return response

    @app.get("/v1/identity/callback")
    def callback(code: str, state: str) -> RedirectResponse:
        completed = service.complete_login(code=code, state=state)
        response = RedirectResponse(
            completed.return_to,
            status_code=status.HTTP_303_SEE_OTHER,
        )
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
        revoked = service.logout_current(request)
        return LogoutResponse(revoked=revoked)

    @app.post("/v1/identity/logout-all", response_model=LogoutAllResponse)
    def logout_all(request: Request) -> LogoutAllResponse:
        return LogoutAllResponse(revoked_sessions=service.logout_all(request))

    @app.post(
        "/v1/identity/backchannel-logout",
        response_model=BackchannelLogoutResult,
    )
    async def backchannel_logout(request: Request) -> BackchannelLogoutResult:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            raise IdentityAuthenticationError("back-channel logout requires form encoding")
        values = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
        tokens = values.get("logout_token", [])
        if len(tokens) != 1 or not tokens[0]:
            raise IdentityAuthenticationError("logout_token is required")
        return service.handle_backchannel_logout(tokens[0])

    @app.post(
        "/v1/identity/memberships",
        response_model=TenantMembership,
        status_code=status.HTTP_201_CREATED,
    )
    def create_membership(
        payload: MembershipCreate,
        request: Request,
    ) -> TenantMembership:
        return service.create_membership(request, payload)

    @app.put(
        "/v1/identity/memberships/{membership_id}/roles",
        response_model=TenantMembership,
    )
    def update_membership_roles(
        membership_id: str,
        payload: MembershipRolesUpdate,
        request: Request,
    ) -> TenantMembership:
        return service.update_membership_roles(request, membership_id, payload)

    @app.post(
        "/v1/identity/memberships/{membership_id}/disable",
        response_model=TenantMembership,
    )
    def disable_membership(
        membership_id: str,
        request: Request,
    ) -> TenantMembership:
        return service.disable_membership(request, membership_id)
