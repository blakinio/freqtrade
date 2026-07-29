from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import update

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import Base, build_engine, build_session_factory
from ai_platform.portal.strategy_lab.catalog import (
    StrategyCatalogError,
    StrategyLabCatalog,
    UnknownStrategyError,
)
from ai_platform.portal.strategy_lab.models import StrategyLabExperimentRow
from ai_platform.portal.strategy_lab.repository import CorruptExperimentResultError
from ai_platform.portal.strategy_lab.router import build_router
from ai_platform.portal.strategy_lab.schema import (
    Candle,
    ExperimentCreateRequest,
    ExperimentTimerange,
)
from ai_platform.portal.strategy_lab.service import (
    InMemoryCandleDataProvider,
    StrategyLabConflictError,
    StrategyLabNotFoundError,
    StrategyLabService,
)
from ai_platform.portal.strategy_lab.simulator import (
    DeterministicStrategySimulator,
    MissingMarketDataError,
    TimeIntegrityError,
)


def _context(tenant_id: str = "tenant-a", *, train: bool = True) -> RequestContext:
    permissions = [Permission.MODEL_READ]
    if train:
        permissions.append(Permission.MODEL_TRAIN)
    return RequestContext(
        tenant_id=tenant_id,
        actor_id="analyst-1",
        actor_type=ActorType.USER,
        permissions=tuple(permissions),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _candles() -> tuple[Candle, ...]:
    closes = (
        [100] * 5
        + [99, 98, 97, 96, 95, 94, 93, 92, 91, 90]
        + [92, 94, 96, 98, 100, 102, 104, 106, 108, 110, 112, 114]
        + [112, 110, 108, 106, 104, 102, 100, 98, 96, 94, 92, 90]
    )
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    result: list[Candle] = []
    previous = Decimal(str(closes[0]))
    for index, raw_close in enumerate(closes):
        close = Decimal(str(raw_close))
        result.append(
            Candle(
                timestamp=timestamp + timedelta(minutes=15 * index),
                pair="BTC/USDT",
                timeframe="15m",
                open=previous,
                high=max(previous, close) + Decimal(1),
                low=min(previous, close) - Decimal(1),
                close=close,
                volume=Decimal(10),
                data_version=hashlib.sha256(f"candle-{index}".encode()).hexdigest(),
            )
        )
        previous = close
    return tuple(result)


def _request(candles: tuple[Candle, ...], **overrides: object) -> ExperimentCreateRequest:
    payload = {
        "strategy_id": "tv_supertrend_v1",
        "strategy_version": "1.0.0",
        "pair": "BTC/USDT",
        "timeframe": "15m",
        "timerange": ExperimentTimerange(
            start_at=candles[0].timestamp,
            end_at=candles[-1].timestamp,
        ),
        "starting_balance": Decimal(10000),
        "fee_rate": Decimal("0.001"),
        "slippage_rate": Decimal(0),
        "parameter_overrides": {"atr_period": 3, "multiplier": 1.5},
    }
    payload.update(overrides)
    return ExperimentCreateRequest.model_validate(payload)


def _service(candles: tuple[Candle, ...]) -> tuple[StrategyLabService, object]:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    clock_values = iter(
        (
            datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
            datetime(2026, 1, 2, 0, 0, 1, tzinfo=UTC),
        )
        * 20
    )
    service = StrategyLabService(
        factory,
        data_provider=InMemoryCandleDataProvider({("BTC/USDT", "15m"): candles}),
        clock=lambda: next(clock_values),
    )
    return service, factory


def test_catalog_contains_two_versioned_clean_room_strategies() -> None:
    definitions = StrategyLabCatalog().list()
    assert [(item.strategy_id, item.strategy_version) for item in definitions] == [
        ("tv_squeeze_momentum_v1", "1.0.0"),
        ("tv_supertrend_v1", "1.0.0"),
    ]
    assert {item.features[0] for item in definitions} == {
        "squeeze_ratio.v1",
        "supertrend_direction.v1",
    }
    assert all(item.provenance["parity_claim"] is False for item in definitions)
    assert all(item.risk_defaults["research_only"] is True for item in definitions)


def test_parameter_boundaries_and_unknown_strategy_fail_closed() -> None:
    catalog = StrategyLabCatalog()
    definition = catalog.get("tv_supertrend_v1", "1.0.0")
    assert catalog.resolve_parameters(definition, {"atr_period": 2})["atr_period"] == 2
    assert catalog.resolve_parameters(definition, {"atr_period": 100})["atr_period"] == 100
    with pytest.raises(StrategyCatalogError, match="below minimum"):
        catalog.resolve_parameters(definition, {"atr_period": 1})
    with pytest.raises(StrategyCatalogError, match="above maximum"):
        catalog.resolve_parameters(definition, {"multiplier": 11})
    with pytest.raises(UnknownStrategyError):
        catalog.get("unknown", "1.0.0")


def test_squeeze_strategy_parameters_and_replay_are_deterministic() -> None:
    candles = _candles()
    catalog = StrategyLabCatalog()
    definition = catalog.get("tv_squeeze_momentum_v1", "1.0.0")
    parameters = catalog.resolve_parameters(
        definition,
        {"bb_length": 5, "kc_length": 100, "bb_mult": 0.5, "kc_mult": 4},
    )
    request = _request(
        candles,
        strategy_id=definition.strategy_id,
        strategy_version=definition.strategy_version,
        parameter_overrides=parameters,
    )
    simulator = DeterministicStrategySimulator()
    kwargs = {
        "experiment_id": UUID(int=9),
        "tenant_id": "tenant-a",
        "request": request,
        "definition": definition,
        "parameters": parameters,
        "candles": candles,
        "started_at": datetime(2026, 1, 2, tzinfo=UTC),
        "finished_at": datetime(2026, 1, 2, 0, 0, 1, tzinfo=UTC),
    }
    assert simulator.run(**kwargs) == simulator.run(**kwargs)
    with pytest.raises(StrategyCatalogError, match="below minimum"):
        catalog.resolve_parameters(definition, {"bb_mult": 0.4})


def test_simulator_is_deterministic_and_has_no_lookahead() -> None:
    candles = _candles()
    catalog = StrategyLabCatalog()
    definition = catalog.get("tv_supertrend_v1", "1.0.0")
    request = _request(candles)
    parameters = catalog.resolve_parameters(definition, request.parameter_overrides)
    simulator = DeterministicStrategySimulator()
    kwargs = {
        "experiment_id": UUID(int=1),
        "tenant_id": "tenant-a",
        "request": request,
        "definition": definition,
        "parameters": parameters,
        "candles": candles,
        "started_at": datetime(2026, 1, 2, tzinfo=UTC),
        "finished_at": datetime(2026, 1, 2, 0, 0, 1, tzinfo=UTC),
    }
    first = simulator.run(**kwargs)
    assert first == simulator.run(**kwargs)
    assert first.trade_count == 1
    assert first.order_submission_performed is False

    prefix = candles[:25]
    prefix_result = simulator.run(
        **{**kwargs, "request": _request(prefix), "candles": prefix}
    )
    prefix_non_forced = tuple(
        signal.signal_id
        for signal in prefix_result.signal_explanations
        if "LAB_EXIT_TIMERANGE_END" not in signal.reason_codes
    )
    full_before_cutoff = tuple(
        signal.signal_id
        for signal in first.signal_explanations
        if signal.timestamp <= prefix[-1].timestamp
    )
    assert prefix_non_forced == full_before_cutoff


@pytest.mark.parametrize("field", ["is_closed", "is_confirmed"])
def test_unavailable_candles_are_rejected(field: str) -> None:
    candles = list(_candles())
    candles[-1] = candles[-1].model_copy(update={field: False})
    definition = StrategyLabCatalog().get("tv_supertrend_v1", "1.0.0")
    request = _request(tuple(candles))
    parameters = StrategyLabCatalog().resolve_parameters(definition, request.parameter_overrides)
    with pytest.raises(TimeIntegrityError):
        DeterministicStrategySimulator().run(
            experiment_id=UUID(int=2),
            tenant_id="tenant-a",
            request=request,
            definition=definition,
            parameters=parameters,
            candles=tuple(candles),
            started_at=datetime(2026, 1, 2, tzinfo=UTC),
            finished_at=datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_missing_data_and_live_execution_attempt_are_rejected() -> None:
    candles = _candles()
    request = _request(candles)
    definition = StrategyLabCatalog().get("tv_supertrend_v1", "1.0.0")
    parameters = StrategyLabCatalog().resolve_parameters(definition, request.parameter_overrides)
    with pytest.raises(MissingMarketDataError):
        DeterministicStrategySimulator().run(
            experiment_id=UUID(int=3),
            tenant_id="tenant-a",
            request=request,
            definition=definition,
            parameters=parameters,
            candles=(),
            started_at=datetime(2026, 1, 2, tzinfo=UTC),
            finished_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    with pytest.raises(ValidationError):
        ExperimentCreateRequest.model_validate(
            {**request.model_dump(), "execution_mode": "live"}
        )


def test_service_persists_idempotently_and_isolates_tenants() -> None:
    candles = _candles()
    service, _factory = _service(candles)
    request = _request(candles)
    first = service.create_experiment(_context(), request, idempotency_key="request-1")
    replay = service.create_experiment(_context(), request, idempotency_key="request-1")
    assert replay.experiment_id == first.experiment_id
    assert service.experiment_detail(_context(), first.experiment_id).trade_count == 1
    assert service.trades(_context(), first.experiment_id, offset=0, limit=10).total == 1
    assert service.signals(_context(), first.experiment_id, offset=0, limit=20).total >= 2
    assert service.equity_curve(_context(), first.experiment_id)
    with pytest.raises(StrategyLabConflictError):
        service.create_experiment(
            _context(),
            request.model_copy(update={"starting_balance": Decimal(9000)}),
            idempotency_key="request-1",
        )
    tenant_b = service.create_experiment(
        _context("tenant-b"), request, idempotency_key="request-1"
    )
    assert tenant_b.experiment_id != first.experiment_id
    assert (
        service.get_experiment(_context("tenant-b"), tenant_b.experiment_id).tenant_id
        == "tenant-b"
    )
    with pytest.raises(StrategyLabNotFoundError):
        service.get_experiment(_context("tenant-b"), first.experiment_id)


def test_read_and_create_permissions_are_enforced() -> None:
    candles = _candles()
    service, _factory = _service(candles)
    with pytest.raises(PermissionError):
        service.create_experiment(
            _context(train=False), _request(candles), idempotency_key="no-train"
        )
    context = _context()
    result = service.create_experiment(context, _request(candles), idempotency_key="read")
    denied = context.model_copy(update={"permissions": ()})
    with pytest.raises(PermissionError):
        service.get_experiment(denied, result.experiment_id)


def test_protected_holdout_and_corrupt_result_fail_closed() -> None:
    candles = _candles()
    service, factory = _service(candles)
    protected = _request(candles).model_copy(
        update={
            "timerange": ExperimentTimerange(
                start_at=datetime(2026, 8, 1, tzinfo=UTC),
                end_at=datetime(2026, 8, 2, tzinfo=UTC),
            )
        }
    )
    with pytest.raises(StrategyLabConflictError, match="protected final holdout"):
        service.create_experiment(_context(), protected, idempotency_key="holdout")

    result = service.create_experiment(_context(), _request(candles), idempotency_key="corrupt")
    with factory() as session, session.begin():
        session.execute(
            update(StrategyLabExperimentRow)
            .where(StrategyLabExperimentRow.experiment_id == str(result.experiment_id))
            .values(experiment_json="{}")
        )
    with pytest.raises(CorruptExperimentResultError):
        service.get_experiment(_context(), result.experiment_id)


def test_api_full_vertical_slice_and_comparison() -> None:
    candles = _candles()
    service, _factory = _service(candles)
    context = _context()
    app = FastAPI()
    app.include_router(build_router(service, lambda: context))
    client = TestClient(app)

    catalog = client.get("/v1/strategy-lab/strategies")
    assert catalog.status_code == 200
    assert {item["strategy_id"] for item in catalog.json()} == {
        "tv_supertrend_v1",
        "tv_squeeze_momentum_v1",
    }

    payload = _request(candles).model_dump(mode="json")
    baseline = client.post(
        "/v1/strategy-lab/experiments",
        json=payload,
        headers={"Idempotency-Key": "api-baseline"},
    )
    assert baseline.status_code == 201
    baseline_id = baseline.json()["experiment_id"]
    variant = client.post(
        "/v1/strategy-lab/experiments",
        json={
            **payload,
            "parameter_overrides": {"atr_period": 4, "multiplier": 1.2},
        },
        headers={"Idempotency-Key": "api-variant"},
    )
    assert variant.status_code == 201
    variant_id = variant.json()["experiment_id"]

    assert client.get("/v1/strategy-lab/experiments").json()[0]["status"] == "COMPLETED"
    assert client.get(f"/v1/strategy-lab/experiments/{baseline_id}").json()["trade_count"] == 1
    assert client.get(f"/v1/strategy-lab/experiments/{baseline_id}/trades").json()["total"] == 1
    assert client.get(f"/v1/strategy-lab/experiments/{baseline_id}/signals").json()["total"] >= 2
    assert client.get(f"/v1/strategy-lab/experiments/{baseline_id}/equity").json()
    comparison = client.get(
        "/v1/strategy-lab/experiments/compare",
        params={"baseline_id": baseline_id, "variant_id": variant_id},
    )
    assert comparison.status_code == 200
    assert "atr_period" in comparison.json()["parameter_differences"]


def test_control_plane_app_exposes_strategy_lab_router() -> None:
    candles = _candles()
    service, factory = _service(candles)
    context = _context()
    client = TestClient(
        create_app(factory, lambda: context, strategy_lab_service=service)
    )

    response = client.get("/v1/strategy-lab/strategies")

    assert response.status_code == 200
    assert response.json()[0]["strategy_id"] == "tv_squeeze_momentum_v1"
