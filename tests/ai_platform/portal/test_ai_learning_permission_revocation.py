from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api_core import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)


def _context(*permissions: Permission) -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="user-a",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def test_ai_read_permission_revocation_applies_on_next_request() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    holder = {"context": _context(Permission.MODEL_READ)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))

    assert client.get("/v1/trade-analysis").status_code == 200
    assert client.get("/v1/insights").status_code == 200
    assert client.get("/v1/learning/history").status_code == 200

    holder["context"] = _context(Permission.BOT_READ)

    for path in ("/v1/trade-analysis", "/v1/insights", "/v1/learning/history"):
        response = client.get(path)
        assert response.status_code == 403
        assert response.json() == {"detail": "permission denied: model.read"}
