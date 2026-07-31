from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from fastapi import FastAPI
from sqlalchemy import select

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.models import TenantMembershipRow
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig, build_identity_service
from ai_platform.portal.identity.schema import MembershipStatus, PrincipalStatus

_SECURE_SESSION_COOKIE = "__Host-portal_session"
_SECURE_CSRF_COOKIE = "__Host-portal_csrf"
_LOCAL_SESSION_COOKIE = "portal_session"
_LOCAL_CSRF_COOKIE = "portal_csrf"


class LocalHttpCookieAdapter:
    """Translate secure production cookie names only in the explicit local-test mode."""

    def __init__(self, app: object):
        self.app = app

    async def __call__(self, scope: dict, receive: object, send: object) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)  # type: ignore[misc]
            return
        adapted_scope = dict(scope)
        adapted_scope["headers"] = [
            (name, _rewrite_request_cookie(value) if name.lower() == b"cookie" else value)
            for name, value in scope.get("headers", [])
        ]

        async def adapted_send(message: dict) -> None:
            if message.get("type") == "http.response.start":
                message = dict(message)
                message["headers"] = [
                    (name, _rewrite_response_cookie(value) if name.lower() == b"set-cookie" else value)
                    for name, value in message.get("headers", [])
                ]
            await send(message)  # type: ignore[misc]

        await self.app(adapted_scope, receive, adapted_send)  # type: ignore[misc]


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


def _ensure_local_owner_membership(session_factory: object, config: IdentityRuntimeConfig) -> None:
    subject = _required("PORTAL_IDENTITY_BOOTSTRAP_SUBJECT")
    display_name = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_DISPLAY_NAME", "Local Portal Owner")
    email = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_EMAIL") or None
    tenant_id = os.environ.get("PORTAL_IDENTITY_BOOTSTRAP_TENANT_ID", "tenant-local")
    now = datetime.now(UTC)
    with session_factory() as session:  # type: ignore[operator]
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


def build_local_test_app() -> FastAPI:
    if os.environ.get("PORTAL_ENVIRONMENT") != "test":
        raise RuntimeError("local-test identity runtime requires PORTAL_ENVIRONMENT=test")
    database_url = _required("PORTAL_DATABASE_URL")
    engine = build_engine(database_url)
    create_schema(engine)
    session_factory = build_session_factory(engine)
    config = IdentityRuntimeConfig.from_environment()
    if not config.allow_insecure_local_http:
        raise RuntimeError("local-test identity runtime requires local_http_test transport")
    _ensure_local_owner_membership(session_factory, config)
    identity_service = build_identity_service(session_factory, config)
    app = create_identity_enabled_app(session_factory, identity_service)

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
