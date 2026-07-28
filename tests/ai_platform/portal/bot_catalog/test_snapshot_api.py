from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.bot_catalog.default_catalog import approved_dry_run_catalog
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    CatalogAccessContext,
    CatalogAccessReasonCode,
)
from ai_platform.portal.bot_catalog.service import BotCatalogService, BotCatalogServiceError
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)


def test_snapshot_service_requires_catalog_read_capability() -> None:
    snapshot = approved_dry_run_catalog()
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))
    access = CatalogAccessContext(tenant_id="tenant-a", capabilities=())

    with pytest.raises(BotCatalogServiceError) as raised:
        service.get_snapshot(access, snapshot.catalog_ref)

    assert raised.value.reason_code == CatalogAccessReasonCode.CAPABILITY_MISSING


def test_snapshot_service_returns_exact_immutable_revision() -> None:
    snapshot = approved_dry_run_catalog()
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))
    access = CatalogAccessContext(
        tenant_id="tenant-a",
        capabilities=(BotManagementCapability.CATALOG_READ,),
    )

    assert service.get_snapshot(access, snapshot.catalog_ref) == snapshot


def test_snapshot_api_is_session_scoped_and_secret_free() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    context = RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_READ,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.get(
        "/v1/bot-management/catalog/portal-approved-dry-run/1"
    )

    assert response.status_code == 200
    payload = response.text.lower()
    assert '"catalog_id":"portal-approved-dry-run"' in payload
    assert "credential" not in payload
    assert "api_key" not in payload
    assert "secret" not in payload
