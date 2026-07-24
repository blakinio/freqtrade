from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime

from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.contracts.execution import (
    ExecutionHealth,
    OpenPosition,
    OrderRecord,
    RuntimeHealthState,
    RuntimeStatus,
    TradeRecord,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent
from ai_platform.portal.execution.config import build_safe_dry_run_config
from ai_platform.portal.execution.errors import (
    RuntimeDriverError,
    RuntimeNotProvisionedError,
    RuntimeReadIncompleteError,
    RuntimeReadIsolationError,
    RuntimeReadUnavailableError,
    RuntimeRevisionConflictError,
    UnsupportedExecutionModeError,
    UnsupportedExecutionOperationError,
)
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    PositionReadResult,
    PrivateRuntimeCollector,
    PrivateRuntimeSnapshot,
    RuntimeReadFreshness,
    RuntimeReadReconciliationStatus,
    TradeReadResult,
)
from ai_platform.portal.execution.runtime import (
    DriverRuntimeState,
    RuntimeArtifactResolver,
    RuntimeContainerSpec,
    RuntimeDriver,
    RuntimeRecord,
)
from ai_platform.portal.execution.workspace import RuntimeWorkspaceStore


Clock = Callable[[], datetime]


class FreqtradeExecutionAdapter:
    def __init__(
        self,
        driver: RuntimeDriver,
        artifact_resolver: RuntimeArtifactResolver,
        workspace_store: RuntimeWorkspaceStore,
        clock: Clock | None = None,
        private_read_collector: PrivateRuntimeCollector | None = None,
    ) -> None:
        self._driver = driver
        self._artifact_resolver = artifact_resolver
        self._workspace_store = workspace_store
        self._clock = clock or (lambda: datetime.now(UTC))
        self._private_read_collector = private_read_collector

    def provision_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        self._require_dry_run(bot)
        runtime_id = self._workspace_store.runtime_id_for(bot.tenant_id, bot.bot_id)
        existing = self._workspace_store.read_record(runtime_id)
        if existing is not None:
            self._require_record_identity(existing, bot.tenant_id, bot.bot_id)
            self._require_revision(existing, bot)

        artifacts = self._artifact_resolver.resolve(bot)
        config = build_safe_dry_run_config(bot, artifacts)
        config_sha256 = self._workspace_store.config_sha256(config)
        if existing is not None and (
            existing.config_sha256 != config_sha256
            or existing.image != artifacts.image
            or existing.strategy_name != artifacts.strategy_name
        ):
            raise RuntimeRevisionConflictError(
                "runtime artifacts changed without a new immutable config revision"
            )
        self._workspace_store.write_config(runtime_id, config)

        record = RuntimeRecord(
            tenant_id=bot.tenant_id,
            bot_id=bot.bot_id,
            runtime_id=runtime_id,
            config_revision=bot.spec.config_revision,
            image=artifacts.image,
            strategy_name=artifacts.strategy_name,
            config_sha256=config_sha256,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            updated_at=self._clock(),
            last_error_code=None,
        )
        self._workspace_store.write_record(record)

        container_spec = RuntimeContainerSpec(
            runtime_id=runtime_id,
            image=artifacts.image,
            workspace=self._workspace_store.workspace_for(runtime_id),
            strategy_name=artifacts.strategy_name,
            labels=self._runtime_labels(bot, runtime_id, context),
        )
        try:
            state = self._driver.provision(container_spec)
        except RuntimeDriverError as exc:
            self._write_failure(record, context, exc.reason_code)
            return self._status(bot.tenant_id, bot.bot_id, runtime_id, BotObservedState.ERROR)

        self._write_success(record, context)
        return self._status(bot.tenant_id, bot.bot_id, runtime_id, self._observed_state(state))

    def start_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        self._require_dry_run(bot)
        record = self._require_record(bot.tenant_id, bot.bot_id)
        self._require_revision(record, bot)
        return self._lifecycle_status(record, context, self._driver.start)

    def pause_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(record, context, self._driver.pause)

    def stop_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(record, context, self._driver.stop)

    def get_health(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> ExecutionHealth:
        record = self._require_record(tenant_id, bot_id)
        if record.last_error_code is not None:
            return ExecutionHealth(
                tenant_id=tenant_id,
                bot_id=bot_id,
                runtime_id=record.runtime_id,
                health=RuntimeHealthState.UNHEALTHY,
                observed_at=self._clock(),
                reason_code=record.last_error_code,
            )
        try:
            state = self._driver.inspect(record.runtime_id)
        except RuntimeDriverError as exc:
            self._write_failure(record, context, exc.reason_code)
            return ExecutionHealth(
                tenant_id=tenant_id,
                bot_id=bot_id,
                runtime_id=record.runtime_id,
                health=RuntimeHealthState.UNHEALTHY,
                observed_at=self._clock(),
                reason_code=exc.reason_code,
            )

        self._write_success(record, context)
        health, reason_code = self._health_state(state)
        return ExecutionHealth(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=record.runtime_id,
            health=health,
            observed_at=self._clock(),
            reason_code=reason_code,
        )

    def get_runtime_status(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        try:
            state = self._driver.inspect(record.runtime_id)
        except RuntimeDriverError as exc:
            self._write_failure(record, context, exc.reason_code)
            return self._status(tenant_id, bot_id, record.runtime_id, BotObservedState.ERROR)

        self._write_success(record, context)
        return self._status(tenant_id, bot_id, record.runtime_id, self._observed_state(state))

    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        del intent, context
        raise UnsupportedExecutionOperationError("ORDER_SUBMISSION_NOT_IMPLEMENTED")

    def collect_private_runtime_snapshot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> PrivateRuntimeSnapshot:
        record = self._require_record(tenant_id, bot_id)
        collector = self._private_read_collector
        if collector is None:
            collector_reason_code = "PRIVATE_RUNTIME_COLLECTOR_NOT_CONFIGURED"
            self._write_failure(record, context, collector_reason_code)
            return self._unavailable_snapshot(record, collector_reason_code)

        reason_code = self._runtime_read_unavailable_reason(record, context)
        if reason_code is not None:
            return collector.unavailable_snapshot(
                tenant_id,
                bot_id,
                record.runtime_id,
                reason_code,
            )

        try:
            snapshot = collector.collect_snapshot(tenant_id, bot_id, record.runtime_id)
        except RuntimeReadIsolationError as exc:
            self._write_failure(record, context, exc.reason_code)
            raise

        failure_reason = self._snapshot_failure_reason(snapshot)
        if failure_reason is None:
            self._write_success(record, context)
        else:
            self._write_failure(record, context, failure_reason)
        return snapshot

    def get_open_positions(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OpenPosition, ...]:
        record = self._require_record(tenant_id, bot_id)
        collector = self._require_private_collector(record, context)
        self._require_runtime_readable(record, context)
        try:
            result = collector.collect_positions(tenant_id, bot_id, record.runtime_id)
        except RuntimeReadIsolationError as exc:
            self._write_failure(record, context, exc.reason_code)
            raise
        self._require_authoritative_result(record, context, result)
        return tuple(
            OpenPosition(
                tenant_id=tenant_id,
                bot_id=bot_id,
                position_id=position.source_position_id,
                pair=position.pair,
                side=position.side,
                amount=position.amount,
                opened_at=position.opened_at,
            )
            for position in result.records
        )

    def get_orders(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OrderRecord, ...]:
        record = self._require_record(tenant_id, bot_id)
        collector = self._require_private_collector(record, context)
        self._require_runtime_readable(record, context)
        try:
            result = collector.collect_orders(tenant_id, bot_id, record.runtime_id)
        except RuntimeReadIsolationError as exc:
            self._write_failure(record, context, exc.reason_code)
            raise
        self._require_authoritative_result(record, context, result)
        if any(order.execution_intent_id is None for order in result.records):
            reason_code = "RUNTIME_READ_ORDER_ATTRIBUTION_MISSING"
            self._write_failure(record, context, reason_code)
            raise RuntimeReadIncompleteError(reason_code)
        return tuple(
            OrderRecord(
                tenant_id=tenant_id,
                bot_id=bot_id,
                order_id=order.source_order_id,
                execution_intent_id=order.execution_intent_id,
                pair=order.pair,
                side=order.side,
                state=order.state,
                amount=order.amount,
                created_at=order.created_at,
            )
            for order in result.records
            if order.execution_intent_id is not None
        )

    def get_trades(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[TradeRecord, ...]:
        record = self._require_record(tenant_id, bot_id)
        collector = self._require_private_collector(record, context)
        self._require_runtime_readable(record, context)
        try:
            result = collector.collect_trades(tenant_id, bot_id, record.runtime_id)
        except RuntimeReadIsolationError as exc:
            self._write_failure(record, context, exc.reason_code)
            raise
        self._require_authoritative_result(record, context, result)
        return tuple(
            TradeRecord(
                tenant_id=tenant_id,
                bot_id=bot_id,
                trade_id=trade.source_trade_id,
                pair=trade.pair,
                state=trade.state,
                opened_at=trade.opened_at,
                closed_at=trade.closed_at,
            )
            for trade in result.records
        )

    def _lifecycle_status(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        operation: Callable[[str], DriverRuntimeState],
    ) -> RuntimeStatus:
        try:
            state = operation(record.runtime_id)
        except RuntimeDriverError as exc:
            self._write_failure(record, context, exc.reason_code)
            return self._status(
                record.tenant_id,
                record.bot_id,
                record.runtime_id,
                BotObservedState.ERROR,
            )

        self._write_success(record, context)
        return self._status(
            record.tenant_id,
            record.bot_id,
            record.runtime_id,
            self._observed_state(state),
        )

    def _require_record(self, tenant_id: str, bot_id: str) -> RuntimeRecord:
        runtime_id = self._workspace_store.runtime_id_for(tenant_id, bot_id)
        record = self._workspace_store.read_record(runtime_id)
        if record is None:
            raise RuntimeNotProvisionedError("runtime has not been provisioned")
        self._require_record_identity(record, tenant_id, bot_id)
        return record

    def _require_private_collector(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
    ) -> PrivateRuntimeCollector:
        collector = self._private_read_collector
        if collector is None:
            reason_code = "PRIVATE_RUNTIME_COLLECTOR_NOT_CONFIGURED"
            self._write_failure(record, context, reason_code)
            raise RuntimeReadUnavailableError(reason_code)
        return collector

    def _require_runtime_readable(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
    ) -> None:
        reason_code = self._runtime_read_unavailable_reason(record, context)
        if reason_code is not None:
            raise RuntimeReadUnavailableError(reason_code)

    def _runtime_read_unavailable_reason(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
    ) -> str | None:
        try:
            state = self._driver.inspect(record.runtime_id)
        except RuntimeDriverError as exc:
            self._write_failure(record, context, exc.reason_code)
            return exc.reason_code
        if state is DriverRuntimeState.RUNNING:
            return None
        reason_code = {
            DriverRuntimeState.MISSING: "RUNTIME_READ_RUNTIME_MISSING",
            DriverRuntimeState.CREATED: "RUNTIME_READ_RUNTIME_NOT_STARTED",
            DriverRuntimeState.STARTING: "RUNTIME_READ_RUNTIME_STARTING",
            DriverRuntimeState.PAUSED: "RUNTIME_READ_RUNTIME_PAUSED",
            DriverRuntimeState.STOPPED: "RUNTIME_READ_RUNTIME_STOPPED",
        }[state]
        self._write_failure(record, context, reason_code)
        return reason_code

    def _unavailable_snapshot(
        self,
        record: RuntimeRecord,
        reason_code: str,
    ) -> PrivateRuntimeSnapshot:
        collector = self._private_read_collector
        if collector is not None:
            return collector.unavailable_snapshot(
                record.tenant_id,
                record.bot_id,
                record.runtime_id,
                reason_code,
            )
        observed_at = self._clock()
        fallback = PrivateRuntimeCollector.__new__(PrivateRuntimeCollector)
        fallback._clock = lambda: observed_at
        return fallback.unavailable_snapshot(
            record.tenant_id,
            record.bot_id,
            record.runtime_id,
            reason_code,
        )

    def _require_authoritative_result(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        result: PositionReadResult | OrderReadResult | TradeReadResult,
    ) -> None:
        status = result.status
        if (
            status.complete
            and status.freshness is RuntimeReadFreshness.CURRENT
            and status.reconciliation_status is RuntimeReadReconciliationStatus.SYNCED
        ):
            self._write_success(record, context)
            return
        reason_code = status.reason_code or "RUNTIME_READ_NOT_AUTHORITATIVE"
        self._write_failure(record, context, reason_code)
        if status.reconciliation_status is RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE:
            raise RuntimeReadUnavailableError(reason_code)
        raise RuntimeReadIncompleteError(reason_code)

    @staticmethod
    def _snapshot_failure_reason(snapshot: PrivateRuntimeSnapshot) -> str | None:
        for status in (
            snapshot.positions.status,
            snapshot.orders.status,
            snapshot.trades.status,
        ):
            if (
                not status.complete
                or status.freshness is not RuntimeReadFreshness.CURRENT
                or status.reconciliation_status is not RuntimeReadReconciliationStatus.SYNCED
            ):
                return status.reason_code or "RUNTIME_READ_NOT_AUTHORITATIVE"
        return None

    @staticmethod
    def _require_record_identity(record: RuntimeRecord, tenant_id: str, bot_id: str) -> None:
        if record.tenant_id != tenant_id or record.bot_id != bot_id:
            raise RuntimeNotProvisionedError("runtime identity does not match tenant and bot")

    @staticmethod
    def _require_revision(record: RuntimeRecord, bot: BotInstance) -> None:
        if record.config_revision != bot.spec.config_revision:
            raise RuntimeRevisionConflictError(
                "provisioned runtime revision does not match bot config revision"
            )

    @staticmethod
    def _require_dry_run(bot: BotInstance) -> None:
        if bot.spec.execution_mode is not ExecutionMode.DRY_RUN:
            raise UnsupportedExecutionModeError("P3 only supports dry_run execution mode")

    def _write_success(self, record: RuntimeRecord, context: CorrelationContext) -> None:
        self._workspace_store.write_record(
            record.model_copy(
                update={
                    "request_id": context.request_id,
                    "correlation_id": context.correlation_id,
                    "causation_id": context.causation_id,
                    "updated_at": self._clock(),
                    "last_error_code": None,
                }
            )
        )

    def _write_failure(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        reason_code: str,
    ) -> None:
        self._workspace_store.write_record(
            record.model_copy(
                update={
                    "request_id": context.request_id,
                    "correlation_id": context.correlation_id,
                    "causation_id": context.causation_id,
                    "updated_at": self._clock(),
                    "last_error_code": reason_code,
                }
            )
        )

    def _status(
        self,
        tenant_id: str,
        bot_id: str,
        runtime_id: str,
        observed_state: BotObservedState,
    ) -> RuntimeStatus:
        return RuntimeStatus(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=runtime_id,
            observed_state=observed_state,
            observed_at=self._clock(),
        )

    @staticmethod
    def _observed_state(state: DriverRuntimeState) -> BotObservedState:
        mapping = {
            DriverRuntimeState.MISSING: BotObservedState.ERROR,
            DriverRuntimeState.CREATED: BotObservedState.CREATED,
            DriverRuntimeState.STARTING: BotObservedState.STARTING,
            DriverRuntimeState.RUNNING: BotObservedState.RUNNING,
            DriverRuntimeState.PAUSED: BotObservedState.PAUSED,
            DriverRuntimeState.STOPPED: BotObservedState.STOPPED,
        }
        return mapping[state]

    @staticmethod
    def _health_state(
        state: DriverRuntimeState,
    ) -> tuple[RuntimeHealthState, str | None]:
        mapping = {
            DriverRuntimeState.MISSING: (RuntimeHealthState.UNHEALTHY, "RUNTIME_MISSING"),
            DriverRuntimeState.CREATED: (RuntimeHealthState.DEGRADED, "RUNTIME_NOT_READY"),
            DriverRuntimeState.STARTING: (RuntimeHealthState.DEGRADED, "RUNTIME_STARTING"),
            DriverRuntimeState.RUNNING: (RuntimeHealthState.HEALTHY, None),
            DriverRuntimeState.PAUSED: (RuntimeHealthState.DEGRADED, "RUNTIME_PAUSED"),
            DriverRuntimeState.STOPPED: (RuntimeHealthState.DEGRADED, "RUNTIME_STOPPED"),
        }
        return mapping[state]

    @staticmethod
    def _runtime_labels(
        bot: BotInstance,
        runtime_id: str,
        context: CorrelationContext,
    ) -> dict[str, str]:
        labels = {
            "ai.portal.runtime_id": runtime_id,
            "ai.portal.tenant_hash": hashlib.sha256(bot.tenant_id.encode()).hexdigest()[:16],
            "ai.portal.bot_hash": hashlib.sha256(bot.bot_id.encode()).hexdigest()[:16],
            "ai.portal.config_revision": str(bot.spec.config_revision),
            "ai.portal.request_id": str(context.request_id),
            "ai.portal.correlation_id": str(context.correlation_id),
        }
        if context.causation_id is not None:
            labels["ai.portal.causation_id"] = str(context.causation_id)
        return labels
