from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.observability.runtime import (
    RuntimeLogQuery,
    RuntimeLogRecord,
    RuntimeObservabilityAvailability,
    RuntimeObservabilityService,
    RuntimeObservabilitySourceStatus,
)


_NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
_CORRELATION_ID = UUID("11111111-1111-4111-8111-111111111111")


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
        correlation_id=_CORRELATION_ID,
    )


class FakeRuntimeObservabilitySource:
    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus:
        return RuntimeObservabilitySourceStatus(
            source_id=f"loki-{tenant_id}",
            availability=RuntimeObservabilityAvailability.AVAILABLE,
            checked_at=_NOW,
            reason_code="SOURCE_READY",
            log_retention_days=14,
            trace_retention_days=7,
            metric_retention_days=30,
            trace_source="tempo-private",
            metric_source="prometheus-private",
            runbook_path="/docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md",
        )

    def search_logs(
        self,
        tenant_id: str,
        query: RuntimeLogQuery,
    ) -> tuple[RuntimeLogRecord, ...]:
        return (
            RuntimeLogRecord(
                record_id=f"record-{tenant_id}",
                tenant_id=tenant_id,
                timestamp=query.end_at - timedelta(minutes=1),
                service="freqtrade-runtime",
                component="exchange-loop",
                environment=Environment.TEST,
                runtime_id="runtime-1",
                bot_id="bot-1",
                correlation_id=query.correlation_id or _CORRELATION_ID,
                trace_id="trace-1",
                span_id="span-1",
                level="ERROR",
                message="runtime request failed",
                fields={"authorization": "secret", "safe": "value"},
                source_id=f"loki-{tenant_id}",
                retention_expires_at=_NOW + timedelta(days=14),
            ),
        )


def _query_payload() -> dict[str, object]:
    return {
        "start_at": (_NOW - timedelta(hours=1)).isoformat(),
        "end_at": _NOW.isoformat(),
        "correlation_id": str(_CORRELATION_ID),
        "limit": 10,
    }


def test_runtime_observability_api_returns_tenant_scoped_redacted_logs(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.AUDIT_READ)
    service = RuntimeObservabilityService(FakeRuntimeObservabilitySource())
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            runtime_observability_service=service,
        )
    )

    availability = client.get("/v1/runtime-observability/availability")
    search = client.post("/v1/runtime-observability/logs/search", json=_query_payload())

    assert availability.status_code == 200
    assert availability.json()["source_id"] == "loki-tenant-a"
    assert "endpoint" not in availability.json()
    assert search.status_code == 200
    assert search.json()["records"][0]["tenant_id"] == "tenant-a"
    assert search.json()["records"][0]["fields"] == {
        "authorization": "[REDACTED]",
        "safe": "value",
    }
    assert search.json()["records"][0]["audit_evidence"] is False


def test_runtime_observability_api_requires_audit_read(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_READ)
    service = RuntimeObservabilityService(FakeRuntimeObservabilitySource())
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            runtime_observability_service=service,
        )
    )

    assert client.get("/v1/runtime-observability/availability").status_code == 403
    assert (
        client.post(
            "/v1/runtime-observability/logs/search",
            json=_query_payload(),
        ).status_code
        == 403
    )


def test_runtime_observability_api_rejects_unbounded_query(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.AUDIT_READ)
    service = RuntimeObservabilityService(FakeRuntimeObservabilitySource())
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            runtime_observability_service=service,
        )
    )
    payload = _query_payload()
    payload["start_at"] = (_NOW - timedelta(hours=25)).isoformat()

    response = client.post("/v1/runtime-observability/logs/search", json=payload)

    assert response.status_code == 422
    assert "24 hours" in response.text
