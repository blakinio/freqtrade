from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


write(
    "ai_platform/portal/valuation/__init__.py",
    '''from ai_platform.portal.valuation.runtime import (
    HttpPrivateRuntimeValuationSource,
    RuntimePositionMark,
    RuntimeValuationSourceResult,
    UnavailableRuntimeValuationSource,
    ValuationService,
    ValuationSnapshot,
    ValuationState,
)

__all__ = [
    "HttpPrivateRuntimeValuationSource",
    "RuntimePositionMark",
    "RuntimeValuationSourceResult",
    "UnavailableRuntimeValuationSource",
    "ValuationService",
    "ValuationSnapshot",
    "ValuationState",
]
''',
)

write(
    "ai_platform/portal/valuation/runtime.py",
    '''from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from pydantic import PositiveInt

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import OperationalPosition
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys


Clock = Callable[[], datetime]
EndpointResolver = Callable[[str], str]
AuthorizationHeaderProvider = Callable[[str], Mapping[str, str]]


class ValuationState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    UNPRICED = "UNPRICED"


class RuntimeValuationRequest(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    timeout_seconds: PositiveInt = 5


class RuntimePositionMark(ContractModel):
    schema_version: Literal[1] = 1
    source_position_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    base_currency: NonEmptyStr
    quote_currency: NonEmptyStr
    entry_rate: Decimal
    mark_rate: Decimal
    leverage: Decimal = Decimal("1")
    source_price_id: NonEmptyStr
    source_observed_at: UtcDateTime


class RuntimeValuationSourceResult(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    observed_at: UtcDateTime
    state: ValuationState
    marks: tuple[RuntimePositionMark, ...] = ()
    reason_code: NonEmptyStr | None = None


class ValuationSnapshot(ContractModel):
    schema_version: Literal[1] = 1
    valuation_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    position_id: NonEmptyStr
    source_position_id: NonEmptyStr | None = None
    source_runtime_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    state: ValuationState
    valuation_currency: NonEmptyStr | None = None
    entry_rate: Decimal | None = None
    mark_rate: Decimal | None = None
    cost_basis: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    source_price_id: NonEmptyStr | None = None
    source_observed_at: UtcDateTime | None = None
    observed_at: UtcDateTime
    method_version: Literal["mark-to-entry-v1"] = "mark-to-entry-v1"
    reason_code: NonEmptyStr | None = None


class RuntimeValuationSource(Protocol):
    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult: ...


class UnavailableRuntimeValuationSource:
    def __init__(self, checked_at: datetime, reason_code: str = "VALUATION_SOURCE_NOT_CONFIGURED") -> None:
        self._checked_at = checked_at
        self._reason_code = reason_code

    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult:
        return RuntimeValuationSourceResult(
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            source_runtime_id=request.source_runtime_id,
            observed_at=self._checked_at,
            state=ValuationState.SOURCE_UNAVAILABLE,
            reason_code=self._reason_code,
        )


class _HttpResponse(Protocol):
    def __enter__(self) -> _HttpResponse: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def read(self, amount: int = -1) -> bytes: ...


HttpOpener = Callable[..., _HttpResponse]


class HttpPrivateRuntimeValuationSource:
    """Bounded server-side client for the private normalized Freqtrade mark source."""

    def __init__(
        self,
        endpoint_resolver: EndpointResolver,
        authorization_headers: AuthorizationHeaderProvider,
        *,
        opener: HttpOpener = urlopen,
        max_body_bytes: int = 1_048_576,
        clock: Clock | None = None,
    ) -> None:
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._endpoint_resolver = endpoint_resolver
        self._authorization_headers = authorization_headers
        self._opener = opener
        self._max_body_bytes = max_body_bytes
        self._clock = clock or (lambda: datetime.now(UTC))

    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult:
        endpoint = self._validated_endpoint(self._endpoint_resolver(request.source_runtime_id))
        http_request = self._request(endpoint, request)
        try:
            body = self._read_body(http_request, request.timeout_seconds)
            result = self._decode(body)
        except TimeoutError:
            return self._unavailable(request, "VALUATION_SOURCE_TIMEOUT")
        except URLError:
            return self._unavailable(request, "VALUATION_SOURCE_UNAVAILABLE")
        except HTTPError as exc:
            reason_code = (
                "VALUATION_SOURCE_AUTHENTICATION_FAILED"
                if exc.code in {401, 403}
                else "VALUATION_SOURCE_UNAVAILABLE"
            )
            return self._unavailable(request, reason_code)
        except ValueError:
            return self._unavailable(request, "VALUATION_SOURCE_PROTOCOL_ERROR")

        if (
            result.tenant_id != request.tenant_id
            or result.bot_id != request.bot_id
            or result.source_runtime_id != request.source_runtime_id
        ):
            raise PermissionDeniedError("valuation source scope mismatch")
        return result

    @staticmethod
    def _validated_endpoint(endpoint: str) -> str:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("invalid private valuation endpoint")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("private valuation endpoint embeds credentials")
        return endpoint

    def _request(self, endpoint: str, request: RuntimeValuationRequest) -> Request:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **dict(self._authorization_headers(request.source_runtime_id)),
        }
        data = json.dumps(request.model_dump(mode="json"), separators=(",", ":")).encode()
        return Request(endpoint, data=data, headers=headers, method="POST")  # noqa: S310

    def _read_body(self, request: Request, timeout_seconds: int) -> bytes:
        with self._opener(request, timeout=timeout_seconds) as response:
            body = response.read(self._max_body_bytes + 1)
        if len(body) > self._max_body_bytes:
            raise ValueError("valuation response too large")
        return body

    @staticmethod
    def _decode(body: bytes) -> RuntimeValuationSourceResult:
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("invalid valuation source envelope")
        reject_sensitive_payload_keys(payload, path="runtime_valuation_source")
        return RuntimeValuationSourceResult.model_validate(payload)

    def _unavailable(
        self,
        request: RuntimeValuationRequest,
        reason_code: str,
    ) -> RuntimeValuationSourceResult:
        return RuntimeValuationSourceResult(
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            source_runtime_id=request.source_runtime_id,
            observed_at=self._clock(),
            state=ValuationState.SOURCE_UNAVAILABLE,
            reason_code=reason_code,
        )


class ValuationService:
    def __init__(
        self,
        session_factory: SessionFactory,
        source: RuntimeValuationSource,
        *,
        operational_repository: OperationalRepository | None = None,
        bot_repository: BotRepository | None = None,
        clock: Clock | None = None,
        stale_after_seconds: int = 120,
    ) -> None:
        if stale_after_seconds < 1:
            raise ValueError("stale_after_seconds must be positive")
        self._session_factory = session_factory
        self._source = source
        self._operations = operational_repository or OperationalRepository()
        self._bots = bot_repository or BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._stale_after_seconds = stale_after_seconds

    def list_valuations(self, context: RequestContext) -> tuple[ValuationSnapshot, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            positions = self._operations.list_positions(session, context.tenant_id)
            bots = {bot.bot_id: bot for bot in self._bots.list_bots(session, context.tenant_id)}

        grouped: dict[tuple[str, str], list[OperationalPosition]] = defaultdict(list)
        for position in positions:
            grouped[(position.bot_id, position.source_runtime_id)].append(position)

        snapshots: list[ValuationSnapshot] = []
        for (bot_id, runtime_id), grouped_positions in sorted(grouped.items()):
            result = self._source.fetch(
                RuntimeValuationRequest(
                    tenant_id=context.tenant_id,
                    bot_id=bot_id,
                    source_runtime_id=runtime_id,
                )
            )
            self._require_scope(context.tenant_id, bot_id, runtime_id, result)
            marks, conflicting = self._marks_by_identity(result.marks)
            bot = bots.get(bot_id)
            for position in sorted(grouped_positions, key=lambda item: item.position_id):
                snapshots.append(
                    self._value_position(
                        position,
                        bot.spec.capital_currency if bot is not None else None,
                        result,
                        marks,
                        conflicting,
                    )
                )
        return tuple(snapshots)

    @staticmethod
    def _require_scope(
        tenant_id: str,
        bot_id: str,
        runtime_id: str,
        result: RuntimeValuationSourceResult,
    ) -> None:
        if (
            result.tenant_id != tenant_id
            or result.bot_id != bot_id
            or result.source_runtime_id != runtime_id
        ):
            raise PermissionDeniedError("valuation source scope mismatch")

    @staticmethod
    def _marks_by_identity(
        marks: tuple[RuntimePositionMark, ...],
    ) -> tuple[dict[str, RuntimePositionMark], set[str]]:
        selected: dict[str, RuntimePositionMark] = {}
        conflicting: set[str] = set()
        for mark in marks:
            existing = selected.get(mark.source_position_id)
            if existing is None:
                selected[mark.source_position_id] = mark
            elif existing.canonical_json() != mark.canonical_json():
                conflicting.add(mark.source_position_id)
        return selected, conflicting

    def _value_position(
        self,
        position: OperationalPosition,
        capital_currency: str | None,
        result: RuntimeValuationSourceResult,
        marks: dict[str, RuntimePositionMark],
        conflicting: set[str],
    ) -> ValuationSnapshot:
        observed_at = self._clock()
        source_id = position.source_position_id
        if position.freshness is RuntimeReadFreshness.SOURCE_UNAVAILABLE:
            return self._empty(position, observed_at, ValuationState.SOURCE_UNAVAILABLE, position.reason_code)
        if position.freshness in {RuntimeReadFreshness.STALE, RuntimeReadFreshness.PARTIAL}:
            return self._empty(position, observed_at, ValuationState.STALE, position.reason_code)
        if position.reconciliation_status is not ReconciliationStatus.SYNCED:
            return self._empty(position, observed_at, ValuationState.UNPRICED, position.reason_code)
        if result.state is ValuationState.SOURCE_UNAVAILABLE:
            return self._empty(position, observed_at, ValuationState.SOURCE_UNAVAILABLE, result.reason_code)
        if result.state is ValuationState.STALE:
            return self._empty(position, observed_at, ValuationState.STALE, result.reason_code)
        if source_id is None:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_POSITION_ID_MISSING")
        if source_id in conflicting:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_CONFLICTING_MARKS")
        mark = marks.get(source_id)
        if mark is None:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_MARK_MISSING")
        if mark.pair != position.pair or mark.side is not position.side:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_MARK_ATTRIBUTION_MISMATCH", mark)
        if capital_currency is None:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_BOT_NOT_FOUND", mark)
        if mark.quote_currency != capital_currency:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_CURRENCY_CONVERSION_UNAVAILABLE", mark)
        if mark.leverage != Decimal("1"):
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_LEVERAGE_UNSUPPORTED", mark)
        if position.amount <= 0 or mark.entry_rate <= 0 or mark.mark_rate <= 0:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_NON_POSITIVE_INPUT", mark)
        age = (observed_at - mark.source_observed_at).total_seconds()
        if age < -5:
            return self._empty(position, observed_at, ValuationState.UNPRICED, "VALUATION_SOURCE_TIME_IN_FUTURE", mark)
        if age > self._stale_after_seconds:
            return self._empty(position, observed_at, ValuationState.STALE, "VALUATION_MARK_STALE", mark)

        cost_basis = position.amount * mark.entry_rate
        market_value = position.amount * mark.mark_rate
        unrealized = (
            market_value - cost_basis
            if position.side is TradeSide.BUY
            else cost_basis - market_value
        )
        return self._snapshot(
            position=position,
            observed_at=observed_at,
            state=ValuationState.CURRENT,
            valuation_currency=mark.quote_currency,
            mark=mark,
            cost_basis=cost_basis,
            market_value=market_value,
            unrealized_pnl=unrealized,
            reason_code=None,
        )

    def _empty(
        self,
        position: OperationalPosition,
        observed_at: datetime,
        state: ValuationState,
        reason_code: str | None,
        mark: RuntimePositionMark | None = None,
    ) -> ValuationSnapshot:
        return self._snapshot(
            position=position,
            observed_at=observed_at,
            state=state,
            valuation_currency=mark.quote_currency if mark is not None else None,
            mark=mark,
            cost_basis=None,
            market_value=None,
            unrealized_pnl=None,
            reason_code=reason_code or "VALUATION_UNAVAILABLE",
        )

    @staticmethod
    def _snapshot(
        *,
        position: OperationalPosition,
        observed_at: datetime,
        state: ValuationState,
        valuation_currency: str | None,
        mark: RuntimePositionMark | None,
        cost_basis: Decimal | None,
        market_value: Decimal | None,
        unrealized_pnl: Decimal | None,
        reason_code: str | None,
    ) -> ValuationSnapshot:
        identity = "\\0".join(
            (
                "mark-to-entry-v1",
                position.tenant_id,
                position.bot_id,
                position.position_id,
                position.source_runtime_id,
                state.value,
                mark.source_price_id if mark is not None else "none",
                mark.source_observed_at.isoformat() if mark is not None else "none",
                reason_code or "none",
            )
        )
        valuation_id = f"valuation:{hashlib.sha256(identity.encode()).hexdigest()[:32]}"
        return ValuationSnapshot(
            valuation_id=valuation_id,
            tenant_id=position.tenant_id,
            bot_id=position.bot_id,
            position_id=position.position_id,
            source_position_id=position.source_position_id,
            source_runtime_id=position.source_runtime_id,
            pair=position.pair,
            side=position.side,
            amount=position.amount,
            state=state,
            valuation_currency=valuation_currency,
            entry_rate=mark.entry_rate if mark is not None else None,
            mark_rate=mark.mark_rate if mark is not None else None,
            cost_basis=cost_basis,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            source_price_id=mark.source_price_id if mark is not None else None,
            source_observed_at=mark.source_observed_at if mark is not None else None,
            observed_at=observed_at,
            reason_code=reason_code,
        )
''',
)

replace_once(
    "ai_platform/portal/control_plane/api.py",
    "from ai_platform.portal.telemetry.service import (\n    InferenceTelemetryService,\n    TelemetryConflictError,\n)\n",
    "from ai_platform.portal.telemetry.service import (\n    InferenceTelemetryService,\n    TelemetryConflictError,\n)\nfrom ai_platform.portal.valuation.runtime import (\n    UnavailableRuntimeValuationSource,\n    ValuationService,\n    ValuationSnapshot,\n)\n",
)
replace_once(
    "ai_platform/portal/control_plane/api.py",
    "def _register_runtime_observability_routes(\n",
    '''def _register_valuation_routes(
    app: FastAPI,
    valuation: ValuationService,
    context_dependency: Callable[..., RequestContext],
) -> None:
    @app.get("/v1/valuations", response_model=list[ValuationSnapshot])
    def list_valuations(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ValuationSnapshot, ...]:
        return valuation.list_valuations(context)


def _register_runtime_observability_routes(
''',
)
replace_once(
    "ai_platform/portal/control_plane/api.py",
    "    runtime_observability_service: RuntimeObservabilityService | None = None,\n) -> FastAPI:\n",
    "    runtime_observability_service: RuntimeObservabilityService | None = None,\n    valuation_service: ValuationService | None = None,\n) -> FastAPI:\n",
)
replace_once(
    "ai_platform/portal/control_plane/api.py",
    "    runtime_observability = runtime_observability_service or RuntimeObservabilityService(\n        UnavailableRuntimeObservabilitySource(checked_at=datetime.now(UTC))\n    )\n",
    "    runtime_observability = runtime_observability_service or RuntimeObservabilityService(\n        UnavailableRuntimeObservabilitySource(checked_at=datetime.now(UTC))\n    )\n    valuation = valuation_service or ValuationService(\n        session_factory,\n        UnavailableRuntimeValuationSource(checked_at=datetime.now(UTC)),\n    )\n",
)
replace_once(
    "ai_platform/portal/control_plane/api.py",
    "    _register_operational_routes(app, operations, context_dependency)\n    _register_runtime_observability_routes(app, runtime_observability, context_dependency)\n",
    "    _register_operational_routes(app, operations, context_dependency)\n    _register_valuation_routes(app, valuation, context_dependency)\n    _register_runtime_observability_routes(app, runtime_observability, context_dependency)\n",
)

replace_once(
    "tests/ai_platform/portal/control_plane/test_api.py",
    '        "/v1/performance",\n',
    '        "/v1/performance",\n        "/v1/valuations",\n',
)

write(
    "tests/ai_platform/portal/valuation/test_runtime.py",
    '''from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory, create_schema
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import OperationalPosition
from ai_platform.portal.security.authorization import PermissionDeniedError
from ai_platform.portal.valuation.runtime import (
    RuntimePositionMark,
    RuntimeValuationRequest,
    RuntimeValuationSourceResult,
    UnavailableRuntimeValuationSource,
    ValuationService,
    ValuationState,
)


NOW = datetime(2026, 7, 24, 18, 0, tzinfo=UTC)


def _context(tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.SERVICE,
        permissions=(Permission.BOT_READ,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _seed(factory, *, side: TradeSide = TradeSide.BUY, currency: str = "USDT") -> None:
    create_context = _context()
    create_context = create_context.model_copy(update={"permissions": (Permission.BOT_CREATE, Permission.BOT_READ)})
    ControlPlaneService(factory).create_bot(
        create_context,
        "bot-1",
        "Valuation bot",
        BotSpec(
            tenant_id="tenant-a",
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency=currency,
            runtime_version="runtime-v1",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
    )
    position = OperationalPosition(
        tenant_id="tenant-a",
        bot_id="bot-1",
        source_runtime_id="runtime-1",
        position_id="position-1",
        source_position_id="source-position-1",
        pair="BTC/USDT",
        side=side,
        amount=Decimal("2"),
        opened_at=NOW - timedelta(hours=1),
        source_updated_at=NOW,
        observed_at=NOW,
        last_reconciled_at=NOW,
        freshness=RuntimeReadFreshness.CURRENT,
        reconciliation_status=ReconciliationStatus.SYNCED,
    )
    with factory() as session, session.begin():
        OperationalRepository().upsert_position(session, position)


class _Source:
    def __init__(self, result: RuntimeValuationSourceResult) -> None:
        self.result = result
        self.requests: list[RuntimeValuationRequest] = []

    def fetch(self, request: RuntimeValuationRequest) -> RuntimeValuationSourceResult:
        self.requests.append(request)
        return self.result


def _mark(*, rate: str = "110", leverage: str = "1", quote: str = "USDT", side=TradeSide.BUY):
    return RuntimePositionMark(
        source_position_id="source-position-1",
        pair="BTC/USDT",
        side=side,
        base_currency="BTC",
        quote_currency=quote,
        entry_rate=Decimal("100"),
        mark_rate=Decimal(rate),
        leverage=Decimal(leverage),
        source_price_id="freqtrade:runtime-1:BTC-USDT:1",
        source_observed_at=NOW,
    )


def _result(*marks: RuntimePositionMark, state: ValuationState = ValuationState.CURRENT):
    return RuntimeValuationSourceResult(
        tenant_id="tenant-a",
        bot_id="bot-1",
        source_runtime_id="runtime-1",
        observed_at=NOW,
        state=state,
        marks=marks,
        reason_code=None if state is ValuationState.CURRENT else "VALUATION_SOURCE_UNAVAILABLE",
    )


def test_current_long_and_short_mark_to_entry_are_deterministic() -> None:
    factory = _factory()
    _seed(factory)
    service = ValuationService(factory, _Source(_result(_mark())), clock=lambda: NOW)

    long_value = service.list_valuations(_context())[0]

    assert long_value.state is ValuationState.CURRENT
    assert long_value.cost_basis == Decimal("200")
    assert long_value.market_value == Decimal("220")
    assert long_value.unrealized_pnl == Decimal("20")
    assert long_value.valuation_currency == "USDT"
    assert long_value.source_price_id == "freqtrade:runtime-1:BTC-USDT:1"

    short_factory = _factory()
    _seed(short_factory, side=TradeSide.SELL)
    short = ValuationService(
        short_factory,
        _Source(_result(_mark(rate="90", side=TradeSide.SELL))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert short.unrealized_pnl == Decimal("20")
    assert short.method_version == "mark-to-entry-v1"


def test_stale_cross_currency_and_leverage_never_produce_numeric_current_value() -> None:
    factory = _factory()
    _seed(factory)
    stale_mark = _mark().model_copy(update={"source_observed_at": NOW - timedelta(minutes=3)})
    stale = ValuationService(
        factory,
        _Source(_result(stale_mark)),
        clock=lambda: NOW,
        stale_after_seconds=120,
    ).list_valuations(_context())[0]
    assert stale.state is ValuationState.STALE
    assert stale.unrealized_pnl is None

    cross = ValuationService(
        factory,
        _Source(_result(_mark(quote="EUR"))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert cross.state is ValuationState.UNPRICED
    assert cross.reason_code == "VALUATION_CURRENCY_CONVERSION_UNAVAILABLE"
    assert cross.market_value is None

    leveraged = ValuationService(
        factory,
        _Source(_result(_mark(leverage="2"))),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert leveraged.state is ValuationState.UNPRICED
    assert leveraged.reason_code == "VALUATION_LEVERAGE_UNSUPPORTED"


def test_unconfigured_source_and_cross_tenant_scope_fail_closed() -> None:
    factory = _factory()
    _seed(factory)
    unavailable = ValuationService(
        factory,
        UnavailableRuntimeValuationSource(NOW),
        clock=lambda: NOW,
    ).list_valuations(_context())[0]
    assert unavailable.state is ValuationState.SOURCE_UNAVAILABLE
    assert unavailable.unrealized_pnl is None

    mismatched = _result(_mark()).model_copy(update={"tenant_id": "tenant-b"})
    with pytest.raises(PermissionDeniedError):
        ValuationService(factory, _Source(mismatched), clock=lambda: NOW).list_valuations(_context())
    assert ValuationService(factory, _Source(_result(_mark())), clock=lambda: NOW).list_valuations(
        _context("tenant-b")
    ) == ()


def test_valuation_api_is_tenant_scoped_and_secret_free() -> None:
    factory = _factory()
    _seed(factory)
    service = ValuationService(factory, _Source(_result(_mark())), clock=lambda: NOW)
    holder = {"context": _context()}
    client = TestClient(create_app(factory, lambda: holder["context"], valuation_service=service))

    response = client.get("/v1/valuations")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["state"] == "CURRENT"
    assert payload[0]["unrealized_pnl"] == "20"
    serialized = response.text.lower()
    for forbidden in ("authorization", "password", "api_key", "api_secret", "private_endpoint"):
        assert forbidden not in serialized

    holder["context"] = _context("tenant-b")
    assert client.get("/v1/valuations").json() == []


def test_task_declares_private_freqtrade_mark_source() -> None:
    task = Path("docs/agents/tasks/FTAI-20260724-portal-pi02-authoritative-valuation.md").read_text(
        encoding="utf-8"
    )
    assert "same pinned Freqtrade runtime" in task
    assert "UNPRICED" in task
''',
)

write(
    "ai_platform/portal/web/lib/valuation.ts",
    '''import "server-only";

import { dataMode, PortalApiConfigurationError, PortalApiResponseError } from "./portal-api";

export type ValuationState = "CURRENT" | "STALE" | "SOURCE_UNAVAILABLE" | "UNPRICED";

export interface ValuationSnapshot {
  valuation_id: string;
  tenant_id: string;
  bot_id: string;
  position_id: string;
  source_position_id: string | null;
  source_runtime_id: string;
  pair: string;
  side: "BUY" | "SELL";
  amount: string;
  state: ValuationState;
  valuation_currency: string | null;
  entry_rate: string | null;
  mark_rate: string | null;
  cost_basis: string | null;
  market_value: string | null;
  unrealized_pnl: string | null;
  source_price_id: string | null;
  source_observed_at: string | null;
  observed_at: string;
  method_version: "mark-to-entry-v1";
  reason_code: string | null;
}

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required in API mode");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  return url.toString().replace(/\/$/, "");
}

function fixtureValuations(): ValuationSnapshot[] {
  return [
    {
      valuation_id: "valuation:fixture-btc",
      tenant_id: "tenant-demo",
      bot_id: "bot-alpha",
      position_id: "position-btc",
      source_position_id: "trade-42",
      source_runtime_id: "runtime-bot-alpha",
      pair: "BTC/USDT",
      side: "BUY",
      amount: "0.04",
      state: "CURRENT",
      valuation_currency: "USDT",
      entry_rate: "61500",
      mark_rate: "62800",
      cost_basis: "2460",
      market_value: "2512",
      unrealized_pnl: "52",
      source_price_id: "fixture:runtime-bot-alpha:BTC-USDT",
      source_observed_at: "2026-07-24T18:00:00Z",
      observed_at: "2026-07-24T18:00:00Z",
      method_version: "mark-to-entry-v1",
      reason_code: null,
    },
  ];
}

export async function listValuations(cookieHeader?: string | null): Promise<ValuationSnapshot[]> {
  if (dataMode() === "fixture") {
    return fixtureValuations();
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/valuations`, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
    },
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as ValuationSnapshot[];
}
''',
)

write(
    "ai_platform/portal/web/app/performance/page.tsx",
    '''import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots, listPerformance } from "@/lib/portal-api";
import { listValuations } from "@/lib/valuation";

export default async function PerformancePage() {
  const cookieHeader = (await cookies()).toString();
  const [performance, valuations, bots] = await Promise.all([
    listPerformance(cookieHeader),
    listValuations(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));
  const current = valuations.filter((valuation) => valuation.state === "CURRENT");
  const unavailable = valuations.filter((valuation) => valuation.state !== "CURRENT").length;
  const unrealized = current.reduce(
    (sum, valuation) => sum + Number(valuation.unrealized_pnl ?? 0),
    0,
  );

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>PNL &amp; Performance</h1></div>
        <span className="freshness">Realized evidence + private runtime marks</span>
      </div>
      <div className={`status-banner ${unavailable === 0 ? "status-info" : "status-warning"}`}>
        <strong>Authoritative valuation boundary</strong>
        <span>
          Current unrealized PNL: {unrealized.toLocaleString()} from {current.length} valued position(s).
          {unavailable > 0 ? ` ${unavailable} position(s) remain stale, unavailable or unpriced.` : ""}
          Realized PNL remains independent closed-trade evidence.
        </span>
      </div>
      <article className="panel">
        <div className="page-heading">
          <div><span className="eyebrow">Closed trades</span><h2>Realized performance</h2></div>
        </div>
        {performance.length === 0 ? (
          <div className="empty-state"><strong>No realized performance available</strong><span>Performance appears after an attributable closed-trade outcome is persisted.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Bot</th><th>Realized PNL</th><th>Fees</th><th>Net PNL</th><th>Trades</th><th>Win / loss</th><th>Reconciliation gaps</th></tr></thead>
              <tbody>
                {performance.map((row) => (
                  <tr key={row.bot_id}>
                    <td><strong>{botNames.get(row.bot_id) ?? row.bot_id}</strong><span>{row.bot_id}</span></td>
                    <td>{row.realized_pnl}</td>
                    <td>{row.fees}</td>
                    <td><strong>{row.net_pnl}</strong></td>
                    <td>{row.trade_count}</td>
                    <td>{row.winning_trades} / {row.losing_trades}</td>
                    <td>{row.reconciliation_gaps}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
      <article className="panel">
        <div className="page-heading">
          <div><span className="eyebrow">Open positions</span><h2>Open position valuation</h2></div>
          <span className="freshness">mark-to-entry-v1</span>
        </div>
        {valuations.length === 0 ? (
          <div className="empty-state"><strong>No open positions</strong><span>No tenant-scoped runtime positions require valuation.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Position</th><th>Bot</th><th>State</th><th>Amount</th><th>Entry</th><th>Mark</th><th>Market value</th><th>Unrealized PNL</th><th>Price evidence</th></tr></thead>
              <tbody>
                {valuations.map((valuation) => (
                  <tr key={valuation.valuation_id}>
                    <td><strong>{valuation.pair}</strong><span>{valuation.source_position_id ?? valuation.position_id}</span></td>
                    <td><strong>{botNames.get(valuation.bot_id) ?? valuation.bot_id}</strong><span>{valuation.source_runtime_id}</span></td>
                    <td><StatusPill value={valuation.state} /></td>
                    <td>{valuation.amount}</td>
                    <td>{valuation.entry_rate ?? "unavailable"}</td>
                    <td>{valuation.mark_rate ?? "unavailable"}</td>
                    <td>{valuation.market_value ?? "unavailable"} {valuation.valuation_currency ?? ""}</td>
                    <td><strong>{valuation.unrealized_pnl ?? "unavailable"}</strong></td>
                    <td><span>{valuation.source_price_id ?? valuation.reason_code ?? "unavailable"}</span><span>{valuation.source_observed_at ? new Date(valuation.source_observed_at).toLocaleString() : "no current timestamp"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
''',
)

write(
    "ai_platform/portal/web/e2e/valuation.spec.ts",
    '''import { expect, test } from "@playwright/test";


test("performance separates realized and authoritative unrealized evidence", async ({ page }) => {
  await page.goto("/performance");
  await expect(page.getByRole("heading", { name: "PNL & Performance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Realized performance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Open position valuation" })).toBeVisible();
  await expect(page.getByText("mark-to-entry-v1")).toBeVisible();
});
''',
)

replace_once(
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "| 5 | `PI-02` Authoritative Valuation and Unrealized PNL | `planned` | attributable current valuation with freshness and reconciliation | PI-01 plus authoritative price source |",
    "| 5 | `PI-02` Authoritative Valuation and Unrealized PNL | `active` | attributable current valuation with freshness and reconciliation | PI-01 plus authoritative price source |",
)
replace_once(
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "The numeric order is the recommended software sequencing. PI-01, PI-03 and PI-04 are complete. No other PI package is active; PI-06 requires an explicit product IdP decision, while PI-02 requires authoritative price-source, currency-conversion and staleness decisions before declaration.",
    "The numeric order is the recommended software sequencing. PI-01, PI-03 and PI-04 are complete. PI-02 is active with the exact pinned private Freqtrade runtime selected as the mark source; PI-06 still requires an explicit product IdP decision.",
)
replace_once(
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "### PI-02 — Authoritative Valuation and Unrealized PNL\n\nStatus: `planned`\n",
    "### PI-02 — Authoritative Valuation and Unrealized PNL\n\nStatus: `active`\n\nImplementation evidence: task `FTAI-20260724-portal-pi02-authoritative-valuation`; merge evidence remains pending.\n",
)
replace_once(
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "PI-02 may now be declared once its authoritative price, conversion and staleness policies are selected. Declare PI-05 after channel/provider and identity/destination ownership are clear.",
    "PI-02 is active with private runtime mark-to-entry v1, exact-quote-only valuation and explicit stale/unpriced states. Declare PI-05 only after channel/provider and identity/destination ownership are clear.",
)
replace_once(
    "docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md",
    "There is no active software PI package. PI-01, PI-03 and PI-04 are durably complete. The next package must be selected and declared separately only after its authoritative external source and policy entry gates are explicitly resolved.\n\nPI-02 is dependency-ready from the runtime-position side but still requires explicit authoritative price, conversion and staleness decisions. PI-06 requires the product IdP, membership source and session/MFA policy. PI-05 requires a channel/provider decision, and PI-07 requires a secret-store/KMS decision before PI-08 can be considered.",
    "The active software package is **PI-02 Authoritative Valuation and Unrealized PNL**. It uses the exact pinned private Freqtrade runtime as the mark source and remains bounded to exact-quote, unit-leverage mark-to-entry valuation.\n\nPI-06 still requires the product IdP, membership source and session/MFA policy. PI-05 requires a channel/provider decision, and PI-07 requires a secret-store/KMS decision before PI-08 can be considered.",
)

replace_once(
    "docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md",
    "The remaining authoritative-source, private-runtime, identity, observability and provider integrations are canonically ordered in `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` as PI-01 through PI-08. PI-01, PI-03 and PI-04 are complete. No software PI package is active; another package must not be declared until its authoritative external source and policy entry gates are explicitly resolved.",
    "The remaining authoritative-source, private-runtime, identity, observability and provider integrations are canonically ordered in `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` as PI-01 through PI-08. PI-01, PI-03 and PI-04 are complete; PI-02 is active with the exact pinned private Freqtrade runtime selected as its authoritative mark source.",
)
replace_once(
    "docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md",
    "Post-P12 continuation is governed by `POST_P12_INTEGRATION_BACKLOG.md`. Read-only PI-01, aggregate-only PI-03 and centralized-observability PI-04 are complete. No software PI package is active; any next declaration must first resolve its authoritative source and policy entry gates. PI-07 must precede PI-08; neither authorizes live capital.",
    "Post-P12 continuation is governed by `POST_P12_INTEGRATION_BACKLOG.md`. Read-only PI-01, aggregate-only PI-03 and centralized-observability PI-04 are complete. PI-02 authoritative valuation is active. PI-07 must precede PI-08; neither authorizes live capital.",
)
replace_once(
    "docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md",
    "Next autonomous software action: select and declare the next bounded PI package only after its authoritative external source and policy entry gates are explicitly resolved. No software PI package is currently active.",
    "Next autonomous software action: complete PI-02 exact-runtime authoritative valuation with explicit stale, source-unavailable and unpriced states; do not broaden into currency-provider integration, execution or live capital.",
)

replace_once(
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "`FTAI-20260723-portal-remaining-product-capabilities` closes the remaining software-addressable shell/read-model gaps",
    "`FTAI-20260724-portal-pi02-authoritative-valuation` adds exact-runtime mark-to-entry valuation with explicit `CURRENT`, `STALE`, `SOURCE_UNAVAILABLE` and `UNPRICED` states. Realized PNL remains separate closed-trade evidence and unsupported currency conversion or leverage never produces a numeric guess.\n\n`FTAI-20260723-portal-remaining-product-capabilities` closes the remaining software-addressable shell/read-model gaps",
)
replace_once(
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "| PNL & Performance | `/performance` | integrated for realized performance | aggregate of persisted attributable TradeOutcome evidence; unrealized PNL remains unavailable without authoritative current-price/position valuation evidence |",
    "| PNL & Performance | `/performance` | integrated for realized and bounded unrealized evidence | realized PNL from persisted closed trades plus tenant-scoped exact-runtime mark-to-entry valuation; stale, unavailable, cross-currency and leveraged positions remain explicitly non-current |",
)
replace_once(
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "## Remaining hard boundaries\n",
    "## PI-02 valuation semantics\n\nThe PNL & Performance page keeps closed-trade realized evidence separate from open-position valuation. Numeric unrealized PNL requires a current reconciled position, an exact source-position match, the pinned runtime's timestamped mark identity, unit leverage and quote currency equal to the bot capital currency. Missing, stale, cross-currency, leveraged or conflicting evidence produces `STALE`, `SOURCE_UNAVAILABLE` or `UNPRICED`, never a fallback number.\n\n## Remaining hard boundaries\n",
)
replace_once(
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "| authoritative current valuation and unrealized PNL | `PI-02` Authoritative Valuation and Unrealized PNL |\n",
    "",
)
replace_once(
    "docs/ai_platform/portal/UI_DELIVERY_STATUS.md",
    "API mode never fabricates PNL, position, order, trade, signal, log, drift, security or audit records.",
    "API mode never fabricates PNL, valuation, position, order, trade, signal, log, drift, security or audit records.",
)

with (ROOT / "docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md").open(
    "a", encoding="utf-8"
) as handle:
    handle.write(
        "\n## PI-02 authoritative valuation boundary\n\n"
        "PI-02 selects the exact pinned private Freqtrade runtime as the mark source for each reconciled open position. "
        "The source is normalized server-side with source-position identity, pair/side, base and quote currency, entry rate, current mark, leverage, source-price identity and observation timestamp. "
        "The portal computes `mark-to-entry-v1` only for current synced unit-leverage positions whose quote currency equals the bot capital currency. "
        "Stale, unavailable, cross-currency, leveraged, missing or conflicting evidence produces explicit non-current state and no numeric valuation. "
        "The browser receives no private runtime endpoint or authorization material, and realized PNL remains closed-trade evidence.\n"
    )

print("PI-02 valuation patch applied")
