from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.observability.runtime import (
    RuntimeLogQuery,
    RuntimeLogRecord,
    RuntimeObservabilityAvailability,
    RuntimeObservabilityService,
    RuntimeObservabilitySourceStatus,
    RuntimeObservabilityUnavailableError,
)


_NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


class OutageSource:
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
        del tenant_id, query
        raise RuntimeObservabilityUnavailableError("RUNTIME_LOG_SOURCE_TIMEOUT")


def test_runtime_service_represents_backend_outage_as_unavailable() -> None:
    context = RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-1",
        actor_type=ActorType.USER,
        permissions=(Permission.AUDIT_READ,),
        request_id=UUID("22222222-2222-4222-8222-222222222222"),
        correlation_id=UUID("11111111-1111-4111-8111-111111111111"),
    )
    query = RuntimeLogQuery(
        start_at=_NOW - timedelta(hours=1),
        end_at=_NOW,
        limit=10,
    )

    result = RuntimeObservabilityService(OutageSource()).search_logs(context, query)

    assert result.records == ()
    assert result.truncated is False
    assert result.source_status.availability is RuntimeObservabilityAvailability.UNAVAILABLE
    assert result.source_status.reason_code == "RUNTIME_LOG_SOURCE_TIMEOUT"
