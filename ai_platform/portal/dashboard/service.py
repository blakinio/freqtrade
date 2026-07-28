from __future__ import annotations

import base64
import binascii
import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Protocol

from ai_platform.portal.contracts.bot_management.pagination import (
    BotManagementListFilters,
    BotManagementSortField,
    BoundedPagination,
    PageInfo,
    SortDirection,
)
from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.execution import OrderState
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import RiskDecision, RiskDecisionOutcome
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.execution.private_read import RuntimeReadFreshness, RuntimeReadKind
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.schema import (
    OperationalOrder,
    OperationalPosition,
    OperationalSourceStatus,
    OperationalTrade,
    PerformanceSummary,
    RuntimeEvidenceSnapshot,
)
from ai_platform.portal.telemetry.schema import DriftHealthStatus, ModelHealthRecord
from ai_platform.portal.valuation.runtime import ValuationSnapshot, ValuationState

from .schema import (
    BotDashboardEvidence,
    BotDashboardItem,
    BotDashboardPage,
    DashboardEvidenceSource,
    DashboardEvidenceState,
    DashboardEvidenceStatus,
    DashboardTotals,
)


class DashboardReadError(ValueError):
    pass


class BotReader(Protocol):
    def list_bots(self, context: RequestContext) -> tuple[BotInstance, ...]: ...


class OperationalReader(Protocol):
    def runtime_evidence(self, context: RequestContext) -> RuntimeEvidenceSnapshot: ...

    def list_performance(self, context: RequestContext) -> tuple[PerformanceSummary, ...]: ...

    def list_risk_events(self, context: RequestContext) -> tuple[RiskDecision, ...]: ...


class ValuationReader(Protocol):
    def list_valuations(self, context: RequestContext) -> tuple[ValuationSnapshot, ...]: ...


class ModelHealthReader(Protocol):
    def model_health(self, context: RequestContext) -> tuple[ModelHealthRecord, ...]: ...


Clock = Callable[[], datetime]

_OPEN_ORDER_STATES = {
    OrderState.SUBMITTED,
    OrderState.OPEN,
    OrderState.PARTIALLY_FILLED,
}
_EXPECTED_RUNTIME_KINDS = set(RuntimeReadKind)
_ATTENTION_STATES = {
    DashboardEvidenceState.ATTENTION,
    DashboardEvidenceState.DEGRADED,
    DashboardEvidenceState.STALE,
    DashboardEvidenceState.PARTIAL,
    DashboardEvidenceState.UNAVAILABLE,
}
_STATE_RANK = {
    DashboardEvidenceState.NOT_APPLICABLE: -1,
    DashboardEvidenceState.CURRENT: 0,
    DashboardEvidenceState.PARTIAL: 1,
    DashboardEvidenceState.ATTENTION: 2,
    DashboardEvidenceState.STALE: 3,
    DashboardEvidenceState.DEGRADED: 4,
    DashboardEvidenceState.UNAVAILABLE: 5,
}


@dataclass(frozen=True)
class _EvidenceIndex:
    positions: dict[str, list[OperationalPosition]]
    orders: dict[str, list[OperationalOrder]]
    trades: dict[str, list[OperationalTrade]]
    runtime_statuses: dict[str, list[OperationalSourceStatus]]
    performance: dict[str, PerformanceSummary]
    valuations: dict[str, list[ValuationSnapshot]]
    model_by_bot: dict[str, list[ModelHealthRecord]]
    model_records: tuple[ModelHealthRecord, ...]


class DashboardReadService:
    def __init__(
        self,
        bots: BotReader,
        operations: OperationalReader,
        valuations: ValuationReader,
        model_health: ModelHealthReader,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._bots = bots
        self._operations = operations
        self._valuations = valuations
        self._model_health = model_health
        self._clock = clock or (lambda: datetime.now(UTC))

    def search(
        self,
        context: RequestContext,
        filters: BotManagementListFilters,
        page: BoundedPagination,
    ) -> BotDashboardPage:
        self._validate_request(filters, page)
        generated_at = self._clock()
        bots = self._bots.list_bots(context)
        runtime = self._operations.runtime_evidence(context)
        performance = self._operations.list_performance(context)
        risk_decisions = self._operations.list_risk_events(context)
        valuations = self._valuations.list_valuations(context)
        model_permission = Permission.MODEL_READ in context.permissions
        model_records = self._model_health.model_health(context) if model_permission else ()

        matching = tuple(bot for bot in bots if self._matches(bot, filters))
        ordered = tuple(
            sorted(
                matching,
                key=lambda bot: bot.bot_id,
                reverse=page.sort_direction is SortDirection.DESC,
            )
        )
        indexed = self._index_evidence(runtime, performance, valuations, model_records)
        all_items = tuple(
            self._item(bot, indexed, model_permission=model_permission) for bot in ordered
        )
        start = self._cursor_start(context.tenant_id, filters, page, len(all_items))
        stop = min(start + page.page_size, len(all_items))
        items = all_items[start:stop]
        next_cursor = (
            self._encode_cursor(context.tenant_id, filters, page, stop)
            if stop < len(all_items)
            else None
        )
        source_statuses = self._source_statuses(
            generated_at,
            all_items,
            self._risk_status(risk_decisions),
        )
        return BotDashboardPage(
            generated_at=generated_at,
            filters=filters,
            items=items,
            page_info=PageInfo(
                requested_page_size=page.page_size,
                result_count=len(items),
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            ),
            totals=self._totals(all_items, len(risk_decisions)),
            source_statuses=source_statuses,
        )

    @staticmethod
    def _validate_request(
        filters: BotManagementListFilters,
        page: BoundedPagination,
    ) -> None:
        if page.sort_field is not BotManagementSortField.BOT_ID:
            raise DashboardReadError("dashboard supports deterministic bot_id sorting only")
        if filters.occurred_from is not None or filters.occurred_to is not None:
            raise DashboardReadError(
                "dashboard bot records do not expose an authoritative occurrence timestamp"
            )

    @staticmethod
    def _matches(bot: BotInstance, filters: BotManagementListFilters) -> bool:
        if filters.bot_ids and bot.bot_id not in filters.bot_ids:
            return False
        if filters.environments and bot.spec.environment not in filters.environments:
            return False
        if filters.states:
            states = {bot.desired_state.value, bot.observed_state.value}
            if not states.intersection(filters.states):
                return False
        return True

    @staticmethod
    def _index_evidence(
        runtime: RuntimeEvidenceSnapshot,
        performance: tuple[PerformanceSummary, ...],
        valuations: tuple[ValuationSnapshot, ...],
        model_records: tuple[ModelHealthRecord, ...],
    ) -> _EvidenceIndex:
        positions: dict[str, list[OperationalPosition]] = defaultdict(list)
        orders: dict[str, list[OperationalOrder]] = defaultdict(list)
        trades: dict[str, list[OperationalTrade]] = defaultdict(list)
        runtime_statuses: dict[str, list[OperationalSourceStatus]] = defaultdict(list)
        valuation_records: dict[str, list[ValuationSnapshot]] = defaultdict(list)
        model_by_bot: dict[str, list[ModelHealthRecord]] = defaultdict(list)
        for position in runtime.positions:
            positions[position.bot_id].append(position)
        for order in runtime.orders:
            orders[order.bot_id].append(order)
        for trade in runtime.trades:
            trades[trade.bot_id].append(trade)
        for status in runtime.source_statuses:
            runtime_statuses[status.bot_id].append(status)
        for valuation in valuations:
            valuation_records[valuation.bot_id].append(valuation)
        for record in model_records:
            if record.bot_id is not None:
                model_by_bot[record.bot_id].append(record)
        return _EvidenceIndex(
            positions=positions,
            orders=orders,
            trades=trades,
            runtime_statuses=runtime_statuses,
            performance={item.bot_id: item for item in performance},
            valuations=valuation_records,
            model_by_bot=model_by_bot,
            model_records=model_records,
        )

    def _item(
        self,
        bot: BotInstance,
        indexed: _EvidenceIndex,
        *,
        model_permission: bool,
    ) -> BotDashboardItem:
        positions = indexed.positions[bot.bot_id]
        orders = indexed.orders[bot.bot_id]
        trades = indexed.trades[bot.bot_id]
        valuations = indexed.valuations[bot.bot_id]
        model_records = list(indexed.model_by_bot[bot.bot_id])
        if not model_records:
            model_records = [
                record
                for record in indexed.model_records
                if record.model_version_id == bot.spec.model_version and record.bot_id is None
            ]
        evidence = BotDashboardEvidence(
            runtime=self._runtime_status(indexed.runtime_statuses[bot.bot_id]),
            valuation=self._valuation_status(len(positions), valuations),
            model=self._model_status(model_records, model_permission=model_permission),
        )
        attention_reasons = self._attention_reasons(bot, evidence)
        performance = indexed.performance.get(bot.bot_id)
        unrealized = [
            valuation.unrealized_pnl
            for valuation in valuations
            if valuation.unrealized_pnl is not None
        ]
        return BotDashboardItem(
            bot_id=bot.bot_id,
            name=bot.name,
            environment=bot.spec.environment,
            execution_mode=bot.spec.execution_mode,
            desired_state=bot.desired_state,
            observed_state=bot.observed_state,
            config_revision=bot.spec.config_revision,
            strategy_version=bot.spec.strategy_version,
            model_version=bot.spec.model_version,
            risk_policy_version=bot.spec.risk_policy_version,
            open_position_count=len(positions),
            open_order_count=sum(1 for order in orders if order.state in _OPEN_ORDER_STATES),
            runtime_trade_count=len(trades),
            realized_net_pnl=performance.net_pnl if performance is not None else None,
            unrealized_pnl=sum(unrealized, Decimal("0")) if unrealized else None,
            evidence=evidence,
            requires_attention=bool(attention_reasons),
            attention_reasons=attention_reasons,
        )

    @staticmethod
    def _runtime_status(
        statuses: list[OperationalSourceStatus],
    ) -> DashboardEvidenceStatus:
        if not statuses:
            return DashboardReadService._status(
                DashboardEvidenceSource.RUNTIME,
                DashboardEvidenceState.UNAVAILABLE,
                "RUNTIME_EVIDENCE_NOT_RECORDED",
            )
        reasons = {status.reason_code for status in statuses if status.reason_code is not None}
        kinds = {status.kind for status in statuses}
        if any(status.freshness is RuntimeReadFreshness.SOURCE_UNAVAILABLE for status in statuses):
            state = DashboardEvidenceState.UNAVAILABLE
        elif any(
            status.reconciliation_status is ReconciliationStatus.MISMATCH for status in statuses
        ):
            state = DashboardEvidenceState.DEGRADED
        elif any(status.freshness is RuntimeReadFreshness.STALE for status in statuses):
            state = DashboardEvidenceState.STALE
        elif (
            kinds != _EXPECTED_RUNTIME_KINDS
            or any(status.freshness is RuntimeReadFreshness.PARTIAL for status in statuses)
            or any(
                status.reconciliation_status is ReconciliationStatus.PENDING for status in statuses
            )
            or any(not status.complete for status in statuses)
        ):
            state = DashboardEvidenceState.PARTIAL
            if kinds != _EXPECTED_RUNTIME_KINDS:
                reasons.add("RUNTIME_EVIDENCE_KINDS_INCOMPLETE")
        else:
            state = DashboardEvidenceState.CURRENT
        return DashboardReadService._status(
            DashboardEvidenceSource.RUNTIME,
            state,
            *reasons,
            observed_at=max(status.last_reconciled_at for status in statuses),
        )

    @staticmethod
    def _valuation_status(
        position_count: int,
        records: list[ValuationSnapshot],
    ) -> DashboardEvidenceStatus:
        if position_count == 0:
            return DashboardReadService._status(
                DashboardEvidenceSource.VALUATION,
                DashboardEvidenceState.NOT_APPLICABLE,
                "NO_OPEN_POSITIONS",
            )
        if not records:
            return DashboardReadService._status(
                DashboardEvidenceSource.VALUATION,
                DashboardEvidenceState.UNAVAILABLE,
                "VALUATION_EVIDENCE_NOT_RECORDED",
            )
        reasons = {record.reason_code for record in records if record.reason_code is not None}
        states = {record.state for record in records}
        if ValuationState.SOURCE_UNAVAILABLE in states:
            state = DashboardEvidenceState.UNAVAILABLE
        elif ValuationState.STALE in states:
            state = DashboardEvidenceState.STALE
        elif ValuationState.UNPRICED in states or len(records) < position_count:
            state = DashboardEvidenceState.PARTIAL
            if len(records) < position_count:
                reasons.add("VALUATION_POSITION_COVERAGE_INCOMPLETE")
        else:
            state = DashboardEvidenceState.CURRENT
        return DashboardReadService._status(
            DashboardEvidenceSource.VALUATION,
            state,
            *reasons,
            observed_at=max(record.observed_at for record in records),
        )

    @staticmethod
    def _model_status(
        records: list[ModelHealthRecord],
        *,
        model_permission: bool,
    ) -> DashboardEvidenceStatus:
        if not model_permission:
            return DashboardReadService._status(
                DashboardEvidenceSource.MODEL,
                DashboardEvidenceState.UNAVAILABLE,
                "MODEL_READ_PERMISSION_MISSING",
            )
        if not records:
            return DashboardReadService._status(
                DashboardEvidenceSource.MODEL,
                DashboardEvidenceState.UNAVAILABLE,
                "MODEL_HEALTH_EVIDENCE_NOT_RECORDED",
            )
        mapping = {
            DriftHealthStatus.HEALTHY: DashboardEvidenceState.CURRENT,
            DriftHealthStatus.ATTENTION: DashboardEvidenceState.ATTENTION,
            DriftHealthStatus.DEGRADED: DashboardEvidenceState.DEGRADED,
            DriftHealthStatus.INSUFFICIENT_EVIDENCE: DashboardEvidenceState.PARTIAL,
            DriftHealthStatus.UNAVAILABLE: DashboardEvidenceState.UNAVAILABLE,
        }
        state = max(
            (mapping[record.drift_status] for record in records),
            key=lambda value: _STATE_RANK[value],
        )
        checked = [
            record.source_checked_at for record in records if record.source_checked_at is not None
        ]
        return DashboardReadService._status(
            DashboardEvidenceSource.MODEL,
            state,
            *(record.drift_reason for record in records),
            observed_at=max(checked) if checked else None,
        )

    @staticmethod
    def _risk_status(risk_decisions: tuple[RiskDecision, ...]) -> DashboardEvidenceStatus:
        if not risk_decisions:
            return DashboardReadService._status(
                DashboardEvidenceSource.RISK,
                DashboardEvidenceState.UNAVAILABLE,
                "RISK_DECISION_EVIDENCE_NOT_RECORDED",
            )
        reasons = {"RISK_DECISION_BOT_ATTRIBUTION_UNAVAILABLE"}
        if any(decision.decision is RiskDecisionOutcome.REJECTED for decision in risk_decisions):
            state = DashboardEvidenceState.ATTENTION
            reasons.add("RISK_REJECTIONS_PRESENT")
        else:
            state = DashboardEvidenceState.PARTIAL
        return DashboardReadService._status(
            DashboardEvidenceSource.RISK,
            state,
            *reasons,
            observed_at=max(decision.occurred_at for decision in risk_decisions),
        )

    @staticmethod
    def _attention_reasons(
        bot: BotInstance,
        evidence: BotDashboardEvidence,
    ) -> tuple[str, ...]:
        reasons: set[str] = set()
        if bot.observed_state is BotObservedState.ERROR:
            reasons.add("BOT_OBSERVED_ERROR")
        if bot.desired_state.value != bot.observed_state.value:
            reasons.add("DESIRED_OBSERVED_STATE_MISMATCH")
        for status in (evidence.runtime, evidence.valuation, evidence.model):
            if status.state in _ATTENTION_STATES:
                reasons.add(f"{status.source.value}_{status.state.value}")
                reasons.update(status.reason_codes)
        return tuple(sorted(reasons))

    @staticmethod
    def _source_statuses(
        generated_at: datetime,
        items: tuple[BotDashboardItem, ...],
        risk_status: DashboardEvidenceStatus,
    ) -> tuple[DashboardEvidenceStatus, ...]:
        statuses = (
            DashboardEvidenceStatus(
                source=DashboardEvidenceSource.CONTROL_PLANE,
                state=DashboardEvidenceState.CURRENT,
                observed_at=generated_at,
            ),
            DashboardReadService._aggregate_status(
                DashboardEvidenceSource.RUNTIME,
                tuple(item.evidence.runtime for item in items),
            ),
            DashboardReadService._aggregate_status(
                DashboardEvidenceSource.VALUATION,
                tuple(item.evidence.valuation for item in items),
            ),
            DashboardReadService._aggregate_status(
                DashboardEvidenceSource.MODEL,
                tuple(item.evidence.model for item in items),
            ),
            risk_status,
        )
        return tuple(sorted(statuses, key=lambda status: status.source.value))

    @staticmethod
    def _aggregate_status(
        source: DashboardEvidenceSource,
        statuses: tuple[DashboardEvidenceStatus, ...],
    ) -> DashboardEvidenceStatus:
        if not statuses:
            return DashboardReadService._status(
                source,
                DashboardEvidenceState.UNAVAILABLE,
                "NO_MATCHING_BOTS",
            )
        applicable = tuple(
            status
            for status in statuses
            if status.state is not DashboardEvidenceState.NOT_APPLICABLE
        )
        if not applicable:
            return DashboardReadService._status(
                source,
                DashboardEvidenceState.NOT_APPLICABLE,
                *(reason for status in statuses for reason in status.reason_codes),
            )
        state = max(
            (status.state for status in applicable),
            key=lambda value: _STATE_RANK[value],
        )
        observed = [status.observed_at for status in applicable if status.observed_at is not None]
        return DashboardReadService._status(
            source,
            state,
            *(reason for status in applicable for reason in status.reason_codes),
            observed_at=max(observed) if observed else None,
        )

    @staticmethod
    def _totals(
        items: tuple[BotDashboardItem, ...],
        risk_decision_count: int,
    ) -> DashboardTotals:
        realized = [item.realized_net_pnl for item in items if item.realized_net_pnl is not None]
        unrealized = [item.unrealized_pnl for item in items if item.unrealized_pnl is not None]
        return DashboardTotals(
            matching_bot_count=len(items),
            active_bot_count=sum(
                1 for item in items if item.observed_state is BotObservedState.RUNNING
            ),
            attention_bot_count=sum(1 for item in items if item.requires_attention),
            open_position_count=sum(item.open_position_count for item in items),
            open_order_count=sum(item.open_order_count for item in items),
            runtime_trade_count=sum(item.runtime_trade_count for item in items),
            risk_decision_count=risk_decision_count,
            realized_net_pnl=sum(realized, Decimal("0")) if realized else None,
            unrealized_pnl=sum(unrealized, Decimal("0")) if unrealized else None,
        )

    @staticmethod
    def _status(
        source: DashboardEvidenceSource,
        state: DashboardEvidenceState,
        *reason_codes: str,
        observed_at: datetime | None = None,
    ) -> DashboardEvidenceStatus:
        return DashboardEvidenceStatus(
            source=source,
            state=state,
            observed_at=observed_at,
            reason_codes=tuple(sorted(set(reason_codes))),
        )

    @classmethod
    def _cursor_start(
        cls,
        tenant_id: str,
        filters: BotManagementListFilters,
        page: BoundedPagination,
        result_count: int,
    ) -> int:
        if page.cursor is None:
            return 0
        payload = cls._decode_cursor(page.cursor)
        expected = {
            "tenant_id": tenant_id,
            "filter_sha256": sha256(filters.canonical_json().encode()).hexdigest(),
            "sort_direction": page.sort_direction.value,
            "page_size": page.page_size,
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            raise DashboardReadError("dashboard cursor does not match the request")
        offset = payload.get("offset")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise DashboardReadError("dashboard cursor offset is invalid")
        if offset > result_count:
            raise DashboardReadError("dashboard cursor offset is outside the result set")
        return offset

    @staticmethod
    def _encode_cursor(
        tenant_id: str,
        filters: BotManagementListFilters,
        page: BoundedPagination,
        offset: int,
    ) -> str:
        payload = json.dumps(
            {
                "tenant_id": tenant_id,
                "filter_sha256": sha256(filters.canonical_json().encode()).hexdigest(),
                "sort_direction": page.sort_direction.value,
                "page_size": page.page_size,
                "offset": offset,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> dict[str, object]:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            raw = base64.b64decode(padded, altchars=b"-_", validate=True)
            payload = json.loads(raw.decode())
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DashboardReadError("dashboard cursor cannot be decoded") from exc
        expected_keys = {
            "tenant_id",
            "filter_sha256",
            "sort_direction",
            "page_size",
            "offset",
        }
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise DashboardReadError("dashboard cursor shape is invalid")
        return payload
