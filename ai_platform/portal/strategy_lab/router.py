from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.strategy_lab.catalog import StrategyCatalogError, UnknownStrategyError
from ai_platform.portal.strategy_lab.repository import CorruptExperimentResultError
from ai_platform.portal.strategy_lab.schema import (
    EquityPoint,
    ExperimentComparison,
    ExperimentCreateRequest,
    ExperimentDetail,
    ExperimentSummary,
    PaginatedSignals,
    PaginatedTrades,
    StrategyLabDefinition,
)
from ai_platform.portal.strategy_lab.service import (
    StrategyLabConflictError,
    StrategyLabDataUnavailableError,
    StrategyLabNotFoundError,
    StrategyLabService,
)
from ai_platform.portal.strategy_lab.simulator import StrategySimulationError


def build_router(
    service: StrategyLabService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/strategy-lab", tags=["strategy-lab"])

    @router.get("/strategies", response_model=list[StrategyLabDefinition])
    def list_strategies(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[StrategyLabDefinition, ...]:
        return service.list_strategies(context)

    @router.post(
        "/experiments",
        response_model=ExperimentDetail,
        status_code=status.HTTP_201_CREATED,
    )
    def create_experiment(
        request: ExperimentCreateRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
        context: RequestContext = Depends(context_dependency),
    ) -> ExperimentDetail:
        try:
            result = service.create_experiment(
                context,
                request,
                idempotency_key=idempotency_key,
            )
            return service.experiment_detail(context, result.experiment_id)
        except UnknownStrategyError as exc:
            raise _http_error(404, "STRATEGY_LAB_UNKNOWN_STRATEGY", exc) from exc
        except StrategyLabConflictError as exc:
            raise _http_error(409, "STRATEGY_LAB_CONFLICT", exc) from exc
        except StrategyLabDataUnavailableError as exc:
            raise _http_error(503, "STRATEGY_LAB_DATA_UNAVAILABLE", exc) from exc
        except (StrategyCatalogError, StrategySimulationError) as exc:
            raise _http_error(422, "STRATEGY_LAB_INVALID_REQUEST", exc) from exc

    @router.get("/experiments", response_model=list[ExperimentSummary])
    def list_experiments(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ExperimentSummary, ...]:
        return service.list_experiments(context, offset=offset, limit=limit)

    @router.get("/experiments/compare", response_model=ExperimentComparison)
    def compare_experiments(
        baseline_id: UUID,
        variant_id: UUID,
        context: RequestContext = Depends(context_dependency),
    ) -> ExperimentComparison:
        return _not_found(lambda: service.compare(context, baseline_id, variant_id))

    @router.get("/experiments/{experiment_id}", response_model=ExperimentDetail)
    def get_experiment(
        experiment_id: UUID,
        context: RequestContext = Depends(context_dependency),
    ) -> ExperimentDetail:
        return _not_found(lambda: service.experiment_detail(context, experiment_id))

    @router.get("/experiments/{experiment_id}/trades", response_model=PaginatedTrades)
    def get_trades(
        experiment_id: UUID,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
        context: RequestContext = Depends(context_dependency),
    ) -> PaginatedTrades:
        return _not_found(
            lambda: service.trades(context, experiment_id, offset=offset, limit=limit)
        )

    @router.get("/experiments/{experiment_id}/equity", response_model=list[EquityPoint])
    def get_equity(
        experiment_id: UUID,
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[EquityPoint, ...]:
        return _not_found(lambda: service.equity_curve(context, experiment_id))

    @router.get("/experiments/{experiment_id}/signals", response_model=PaginatedSignals)
    def get_signals(
        experiment_id: UUID,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
        context: RequestContext = Depends(context_dependency),
    ) -> PaginatedSignals:
        return _not_found(
            lambda: service.signals(context, experiment_id, offset=offset, limit=limit)
        )

    return router


T = TypeVar("T")


def _not_found(callback: Callable[[], T]) -> T:
    try:
        return callback()
    except StrategyLabNotFoundError as exc:
        raise _http_error(404, "STRATEGY_LAB_EXPERIMENT_NOT_FOUND", exc) from exc
    except StrategyLabConflictError as exc:
        raise _http_error(409, "STRATEGY_LAB_CONFLICT", exc) from exc
    except CorruptExperimentResultError as exc:
        raise _http_error(500, "STRATEGY_LAB_CORRUPT_RESULT", exc) from exc


def _http_error(status_code: int, reason_code: str, exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"reason_code": reason_code, "message": str(exc)},
    )
