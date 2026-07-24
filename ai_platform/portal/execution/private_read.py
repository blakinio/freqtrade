from __future__ import annotations

import json
import socket
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from time import sleep
from typing import Any, Literal, Protocol, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import PositiveInt

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.execution import OrderState, TradeState
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.execution.errors import (
    RuntimeReadAuthenticationError,
    RuntimeReadError,
    RuntimeReadIsolationError,
    RuntimeReadProtocolError,
    RuntimeReadTimeoutError,
    RuntimeReadUnavailableError,
)


Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
EndpointResolver = Callable[[str, "RuntimeReadKind"], str]
AuthorizationHeaderProvider = Callable[[str], Mapping[str, str]]


class RuntimeReadKind(StrEnum):
    OPEN_POSITIONS = "OPEN_POSITIONS"
    ORDERS = "ORDERS"
    TRADES = "TRADES"


class RuntimeReadFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    PARTIAL = "PARTIAL"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class RuntimeReadReconciliationStatus(StrEnum):
    SYNCED = "SYNCED"
    PENDING = "PENDING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    MISMATCH = "MISMATCH"


class RuntimeReadRequest(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    kind: RuntimeReadKind
    cursor: NonEmptyStr | None = None
    page_size: PositiveInt
    timeout_seconds: PositiveInt


class PrivateRuntimePage(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    kind: RuntimeReadKind
    source_observed_at: UtcDateTime
    records: tuple[dict[str, Any], ...]
    next_cursor: NonEmptyStr | None = None
    complete: bool


class PrivateRuntimeTransport(Protocol):
    """Private collector transport. It is never injected into browser-facing code."""

    def fetch_page(self, request: RuntimeReadRequest) -> PrivateRuntimePage: ...


class PrivatePositionRecord(ContractModel):
    source_position_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    opened_at: UtcDateTime
    source_updated_at: UtcDateTime


class PrivateOrderRecord(ContractModel):
    source_order_id: NonEmptyStr
    source_trade_id: NonEmptyStr | None = None
    execution_intent_id: NonEmptyStr | None = None
    pair: NonEmptyStr
    side: TradeSide
    state: OrderState
    amount: Decimal
    created_at: UtcDateTime
    source_updated_at: UtcDateTime


class PrivateTradeRecord(ContractModel):
    source_trade_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    state: TradeState
    amount: Decimal
    opened_at: UtcDateTime
    closed_at: UtcDateTime | None = None
    realized_pnl: Decimal | None = None
    fees: Decimal | None = None
    exit_reason: NonEmptyStr | None = None
    source_updated_at: UtcDateTime


class RuntimeReadStatus(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    kind: RuntimeReadKind
    source_observed_at: UtcDateTime | None = None
    observed_at: UtcDateTime
    last_reconciled_at: UtcDateTime
    freshness: RuntimeReadFreshness
    reconciliation_status: RuntimeReadReconciliationStatus
    complete: bool
    record_count: int
    reason_code: NonEmptyStr | None = None


class PositionReadResult(ContractModel):
    status: RuntimeReadStatus
    records: tuple[PrivatePositionRecord, ...]


class OrderReadResult(ContractModel):
    status: RuntimeReadStatus
    records: tuple[PrivateOrderRecord, ...]


class TradeReadResult(ContractModel):
    status: RuntimeReadStatus
    records: tuple[PrivateTradeRecord, ...]


class PrivateRuntimeSnapshot(ContractModel):
    schema_version: Literal[1] = 1
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    observed_at: UtcDateTime
    positions: PositionReadResult
    orders: OrderReadResult
    trades: TradeReadResult


class HttpResponse(Protocol):
    def __enter__(self) -> "HttpResponse": ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def read(self, amount: int = -1) -> bytes: ...


HttpOpener = Callable[..., HttpResponse]


class HttpPrivateRuntimeTransport:
    """HTTP client for a trusted private collector, not for browser or public ingress use."""

    def __init__(
        self,
        endpoint_resolver: EndpointResolver,
        authorization_headers: AuthorizationHeaderProvider,
        *,
        opener: HttpOpener = urlopen,
        max_body_bytes: int = 1_048_576,
    ) -> None:
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._endpoint_resolver = endpoint_resolver
        self._authorization_headers = authorization_headers
        self._opener = opener
        self._max_body_bytes = max_body_bytes

    def fetch_page(self, request: RuntimeReadRequest) -> PrivateRuntimePage:
        endpoint = self._endpoint_resolver(request.source_runtime_id, request.kind)
        if not endpoint.startswith(("http://", "https://")):
            raise RuntimeReadProtocolError("RUNTIME_READ_INVALID_PRIVATE_ENDPOINT")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **dict(self._authorization_headers(request.source_runtime_id)),
        }
        encoded = json.dumps(request.model_dump(mode="json"), separators=(",", ":")).encode()
        http_request = Request(endpoint, data=encoded, headers=headers, method="POST")
        try:
            with self._opener(http_request, timeout=request.timeout_seconds) as response:
                body = response.read(self._max_body_bytes + 1)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise RuntimeReadAuthenticationError() from None
            if exc.code in {408, 504}:
                raise RuntimeReadTimeoutError() from None
            if exc.code == 404:
                raise RuntimeReadUnavailableError("RUNTIME_READ_RUNTIME_NOT_FOUND") from None
            if exc.code == 429 or exc.code >= 500:
                raise RuntimeReadUnavailableError("RUNTIME_READ_COLLECTOR_UNAVAILABLE") from None
            raise RuntimeReadProtocolError("RUNTIME_READ_HTTP_REJECTED") from None
        except (TimeoutError, socket.timeout):
            raise RuntimeReadTimeoutError() from None
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise RuntimeReadTimeoutError() from None
            raise RuntimeReadUnavailableError("RUNTIME_READ_TRANSPORT_UNAVAILABLE") from None

        if len(body) > self._max_body_bytes:
            raise RuntimeReadProtocolError("RUNTIME_READ_RESPONSE_TOO_LARGE")
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise RuntimeReadProtocolError("RUNTIME_READ_INVALID_JSON") from None
        if not isinstance(payload, dict):
            raise RuntimeReadProtocolError("RUNTIME_READ_INVALID_ENVELOPE")
        try:
            reject_sensitive_payload_keys(payload, path="private_runtime_page")
            return PrivateRuntimePage.model_validate(payload)
        except ValueError:
            raise RuntimeReadProtocolError("RUNTIME_READ_INVALID_PAYLOAD") from None


_RecordT = TypeVar(
    "_RecordT",
    PrivatePositionRecord,
    PrivateOrderRecord,
    PrivateTradeRecord,
)


class PrivateRuntimeCollector:
    def __init__(
        self,
        transport: PrivateRuntimeTransport,
        *,
        clock: Clock | None = None,
        sleeper: Sleeper = sleep,
        page_size: int = 100,
        timeout_seconds: int = 5,
        max_pages: int = 100,
        max_retries: int = 2,
        retry_delay_seconds: float = 0.05,
        stale_after_seconds: int = 120,
    ) -> None:
        for name, value in {
            "page_size": page_size,
            "timeout_seconds": timeout_seconds,
            "max_pages": max_pages,
            "stale_after_seconds": stale_after_seconds,
        }.items():
            if value < 1:
                raise ValueError(f"{name} must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")
        self._transport = transport
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper
        self._page_size = page_size
        self._timeout_seconds = timeout_seconds
        self._max_pages = max_pages
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._stale_after_seconds = stale_after_seconds

    def collect_positions(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> PositionReadResult:
        records, status = self._collect(
            tenant_id,
            bot_id,
            source_runtime_id,
            RuntimeReadKind.OPEN_POSITIONS,
            PrivatePositionRecord,
            "source_position_id",
        )
        return PositionReadResult(status=status, records=tuple(records))

    def collect_orders(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> OrderReadResult:
        records, status = self._collect(
            tenant_id,
            bot_id,
            source_runtime_id,
            RuntimeReadKind.ORDERS,
            PrivateOrderRecord,
            "source_order_id",
        )
        return OrderReadResult(status=status, records=tuple(records))

    def collect_trades(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> TradeReadResult:
        records, status = self._collect(
            tenant_id,
            bot_id,
            source_runtime_id,
            RuntimeReadKind.TRADES,
            PrivateTradeRecord,
            "source_trade_id",
        )
        return TradeReadResult(status=status, records=tuple(records))

    def collect_snapshot(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> PrivateRuntimeSnapshot:
        positions = self.collect_positions(tenant_id, bot_id, source_runtime_id)
        orders = self.collect_orders(tenant_id, bot_id, source_runtime_id)
        trades = self.collect_trades(tenant_id, bot_id, source_runtime_id)
        observed_at = max(
            positions.status.observed_at,
            orders.status.observed_at,
            trades.status.observed_at,
        )
        return PrivateRuntimeSnapshot(
            tenant_id=tenant_id,
            bot_id=bot_id,
            source_runtime_id=source_runtime_id,
            observed_at=observed_at,
            positions=positions,
            orders=orders,
            trades=trades,
        )

    def unavailable_snapshot(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
        reason_code: str,
    ) -> PrivateRuntimeSnapshot:
        observed_at = self._clock()

        def status(kind: RuntimeReadKind) -> RuntimeReadStatus:
            return RuntimeReadStatus(
                tenant_id=tenant_id,
                bot_id=bot_id,
                source_runtime_id=source_runtime_id,
                kind=kind,
                observed_at=observed_at,
                last_reconciled_at=observed_at,
                freshness=RuntimeReadFreshness.SOURCE_UNAVAILABLE,
                reconciliation_status=RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE,
                complete=False,
                record_count=0,
                reason_code=reason_code,
            )

        return PrivateRuntimeSnapshot(
            tenant_id=tenant_id,
            bot_id=bot_id,
            source_runtime_id=source_runtime_id,
            observed_at=observed_at,
            positions=PositionReadResult(
                status=status(RuntimeReadKind.OPEN_POSITIONS), records=()
            ),
            orders=OrderReadResult(status=status(RuntimeReadKind.ORDERS), records=()),
            trades=TradeReadResult(status=status(RuntimeReadKind.TRADES), records=()),
        )

    def _collect(
        self,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
        kind: RuntimeReadKind,
        record_type: type[_RecordT],
        identity_field: str,
    ) -> tuple[list[_RecordT], RuntimeReadStatus]:
        observed_at = self._clock()
        cursor: str | None = None
        source_observed_at: datetime | None = None
        records_by_id: dict[str, _RecordT] = {}
        mismatch = False
        reason_code: str | None = None
        complete = False

        for _page_number in range(self._max_pages):
            request = RuntimeReadRequest(
                tenant_id=tenant_id,
                bot_id=bot_id,
                source_runtime_id=source_runtime_id,
                kind=kind,
                cursor=cursor,
                page_size=self._page_size,
                timeout_seconds=self._timeout_seconds,
            )
            try:
                page = self._fetch_with_retry(request)
            except RuntimeReadIsolationError:
                raise
            except RuntimeReadError as exc:
                reason_code = exc.reason_code
                if records_by_id:
                    return list(records_by_id.values()), self._status(
                        tenant_id=tenant_id,
                        bot_id=bot_id,
                        source_runtime_id=source_runtime_id,
                        kind=kind,
                        source_observed_at=source_observed_at,
                        observed_at=observed_at,
                        freshness=RuntimeReadFreshness.PARTIAL,
                        reconciliation_status=RuntimeReadReconciliationStatus.PENDING,
                        complete=False,
                        record_count=len(records_by_id),
                        reason_code=reason_code,
                    )
                return [], self._status(
                    tenant_id=tenant_id,
                    bot_id=bot_id,
                    source_runtime_id=source_runtime_id,
                    kind=kind,
                    source_observed_at=None,
                    observed_at=observed_at,
                    freshness=RuntimeReadFreshness.SOURCE_UNAVAILABLE,
                    reconciliation_status=RuntimeReadReconciliationStatus.SOURCE_UNAVAILABLE,
                    complete=False,
                    record_count=0,
                    reason_code=reason_code,
                )

            self._require_page_scope(page, request)
            source_observed_at = (
                page.source_observed_at
                if source_observed_at is None
                else max(source_observed_at, page.source_observed_at)
            )
            for raw_record in page.records:
                try:
                    reject_sensitive_payload_keys(raw_record, path=f"{kind.value}.record")
                    record = record_type.model_validate(raw_record)
                except ValueError:
                    reason_code = "RUNTIME_READ_INVALID_RECORD"
                    return list(records_by_id.values()), self._status(
                        tenant_id=tenant_id,
                        bot_id=bot_id,
                        source_runtime_id=source_runtime_id,
                        kind=kind,
                        source_observed_at=source_observed_at,
                        observed_at=observed_at,
                        freshness=RuntimeReadFreshness.PARTIAL,
                        reconciliation_status=RuntimeReadReconciliationStatus.MISMATCH,
                        complete=False,
                        record_count=len(records_by_id),
                        reason_code=reason_code,
                    )
                identity = str(getattr(record, identity_field))
                existing = records_by_id.get(identity)
                if existing is not None and existing.canonical_json() != record.canonical_json():
                    mismatch = True
                else:
                    records_by_id[identity] = record

            if page.complete:
                if page.next_cursor is not None:
                    raise RuntimeReadProtocolError("RUNTIME_READ_COMPLETE_PAGE_HAS_CURSOR")
                complete = True
                break
            if page.next_cursor is None or page.next_cursor == cursor:
                reason_code = "RUNTIME_READ_INVALID_PAGINATION"
                break
            cursor = page.next_cursor
        else:
            reason_code = "RUNTIME_READ_PAGE_LIMIT_EXCEEDED"

        if not complete:
            return list(records_by_id.values()), self._status(
                tenant_id=tenant_id,
                bot_id=bot_id,
                source_runtime_id=source_runtime_id,
                kind=kind,
                source_observed_at=source_observed_at,
                observed_at=observed_at,
                freshness=RuntimeReadFreshness.PARTIAL,
                reconciliation_status=(
                    RuntimeReadReconciliationStatus.MISMATCH
                    if reason_code == "RUNTIME_READ_INVALID_PAGINATION"
                    else RuntimeReadReconciliationStatus.PENDING
                ),
                complete=False,
                record_count=len(records_by_id),
                reason_code=reason_code or "RUNTIME_READ_PARTIAL_RESPONSE",
            )

        assert source_observed_at is not None
        age_seconds = max(0.0, (observed_at - source_observed_at).total_seconds())
        if mismatch:
            freshness = (
                RuntimeReadFreshness.STALE
                if age_seconds > self._stale_after_seconds
                else RuntimeReadFreshness.CURRENT
            )
            reconciliation = RuntimeReadReconciliationStatus.MISMATCH
            reason_code = "RUNTIME_READ_DUPLICATE_MISMATCH"
        elif age_seconds > self._stale_after_seconds:
            freshness = RuntimeReadFreshness.STALE
            reconciliation = RuntimeReadReconciliationStatus.PENDING
            reason_code = "RUNTIME_READ_SOURCE_STALE"
        else:
            freshness = RuntimeReadFreshness.CURRENT
            reconciliation = RuntimeReadReconciliationStatus.SYNCED

        return list(records_by_id.values()), self._status(
            tenant_id=tenant_id,
            bot_id=bot_id,
            source_runtime_id=source_runtime_id,
            kind=kind,
            source_observed_at=source_observed_at,
            observed_at=observed_at,
            freshness=freshness,
            reconciliation_status=reconciliation,
            complete=True,
            record_count=len(records_by_id),
            reason_code=reason_code,
        )

    def _fetch_with_retry(self, request: RuntimeReadRequest) -> PrivateRuntimePage:
        last_error: RuntimeReadError | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return self._transport.fetch_page(request)
            except RuntimeReadError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self._max_retries:
                    raise
                self._sleeper(self._retry_delay_seconds * (attempt + 1))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _require_page_scope(page: PrivateRuntimePage, request: RuntimeReadRequest) -> None:
        if (
            page.tenant_id != request.tenant_id
            or page.bot_id != request.bot_id
            or page.source_runtime_id != request.source_runtime_id
            or page.kind is not request.kind
        ):
            raise RuntimeReadIsolationError()

    @staticmethod
    def _status(
        *,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
        kind: RuntimeReadKind,
        source_observed_at: datetime | None,
        observed_at: datetime,
        freshness: RuntimeReadFreshness,
        reconciliation_status: RuntimeReadReconciliationStatus,
        complete: bool,
        record_count: int,
        reason_code: str | None,
    ) -> RuntimeReadStatus:
        return RuntimeReadStatus(
            tenant_id=tenant_id,
            bot_id=bot_id,
            source_runtime_id=source_runtime_id,
            kind=kind,
            source_observed_at=source_observed_at,
            observed_at=observed_at,
            last_reconciled_at=observed_at,
            freshness=freshness,
            reconciliation_status=reconciliation_status,
            complete=complete,
            record_count=record_count,
            reason_code=reason_code,
        )
