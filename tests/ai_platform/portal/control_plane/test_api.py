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


def _spec(tenant_id: str, revision: int = 1) -> BotSpec:
    return BotSpec(
        tenant_id=tenant_id,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-connection-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        config_revision=revision,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
    )


def _create_payload(tenant_id: str) -> dict[str, object]:
    return {
        "bot_id": "bot-1",
        "name": "Portal bot",
        "spec": _spec(tenant_id).model_dump(mode="json"),
    }


def test_api_fails_closed_without_trusted_identity_provider(
    session_factory: SessionFactory,
) -> None:
    client = TestClient(create_app(session_factory))

    response = client.get(
        "/v1/bots",
        headers={
            "x-tenant-id": "tenant-a",
            "x-actor-id": "actor-a",
            "x-role": "admin",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "trusted application identity context is not configured"


def test_api_enforces_tenant_isolation_without_resource_disclosure(
    session_factory: SessionFactory,
) -> None:
    holder = {
        "context": _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_READ),
    }
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.post("/v1/bots", json=_create_payload("tenant-a")).status_code == 201

    holder["context"] = _context("tenant-b", Permission.BOT_READ)
    assert client.get("/v1/bots/bot-1").status_code == 404
    assert client.get("/v1/bots").json() == []
    assert client.get("/v1/orders").json() == []
    assert client.get("/v1/positions").json() == []
    assert client.get("/v1/trades").json() == []
    assert client.get("/v1/signals").json() == []
    assert client.get("/v1/grid-bots").json() == []


def test_api_enforces_server_side_permissions(session_factory: SessionFactory) -> None:
    context = _context("tenant-a", Permission.BOT_READ)
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.post("/v1/bots", json=_create_payload("tenant-a"))

    assert response.status_code == 403
    assert "permission denied" in response.json()["detail"]


def test_api_rejects_cross_tenant_bot_spec(session_factory: SessionFactory) -> None:
    context = _context("tenant-a", Permission.BOT_CREATE)
    client = TestClient(create_app(session_factory, lambda: context))

    response = client.post("/v1/bots", json=_create_payload("tenant-b"))

    assert response.status_code == 403
    assert response.json()["detail"] == "tenant scope mismatch"


def test_api_rejects_undeclared_raw_exchange_secret_fields(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_CREATE)
    client = TestClient(create_app(session_factory, lambda: context))
    spec = _spec("tenant-a").model_dump(mode="json")
    spec["api_key"] = "not-accepted"
    payload: dict[str, object] = {
        "bot_id": "bot-1",
        "name": "Portal bot",
        "spec": spec,
    }

    response = client.post("/v1/bots", json=payload)

    assert response.status_code == 422


def test_api_desired_state_changes_intent_without_claiming_observed_execution(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_CREATE)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    created = client.post("/v1/bots", json=_create_payload("tenant-a")).json()

    holder["context"] = _context("tenant-a", Permission.BOT_START)
    response = client.post(
        "/v1/bots/bot-1/desired-state",
        json={"desired_state": "RUNNING"},
    )

    assert response.status_code == 200
    assert response.json()["desired_state"] == "RUNNING"
    assert response.json()["observed_state"] == created["observed_state"] == "CREATED"


def test_read_only_portal_data_routes_fail_closed_through_trusted_context(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.MODEL_READ)
    client = TestClient(create_app(session_factory, lambda: context))

    assert client.get("/v1/models").json() == []
    assert client.get("/v1/trade-analysis").json() == []
    assert client.get("/v1/insights").json() == []
    assert client.get("/v1/learning/history").json() == []
    assert client.get("/v1/model-health").json() == []


def test_operational_routes_return_truthful_empty_state_and_protect_audit_reads(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_READ)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))

    for path in ("/v1/positions", "/v1/orders", "/v1/trades", "/v1/performance", "/v1/risk-events"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == []

    assert client.get("/v1/audit-events").status_code == 403
    assert client.get("/v1/execution-activity").status_code == 403
    assert client.get("/v1/runtime-log-availability").status_code == 403

    holder["context"] = _context("tenant-a", Permission.AUDIT_READ)
    assert client.get("/v1/audit-events").json() == []
    assert client.get("/v1/execution-activity").json() == []
    assert client.get("/v1/runtime-log-availability").json()["available"] is False


def test_audit_route_reads_only_current_tenant_with_explicit_permission(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_CREATE)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.post("/v1/bots", json=_create_payload("tenant-a")).status_code == 201

    holder["context"] = _context("tenant-a", Permission.AUDIT_READ)
    events = client.get("/v1/audit-events").json()
    assert len(events) == 1
    assert events[0]["tenant_id"] == "tenant-a"
    assert events[0]["action"] == "bot.created"

    holder["context"] = _context("tenant-b", Permission.AUDIT_READ)
    assert client.get("/v1/audit-events").json() == []


def test_openapi_surface_contains_only_control_plane_business_routes(
    session_factory: SessionFactory,
) -> None:
    client = TestClient(create_app(session_factory))

    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/v1/bots",
        "/v1/bots/{bot_id}",
        "/v1/bots/{bot_id}/revisions",
        "/v1/bots/{bot_id}/desired-state",
        "/v1/terminal/intents",
        "/v1/models",
        "/v1/trade-analysis",
        "/v1/insights",
        "/v1/learning/history",
        "/v1/positions",
        "/v1/orders",
        "/v1/trades",
        "/v1/runtime-evidence",
        "/v1/performance",
        "/v1/risk-events",
        "/v1/audit-events",
        "/v1/execution-activity",
        "/v1/signals",
        "/v1/strategies",
        "/v1/grid-bots",
        "/v1/notifications",
        "/v1/notifications/preferences",
        "/v1/profile",
        "/v1/admin/overview",
        "/v1/inference-telemetry/windows",
        "/v1/inference-telemetry/source-status",
        "/v1/model-health",
        "/v1/runtime-log-availability",
    }
    serialized = str(schema).lower()
    for forbidden in ("api_key", "api_secret", "passphrase", "websocket_token"):
        assert forbidden not in serialized


def test_api_bot_response_contains_only_opaque_exchange_reference(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_CREATE)
    client = TestClient(create_app(session_factory, lambda: context))

    payload = client.post("/v1/bots", json=_create_payload("tenant-a")).json()

    assert payload["spec"]["exchange_connection_ref"] == "exchange-connection-1"
    for forbidden in ("api_key", "api_secret", "passphrase", "secret_ref"):
        assert forbidden not in payload["spec"]
