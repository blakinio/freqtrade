from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable
from uuid import uuid5

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
    ResolvedRuntimeArtifacts,
    RuntimeArtifactResolver,
    RuntimeRecord,
)
from ai_platform.portal.execution.workspace import RuntimeWorkspaceStore
from ai_platform.portal.runtime_supervisor import (
    SupervisorOperation,
    SupervisorOutcome,
    SupervisorRequest,
)


Clock = Callable[[], datetime]


@runtime_checkable
class RuntimeSupervisorClient(Protocol):
    """Narrow lifecycle client; ordinary workers never receive RuntimeDriver authority."""

    def execute(self, request: SupervisorRequest) -> SupervisorOutcome: ...


class FreqtradeExecutionAdapter:
    def __init__(
        self,
        supervisor: RuntimeSupervisorClient,
        artifact_resolver: RuntimeArtifactResolver,
        workspace_store: RuntimeWorkspaceStore,
        clock: Clock | None = None,
        private_read_collector: PrivateRuntimeCollector | None = None,
    ) -> None:
        if not isinstance(supervisor, RuntimeSupervisorClient):
            raise TypeError("execution adapter requires the narrow Runtime Supervisor client")
        self._supervisor = supervisor
        self._artifact_resolver = artifact_resolver
        self._workspace_store = workspace_store
        self._clock = clock or (lambda: datetime.now(UTC))
        self._private_read_collector = private_read_collector

    def provision_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        generation_id = self._desired_generation_id(bot)
        artifacts = self._artifact_resolver.resolve(
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        self._require_resolved_identity(
            artifacts,
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        self._require_dry_run_material(artifacts)
        self._require_exact_image_reference(artifacts)

        config = build_safe_dry_run_config(artifacts)
        config_sha256 = self._workspace_store.config_sha256(config)
        if config_sha256 != artifacts.normalized_runtime_config_digest:
            raise RuntimeRevisionConflictError(
                "resolved runtime config does not match RuntimeGeneration config digest"
            )

        runtime_id = self._workspace_store.runtime_id_for(
            bot.tenant_id,
            bot.bot_id,
            generation_id,
        )
        current = self._workspace_store.read_current_record(
            bot.tenant_id,
            bot.bot_id,
        )
        if current is not None:
            self._require_record_identity(current, bot.tenant_id, bot.bot_id)
            if current.generation_id != generation_id:
                if artifacts.generation_ordinal <= current.generation_ordinal:
                    raise RuntimeRevisionConflictError(
                        "new RuntimeGeneration ordinal must be greater than current generation"
                    )
                previous = self._execute_supervisor(
                    current,
                    context,
                    SupervisorOperation.INSPECT_GENERATION,
                )
                if not previous.accepted or previous.state is None:
                    raise RuntimeRevisionConflictError(
                        "previous runtime generation inspection was rejected by Runtime Supervisor"
                    )
                if previous.state not in {
                    DriverRuntimeState.MISSING,
                    DriverRuntimeState.CREATED,
                    DriverRuntimeState.STOPPED,
                }:
                    raise RuntimeRevisionConflictError(
                        "previous runtime generation must be stopped before replacement"
                    )

        existing = self._workspace_store.read_record(runtime_id)
        if existing is not None:
            self._require_record_identity(existing, bot.tenant_id, bot.bot_id)
            self._require_generation(existing, generation_id)
            self._require_material_unchanged(
                existing,
                artifacts,
                config_sha256,
            )

        try:
            self._workspace_store.write_config(runtime_id, config)
        except ValueError as exc:
            raise RuntimeRevisionConflictError(str(exc)) from exc
        self._workspace_store.ensure_state(runtime_id)

        record = RuntimeRecord(
            tenant_id=bot.tenant_id,
            bot_id=bot.bot_id,
            generation_id=generation_id,
            generation_ordinal=artifacts.generation_ordinal,
            generation_spec_digest=artifacts.generation_spec_digest,
            state_version=bot.state_version,
            config_revision_id=artifacts.config_revision_id,
            config_revision=artifacts.config_revision,
            config_revision_digest=artifacts.config_revision_digest,
            normalized_runtime_config_digest=artifacts.normalized_runtime_config_digest,
            runtime_image_digest=artifacts.runtime_image_digest,
            strategy_artifact_digest=artifacts.strategy_artifact_digest,
            model_artifact_digest=artifacts.model_artifact_digest,
            runtime_id=runtime_id,
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

        outcome = self._execute_supervisor(
            record,
            context,
            SupervisorOperation.ENSURE_PROVISIONED,
            expected_state_version=bot.state_version,
        )
        if not outcome.accepted or outcome.state is None or outcome.state_version < 1:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return self._status(
                bot.tenant_id,
                bot.bot_id,
                runtime_id,
                BotObservedState.ERROR,
            )

        record = record.model_copy(update={"state_version": outcome.state_version})
        try:
            self._workspace_store.set_current_record(record)
        except ValueError as exc:
            raise RuntimeRevisionConflictError(str(exc)) from exc
        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            bot.tenant_id,
            bot.bot_id,
            runtime_id,
            self._observed_state(outcome.state),
        )

    def start_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(bot.tenant_id, bot.bot_id)
        self._require_generation(record, self._desired_generation_id(bot))
        return self._lifecycle_status(
            record,
            context,
            SupervisorOperation.ENSURE_RUNNING,
            expected_state_version=bot.state_version,
        )

    def pause_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(record, context, SupervisorOperation.ENSURE_PAUSED)

    def stop_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        return self._lifecycle_status(record, context, SupervisorOperation.ENSURE_STOPPED)

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
        outcome = self._execute_supervisor(record, context, SupervisorOperation.INSPECT_GENERATION)
        if not outcome.accepted or outcome.state is None:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return ExecutionHealth(
                tenant_id=tenant_id,
                bot_id=bot_id,
                runtime_id=record.runtime_id,
                health=RuntimeHealthState.UNHEALTHY,
                observed_at=self._clock(),
                reason_code=reason_code,
            )

        self._write_success(record, context, state_version=outcome.state_version)
        health, health_reason_code = self._health_state(outcome.state)
        return ExecutionHealth(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=record.runtime_id,
            health=health,
            observed_at=self._clock(),
            reason_code=health_reason_code,
        )

    def get_runtime_status(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        record = self._require_record(tenant_id, bot_id)
        outcome = self._execute_supervisor(record, context, SupervisorOperation.INSPECT_GENERATION)
        if not outcome.accepted or outcome.state is None:
            self._write_failure(record, context, self._outcome_reason(outcome))
            return self._status(
                tenant_id,
                bot_id,
                record.runtime_id,
                BotObservedState.ERROR,
            )

        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            tenant_id,
            bot_id,
            record.runtime_id,
            self._observed_state(outcome.state),
        )

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
            snapshot = collector.collect_snapshot(
                tenant_id,
                bot_id,
                record.runtime_id,
            )
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
            result = collector.collect_positions(
                tenant_id,
                bot_id,
                record.runtime_id,
            )
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
            result = collector.collect_orders(
                tenant_id,
                bot_id,
                record.runtime_id,
            )
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
            result = collector.collect_trades(
                tenant_id,
                bot_id,
                record.runtime_id,
            )
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
        operation: SupervisorOperation,
        *,
        expected_state_version: int | None = None,
    ) -> RuntimeStatus:
        outcome = self._execute_supervisor(
            record,
            context,
            operation,
            expected_state_version=expected_state_version,
        )
        if not outcome.accepted or outcome.state is None:
            self._write_failure(record, context, self._outcome_reason(outcome))
            return self._status(
                record.tenant_id,
                record.bot_id,
                record.runtime_id,
                BotObservedState.ERROR,
            )
        self._write_success(record, context, state_version=outcome.state_version)
        return self._status(
            record.tenant_id,
            record.bot_id,
            record.runtime_id,
            self._observed_state(outcome.state),
        )

    def _execute_supervisor(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        operation: SupervisorOperation,
        *,
        expected_state_version: int | None = None,
    ) -> SupervisorOutcome:
        state_version = (
            record.state_version if expected_state_version is None else expected_state_version
        )
        command_id = uuid5(
            context.request_id,
            ":".join(
                (
                    record.tenant_id,
                    record.bot_id,
                    record.generation_id,
                    operation.value,
                    str(state_version),
                )
            ),
        )
        return self._supervisor.execute(
            SupervisorRequest(
                tenant_id=record.tenant_id,
                bot_id=record.bot_id,
                generation_id=record.generation_id,
                generation_spec_digest=record.generation_spec_digest,
                operation=operation,
                command_id=command_id,
                expected_generation_ordinal=record.generation_ordinal,
                expected_state_version=state_version,
                correlation_id=context.correlation_id,
                causation_id=context.causation_id,
            )
        )

    @staticmethod
    def _outcome_reason(outcome: SupervisorOutcome) -> str:
        return outcome.driver_reason_code or outcome.code.value

    def _require_record(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> RuntimeRecord:
        record = self._workspace_store.read_current_record(tenant_id, bot_id)
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
        outcome = self._execute_supervisor(record, context, SupervisorOperation.INSPECT_GENERATION)
        if not outcome.accepted or outcome.state is None:
            reason_code = self._outcome_reason(outcome)
            self._write_failure(record, context, reason_code)
            return reason_code
        state = outcome.state
        self._write_success(record, context, state_version=outcome.state_version)
        if state is DriverRuntimeState.RUNNING:
            return None
        reason_code = {
            DriverRuntimeState.MISSING: "RUNTIME_READ_RUNTIME_MISSING",
            DriverRuntimeState.CREATED: "RUNTIME_READ_RUNTIME_NOT_STARTED",
            DriverRuntimeState.STARTING: "RUNTIME_READ_RUNTIME_STARTING",
            DriverRuntimeState.PAUSED: "RUNTIME_READ_RUNTIME_PAUSED",
            DriverRuntimeState.STOPPED: "RUNTIME_READ_RUNTIME_STOPPED",
        }[state]
        self._write_failure(record, context, reason_code, state_version=outcome.state_version)
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
    def _snapshot_failure_reason(
        snapshot: PrivateRuntimeSnapshot,
    ) -> str | None:
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
    def _require_record_identity(
        record: RuntimeRecord,
        tenant_id: str,
        bot_id: str,
    ) -> None:
        if record.tenant_id != tenant_id or record.bot_id != bot_id:
            raise RuntimeNotProvisionedError("runtime identity does not match tenant and bot")

    @staticmethod
    def _require_generation(
        record: RuntimeRecord,
        generation_id: str,
    ) -> None:
        if record.generation_id != generation_id:
            raise RuntimeRevisionConflictError(
                "provisioned runtime generation does not match desired RuntimeGeneration"
            )

    @staticmethod
    def _desired_generation_id(bot: BotInstance) -> str:
        generation_id = bot.desired_runtime_generation_id
        if generation_id is None:
            raise RuntimeNotProvisionedError("bot has no desired RuntimeGeneration")
        return generation_id

    @staticmethod
    def _require_resolved_identity(
        artifacts: ResolvedRuntimeArtifacts,
        tenant_id: str,
        bot_id: str,
        generation_id: str,
    ) -> None:
        if (
            artifacts.tenant_id != tenant_id
            or artifacts.bot_id != bot_id
            or artifacts.generation_id != generation_id
        ):
            raise RuntimeRevisionConflictError(
                "resolved runtime material does not match requested RuntimeGeneration identity"
            )

    @staticmethod
    def _require_dry_run_material(
        artifacts: ResolvedRuntimeArtifacts,
    ) -> None:
        if artifacts.execution_mode is not ExecutionMode.DRY_RUN:
            raise UnsupportedExecutionModeError("P3 only supports dry_run execution mode")

    @staticmethod
    def _require_exact_image_reference(
        artifacts: ResolvedRuntimeArtifacts,
    ) -> None:
        expected_suffix = f"@sha256:{artifacts.runtime_image_digest}"
        if not artifacts.image.endswith(expected_suffix):
            raise RuntimeRevisionConflictError(
                "runtime image reference does not match RuntimeGeneration image digest"
            )

    @staticmethod
    def _require_material_unchanged(
        record: RuntimeRecord,
        artifacts: ResolvedRuntimeArtifacts,
        config_sha256: str,
    ) -> None:
        if (
            record.generation_ordinal != artifacts.generation_ordinal
            or record.generation_spec_digest != artifacts.generation_spec_digest
            or record.config_revision_id != artifacts.config_revision_id
            or record.config_revision != artifacts.config_revision
            or record.config_revision_digest != artifacts.config_revision_digest
            or record.normalized_runtime_config_digest != artifacts.normalized_runtime_config_digest
            or record.runtime_image_digest != artifacts.runtime_image_digest
            or record.strategy_artifact_digest != artifacts.strategy_artifact_digest
            or record.model_artifact_digest != artifacts.model_artifact_digest
            or record.config_sha256 != config_sha256
            or record.image != artifacts.image
            or record.strategy_name != artifacts.strategy_name
        ):
            raise RuntimeRevisionConflictError(
                "runtime material changed without a new immutable RuntimeGeneration"
            )

    def _write_success(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        *,
        state_version: int | None = None,
    ) -> None:
        self._write_record_status(record, context, None, state_version=state_version)

    def _write_failure(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        reason_code: str,
        *,
        state_version: int | None = None,
    ) -> None:
        self._write_record_status(record, context, reason_code, state_version=state_version)

    def _write_record_status(
        self,
        record: RuntimeRecord,
        context: CorrelationContext,
        reason_code: str | None,
        *,
        state_version: int | None = None,
    ) -> None:
        update: dict[str, object] = {
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "causation_id": context.causation_id,
            "updated_at": self._clock(),
            "last_error_code": reason_code,
        }
        if state_version is not None and state_version >= 1:
            update["state_version"] = state_version
        self._workspace_store.write_record(record.model_copy(update=update))

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
        return {
            DriverRuntimeState.MISSING: BotObservedState.ERROR,
            DriverRuntimeState.CREATED: BotObservedState.CREATED,
            DriverRuntimeState.STARTING: BotObservedState.STARTING,
            DriverRuntimeState.RUNNING: BotObservedState.RUNNING,
            DriverRuntimeState.PAUSED: BotObservedState.PAUSED,
            DriverRuntimeState.STOPPED: BotObservedState.STOPPED,
        }[state]

    @staticmethod
    def _health_state(
        state: DriverRuntimeState,
    ) -> tuple[RuntimeHealthState, str | None]:
        return {
            DriverRuntimeState.MISSING: (
                RuntimeHealthState.UNHEALTHY,
                "RUNTIME_MISSING",
            ),
            DriverRuntimeState.CREATED: (
                RuntimeHealthState.DEGRADED,
                "RUNTIME_NOT_READY",
            ),
            DriverRuntimeState.STARTING: (
                RuntimeHealthState.DEGRADED,
                "RUNTIME_STARTING",
            ),
            DriverRuntimeState.RUNNING: (
                RuntimeHealthState.HEALTHY,
                None,
            ),
            DriverRuntimeState.PAUSED: (
                RuntimeHealthState.DEGRADED,
                "RUNTIME_PAUSED",
            ),
            DriverRuntimeState.STOPPED: (
                RuntimeHealthState.DEGRADED,
                "RUNTIME_STOPPED",
            ),
        }[state]

    @staticmethod
    def _runtime_labels(
        bot: BotInstance,
        generation_id: str,
        config_revision: int,
        runtime_id: str,
        context: CorrelationContext,
    ) -> dict[str, str]:
        labels = {
            "ai.portal.runtime_id": runtime_id,
            "ai.portal.tenant_hash": hashlib.sha256(bot.tenant_id.encode()).hexdigest()[:16],
            "ai.portal.bot_hash": hashlib.sha256(bot.bot_id.encode()).hexdigest()[:16],
            "ai.portal.generation_hash": hashlib.sha256(generation_id.encode()).hexdigest()[:16],
            "ai.portal.config_revision": str(config_revision),
            "ai.portal.request_id": str(context.request_id),
            "ai.portal.correlation_id": str(context.correlation_id),
        }
        if context.causation_id is not None:
            labels["ai.portal.causation_id"] = str(context.causation_id)
        return labels
