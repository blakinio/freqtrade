from __future__ import annotations

import os

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.database.schema import EXPECTED_SCHEMA_REVISION, assert_schema_ready
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig, build_identity_service


_REQUIRED_COMPOSED_ROUTES = frozenset(
    {
        "/v1/identity/login",
        "/v1/identity/session",
        "/v1/bots",
        "/v1/positions",
        "/v1/terminal/intents",
        "/v1/models",
        "/v1/strategies",
        "/v1/valuations",
        "/v1/runtime-observability/availability",
    }
)


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required public Portal setting is missing: {name}")
    return value


def _assert_full_router_inventory(app: FastAPI) -> int:
    paths = {route.path for route in app.routes}
    missing = sorted(_REQUIRED_COMPOSED_ROUTES - paths)
    if missing:
        raise RuntimeError(
            "public Portal composition is missing canonical routes: " + ", ".join(missing)
        )
    return len(paths)


def build_public_app() -> FastAPI:
    environment = _required("PORTAL_ENVIRONMENT")
    if environment not in {"production", "staging"}:
        raise RuntimeError("public Portal runtime requires production or staging")

    database_url = _required("PORTAL_DATABASE_URL")
    engine = build_engine(database_url)
    if environment == "production" and engine.dialect.name != "postgresql":
        engine.dispose()
        raise RuntimeError("public production runtime requires PostgreSQL")

    schema_report = assert_schema_ready(engine)
    session_factory = build_session_factory(engine)
    identity_config = IdentityRuntimeConfig.from_environment()
    if identity_config.transport_mode != "secure_https":
        engine.dispose()
        raise RuntimeError("public Portal runtime requires HTTPS identity transport")

    identity_service = build_identity_service(session_factory, identity_config)
    app = create_identity_enabled_app(session_factory, identity_service)
    app.title = "Freqtrade Portal Authenticated Control Plane"
    app.state.schema_report = schema_report
    app.state.database_engine = engine
    app.state.identity_config = identity_config
    app.state.public_runtime_unprivileged = True
    route_count = _assert_full_router_inventory(app)

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {
            "status": "alive",
            "role": "portal-api",
            "live_capital_authorized": False,
        }

    @app.get("/readyz", include_in_schema=False)
    def readyz() -> dict[str, object] | JSONResponse:
        try:
            current_schema = assert_schema_ready(engine)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "role": "portal-api",
                    "live_capital_authorized": False,
                },
            )
        return {
            "status": "ready",
            "role": "portal-api",
            "identity_transport": identity_config.transport_mode,
            "identity_fixture": False,
            "membership_bootstrap": "explicit_only",
            "database_dialect": engine.dialect.name,
            "schema_revision": current_schema.get("revision", EXPECTED_SCHEMA_REVISION),
            "canonical_schema_revision": EXPECTED_SCHEMA_REVISION,
            "route_count": route_count,
            "required_router_inventory_complete": True,
            "runtime_authority": "unprivileged",
            "live_capital_authorized": False,
        }

    return app


app = build_public_app()
