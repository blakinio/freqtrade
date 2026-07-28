from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.bot_management.pagination import (
    BotManagementListFilters,
    BotManagementSortField,
    BoundedPagination,
)
from ai_platform.portal.contracts.bots import BotInstance, BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.dashboard.schema import DashboardEvidenceState
from ai_platform.portal.dashboard.service import DashboardReadError, DashboardReadService
from ai_platform.portal.execution.private_read import RuntimeReadFreshness, RuntimeReadKind
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.schema import OperationalSourceStatus, RuntimeEvidenceSnapshot
from ai_platform.portal.telemetry.schema import (
    DriftHealthStatus,
    ModelHealthRecord,
    TelemetrySourceAvailability,
)


NOW = datetime(2026, 7, 28, 18, 0, tzinfo=UTC)


def _context(tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_READ, Permission.MODEL_READ),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _bot(bot_id: str, *, environment: Environment = Environment.TEST) -> BotInstance:
    return BotInstance(
        bot_id=bot_id,
        tenant_id="tenant-a",
        name=f"Bot {bot_id}",
        spec=BotSpec(
            tenant_id="tenant-a",
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
            environment=environment,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
        desired_state="RUNNING",
        observed_state="RUNNING",
    )


class _Bots:
    def __init__(self, *bots: BotInstance) -> None:
        self._bots = bots

    def list_bots(self, _context: RequestContext) -> tuple[BotInstance, ...]:
        return self._bots


class _Operations:
    def __init__(self, runtime: RuntimeEvidenceSnapshot | None = None) -> None:
        self._runtime = runtime or RuntimeEvidenceSnapshot(
            positions=(),
            orders=(),
            trades=(),
            source_statuses=(),
        )

    def runtime_evidence(self, _context: RequestContext) -> RuntimeEvidenceSnapshot:
        return self._runtime

    def list_performance(self, _context: RequestContext) -> tuple[object, ...]:
        return ()

    def list_risk_events(self, _context: RequestContext) -> tuple[object, ...]:
        return ()


class _Valuations:
    def list_valuations(self, _context: RequestContext) -> tuple[object, ...]:
        return ()


class _Models:
    def __init__(self, *records: ModelHealthRecord) -> None:
        self._records = records

    def model_health(self, _context: RequestContext) -> tuple[ModelHealthRecord, ...]:
        return self._records


def _page(page_size: int = 50, cursor: str | None = None) -> BoundedPagination:
    return BoundedPagination(
        page_size=page_size,
        cursor=cursor,
        sort_field=BotManagementSortField.BOT_ID,
    )


def _service(
    bots: _Bots,
    operations: _Operations | None = None,
    models: _Models | None = None,
) -> DashboardReadService:
    return DashboardReadService(
        bots,
        operations or _Operations(),
        _Valuations(),
        models or _Models(),
        clock=lambda: NOW,
    )


def test_empty_dashboard_is_truthful_and_bounded() -> None:
    result = _service(_Bots()).search(_context(), BotManagementListFilters(), _page())

    assert result.items == ()
    assert result.totals.matching_bot_count == 0
    assert result.page_info.result_count == 0
    statuses = {status.source.value: status.state for status in result.source_statuses}
    assert statuses["CONTROL_PLANE"] is DashboardEvidenceState.CURRENT
    assert statuses["RUNTIME"] is DashboardEvidenceState.UNAVAILABLE
    assert statuses["MODEL"] is DashboardEvidenceState.UNAVAILABLE
    assert statuses["RISK"] is DashboardEvidenceState.UNAVAILABLE


def test_missing_authoritative_sources_are_not_inferred_as_healthy() -> None:
    result = _service(_Bots(_bot("bot-1"))).search(
        _context(),
        BotManagementListFilters(),
        _page(),
    )

    item = result.items[0]
    assert item.evidence.runtime.state is DashboardEvidenceState.UNAVAILABLE
    assert item.evidence.model.state is DashboardEvidenceState.UNAVAILABLE
    assert item.evidence.valuation.state is DashboardEvidenceState.NOT_APPLICABLE
    assert item.requires_attention is True
    serialized = result.model_dump_json().lower()
    for forbidden in ("api_key", "api_secret", "passphrase", "private_endpoint"):
        assert forbidden not in serialized


def test_current_runtime_and_model_evidence_clear_bot_attention() -> None:
    runtime = RuntimeEvidenceSnapshot(
        positions=(),
        orders=(),
        trades=(),
        source_statuses=tuple(
            OperationalSourceStatus(
                tenant_id="tenant-a",
                bot_id="bot-1",
                source_runtime_id="runtime-1",
                kind=kind,
                source_observed_at=NOW,
                observed_at=NOW,
                last_reconciled_at=NOW,
                freshness=RuntimeReadFreshness.CURRENT,
                reconciliation_status=ReconciliationStatus.SYNCED,
                complete=True,
                record_count=0,
            )
            for kind in RuntimeReadKind
        ),
    )
    model = ModelHealthRecord(
        health_record_id="model-v1:bot-1:runtime-1",
        model_version_id="model-v1",
        tenant_id="tenant-a",
        model_family_id="family-1",
        lifecycle_state="DRY_RUN",
        created_at=NOW,
        training_window_end=NOW,
        metadata_age_days=0,
        drift_status=DriftHealthStatus.HEALTHY,
        drift_reason="DRIFT_WITHIN_POLICY",
        bot_id="bot-1",
        source_availability=TelemetrySourceAvailability.AVAILABLE,
        source_checked_at=NOW,
    )

    result = _service(_Bots(_bot("bot-1")), _Operations(runtime), _Models(model)).search(
        _context(),
        BotManagementListFilters(),
        _page(),
    )

    item = result.items[0]
    assert item.evidence.runtime.state is DashboardEvidenceState.CURRENT
    assert item.evidence.model.state is DashboardEvidenceState.CURRENT
    assert item.requires_attention is False


def test_filters_and_cursor_are_deterministic() -> None:
    service = _service(
        _Bots(
            _bot("bot-b", environment=Environment.STAGING),
            _bot("bot-a", environment=Environment.TEST),
        )
    )
    filters = BotManagementListFilters(environments=(Environment.TEST,))

    first = service.search(_context(), filters, _page(page_size=1))
    assert [item.bot_id for item in first.items] == ["bot-a"]
    assert first.page_info.has_more is False

    all_filters = BotManagementListFilters()
    paged = service.search(_context(), all_filters, _page(page_size=1))
    assert [item.bot_id for item in paged.items] == ["bot-a"]
    assert paged.page_info.next_cursor is not None
    second = service.search(
        _context(),
        all_filters,
        _page(page_size=1, cursor=paged.page_info.next_cursor),
    )
    assert [item.bot_id for item in second.items] == ["bot-b"]

    with pytest.raises(DashboardReadError, match="does not match"):
        service.search(
            _context(),
            BotManagementListFilters(states=("RUNNING",)),
            _page(page_size=1, cursor=paged.page_info.next_cursor),
        )
