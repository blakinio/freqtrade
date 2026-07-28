from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)


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


def _create_payload(tenant_id: str) -> dict[str, object]:
    return {
        "bot_id": "bot-1",
        "name": "Dashboard bot",
        "spec": BotSpec(
            tenant_id=tenant_id,
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation="1000",
            capital_currency="USDT",
            runtime_version="freqtrade-2026.7",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ).model_dump(mode="json"),
    }


def _search_payload() -> dict[str, object]:
    return {
        "filters": {
            "bot_ids": [],
            "environments": ["test"],
            "states": [],
            "occurred_from": None,
            "occurred_to": None,
        },
        "page": {
            "page_size": 50,
            "cursor": None,
            "sort_field": "bot_id",
            "sort_direction": "asc",
        },
    }


def test_dashboard_route_is_tenant_scoped_and_fail_closed(
    session_factory: SessionFactory,
) -> None:
    holder = {
        "context": _context(
            "tenant-a",
            Permission.BOT_CREATE,
            Permission.BOT_READ,
            Permission.MODEL_READ,
        )
    }
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.post("/v1/bots", json=_create_payload("tenant-a")).status_code == 201

    response = client.post("/v1/bot-management/dashboard/search", json=_search_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["totals"]["matching_bot_count"] == 1
    assert payload["items"][0]["bot_id"] == "bot-1"
    assert payload["items"][0]["evidence"]["runtime"]["state"] == "UNAVAILABLE"
    assert payload["items"][0]["evidence"]["model"]["state"] == "UNAVAILABLE"
    serialized = response.text.lower()
    for forbidden in ("api_key", "api_secret", "passphrase", "private_endpoint"):
        assert forbidden not in serialized

    holder["context"] = _context("tenant-b", Permission.BOT_READ, Permission.MODEL_READ)
    isolated = client.post("/v1/bot-management/dashboard/search", json=_search_payload())
    assert isolated.status_code == 200
    assert isolated.json()["items"] == []


def test_dashboard_route_requires_bot_read_permission(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.MODEL_READ)
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.post("/v1/bot-management/dashboard/search", json=_search_payload())

    assert response.status_code == 403
    assert "permission denied" in response.json()["detail"]
