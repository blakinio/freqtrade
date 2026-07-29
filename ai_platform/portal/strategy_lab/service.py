from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.security.authorization import require_permission
from ai_platform.portal.strategy_lab.catalog import StrategyLabCatalog
from ai_platform.portal.strategy_lab.repository import StrategyLabRepository
from ai_platform.portal.strategy_lab.schema import (
    Candle,
    EquityPoint,
    ExperimentComparison,
    ExperimentCreateRequest,
    ExperimentDetail,
    ExperimentResult,
    ExperimentSummary,
    PaginatedSignals,
    PaginatedTrades,
    StrategyLabDefinition,
)
from ai_platform.portal.strategy_lab.simulator import DeterministicStrategySimulator


FINAL_HOLDOUT_START = datetime(2026, 8, 1, tzinfo=UTC)
FINAL_HOLDOUT_END = datetime(2026, 10, 1, tzinfo=UTC)
MAX_CANDLES = 5_000
MAX_EQUITY_POINTS = 2_000


class StrategyLabNotFoundError(LookupError):
    pass


class StrategyLabConflictError(RuntimeError):
    pass


class StrategyLabDataUnavailableError(RuntimeError):
    pass


class CandleDataProvider(Protocol):
    def load(self, request: ExperimentCreateRequest) -> tuple[Candle, ...]: ...


class UnavailableCandleDataProvider:
    def load(self, request: ExperimentCreateRequest) -> tuple[Candle, ...]:
        raise StrategyLabDataUnavailableError(
            "strategy lab candle data provider is not configured"
        )


class InMemoryCandleDataProvider:
    def __init__(self, datasets: Mapping[tuple[str, str], tuple[Candle, ...]]) -> None:
        self._datasets = dict(datasets)

    def load(self, request: ExperimentCreateRequest) -> tuple[Candle, ...]:
        candles = self._datasets.get((request.pair, request.timeframe), ())
        return tuple(
            candle
            for candle in candles
            if request.timerange.start_at <= candle.timestamp <= request.timerange.end_at
        )


class RepositoryJsonCandleDataProvider:
    _SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @classmethod
    def from_environment(cls) -> CandleDataProvider:
        value = os.environ.get("STRATEGY_LAB_DATA_ROOT")
        if value:
            return cls(Path(value))
        repository_root = Path(__file__).resolve().parents[3]
        return cls(repository_root / "ai_platform" / "research" / "strategy_lab" / "data")

    def load(self, request: ExperimentCreateRequest) -> tuple[Candle, ...]:
        pair_key = request.pair.replace("/", "_").replace(":", "_")
        if not self._SAFE_COMPONENT.fullmatch(pair_key) or not self._SAFE_COMPONENT.fullmatch(
            request.timeframe
        ):
            raise StrategyLabDataUnavailableError("invalid candle dataset identity")
        path = (self._root / f"{pair_key}-{request.timeframe}.json").resolve()
        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise StrategyLabDataUnavailableError("candle dataset path escapes root") from exc
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            candles = tuple(Candle.model_validate(item) for item in payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise StrategyLabDataUnavailableError(f"unable to load candle dataset: {path}") from exc
        return tuple(
            candle
            for candle in candles
            if request.timerange.start_at <= candle.timestamp <= request.timerange.end_at
        )


Clock = Callable[[], datetime]


class StrategyLabService:
    def __init__(
        self,
        session_factory: SessionFactory,
        *,
        data_provider: CandleDataProvider | None = None,
        catalog: StrategyLabCatalog | None = None,
        repository: StrategyLabRepository | None = None,
        simulator: DeterministicStrategySimulator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._data_provider = data_provider or RepositoryJsonCandleDataProvider.from_environment()
        self._catalog = catalog or StrategyLabCatalog()
        self._repository = repository or StrategyLabRepository()
        self._simulator = simulator or DeterministicStrategySimulator()
        self._clock = clock or (lambda: datetime.now(UTC))

    def list_strategies(self, context: RequestContext) -> tuple[StrategyLabDefinition, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        return self._catalog.list()

    def create_experiment(
        self,
        context: RequestContext,
        request: ExperimentCreateRequest,
        *,
        idempotency_key: str,
    ) -> ExperimentResult:
        require_permission(context.permissions, Permission.MODEL_TRAIN)
        key = idempotency_key.strip()
        if not 1 <= len(key) <= 128:
            raise ValueError("idempotency key must contain 1 to 128 characters")
        self._validate_timerange(request)
        request_digest = hashlib.sha256(request.canonical_json().encode("utf-8")).hexdigest()
        with self._session_factory() as session:
            existing = self._repository.get_by_idempotency(session, context.tenant_id, key)
        if existing is not None:
            result, existing_digest = existing
            if existing_digest != request_digest:
                raise StrategyLabConflictError(
                    "idempotency key was already used for a different experiment request"
                )
            return result

        definition = self._catalog.get(request.strategy_id, request.strategy_version)
        parameters = self._catalog.resolve_parameters(definition, request.parameter_overrides)
        candles = self._data_provider.load(request)
        if len(candles) > MAX_CANDLES:
            raise ValueError(f"experiment candle count exceeds limit {MAX_CANDLES}")
        started_at = self._clock()
        experiment_id = uuid5(
            NAMESPACE_URL,
            f"strategy-lab:{context.tenant_id}:{key}:{request_digest}",
        )
        result = self._simulator.run(
            experiment_id=experiment_id,
            tenant_id=context.tenant_id,
            request=request,
            definition=definition,
            parameters=parameters,
            candles=candles,
            started_at=started_at,
            finished_at=self._clock(),
        )
        try:
            with self._session_factory() as session, session.begin():
                self._repository.add(
                    session,
                    result,
                    idempotency_key=key,
                    request_digest=request_digest,
                )
        except IntegrityError:
            with self._session_factory() as session:
                concurrent = self._repository.get_by_idempotency(
                    session, context.tenant_id, key
                )
            if concurrent is None:
                raise
            concurrent_result, concurrent_digest = concurrent
            if concurrent_digest != request_digest:
                raise StrategyLabConflictError(
                    "idempotency key was concurrently used for a different request"
                )
            return concurrent_result
        return result

    def list_experiments(
        self,
        context: RequestContext,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[ExperimentSummary, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        if offset < 0 or not 1 <= limit <= 200:
            raise ValueError("invalid experiment pagination")
        with self._session_factory() as session:
            return self._repository.list(
                session,
                context.tenant_id,
                offset=offset,
                limit=limit,
            )

    def get_experiment(
        self, context: RequestContext, experiment_id: UUID | str
    ) -> ExperimentResult:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            result = self._repository.get(session, context.tenant_id, str(experiment_id))
        if result is None:
            raise StrategyLabNotFoundError("strategy lab experiment not found")
        return result

    def experiment_detail(
        self, context: RequestContext, experiment_id: UUID | str
    ) -> ExperimentDetail:
        result = self.get_experiment(context, experiment_id)
        return ExperimentDetail.model_validate(
            result.model_dump(exclude={"equity_curve", "trades", "signal_explanations"})
        )

    def trades(
        self,
        context: RequestContext,
        experiment_id: UUID | str,
        *,
        offset: int,
        limit: int,
    ) -> PaginatedTrades:
        if offset < 0 or not 1 <= limit <= 200:
            raise ValueError("invalid trade pagination")
        result = self.get_experiment(context, experiment_id)
        return PaginatedTrades(
            items=result.trades[offset : offset + limit],
            offset=offset,
            limit=limit,
            total=len(result.trades),
        )

    def signals(
        self,
        context: RequestContext,
        experiment_id: UUID | str,
        *,
        offset: int,
        limit: int,
    ) -> PaginatedSignals:
        if offset < 0 or not 1 <= limit <= 500:
            raise ValueError("invalid signal pagination")
        result = self.get_experiment(context, experiment_id)
        return PaginatedSignals(
            items=result.signal_explanations[offset : offset + limit],
            offset=offset,
            limit=limit,
            total=len(result.signal_explanations),
        )

    def equity_curve(
        self, context: RequestContext, experiment_id: UUID | str
    ) -> tuple[EquityPoint, ...]:
        result = self.get_experiment(context, experiment_id)
        points = result.equity_curve
        if len(points) <= MAX_EQUITY_POINTS:
            return points
        step = max(1, len(points) // MAX_EQUITY_POINTS)
        bounded = points[::step]
        if bounded[-1] != points[-1]:
            bounded = (*bounded, points[-1])
        return tuple(bounded[:MAX_EQUITY_POINTS])

    def compare(
        self,
        context: RequestContext,
        baseline_experiment_id: UUID | str,
        variant_experiment_id: UUID | str,
    ) -> ExperimentComparison:
        baseline = self.get_experiment(context, baseline_experiment_id)
        variant = self.get_experiment(context, variant_experiment_id)
        comparable_identity = (
            baseline.strategy_id,
            baseline.strategy_version,
            baseline.pair,
            baseline.timeframe,
            baseline.timerange,
        )
        variant_identity = (
            variant.strategy_id,
            variant.strategy_version,
            variant.pair,
            variant.timeframe,
            variant.timerange,
        )
        if comparable_identity != variant_identity:
            raise StrategyLabConflictError(
                "experiments must share strategy, pair, timeframe and timerange"
            )
        names = sorted(set(baseline.parameters) | set(variant.parameters))
        parameter_differences = {
            name: (baseline.parameters.get(name), variant.parameters.get(name))
            for name in names
            if baseline.parameters.get(name) != variant.parameters.get(name)
        }
        return ExperimentComparison(
            baseline_experiment_id=baseline.experiment_id,
            variant_experiment_id=variant.experiment_id,
            metric_deltas={
                "trade_count": Decimal(variant.trade_count - baseline.trade_count),
                "win_rate": variant.win_rate - baseline.win_rate,
                "profit_abs": variant.profit_abs - baseline.profit_abs,
                "profit_pct": variant.profit_pct - baseline.profit_pct,
                "max_drawdown": variant.max_drawdown - baseline.max_drawdown,
                "average_trade": variant.average_trade - baseline.average_trade,
                "exposure": variant.exposure - baseline.exposure,
            },
            parameter_differences=parameter_differences,
        )

    @staticmethod
    def _validate_timerange(request: ExperimentCreateRequest) -> None:
        start = request.timerange.start_at
        end = request.timerange.end_at
        if start < FINAL_HOLDOUT_END and end > FINAL_HOLDOUT_START:
            raise StrategyLabConflictError(
                "experiment timerange overlaps protected final holdout v2"
            )
