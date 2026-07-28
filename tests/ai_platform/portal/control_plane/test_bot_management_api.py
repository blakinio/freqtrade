from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.signals import (
    SignalAuthenticationMode,
    SignalAuthenticationReference,
)
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.bot_management import (
    UnavailableSignatureVerificationProvider,
    capabilities_from_request,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.signal_control.schema import SignatureVerificationStatus


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str, *permissions: Permission) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def test_capability_bridge_is_deterministic_and_admin_receives_frozen_vocabulary() -> None:
    admin = capabilities_from_request(_context("tenant-a", Permission.ADMIN_MANAGE))
    values = [item.value for item in admin]

    assert admin == tuple(sorted(BotManagementCapability, key=lambda item: item.value))
    assert values == sorted(values)
    assert len(values) == len(set(values))


def test_coarse_permissions_do_not_grant_exchange_or_execution_capabilities() -> None:
    capabilities = capabilities_from_request(
        _context("tenant-a", Permission.BOT_READ, Permission.BOT_CREATE)
    )

    assert BotManagementCapability.CATALOG_READ in capabilities
    assert BotManagementCapability.BOT_CREATE in capabilities
    assert BotManagementCapability.EXCHANGE_CONNECTION_CREATE not in capabilities
    assert BotManagementCapability.POSITION_CLOSE not in capabilities


def test_default_signature_provider_fails_closed_without_resolving_a_secret() -> None:
    provider = UnavailableSignatureVerificationProvider()

    decision = provider.verify(
        authentication_ref=SignalAuthenticationReference(
            reference_id="sigref_12345678",
            version=1,
        ),
        authentication_mode=SignalAuthenticationMode.HMAC_SHA256,
        canonical_payload=b"{}",
        signature=b"signature",
    )

    assert decision.status == SignatureVerificationStatus.UNAVAILABLE
    assert decision.evidence_ref is None


def test_bot_management_routes_fail_closed_without_identity(
    session_factory: SessionFactory,
) -> None:
    client = TestClient(create_app(session_factory))

    response = client.get("/v1/bot-management/exchanges")

    assert response.status_code == 401


def test_exchange_metadata_list_is_tenant_scoped_and_permission_gated(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_READ)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))

    denied = client.get("/v1/bot-management/exchanges")
    assert denied.status_code == 403

    holder["context"] = _context("tenant-a", Permission.ADMIN_MANAGE)
    allowed = client.get("/v1/bot-management/exchanges")
    assert allowed.status_code == 200
    assert allowed.json() == []


def test_missing_server_catalog_is_explicit_not_empty_success(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_READ)
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.get("/v1/bot-management/catalog/approved/latest")

    assert response.status_code == 404
    assert response.json()["reason_codes"] == ["CATALOG_NOT_FOUND"]


def test_create_schema_registers_durable_bot_command_tables() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)

    tables = set(inspect(engine).get_table_names())
    assert {
        "portal_bot_commands",
        "portal_bot_command_history",
        "portal_bot_command_idempotency_conflicts",
    }.issubset(tables)
