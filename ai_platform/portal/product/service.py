from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditAction, AuditResult
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.contracts.identity import Permission, RoleName
from ai_platform.portal.contracts.risk import RiskDecisionOutcome, TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import BotNotFoundError
from ai_platform.portal.model_control.service import ModelControlService
from ai_platform.portal.product.repository import ProductCapabilityRepository
from ai_platform.portal.product.schema import (
    AdministrationOverview,
    GridBotConfig,
    ModelHealthRecord,
    NotificationCategory,
    NotificationEntry,
    NotificationPreference,
    NotificationSeverity,
    ProfileSecurityView,
    RuntimeLogAvailability,
    SignalEvent,
    SignalSource,
    StrategyCatalogEntry,
    StrategyKind,
    StrategyRuntimeStatus,
    TelemetryAvailability,
    utc_age_days,
)
from ai_platform.portal.risk.repository import RiskRepository
from ai_platform.portal.security.authorization import builtin_role, require_permission


Clock = Callable[[], datetime]

_EXECUTION_NOTIFICATION_ACTIONS = {
    AuditAction.BOT_START_REQUESTED,
    AuditAction.BOT_PAUSE_REQUESTED,
    AuditAction.BOT_STOP_REQUESTED,
    AuditAction.BOT_STARTED,
    AuditAction.BOT_STOPPED,
    AuditAction.MANUAL_TRADE_INTENT,
    AuditAction.KILL_SWITCH_ACTIVATED,
    AuditAction.KILL_SWITCH_RELEASED,
}

_STRATEGY_CATALOG = (
    StrategyCatalogEntry(
        strategy_version="ai-directional-v1",
        display_name="AI Directional",
        description=(
            "Immutable directional strategy reference used by existing "
            "dry-run bot configurations. Predictions remain subject to "
            "deterministic risk controls."
        ),
        kind=StrategyKind.DIRECTIONAL,
        allowed_execution_modes=(ExecutionMode.SIMULATED, ExecutionMode.DRY_RUN),
        runtime_status=StrategyRuntimeStatus.BOT_REFERENCE,
    ),
    StrategyCatalogEntry(
        strategy_version="grid-dry-run-v1",
        display_name="Grid Dry Run",
        description=(
            "Portal-managed grid configuration contract restricted to dry-run. "
            "Runtime activation remains behind the private execution boundary."
        ),
        kind=StrategyKind.GRID,
        allowed_execution_modes=(ExecutionMode.DRY_RUN,),
        runtime_status=StrategyRuntimeStatus.PORTAL_CONFIG_ONLY,
    ),
)


class ProductCapabilityService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: ProductCapabilityRepository | None = None,
        bot_repository: BotRepository | None = None,
        risk_repository: RiskRepository | None = None,
        model_control_service: ModelControlService | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or ProductCapabilityRepository()
        self._bot_repository = bot_repository or BotRepository()
        self._risk_repository = risk_repository or RiskRepository()
        self._model_control = model_control_service or ModelControlService(session_factory)
        self._clock = clock or (lambda: datetime.now(UTC))

    def submit_signal(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        pair: str,
        side: TradeSide,
        timeframe: str,
        confidence: Decimal,
        rationale: str,
    ) -> SignalEvent:
        require_permission(context.permissions, Permission.TRADE_MANUAL_EXECUTE)
        with self._session_factory() as session:
            bot = self._bot_repository.get_bot(session, context.tenant_id, bot_id)
        if bot is None:
            raise BotNotFoundError("bot not found")
        if pair not in bot.spec.pair_universe:
            raise ValueError("signal pair is outside the bot pair universe")
        if timeframe != bot.spec.timeframe:
            raise ValueError("signal timeframe must match the immutable bot configuration")

        signal = SignalEvent(
            signal_id=uuid4(),
            tenant_id=context.tenant_id,
            bot_id=bot_id,
            pair=pair,
            side=side,
            timeframe=timeframe,
            confidence=confidence,
            rationale=rationale,
            source=SignalSource.MANUAL,
            created_by_actor_id=context.actor_id,
            occurred_at=self._clock(),
            context=context.correlation_context(),
            execution_authority=False,
        )
        with self._session_factory() as session, session.begin():
            self._repository.add_signal(session, signal)
        return signal

    def list_signals(self, context: RequestContext) -> tuple[SignalEvent, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_signals(session, context.tenant_id)

    def list_strategies(self, context: RequestContext) -> tuple[StrategyCatalogEntry, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        return _STRATEGY_CATALOG

    def create_grid_config(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        pair: str,
        lower_price: Decimal,
        upper_price: Decimal,
        levels: int,
        quote_allocation: Decimal,
    ) -> GridBotConfig:
        require_permission(context.permissions, Permission.BOT_CREATE)
        with self._session_factory() as session:
            bot = self._bot_repository.get_bot(session, context.tenant_id, bot_id)
        if bot is None:
            raise BotNotFoundError("bot not found")
        if bot.spec.execution_mode != ExecutionMode.DRY_RUN:
            raise ValueError("grid configuration requires a dry_run bot")
        if bot.spec.strategy_version != "grid-dry-run-v1":
            raise ValueError("grid configuration requires strategy_version grid-dry-run-v1")
        if pair not in bot.spec.pair_universe:
            raise ValueError("grid pair is outside the bot pair universe")

        config = GridBotConfig(
            grid_config_id=uuid4(),
            tenant_id=context.tenant_id,
            bot_id=bot_id,
            pair=pair,
            strategy_version="grid-dry-run-v1",
            lower_price=lower_price,
            upper_price=upper_price,
            levels=levels,
            quote_allocation=quote_allocation,
            execution_mode=ExecutionMode.DRY_RUN,
            created_by_actor_id=context.actor_id,
            created_at=self._clock(),
        )
        with self._session_factory() as session, session.begin():
            self._repository.add_grid_config(session, config)
        return config

    def list_grid_configs(self, context: RequestContext) -> tuple[GridBotConfig, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_grid_configs(session, context.tenant_id)

    def get_notification_preference(self, context: RequestContext) -> NotificationPreference:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            stored = self._repository.get_notification_preference(
                session,
                context.tenant_id,
                context.actor_id,
            )
        if stored is not None:
            return stored
        return NotificationPreference(
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            updated_at=self._clock(),
        )

    def update_notification_preference(
        self,
        context: RequestContext,
        *,
        in_app_enabled: bool,
        signal_events: bool,
        risk_events: bool,
        execution_events: bool,
    ) -> NotificationPreference:
        require_permission(context.permissions, Permission.BOT_READ)
        preference = NotificationPreference(
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            in_app_enabled=in_app_enabled,
            signal_events=signal_events,
            risk_events=risk_events,
            execution_events=execution_events,
            updated_at=self._clock(),
        )
        with self._session_factory() as session, session.begin():
            self._repository.upsert_notification_preference(session, preference)
        return preference

    def _signal_notifications(
        self,
        session: Session,
        context: RequestContext,
    ) -> tuple[NotificationEntry, ...]:
        entries: list[NotificationEntry] = []
        for signal in self._repository.list_signals(session, context.tenant_id):
            summary = f"{signal.side.value} signal recorded for {signal.pair} on {signal.bot_id}"
            entries.append(
                NotificationEntry(
                    notification_id=f"signal:{signal.signal_id}",
                    tenant_id=context.tenant_id,
                    category=NotificationCategory.SIGNAL,
                    severity=NotificationSeverity.INFO,
                    summary=summary,
                    resource_type="signal",
                    resource_id=str(signal.signal_id),
                    occurred_at=signal.occurred_at,
                )
            )
        return tuple(entries)

    def _risk_notifications(
        self,
        session: Session,
        context: RequestContext,
    ) -> tuple[NotificationEntry, ...]:
        entries: list[NotificationEntry] = []
        decisions = self._risk_repository.list_risk_decisions(
            session,
            context.tenant_id,
        )
        for decision in decisions:
            rejected = decision.decision is RiskDecisionOutcome.REJECTED
            severity = NotificationSeverity.ATTENTION if rejected else NotificationSeverity.INFO
            reason = ", ".join(decision.reason_codes)
            if not reason:
                reason = "no reason code"
            entries.append(
                NotificationEntry(
                    notification_id=f"risk:{decision.risk_decision_id}",
                    tenant_id=context.tenant_id,
                    category=NotificationCategory.RISK,
                    severity=severity,
                    summary=f"Risk decision {decision.decision.value}: {reason}",
                    resource_type="risk_decision",
                    resource_id=str(decision.risk_decision_id),
                    occurred_at=decision.occurred_at,
                )
            )
        return tuple(entries)

    def _execution_notifications(
        self,
        session: Session,
        context: RequestContext,
    ) -> tuple[NotificationEntry, ...]:
        entries: list[NotificationEntry] = []
        events = self._bot_repository.list_audit_events(session, context.tenant_id)
        for event in events:
            if event.actor_id != context.actor_id:
                continue
            if event.action not in _EXECUTION_NOTIFICATION_ACTIONS:
                continue
            severity = (
                NotificationSeverity.INFO
                if event.result is AuditResult.SUCCEEDED
                else NotificationSeverity.ATTENTION
            )
            entries.append(
                NotificationEntry(
                    notification_id=f"execution:{event.audit_id}",
                    tenant_id=context.tenant_id,
                    category=NotificationCategory.EXECUTION,
                    severity=severity,
                    summary=f"{event.action.value}: {event.result.value}",
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    occurred_at=event.occurred_at,
                )
            )
        return tuple(entries)

    def list_notifications(self, context: RequestContext) -> tuple[NotificationEntry, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        preference = self.get_notification_preference(context)
        if not preference.in_app_enabled:
            return ()

        entries: list[NotificationEntry] = []
        with self._session_factory() as session:
            if preference.signal_events:
                entries.extend(self._signal_notifications(session, context))
            if preference.risk_events:
                entries.extend(self._risk_notifications(session, context))
            if preference.execution_events:
                entries.extend(self._execution_notifications(session, context))
        entries.sort(
            key=lambda item: (item.occurred_at, item.notification_id),
            reverse=True,
        )
        return tuple(entries)

    def profile_security(self, context: RequestContext) -> ProfileSecurityView:
        permissions = tuple(sorted(context.permissions, key=lambda item: item.value))
        return ProfileSecurityView(
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            actor_type=context.actor_type,
            permissions=permissions,
            authentication_boundary="trusted-application-identity",
            mfa_status="MANAGED_BY_EXTERNAL_IDENTITY_PROVIDER",
            session_management="MANAGED_BY_EXTERNAL_IDENTITY_PROVIDER",
            secrets_exposed=False,
        )

    def administration_overview(self, context: RequestContext) -> AdministrationOverview:
        require_permission(context.permissions, Permission.ADMIN_MANAGE)
        roles = tuple(builtin_role(context.tenant_id, role_name) for role_name in RoleName)
        permissions = tuple(sorted(context.permissions, key=lambda item: item.value))
        return AdministrationOverview(
            tenant_id=context.tenant_id,
            current_actor_id=context.actor_id,
            current_permissions=permissions,
            builtin_roles=roles,
            membership_source="external-identity-provider",
        )

    def model_health(self, context: RequestContext) -> tuple[ModelHealthRecord, ...]:
        models = self._model_control.list_models(context)
        now = self._clock()
        return tuple(
            ModelHealthRecord(
                model_version_id=model.model_version_id,
                tenant_id=model.tenant_id,
                model_family_id=model.model_family_id,
                lifecycle_state=model.lifecycle_state.value,
                created_at=model.created_at,
                training_window_end=model.training_window.end_at,
                metadata_age_days=utc_age_days(now, model.created_at),
                drift_status=TelemetryAvailability.UNAVAILABLE,
                drift_reason="CANONICAL_DRIFT_TELEMETRY_SOURCE_NOT_CONFIGURED",
            )
            for model in models
        )

    def runtime_log_availability(
        self,
        context: RequestContext,
    ) -> RuntimeLogAvailability:
        require_permission(context.permissions, Permission.AUDIT_READ)
        return RuntimeLogAvailability(
            available=False,
            source="portal-execution-activity",
            reason_code="CENTRALIZED_RUNTIME_STDOUT_STDERR_SOURCE_NOT_CONFIGURED",
            checked_at=self._clock(),
        )
