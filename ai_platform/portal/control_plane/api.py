from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ai_platform.portal.contracts.bots import BotDesiredState, BotInstance, BotSpec
from ai_platform.portal.contracts.risk import TradeSide
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
from ai_platform.portal.risk.service import RiskConflictError, RiskPolicyNotFoundError
from ai_platform.portal.risk.terminal import (
    RiskSnapshotUnavailableError,
    TerminalIntentResult,
    TerminalService,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


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


def create_app(
    session_factory: SessionFactory,
    identity_context_provider: IdentityContextProvider | None = None,
    terminal_service: TerminalService | None = None,
) -> FastAPI:
    app = FastAPI(
        title="AI Trading Portal Control Plane",
        version="0.1.0",
    )
    service = ControlPlaneService(session_factory)
    terminal = terminal_service or TerminalService(session_factory)
    context_dependency = identity_dependency(identity_context_provider)
    _register_exception_handlers(app)
    _register_terminal_route(app, terminal, context_dependency)

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

    return app
