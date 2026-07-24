from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request
from uuid import UUID

import pytest

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.observability.redaction import REDACTED
from ai_platform.portal.observability.runtime import (
    HttpLokiQueryTransport,
    LokiRuntimeObservabilitySource,
    RuntimeLogQuery,
    RuntimeLogRecord,
    RuntimeObservabilityAvailability,
    RuntimeObservabilityProtocolError,
    RuntimeObservabilityService,
    RuntimeObservabilitySourceStatus,
    RuntimeObservabilityUnavailableError,
    UnavailableRuntimeObservabilitySource,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


_NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
_CORRELATION_ID = UUID("11111111-1111-4111-8111-111111111111")


def _context(*permissions: Permission, tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id="actor-1",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=UUID("22222222-2222-4222-8222-222222222222"),
        correlation_id=_CORRELATION_ID,
    )


def _query(**overrides: Any) -> RuntimeLogQuery:
    values: dict[str, Any] = {
        "start_at": _NOW - timedelta(hours=1),
        "end_at": _NOW,
        "correlation_id": _CORRELATION_ID,
        "runtime_id": "runtime-1",
        "limit": 10,
    }
    values.update(overrides)
    return RuntimeLogQuery(**values)


def _status(
    availability: RuntimeObservabilityAvailability = RuntimeObservabilityAvailability.AVAILABLE,
) -> RuntimeObservabilitySourceStatus:
    return RuntimeObservabilitySourceStatus(
        source_id="loki-private",
        availability=availability,
        checked_at=_NOW,
        reason_code=(
            "SOURCE_READY" if availability is RuntimeObservabilityAvailability.AVAILABLE else "DOWN"
        ),
        log_retention_days=14,
        trace_retention_days=7,
        metric_retention_days=30,
        trace_source="tempo-private",
        metric_source="prometheus-private",
        runbook_path="/docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md",
    )


def _record_payload(
    *,
    tenant_id: str = "tenant-a",
    sensitive_value: str = "top-secret",
) -> dict[str, Any]:
    return {
        "record_id": "record-1",
        "tenant_id": tenant_id,
        "timestamp": _NOW.isoformat(),
        "service": "freqtrade-runtime",
        "component": "exchange-loop",
        "environment": Environment.STAGING.value,
        "runtime_id": "runtime-1",
        "bot_id": "bot-1",
        "correlation_id": str(_CORRELATION_ID),
        "trace_id": "trace-1",
        "span_id": "span-1",
        "level": "ERROR",
        "message": "exchange request failed",
        "fields": {
            "api_key": sensitive_value,
            "nested": {"authorization": sensitive_value, "safe": "ok"},
        },
        "source_id": "loki-private",
        "retention_expires_at": (_NOW + timedelta(days=14)).isoformat(),
        "audit_evidence": False,
    }


class FakeLokiTransport:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.last_query: str | None = None
        self.last_tenant_id: str | None = None

    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus:
        self.last_tenant_id = tenant_id
        return _status()

    def query_range(
        self,
        *,
        tenant_id: str,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
    ) -> dict[str, Any]:
        assert start_ns < end_ns
        assert limit == 10
        self.last_tenant_id = tenant_id
        self.last_query = query
        return {
            "status": "success",
            "data": {
                "result": [
                    {
                        "stream": {"tenant_id": tenant_id},
                        "values": [[str(start_ns), json.dumps(self.payload)]],
                    }
                ]
            },
        }


class FakeHttpResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self, amount: int = -1) -> bytes:
        return self._body if amount < 0 else self._body[:amount]


class CapturingOpener:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self.request: Request | None = None
        self.timeout: int | None = None

    def __call__(self, request: Request, *, timeout: int) -> FakeHttpResponse:
        self.request = request
        self.timeout = timeout
        return FakeHttpResponse(self._body)


class TimeoutOpener:
    def __call__(self, request: Request, *, timeout: int) -> FakeHttpResponse:
        del request, timeout
        raise TimeoutError


def _http_transport(
    opener: CapturingOpener | TimeoutOpener,
    *,
    endpoint: str = "https://loki.internal/loki/api/v1/query_range",
    max_body_bytes: int = 1_048_576,
) -> HttpLokiQueryTransport:
    return HttpLokiQueryTransport(
        lambda tenant_id: endpoint,
        lambda tenant_id: {"Authorization": f"Bearer private-{tenant_id}"},
        lambda tenant_id: _status(),
        opener=opener,
        timeout_seconds=3,
        max_body_bytes=max_body_bytes,
    )


def test_loki_source_enforces_tenant_selector_and_redacts_nested_secrets() -> None:
    transport = FakeLokiTransport(_record_payload())
    source = LokiRuntimeObservabilitySource(transport)
    service = RuntimeObservabilityService(source)

    result = service.search_logs(_context(Permission.AUDIT_READ), _query())

    assert transport.last_tenant_id == "tenant-a"
    assert transport.last_query is not None
    assert 'tenant_id="tenant-a"' in transport.last_query
    assert 'runtime_id="runtime-1"' in transport.last_query
    assert str(_CORRELATION_ID) in transport.last_query
    assert result.source_status.availability is RuntimeObservabilityAvailability.AVAILABLE
    assert len(result.records) == 1
    assert result.records[0].fields == {
        "api_key": REDACTED,
        "nested": {"authorization": REDACTED, "safe": "ok"},
    }
    assert result.records[0].audit_evidence is False


def test_http_loki_transport_builds_bounded_server_side_query() -> None:
    opener = CapturingOpener(b'{"status":"success","data":{"result":[]}}')
    transport = _http_transport(opener)

    response = transport.query_range(
        tenant_id="tenant-a",
        query='{tenant_id="tenant-a"}',
        start_ns=100,
        end_ns=200,
        limit=10,
    )

    assert response["status"] == "success"
    assert opener.timeout == 3
    assert opener.request is not None
    assert opener.request.get_header("Authorization") == "Bearer private-tenant-a"
    parsed = urlsplit(opener.request.full_url)
    assert parsed.scheme == "https"
    assert parsed.hostname == "loki.internal"
    assert parse_qs(parsed.query) == {
        "query": ['{tenant_id="tenant-a"}'],
        "start": ["100"],
        "end": ["200"],
        "limit": ["10"],
        "direction": ["backward"],
    }


def test_http_loki_transport_rejects_oversized_or_credentialed_source() -> None:
    with pytest.raises(RuntimeObservabilityProtocolError, match="RESPONSE_TOO_LARGE"):
        _http_transport(CapturingOpener(b"123456"), max_body_bytes=5).query_range(
            tenant_id="tenant-a",
            query='{tenant_id="tenant-a"}',
            start_ns=100,
            end_ns=200,
            limit=10,
        )

    with pytest.raises(RuntimeObservabilityProtocolError, match="EMBEDS_CREDENTIALS"):
        _http_transport(
            CapturingOpener(b"{}"),
            endpoint="https://user:password@loki.internal/loki/api/v1/query_range",
        ).query_range(
            tenant_id="tenant-a",
            query='{tenant_id="tenant-a"}',
            start_ns=100,
            end_ns=200,
            limit=10,
        )


def test_http_loki_transport_exposes_timeout_as_source_unavailable() -> None:
    with pytest.raises(RuntimeObservabilityUnavailableError, match="TIMEOUT"):
        _http_transport(TimeoutOpener()).query_range(
            tenant_id="tenant-a",
            query='{tenant_id="tenant-a"}',
            start_ns=100,
            end_ns=200,
            limit=10,
        )


def test_unavailable_source_is_explicit_and_returns_no_raw_logs() -> None:
    source = UnavailableRuntimeObservabilitySource(checked_at=_NOW)
    service = RuntimeObservabilityService(source)

    result = service.search_logs(_context(Permission.AUDIT_READ), _query())

    assert result.records == ()
    assert result.truncated is False
    assert result.source_status.availability is RuntimeObservabilityAvailability.UNAVAILABLE
    assert result.source_status.reason_code == (
        "CENTRALIZED_RUNTIME_OBSERVABILITY_SOURCE_NOT_CONFIGURED"
    )


def test_runtime_log_reads_require_audit_permission() -> None:
    service = RuntimeObservabilityService(UnavailableRuntimeObservabilitySource(checked_at=_NOW))

    with pytest.raises(PermissionDeniedError):
        service.availability(_context(Permission.BOT_READ))

    with pytest.raises(PermissionDeniedError):
        service.search_logs(_context(Permission.BOT_READ), _query())


def test_loki_source_rejects_cross_tenant_record() -> None:
    source = LokiRuntimeObservabilitySource(
        FakeLokiTransport(_record_payload(tenant_id="tenant-b"))
    )
    service = RuntimeObservabilityService(source)

    with pytest.raises(RuntimeObservabilityProtocolError, match="TENANT_MISMATCH"):
        service.search_logs(_context(Permission.AUDIT_READ), _query())


def test_query_range_and_limit_are_bounded() -> None:
    with pytest.raises(ValueError, match="24 hours"):
        _query(start_at=_NOW - timedelta(hours=25))

    with pytest.raises(ValueError):
        _query(limit=201)


def test_runtime_log_record_cannot_claim_audit_evidence() -> None:
    payload = _record_payload()
    payload["audit_evidence"] = True

    with pytest.raises(ValueError, match="audit evidence"):
        RuntimeLogRecord.model_validate(payload)
