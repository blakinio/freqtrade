from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.bots import BotDesiredState, BotInstance, BotSpec
from ai_platform.portal.contracts.models import ModelVersion
from ai_platform.portal.contracts.risk import RiskDecision, TradeSide
from ai_platform.portal.control_plane.context import (
    IdentityContextProvider,
    RequestContext,
    identity_dependency,
)
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.service import (
    BotNotFoundError,
    ControlPlaneConflictError,
    ControlPlaneService,
)
from ai_platform.portal.intelligence.schema import TradeAnalysis, TradeInsight
from ai_platform.portal.intelligence.service import TradeIntelligenceService
from ai_platform.portal.learning.schema import LearningHistoryEntry
from ai_platform.portal.learning.service import LearningService
from ai_platform.portal.model_control.service import ModelControlService
from ai_platform.portal.observability.runtime import (
    RuntimeLogQuery,
    RuntimeLogSearchResult,
    RuntimeObservabilityProtocolError,
    RuntimeObservabilityService,
    RuntimeObservabilitySourceStatus,
    UnavailableRuntimeObservabilitySource,
)
from ai_platform.portal.operations.schema import (
    ExecutionActivityEntry,
    OperationalOrder,
    OperationalPosition,
    PerformanceSummary,
    RuntimeEvidenceSnapshot,
    TradeHistoryEntry,
)
from ai_platform.portal.operations.service import OperationalReadService
from ai_platform.portal.product.schema import (
    AdministrationOverview,
    GridBotConfig,
    NotificationEntry,
    NotificationPreference,
    ProfileSecurityView,
    RuntimeLogAvailability,
    SignalEvent,
    StrategyCatalogEntry,
)
from ai_platform.portal.product.service import ProductCapabilityService
from ai_platform.portal.risk.service import RiskConflictError, RiskPolicyNotFoundError
from ai_platform.portal.risk.terminal import (
    RiskSnapshotUnavailableError,
    TerminalIntentResult,
    TerminalService,
)
from ai_platform.portal.security.authorization import PermissionDeniedError
from ai_platform.portal.telemetry.schema import (
    InferenceTelemetryEnvelope,
    InferenceTelemetrySourceStatus,
    ModelHealthRecord,
)
from ai_platform.portal.telemetry.service import (
    InferenceTelemetryService,
    TelemetryConflictError,
)


class CreateBotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_id: str
    name: str
    spec: BotSpec


class ReviseBotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec: BotSpec


class DesiredStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    desired_state: BotDesiredState


class TerminalIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_id: str
    pair: str
    side: TradeSide
    amount: Decimal


class SubmitSignalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_id: str
    pair: str
    side: TradeSide
    timeframe: str
    confidence: Decimal
    rationale: str


class CreateGridBotConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_id: str
    pair: str
    lower_price: Decimal
    upper_price: Decimal
    levels: int
    quote_allocation: Decimal


class UpdateNotificationPreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    in_app_enabled: bool
    signal_events: bool
    risk_events: bool
    execution_events: bool


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(
        _request: object,
        exc: PermissionDeniedError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

    @app.exception_handler(BotNotFoundError)
    async def not_found_handler(_request: object, exc: BotNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(RiskPolicyNotFoundError)
    async def risk_not_found_handler(
        _request: object,
        exc: RiskPolicyNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ControlPlaneConflictError)
    async def conflict_handler(_request: object, exc: ControlPlaneConflictError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(RiskConflictError)
    async def risk_conflict_handler(_request: object, exc: RiskConflictError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(TelemetryConflictError)
    async def telemetry_conflict_handler(
        _request: object,
        exc: TelemetryConflictError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(RuntimeObservabilityProtocolError)
    async def runtime_observability_protocol_handler(
        _request: object,
        exc: RuntimeObservabilityProtocolError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})

    @app.exception_handler(RiskSnapshotUnavailableError)
    async def risk_snapshot_unavailable_handler(
        _request: object,
        exc: RiskSnapshotUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def validation_handler(_request: object, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )


def _register_terminal_route(
    app: FastAPI,
    terminal: TerminalService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.post("/v1/terminal/intents", response_model=TerminalIntentResult)
    def submit_terminal_intent(
        request: TerminalIntentRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> TerminalIntentResult:
        return terminal.submit_manual_intent(
            context,
            bot_id=request.bot_id,
            pair=request.pair,
            side=request.side,
            amount=request.amount,
        )


def _register_operational_routes(
    app: FastAPI,
    operations: OperationalReadService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.get("/v1/positions", response_model=list[OperationalPosition])
    def list_positions(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[OperationalPosition, ...]:
        return operations.list_positions(context)

    @app.get("/v1/orders", response_model=list[OperationalOrder])
    def list_orders(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[OperationalOrder, ...]:
        return operations.list_orders(context)

    @app.get("/v1/trades", response_model=list[TradeHistoryEntry])
    def list_trades(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[TradeHistoryEntry, ...]:
        return operations.list_trades(context)

    @app.get("/v1/runtime-evidence", response_model=RuntimeEvidenceSnapshot)
    def runtime_evidence(
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeEvidenceSnapshot:
        return operations.runtime_evidence(context)

    @app.get("/v1/performance", response_model=list[PerformanceSummary])
    def list_performance(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[PerformanceSummary, ...]:
        return operations.list_performance(context)

    @app.get("/v1/risk-events", response_model=list[RiskDecision])
    def list_risk_events(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[RiskDecision, ...]:
        return operations.list_risk_events(context)

    @app.get("/v1/audit-events", response_model=list[AuditEvent])
    def list_audit_events(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[AuditEvent, ...]:
        return operations.list_audit_events(context)

    @app.get("/v1/execution-activity", response_model=list[ExecutionActivityEntry])
    def list_execution_activity(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ExecutionActivityEntry, ...]:
        return operations.list_execution_activity(context)


def _register_runtime_observability_routes(
    app: FastAPI,
    runtime_observability: RuntimeObservabilityService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.get(
        "/v1/runtime-observability/availability",
        response_model=RuntimeObservabilitySourceStatus,
    )
    def runtime_observability_availability(
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeObservabilitySourceStatus:
        return runtime_observability.availability(context)

    @app.post(
        "/v1/runtime-observability/logs/search",
        response_model=RuntimeLogSearchResult,
    )
    def search_runtime_logs(
        request: RuntimeLogQuery,
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeLogSearchResult:
        return runtime_observability.search_logs(context, request)


def _register_signal_strategy_routes(
    app: FastAPI,
    product: ProductCapabilityService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.get("/v1/signals", response_model=list[SignalEvent])
    def list_signals(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[SignalEvent, ...]:
        return product.list_signals(context)

    @app.post("/v1/signals", response_model=SignalEvent, status_code=status.HTTP_201_CREATED)
    def submit_signal(
        request: SubmitSignalRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalEvent:
        return product.submit_signal(
            context,
            bot_id=request.bot_id,
            pair=request.pair,
            side=request.side,
            timeframe=request.timeframe,
            confidence=request.confidence,
            rationale=request.rationale,
        )

    @app.get("/v1/strategies", response_model=list[StrategyCatalogEntry])
    def list_strategies(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[StrategyCatalogEntry, ...]:
        return product.list_strategies(context)

    @app.get("/v1/grid-bots", response_model=list[GridBotConfig])
    def list_grid_bots(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[GridBotConfig, ...]:
        return product.list_grid_configs(context)

    @app.post("/v1/grid-bots", response_model=GridBotConfig, status_code=status.HTTP_201_CREATED)
    def create_grid_bot(
        request: CreateGridBotConfigRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> GridBotConfig:
        return product.create_grid_config(
            context,
            bot_id=request.bot_id,
            pair=request.pair,
            lower_price=request.lower_price,
            upper_price=request.upper_price,
            levels=request.levels,
            quote_allocation=request.quote_allocation,
        )


def _register_platform_capability_routes(
    app: FastAPI,
    product: ProductCapabilityService,
    telemetry: InferenceTelemetryService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.get("/v1/notifications", response_model=list[NotificationEntry])
    def list_notifications(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[NotificationEntry, ...]:
        return product.list_notifications(context)

    @app.get("/v1/notifications/preferences", response_model=NotificationPreference)
    def get_notification_preferences(
        context: RequestContext = Depends(context_dependency),
    ) -> NotificationPreference:
        return product.get_notification_preference(context)

    @app.put("/v1/notifications/preferences", response_model=NotificationPreference)
    def update_notification_preferences(
        request: UpdateNotificationPreferenceRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> NotificationPreference:
        return product.update_notification_preference(
            context,
            in_app_enabled=request.in_app_enabled,
            signal_events=request.signal_events,
            risk_events=request.risk_events,
            execution_events=request.execution_events,
        )

    @app.get("/v1/profile", response_model=ProfileSecurityView)
    def profile_security(
        context: RequestContext = Depends(context_dependency),
    ) -> ProfileSecurityView:
        return product.profile_security(context)

    @app.get("/v1/admin/overview", response_model=AdministrationOverview)
    def administration_overview(
        context: RequestContext = Depends(context_dependency),
    ) -> AdministrationOverview:
        return product.administration_overview(context)

    @app.post(
        "/v1/inference-telemetry/windows",
        response_model=InferenceTelemetryEnvelope,
        status_code=status.HTTP_201_CREATED,
    )
    def ingest_inference_telemetry(
        request: InferenceTelemetryEnvelope,
        context: RequestContext = Depends(context_dependency),
    ) -> InferenceTelemetryEnvelope:
        return telemetry.ingest_window(context, request)

    @app.get(
        "/v1/inference-telemetry/windows",
        response_model=list[InferenceTelemetryEnvelope],
    )
    def list_inference_telemetry(
        model_version_id: str | None = None,
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[InferenceTelemetryEnvelope, ...]:
        return telemetry.list_windows(context, model_version_id)

    @app.post(
        "/v1/inference-telemetry/source-status",
        response_model=InferenceTelemetrySourceStatus,
    )
    def record_inference_telemetry_source_status(
        request: InferenceTelemetrySourceStatus,
        context: RequestContext = Depends(context_dependency),
    ) -> InferenceTelemetrySourceStatus:
        return telemetry.record_source_status(context, request)

    @app.get("/v1/model-health", response_model=list[ModelHealthRecord])
    def model_health(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ModelHealthRecord, ...]:
        return telemetry.model_health(context)

    @app.get("/v1/runtime-log-availability", response_model=RuntimeLogAvailability)
    def runtime_log_availability(
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeLogAvailability:
        return product.runtime_log_availability(context)


def create_app(
    session_factory: SessionFactory,
    identity_context_provider: IdentityContextProvider | None = None,
    terminal_service: TerminalService | None = None,
    model_control_service: ModelControlService | None = None,
    trade_intelligence_service: TradeIntelligenceService | None = None,
    learning_service: LearningService | None = None,
    operational_read_service: OperationalReadService | None = None,
    product_capability_service: ProductCapabilityService | None = None,
    inference_telemetry_service: InferenceTelemetryService | None = None,
    runtime_observability_service: RuntimeObservabilityService | None = None,
) -> FastAPI:
    app = FastAPI(
        title="AI Trading Portal Control Plane",
        version="0.1.0",
    )
    service = ControlPlaneService(session_factory)
    terminal = terminal_service or TerminalService(session_factory)
    model_control = model_control_service or ModelControlService(session_factory)
    trade_intelligence = trade_intelligence_service or TradeIntelligenceService(session_factory)
    learning = learning_service or LearningService(session_factory)
    operations = operational_read_service or OperationalReadService(
        session_factory,
        intelligence_service=trade_intelligence,
    )
    product = product_capability_service or ProductCapabilityService(
        session_factory,
        model_control_service=model_control,
    )
    telemetry = inference_telemetry_service or InferenceTelemetryService(session_factory)
    runtime_observability = runtime_observability_service or RuntimeObservabilityService(
        UnavailableRuntimeObservabilitySource(checked_at=datetime.now(UTC))
    )
    context_dependency = identity_dependency(identity_context_provider)
    _register_exception_handlers(app)
    _register_terminal_route(app, terminal, context_dependency)
    _register_operational_routes(app, operations, context_dependency)
    _register_runtime_observability_routes(app, runtime_observability, context_dependency)
    _register_signal_strategy_routes(app, product, context_dependency)
    _register_platform_capability_routes(app, product, telemetry, context_dependency)

    @app.post("/v1/bots", response_model=BotInstance, status_code=status.HTTP_201_CREATED)
    def create_bot(
        request: CreateBotRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotInstance:
        return service.create_bot(context, request.bot_id, request.name, request.spec)

    @app.get("/v1/bots", response_model=list[BotInstance])
    def list_bots(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[BotInstance, ...]:
        return service.list_bots(context)

    @app.get("/v1/bots/{bot_id}", response_model=BotInstance)
    def get_bot(
        bot_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> BotInstance:
        return service.get_bot(context, bot_id)

    @app.post("/v1/bots/{bot_id}/revisions", response_model=BotInstance)
    def revise_bot(
        bot_id: str,
        request: ReviseBotRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotInstance:
        return service.revise_bot(context, bot_id, request.spec)

    @app.post("/v1/bots/{bot_id}/desired-state", response_model=BotInstance)
    def set_desired_state(
        bot_id: str,
        request: DesiredStateRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotInstance:
        return service.set_desired_state(context, bot_id, request.desired_state)

    @app.get("/v1/models", response_model=list[ModelVersion])
    def list_models(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ModelVersion, ...]:
        return model_control.list_models(context)

    @app.get("/v1/trade-analysis", response_model=list[TradeAnalysis])
    def list_trade_analysis(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[TradeAnalysis, ...]:
        return trade_intelligence.list_analyses(context)

    @app.get("/v1/insights", response_model=list[TradeInsight])
    def list_trade_insights(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[TradeInsight, ...]:
        return tuple(analysis.insight for analysis in trade_intelligence.list_analyses(context))

    @app.get("/v1/learning/history", response_model=list[LearningHistoryEntry])
    def list_learning_history(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[LearningHistoryEntry, ...]:
        return learning.history_all(context)

    return app
