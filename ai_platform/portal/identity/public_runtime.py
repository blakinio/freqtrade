from __future__ import annotations

import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict

from ai_platform.portal.control_plane.database import (
    Base,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.identity.oidc import OidcProviderUnavailable
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig, build_identity_service
from ai_platform.portal.identity.schema import BackchannelLogoutResult, PortalSessionView
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


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required public identity setting is missing: {name}")
    return value


def _expire_identity_cookies(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=False,
        samesite="lax",
    )


def _register_identity_routes(app: FastAPI, service: IdentityService) -> None:  # noqa: C901
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

    @app.get("/v1/identity/login")
    def login(tenant_id: str | None = None, return_to: str = "/") -> RedirectResponse:
        result = service.begin_login(
            requested_tenant_id=tenant_id,
            return_to=return_to,
        )
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
    def logout(request: Request, response: Response) -> LogoutResponse:
        revoked = service.logout_current(request)
        _expire_identity_cookies(response)
        response.headers["cache-control"] = "no-store"
        return LogoutResponse(revoked=revoked)

    @app.post("/v1/identity/logout-all", response_model=LogoutAllResponse)
    def logout_all(request: Request, response: Response) -> LogoutAllResponse:
        revoked_sessions = service.logout_all(request)
        _expire_identity_cookies(response)
        response.headers["cache-control"] = "no-store"
        return LogoutAllResponse(revoked_sessions=revoked_sessions)

    @app.post("/v1/identity/backchannel-logout", response_model=BackchannelLogoutResult)
    async def backchannel_logout(request: Request) -> BackchannelLogoutResult:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            raise IdentityAuthenticationError(
                "back-channel logout requires form encoding"
            )
        values = parse_qs(
            (await request.body()).decode("utf-8"),
            strict_parsing=True,
        )
        tokens = values.get("logout_token", [])
        if len(tokens) != 1 or not tokens[0]:
            raise IdentityAuthenticationError("logout_token is required")
        return service.handle_backchannel_logout(tokens[0])


def build_public_app() -> FastAPI:
    environment = _required("PORTAL_ENVIRONMENT")
    if environment not in {"production", "staging"}:
        raise RuntimeError("public identity runtime requires production or staging")
    database_url = _required("PORTAL_DATABASE_URL")
    engine = build_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    config = IdentityRuntimeConfig.from_environment()
    if config.transport_mode != "https":
        raise RuntimeError("public identity runtime requires HTTPS transport")
    identity_service = build_identity_service(session_factory, config)
    app = FastAPI(title="Freqtrade Portal Public Identity Session API")
    _register_identity_routes(app, identity_service)

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {
            "status": "ok",
            "identity_transport": config.transport_mode,
            "identity_fixture": False,
            "membership_bootstrap": "explicit_only",
            "live_capital_authorized": False,
        }

    return app


app = build_public_app()
