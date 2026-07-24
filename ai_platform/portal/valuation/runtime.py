from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from pydantic import PositiveInt

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import OperationalPosition
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission


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
    def __init__(
        self,
        checked_at: datetime,
        reason_code: str = "VALUATION_SOURCE_NOT_CONFIGURED",
    ) -> None:
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
    """Bounded server-side client for normalized marks from one private runtime."""

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
        try:
            endpoint = self._validated_endpoint(self._endpoint_resolver(request.source_runtime_id))
            http_request = self._request(endpoint, request)
            body = self._read_body(http_request, request.timeout_seconds)
            result = self._decode(body)
        except HTTPError as exc:
            reason_code = (
                "VALUATION_SOURCE_AUTHENTICATION_FAILED"
                if exc.code in {401, 403}
                else "VALUATION_SOURCE_UNAVAILABLE"
            )
            return self._unavailable(request, reason_code)
        except TimeoutError:
            return self._unavailable(request, "VALUATION_SOURCE_TIMEOUT")
        except URLError as exc:
            reason_code = (
                "VALUATION_SOURCE_TIMEOUT"
                if isinstance(exc.reason, TimeoutError)
                else "VALUATION_SOURCE_UNAVAILABLE"
            )
            return self._unavailable(request, reason_code)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return self._unavailable(request, "VALUATION_SOURCE_PROTOCOL_ERROR")

        self._require_scope(request, result)
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
        # S310 is safe after _validated_endpoint restricts the URL to HTTP(S) with a hostname.
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

    @staticmethod
    def _require_scope(
        request: RuntimeValuationRequest,
        result: RuntimeValuationSourceResult,
    ) -> None:
        if (
            result.tenant_id != request.tenant_id
            or result.bot_id != request.bot_id
            or result.source_runtime_id != request.source_runtime_id
        ):
            raise PermissionDeniedError("valuation source scope mismatch")

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
            capital_currency = bot.spec.capital_currency if bot is not None else None
            for position in sorted(grouped_positions, key=lambda item: item.position_id):
                snapshots.append(
                    self._value_position(
                        position,
                        capital_currency,
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
            return self._empty(
                position,
                observed_at,
                ValuationState.SOURCE_UNAVAILABLE,
                position.reason_code,
            )
        if position.freshness in {RuntimeReadFreshness.STALE, RuntimeReadFreshness.PARTIAL}:
            return self._empty(position, observed_at, ValuationState.STALE, position.reason_code)
        if position.reconciliation_status is not ReconciliationStatus.SYNCED:
            return self._empty(position, observed_at, ValuationState.UNPRICED, position.reason_code)
        if result.state is ValuationState.SOURCE_UNAVAILABLE:
            return self._empty(
                position,
                observed_at,
                ValuationState.SOURCE_UNAVAILABLE,
                result.reason_code,
            )
        if result.state is ValuationState.STALE:
            return self._empty(position, observed_at, ValuationState.STALE, result.reason_code)
        if result.state is ValuationState.UNPRICED:
            return self._empty(position, observed_at, ValuationState.UNPRICED, result.reason_code)
        if source_id is None:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_POSITION_ID_MISSING",
            )
        if source_id in conflicting:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_CONFLICTING_MARKS",
            )
        mark = marks.get(source_id)
        if mark is None:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_MARK_MISSING",
            )
        if mark.pair != position.pair or mark.side is not position.side:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_MARK_ATTRIBUTION_MISMATCH",
                mark,
            )
        if capital_currency is None:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_BOT_NOT_FOUND",
                mark,
            )
        if mark.quote_currency != capital_currency:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_CURRENCY_CONVERSION_UNAVAILABLE",
                mark,
            )
        if mark.leverage != Decimal("1"):
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_LEVERAGE_UNSUPPORTED",
                mark,
            )
        if position.amount <= 0 or mark.entry_rate <= 0 or mark.mark_rate <= 0:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_NON_POSITIVE_INPUT",
                mark,
            )
        age_seconds = (observed_at - mark.source_observed_at).total_seconds()
        if age_seconds < -5:
            return self._empty(
                position,
                observed_at,
                ValuationState.UNPRICED,
                "VALUATION_SOURCE_TIME_IN_FUTURE",
                mark,
            )
        if age_seconds > self._stale_after_seconds:
            return self._empty(
                position,
                observed_at,
                ValuationState.STALE,
                "VALUATION_MARK_STALE",
                mark,
            )

        cost_basis = position.amount * mark.entry_rate
        market_value = position.amount * mark.mark_rate
        unrealized_pnl = (
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
            unrealized_pnl=unrealized_pnl,
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
        identity = "\0".join(
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
