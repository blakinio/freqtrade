# ruff: noqa: S310

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from collections import deque
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, OpenerDirector, ProxyHandler, Request, build_opener

from ai_platform.research.liquidations.contracts import LiquidationEvent, event_from_json_dict
from ai_platform.wickhunter.candidate_paper_runtime_service import (
    CandidatePaperRuntimeService,
)
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    BotMode,
    DriftState,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    SourceHealth,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.parameters import DEFAULT_RESEARCH_BOUNDS
from ai_platform.wickhunter.risk import WickHunterRiskContext, WickHunterRiskLimits
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import ShadowRuntimePolicy, ShadowRuntimeTick
from ai_platform.wickhunter.strategy import SignalMemory
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot, UniverseInstrumentDecision


LIQUID20_SCHEMA_VERSION = "wickhunter-liquid20-public-snapshot-v1"
HEALTH_SCHEMA_VERSION = "wickhunter-paper-runtime-operator-health-v1"
DEFAULT_PUBLIC_MARKET_BASE_URL = "https://fapi.binance.com"
DEFAULT_POLL_SECONDS = 600
DEFAULT_MAX_SOURCE_AGE_MS = 300_000
MAX_PUBLIC_MARKET_WORKERS = 8
PUBLIC_KLINE_LIMIT = 1500
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_HTTP_BYTES = 1024 * 1024
TERMINAL_PUBLIC_SYMBOL_CODES = frozenset({-4108, -1121})
MAX_LIVE_EVENTS = 20_000
MAX_EVENTS_PER_SYMBOL = 500
MAX_LIQUID20_SYMBOLS = 20
LIVE_HISTORY_WINDOW_MS = 86_400_000
LIVE_POINTER_NAME = "live-state-v1.json"
RUN_STATE_NAME = "run-state-v1.json"
LIQUID20_LIVE_CONTRACT = "liquidation-live-state-v1"
EXPECTED_LIVE_SOURCES = ("binance-usdm", "bybit-linear", "okx-swap")
MAX_LIVE_RUNS_PER_WINDOW = 64
MAX_LIVE_SOURCE_BYTES = 128 * 1024 * 1024
MAX_LIVE_SOURCE_EVENTS = 250_000
MAX_LIVE_EVENT_ROW_BYTES = 1024 * 1024
MAX_UNCOMMITTED_LIVE_EVENTS = 10_000
LIVE_SNAPSHOT_READ_ATTEMPTS = 10
LIVE_SNAPSHOT_RETRY_SECONDS = 0.1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,30}$")
LIVE_RUN_ID_RE = re.compile(r"^liquid20-(?P<day>\d{8})T\d{6}Z-\d+$")
FORBIDDEN_ENVIRONMENT_NAMES = (
    "OKX_API_KEY",
    "OKX_API_SECRET",
    "OKX_SECRET_KEY",
    "OKX_PASSPHRASE",
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "FT_EXCHANGE_KEY",
    "FT_EXCHANGE_SECRET",
    "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
ZERO_AUTHORITY = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


class CandidatePaperRuntimeOperatorError(RuntimeError):
    """Raised when the persistent PAPER operator must fail closed."""


class _PublicMarketSymbolUnavailable(CandidatePaperRuntimeOperatorError):
    """Raised only for terminal Binance USD-M symbol lifecycle states."""

    def __init__(self, symbol: str, exchange_code: int) -> None:
        self.symbol = symbol
        self.exchange_code = exchange_code
        super().__init__(f"public market symbol is unavailable: {symbol}")


class _TransientLiquid20SnapshotError(CandidatePaperRuntimeOperatorError):
    """Raised when an atomic producer publication is observed mid-commit."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


@dataclass(frozen=True, slots=True)
class Liquid20Snapshot:
    snapshot_id: str
    observed_at_ms: int
    events: tuple[LiquidationEvent, ...]
    histories: tuple[LiquidationHistorySnapshot, ...]
    source_states: tuple[LiquidationSourceState, ...]
    universe: DynamicUniverseSnapshot

    def history_for(self, symbol: str) -> LiquidationHistorySnapshot:
        normalized = symbol.upper()
        matches = [item for item in self.histories if item.symbol.upper() == normalized]
        if len(matches) != 1:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 history must contain exactly one row for {normalized}"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class PublicMarketSnapshot:
    symbol: str
    observed_at_ms: int
    decision_price: Decimal
    completed_candle_close_ms: int
    quote_volume_24h_usd: Decimal
    spread_bps: Decimal
    trend_return_ratio: Decimal
    volatility_ratio: Decimal
    vwap: Decimal
    vwma: Decimal
    wick_ratio: Decimal
    atr_ratio: Decimal
    open_interest_usd: Decimal
    funding_rate: Decimal

    def market_context(
        self,
        *,
        market_wide_liquidation_intensity: Decimal,
    ) -> MarketContextSnapshot:
        completed_at = self.completed_candle_close_ms
        completed_source = "completed_candle:binance-usdm-public-1m"
        metrics = (
            AvailableMetric(
                "funding_rate",
                self.funding_rate,
                self.observed_at_ms,
                "binance-usdm-public-premium-index",
            ),
            AvailableMetric(
                "open_interest_usd",
                self.open_interest_usd,
                self.observed_at_ms,
                "binance-usdm-public-open-interest",
            ),
            AvailableMetric(
                "quote_volume_24h_usd",
                self.quote_volume_24h_usd,
                completed_at,
                completed_source,
            ),
            AvailableMetric(
                "spread_bps",
                self.spread_bps,
                self.observed_at_ms,
                "binance-usdm-public-book-ticker",
            ),
            AvailableMetric(
                "trend_return_ratio",
                self.trend_return_ratio,
                completed_at,
                completed_source,
            ),
            AvailableMetric(
                "volatility_ratio",
                self.volatility_ratio,
                completed_at,
                completed_source,
            ),
            AvailableMetric("vwap", self.vwap, completed_at, completed_source),
            AvailableMetric("vwma", self.vwma, completed_at, completed_source),
            AvailableMetric(
                "wick_ratio",
                self.wick_ratio,
                completed_at,
                completed_source,
            ),
            AvailableMetric(
                "atr_ratio",
                self.atr_ratio,
                completed_at,
                completed_source,
            ),
            AvailableMetric(
                "market_wide_liquidation_intensity",
                market_wide_liquidation_intensity,
                self.observed_at_ms,
                "liquid20-live:market-wide",
            ),
        )
        return MarketContextSnapshot(
            symbol=self.symbol,
            decision_timestamp_ms=self.observed_at_ms,
            decision_price=self.decision_price,
            completed_candle_close_ms=completed_at,
            metrics=tuple(sorted(metrics, key=lambda metric: metric.name)),
        )


def _require_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidatePaperRuntimeOperatorError(f"{field} must contain an object")
    return value


def _require_list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise CandidatePaperRuntimeOperatorError(f"{field} must contain an array")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer") from exc
    if parsed <= 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be > 0")
    return parsed


def _non_negative_integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer") from exc
    if parsed < 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be >= 0")
    return parsed


def _decimal(
    value: object, *, field: str, positive: bool = False, non_negative: bool = False
) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be finite")
    if positive and parsed <= 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be > 0")
    if non_negative and parsed < 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be >= 0")
    return parsed


def _assert_regular_absolute(path: Path, *, field: str, must_exist: bool = True) -> None:
    if not path.is_absolute():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be absolute")
    if path.is_symlink():
        raise CandidatePaperRuntimeOperatorError(f"{field} cannot be a symlink")
    if must_exist and not path.exists():
        raise CandidatePaperRuntimeOperatorError(f"{field} does not exist")


def assert_closed_authority_environment(environment: Mapping[str, str] | None = None) -> None:
    values = os.environ if environment is None else environment
    present = sorted(name for name in FORBIDDEN_ENVIRONMENT_NAMES if values.get(name))
    if present:
        raise CandidatePaperRuntimeOperatorError(
            f"forbidden credential or proxy environment present: {','.join(present)}"
        )


def _read_bounded_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be a regular file")
    size = path.stat().st_size
    if size <= 0 or size > MAX_INPUT_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} size is outside the accepted bound")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to read {field}") from exc
    return _require_object(payload, field=field)


def _parse_live_source_event(
    row: dict[str, Any],
    *,
    source: str,
    observed_at_ms: int,
) -> LiquidationEvent:
    try:
        event = event_from_json_dict(row)
    except ValueError as exc:
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source event is invalid: {source}"
        ) from exc
    if event.source != source:
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 event source does not match its immutable source file"
        )
    if event.received_at_ms > observed_at_ms:
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 event was unavailable at live observation time"
        )
    return event


def _read_committed_jsonl_tail(  # noqa: C901
    path: Path,
    *,
    field: str,
    committed_rows: int,
    allow_uncommitted_suffix: bool,
    source: str,
    observed_at_ms: int,
    suffix_available_at_ms: Callable[[], int],
) -> tuple[dict[str, Any], ...]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be a regular file")
    if committed_rows > MAX_LIVE_SOURCE_EVENTS:
        raise CandidatePaperRuntimeOperatorError(f"{field} committed event count is too large")
    size = path.stat().st_size
    if size < 0 or size > MAX_LIVE_SOURCE_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} size is outside the accepted bound")
    if size == 0:
        if committed_rows != 0:
            raise CandidatePaperRuntimeOperatorError(f"{field} contradicts events_written")
        return ()

    rows: deque[dict[str, Any]] = deque(maxlen=MAX_LIVE_EVENTS)
    committed_seen = 0
    suffix_seen = 0
    bytes_seen = 0
    seen_event_ids: set[str] = set()
    previous_received_at_ms: int | None = None
    try:
        with path.open("rb") as handle:
            while bytes_seen < size:
                raw = handle.readline(min(size - bytes_seen, MAX_LIVE_EVENT_ROW_BYTES + 1))
                if not raw:
                    raise CandidatePaperRuntimeOperatorError(f"{field} changed during bounded read")
                bytes_seen += len(raw)
                if len(raw) > MAX_LIVE_EVENT_ROW_BYTES:
                    raise CandidatePaperRuntimeOperatorError(f"{field} contains an oversized event")
                if bytes_seen > MAX_LIVE_SOURCE_BYTES:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} size is outside the accepted bound"
                    )
                if not raw.endswith(b"\n") or not raw.strip():
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contains an incomplete event"
                    )
                payload = json.loads(raw.decode("utf-8"))
                row = _require_object(payload, field=field)
                if committed_seen < committed_rows:
                    event = _parse_live_source_event(
                        row,
                        source=source,
                        observed_at_ms=observed_at_ms,
                    )
                    if event.source_event_id in seen_event_ids:
                        raise CandidatePaperRuntimeOperatorError(
                            f"{field} contains duplicate event identities"
                        )
                    seen_event_ids.add(event.source_event_id)
                    previous_received_at_ms = event.received_at_ms
                    rows.append(row)
                    committed_seen += 1
                    continue
                suffix_seen += 1
                if not allow_uncommitted_suffix:
                    raise CandidatePaperRuntimeOperatorError(f"{field} contradicts events_written")
                if suffix_seen > MAX_UNCOMMITTED_LIVE_EVENTS:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contains too many uncommitted events"
                    )
                event = _parse_live_source_event(
                    row,
                    source=source,
                    observed_at_ms=suffix_available_at_ms(),
                )
                if event.source_event_id in seen_event_ids:
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} contains duplicate event identities"
                    )
                if (
                    previous_received_at_ms is not None
                    and event.received_at_ms < previous_received_at_ms
                ):
                    raise CandidatePaperRuntimeOperatorError(
                        f"{field} suffix reception order regressed"
                    )
                seen_event_ids.add(event.source_event_id)
                previous_received_at_ms = event.received_at_ms
    except CandidatePaperRuntimeOperatorError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to read {field}") from exc

    if committed_seen != committed_rows:
        raise CandidatePaperRuntimeOperatorError(f"{field} contradicts events_written")
    return tuple(rows)


def _live_source_state(
    source: str,
    payload: dict[str, Any],
    *,
    observed_at_ms: int,
    maximum_age_ms: int,
) -> LiquidationSourceState:
    configured = payload.get("configured") is True
    connected = payload.get("connected") is True
    events_written = _non_negative_integer(
        payload.get("events_written", 0), field=f"{source} events_written"
    )
    last_received_raw = payload.get("last_event_received_at_ms")
    heartbeat_raw = payload.get("last_heartbeat_at_ms")
    last_received = (
        None
        if last_received_raw is None
        else _integer(last_received_raw, field=f"{source} last event receipt")
    )
    heartbeat = (
        None if heartbeat_raw is None else _integer(heartbeat_raw, field=f"{source} heartbeat")
    )
    if any(value is not None and value > observed_at_ms for value in (last_received, heartbeat)):
        raise CandidatePaperRuntimeOperatorError(
            f"{source} live source timestamp is from the future"
        )
    coverage_available = configured and events_written > 0
    if not configured or not connected:
        health = SourceHealth.OFFLINE
    elif not coverage_available or last_received is None or heartbeat is None:
        health = SourceHealth.STALE
    elif (
        observed_at_ms - last_received > maximum_age_ms
        or observed_at_ms - heartbeat > maximum_age_ms
    ):
        health = SourceHealth.STALE
    else:
        health = SourceHealth.HEALTHY
    return LiquidationSourceState(
        source=source,
        health=health,
        coverage_available=coverage_available,
        last_received_at_ms=last_received,
        observed_at_ms=observed_at_ms,
    )


def _live_history(
    symbol: str,
    events: tuple[LiquidationEvent, ...],
) -> LiquidationHistorySnapshot:
    ordered = tuple(sorted(events, key=lambda item: (item.received_at_ms, item.source_event_id)))
    if not ordered:
        raise CandidatePaperRuntimeOperatorError(f"live Liquid20 history is empty for {symbol}")
    event_notionals = tuple(item.notional_usd for item in ordered)
    burst_totals: dict[int, Decimal] = {}
    for event in ordered:
        minute = event.received_at_ms // 60_000
        burst_totals[minute] = burst_totals.get(minute, Decimal("0")) + event.notional_usd
    minutes = sorted(burst_totals)
    previous_burst = None
    if len(minutes) > 1:
        previous_minute = minutes[-2]
        previous_burst = max(
            item.received_at_ms
            for item in ordered
            if item.received_at_ms // 60_000 == previous_minute
        )
    available_at_ms = max(item.received_at_ms for item in ordered)
    identity = {
        "symbol": symbol,
        "event_ids": [item.source_event_id for item in ordered],
        "available_at_ms": available_at_ms,
    }
    history_id = canonical_sha256(identity)
    history_body = {
        **identity,
        "event_notionals_usd": [str(value) for value in event_notionals],
        "burst_window_notionals_usd": [str(burst_totals[minute]) for minute in minutes],
        "previous_burst_received_at_ms": previous_burst,
        "history_id": history_id,
    }
    return LiquidationHistorySnapshot(
        symbol=symbol,
        event_notionals_usd=event_notionals,
        burst_window_notionals_usd=tuple(burst_totals[minute] for minute in minutes),
        previous_burst_received_at_ms=previous_burst,
        available_at_ms=available_at_ms,
        history_id=history_id,
        history_sha256=canonical_sha256(history_body),
    )


def _assert_live_zero_authority(payload: Mapping[str, object], *, field: str) -> None:
    if (
        payload.get("trading_credentials_present") is not False
        or payload.get("execution_enabled") is not False
        or payload.get("trading_authorized") is not False
        or payload.get("orders_submitted", 0) != 0
    ):
        raise CandidatePaperRuntimeOperatorError(f"{field} contains forbidden authority")


def _validate_live_run_state(
    payload: dict[str, Any],
    *,
    run_id: str,
    expected_run_state: str,
) -> dict[str, Any]:
    if payload.get("schema_version") != 1:
        raise CandidatePaperRuntimeOperatorError("Liquid20 run-state schema mismatch")
    if payload.get("contract") != LIQUID20_LIVE_CONTRACT:
        raise CandidatePaperRuntimeOperatorError("Liquid20 run-state contract mismatch")
    if payload.get("run_id") != run_id:
        raise CandidatePaperRuntimeOperatorError("Liquid20 run-state identity mismatch")
    if payload.get("run_state") != expected_run_state:
        raise CandidatePaperRuntimeOperatorError("Liquid20 run-state lifecycle mismatch")
    _assert_live_zero_authority(payload, field="Liquid20 run state")
    source_payloads = _require_object(
        payload.get("sources"),
        field=f"Liquid20 source states for {run_id}",
    )
    if tuple(sorted(source_payloads)) != EXPECTED_LIVE_SOURCES:
        raise CandidatePaperRuntimeOperatorError("Liquid20 source set mismatch")
    return source_payloads


def _relevant_live_run_ids(
    runs_root: Path,
    *,
    active_run_id: str,
    history_start_ms: int,
) -> tuple[str, ...]:
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise CandidatePaperRuntimeOperatorError("Liquid20 live runs root is invalid")
    run_ids = tuple(
        sorted(
            entry.name
            for entry in runs_root.iterdir()
            if entry.is_dir() and not entry.is_symlink() and LIVE_RUN_ID_RE.fullmatch(entry.name)
        )
    )
    if not run_ids or run_ids[-1] != active_run_id:
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 live pointer does not select the newest regular run"
        )
    history_start_day = datetime.fromtimestamp(
        history_start_ms / 1000,
        tz=UTC,
    ).strftime("%Y%m%d")
    relevant = tuple(run_id for run_id in run_ids if run_id[9:17] >= history_start_day)
    if not relevant or active_run_id not in relevant:
        raise CandidatePaperRuntimeOperatorError("Liquid20 history run set is empty")
    if len(relevant) > MAX_LIVE_RUNS_PER_WINDOW:
        raise CandidatePaperRuntimeOperatorError("Liquid20 history contains too many run epochs")
    return relevant


def _read_live_source_events(
    run_root: Path,
    *,
    source: str,
    source_row: dict[str, Any],
    observed_at_ms: int,
    suffix_available_at_ms: Callable[[], int],
    history_start_ms: int,
    allow_uncommitted_suffix: bool,
) -> tuple[LiquidationEvent, ...]:
    event_path = run_root / f"{source}.ndjson"
    events_written = _non_negative_integer(
        source_row.get("events_written", 0),
        field=f"{source} events_written",
    )
    configured = source_row.get("configured") is True
    if not event_path.exists():
        if (
            events_written == 0
            and not configured
            and source_row.get("last_event_received_at_ms") is None
        ):
            return ()
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} must be a regular file"
        )
    if events_written == 0 and not configured and event_path.stat().st_size != 0:
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} contradict events_written"
        )

    event_rows = _read_committed_jsonl_tail(
        event_path,
        field=f"Liquid20 source events {source}",
        committed_rows=events_written,
        allow_uncommitted_suffix=allow_uncommitted_suffix and configured,
        source=source,
        observed_at_ms=observed_at_ms,
        suffix_available_at_ms=suffix_available_at_ms,
    )
    if events_written == 0:
        if source_row.get("last_event_received_at_ms") is not None:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 source state {source} has a receipt without events"
            )
        return ()

    parsed_events = [
        _parse_live_source_event(
            row,
            source=source,
            observed_at_ms=observed_at_ms,
        )
        for row in event_rows
    ]

    claimed_last_received = _integer(
        source_row.get("last_event_received_at_ms"),
        field=f"{source} last event receipt",
    )
    if max(event.received_at_ms for event in parsed_events) != claimed_last_received:
        raise CandidatePaperRuntimeOperatorError(
            f"Liquid20 source events {source} do not match the state receipt"
        )
    return tuple(event for event in parsed_events if event.received_at_ms >= history_start_ms)


def _load_liquid20_live_root_once(  # noqa: C901
    root: Path,
    *,
    now_ms: int,
    maximum_age_ms: int,
    suffix_available_at_ms: Callable[[], int],
) -> Liquid20Snapshot:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 live root must be an absolute regular directory"
        )
    pointer = _read_bounded_json(root / LIVE_POINTER_NAME, field="Liquid20 live pointer")
    if pointer.get("schema_version") != 1:
        raise CandidatePaperRuntimeOperatorError("Liquid20 live pointer schema mismatch")
    contract = str(pointer.get("contract", "")).strip()
    run_id = str(pointer.get("active_run_id", ""))
    if contract != LIQUID20_LIVE_CONTRACT:
        raise CandidatePaperRuntimeOperatorError("Liquid20 live contract mismatch")
    if LIVE_RUN_ID_RE.fullmatch(run_id) is None:
        raise CandidatePaperRuntimeOperatorError("Liquid20 live run identity is invalid")

    active_state = _require_object(pointer.get("state"), field="Liquid20 live state")
    active_source_payloads = _validate_live_run_state(
        active_state,
        run_id=run_id,
        expected_run_state="active",
    )
    observed_at_ms = _integer(
        pointer.get("collector_heartbeat_at_ms"),
        field="Liquid20 collector heartbeat",
    )
    state_heartbeat = _integer(
        active_state.get("collector_heartbeat_at_ms"),
        field="Liquid20 state heartbeat",
    )
    if state_heartbeat != observed_at_ms:
        raise CandidatePaperRuntimeOperatorError("Liquid20 heartbeat identity mismatch")
    validation_at_ms = suffix_available_at_ms()
    age_ms = validation_at_ms - observed_at_ms
    if age_ms < 0:
        raise CandidatePaperRuntimeOperatorError("Liquid20 live pointer is from the future")
    if age_ms > maximum_age_ms:
        raise CandidatePaperRuntimeOperatorError("Liquid20 live pointer is stale")

    source_states = tuple(
        _live_source_state(
            source,
            _require_object(
                active_source_payloads[source],
                field=f"Liquid20 source state {source}",
            ),
            observed_at_ms=observed_at_ms,
            maximum_age_ms=maximum_age_ms,
        )
        for source in EXPECTED_LIVE_SOURCES
    )

    history_start_ms = observed_at_ms - LIVE_HISTORY_WINDOW_MS
    runs_root = root / "runs"
    relevant_run_ids = _relevant_live_run_ids(
        runs_root,
        active_run_id=run_id,
        history_start_ms=history_start_ms,
    )
    events: list[LiquidationEvent] = []
    for historical_run_id in relevant_run_ids:
        run_root = runs_root / historical_run_id
        run_state = _read_bounded_json(
            run_root / RUN_STATE_NAME,
            field=f"Liquid20 run state {historical_run_id}",
        )
        expected_state = "active" if historical_run_id == run_id else "completed"
        run_source_payloads = _validate_live_run_state(
            run_state,
            run_id=historical_run_id,
            expected_run_state=expected_state,
        )
        allow_legacy_restart_suffix = (
            expected_state == "completed"
            and run_state.get("completion_reason") == "collector-restart"
        )
        if historical_run_id == run_id and run_state != active_state:
            raise _TransientLiquid20SnapshotError("Liquid20 active pointer and run state differ")
        for source in EXPECTED_LIVE_SOURCES:
            source_row = _require_object(
                run_source_payloads[source],
                field=f"Liquid20 source state {source}",
            )
            events.extend(
                _read_live_source_events(
                    run_root,
                    source=source,
                    source_row=source_row,
                    observed_at_ms=observed_at_ms,
                    suffix_available_at_ms=suffix_available_at_ms,
                    history_start_ms=history_start_ms,
                    allow_uncommitted_suffix=(
                        historical_run_id == run_id or allow_legacy_restart_suffix
                    ),
                )
            )

    ordered_events = tuple(
        sorted(events, key=lambda item: (item.source_event_id, item.received_at_ms))
    )
    event_ids = [item.source_event_id for item in ordered_events]
    if not ordered_events:
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 live root contains no events in the history window"
        )
    if len(event_ids) != len(set(event_ids)):
        raise CandidatePaperRuntimeOperatorError("Liquid20 live event identities are duplicated")

    by_symbol: dict[str, list[LiquidationEvent]] = {}
    for event in ordered_events:
        symbol = event.symbol.upper()
        if not SYMBOL_RE.fullmatch(symbol):
            raise CandidatePaperRuntimeOperatorError("Liquid20 live event symbol is invalid")
        by_symbol.setdefault(symbol, []).append(event)
    ranked_symbols = sorted(
        by_symbol,
        key=lambda symbol: (
            -sum((item.notional_usd for item in by_symbol[symbol]), Decimal("0")),
            -max(item.received_at_ms for item in by_symbol[symbol]),
            symbol,
        ),
    )[:MAX_LIQUID20_SYMBOLS]
    selected_symbols = tuple(sorted(ranked_symbols))
    histories = tuple(
        _live_history(
            symbol,
            tuple(
                sorted(
                    by_symbol[symbol],
                    key=lambda item: (item.received_at_ms, item.source_event_id),
                )[-MAX_EVENTS_PER_SYMBOL:]
            ),
        )
        for symbol in selected_symbols
    )

    universe = DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version=LIQUID20_LIVE_CONTRACT,
        selected_at_ms=observed_at_ms,
        decisions=tuple(
            UniverseInstrumentDecision(
                canonical_instrument_id=f"perpetual:{symbol}",
                canonical_symbol=symbol,
                included=True,
                reason_codes=("live_liquid20_observed",),
            )
            for symbol in selected_symbols
        ),
    )
    snapshot_body = {
        "contract": contract,
        "active_run_id": run_id,
        "source_run_ids": list(relevant_run_ids),
        "observed_at_ms": observed_at_ms,
        "event_ids": event_ids,
        "history_hashes": [item.history_sha256 for item in histories],
        "source_states": [
            {
                "source": item.source,
                "health": item.health.value,
                "coverage_available": item.coverage_available,
                "last_received_at_ms": item.last_received_at_ms,
                "observed_at_ms": item.observed_at_ms,
            }
            for item in source_states
        ],
        "selected_symbols": list(selected_symbols),
    }
    if _read_bounded_json(root / LIVE_POINTER_NAME, field="Liquid20 live pointer") != pointer:
        raise _TransientLiquid20SnapshotError("Liquid20 live pointer changed during snapshot read")
    return Liquid20Snapshot(
        canonical_sha256(snapshot_body),
        observed_at_ms,
        ordered_events,
        histories,
        source_states,
        universe,
    )


def _load_liquid20_live_root(
    root: Path,
    *,
    now_ms: int,
    maximum_age_ms: int,
) -> Liquid20Snapshot:
    snapshot_started_ns = time.monotonic_ns()

    def suffix_available_at_ms() -> int:
        elapsed_ns = time.monotonic_ns() - snapshot_started_ns
        if elapsed_ns < 0:
            raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot clock moved backwards")
        return now_ms + elapsed_ns // 1_000_000

    last_error: _TransientLiquid20SnapshotError | None = None
    for attempt in range(LIVE_SNAPSHOT_READ_ATTEMPTS):
        try:
            return _load_liquid20_live_root_once(
                root,
                now_ms=now_ms,
                maximum_age_ms=maximum_age_ms,
                suffix_available_at_ms=suffix_available_at_ms,
            )
        except _TransientLiquid20SnapshotError as exc:
            last_error = exc
            if attempt + 1 < LIVE_SNAPSHOT_READ_ATTEMPTS:
                time.sleep(LIVE_SNAPSHOT_RETRY_SECONDS)
    raise CandidatePaperRuntimeOperatorError(
        "unable to obtain a stable Liquid20 live snapshot"
    ) from last_error


def load_liquid20_snapshot(
    path: Path,
    *,
    now_ms: int,
    maximum_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS,
) -> Liquid20Snapshot:
    if maximum_age_ms < 1:
        raise CandidatePaperRuntimeOperatorError("maximum Liquid20 age must be positive")
    return _load_liquid20_live_root(
        path,
        now_ms=now_ms,
        maximum_age_ms=maximum_age_ms,
    )


def _public_url(base_url: str, path: str, parameters: dict[str, object]) -> str:
    parsed = urlparse(base_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise CandidatePaperRuntimeOperatorError("public market base URL is not allowed") from exc
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or not parsed.hostname
        or port not in {None, 443}
    ):
        raise CandidatePaperRuntimeOperatorError("public market base URL is not allowed")
    if parsed.hostname.lower() != "fapi.binance.com":
        raise CandidatePaperRuntimeOperatorError("public market host is not allowlisted")
    return f"{base_url.rstrip('/')}{path}?{urlencode(parameters)}"


def _read_public_json(
    opener: OpenerDirector,
    *,
    url: str,
    field: str,
    symbol: str | None = None,
) -> object:
    request = Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "wickhunter-paper-runtime-operator/1"},
    )
    try:
        with opener.open(request, timeout=15) as response:
            if response.geturl() != url:
                raise CandidatePaperRuntimeOperatorError(f"{field} redirected unexpectedly")
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if "application/json" not in content_type:
                raise CandidatePaperRuntimeOperatorError(
                    f"{field} returned a non-JSON content type"
                )
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > MAX_HTTP_BYTES:
                raise CandidatePaperRuntimeOperatorError(f"{field} response is too large")
            body = response.read(MAX_HTTP_BYTES + 1)
    except CandidatePaperRuntimeOperatorError:
        raise
    except HTTPError as exc:
        error_body = exc.read(MAX_HTTP_BYTES + 1)
        error_payload: object = None
        if len(error_body) <= MAX_HTTP_BYTES:
            try:
                error_payload = json.loads(error_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_payload = None
        if (
            exc.code == 400
            and symbol is not None
            and isinstance(error_payload, dict)
            and isinstance(error_payload.get("code"), int)
            and error_payload["code"] in TERMINAL_PUBLIC_SYMBOL_CODES
        ):
            raise _PublicMarketSymbolUnavailable(
                symbol,
                int(error_payload["code"]),
            ) from exc
        raise CandidatePaperRuntimeOperatorError(f"unable to fetch {field}") from exc
    except Exception as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to fetch {field}") from exc
    if len(body) > MAX_HTTP_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} response is too large")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} returned malformed JSON") from exc


def _market_wide_liquidation_intensity(
    events: tuple[LiquidationEvent, ...],
    *,
    decision_timestamp_ms: int,
    burst_window_ms: int,
) -> Decimal:
    if burst_window_ms <= 0:
        raise CandidatePaperRuntimeOperatorError(
            "market-wide liquidation burst window must be positive"
        )
    history_start_ms = decision_timestamp_ms - LIVE_HISTORY_WINDOW_MS
    current_start_ms = decision_timestamp_ms - burst_window_ms
    complete_bucket_count = (current_start_ms - history_start_ms) // burst_window_ms
    if complete_bucket_count < 1:
        raise CandidatePaperRuntimeOperatorError(
            "market-wide liquidation intensity lacks a complete history bucket"
        )
    aligned_history_start_ms = current_start_ms - complete_bucket_count * burst_window_ms
    current_notional = Decimal("0")
    history_buckets = [Decimal("0") for _ in range(complete_bucket_count)]
    for event in events:
        available_at_ms = event.received_at_ms
        if available_at_ms > decision_timestamp_ms:
            continue
        if current_start_ms <= available_at_ms <= decision_timestamp_ms:
            current_notional += event.notional_usd
        elif aligned_history_start_ms <= available_at_ms < current_start_ms:
            bucket_index = (available_at_ms - aligned_history_start_ms) // burst_window_ms
            if 0 <= bucket_index < complete_bucket_count:
                history_buckets[bucket_index] += event.notional_usd
    baseline = sum(history_buckets, Decimal("0")) / Decimal(complete_bucket_count)
    if baseline <= 0:
        raise CandidatePaperRuntimeOperatorError(
            "market-wide liquidation intensity lacks positive history"
        )
    return current_notional / baseline


def fetch_public_market_snapshot(  # noqa: C901
    *,
    symbol: str,
    observed_at_ms: int,
    base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL,
    opener: OpenerDirector | None = None,
) -> PublicMarketSnapshot:
    normalized = symbol.upper()
    if not SYMBOL_RE.fullmatch(normalized):
        raise CandidatePaperRuntimeOperatorError("public market symbol is invalid")
    if observed_at_ms <= 0:
        raise CandidatePaperRuntimeOperatorError("public market observation time must be positive")
    assert_closed_authority_environment()
    client = opener or build_opener(ProxyHandler({}), _NoRedirectHandler())
    premium = _require_object(
        _read_public_json(
            client,
            url=_public_url(
                base_url,
                "/fapi/v1/premiumIndex",
                {"symbol": normalized},
            ),
            field="public premium index",
            symbol=normalized,
        ),
        field="public premium index",
    )
    book = _require_object(
        _read_public_json(
            client,
            url=_public_url(
                base_url,
                "/fapi/v1/ticker/bookTicker",
                {"symbol": normalized},
            ),
            field="public book ticker",
            symbol=normalized,
        ),
        field="public book ticker",
    )
    open_interest = _require_object(
        _read_public_json(
            client,
            url=_public_url(
                base_url,
                "/fapi/v1/openInterest",
                {"symbol": normalized},
            ),
            field="public open interest",
            symbol=normalized,
        ),
        field="public open interest",
    )
    klines = _require_list(
        _read_public_json(
            client,
            url=_public_url(
                base_url,
                "/fapi/v1/klines",
                {"symbol": normalized, "interval": "1m", "limit": PUBLIC_KLINE_LIMIT},
            ),
            field="public klines",
            symbol=normalized,
        ),
        field="public klines",
    )
    for response, field in (
        (premium, "public premium index"),
        (book, "public book ticker"),
        (open_interest, "public open interest"),
    ):
        if str(response.get("symbol", "")).upper() != normalized:
            raise CandidatePaperRuntimeOperatorError(f"{field} symbol identity mismatch")

    completed: list[tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]] = []
    for raw in klines:
        row = _require_list(raw, field="public kline")
        if len(row) < 8:
            raise CandidatePaperRuntimeOperatorError("public kline is malformed")
        close_ms = _integer(row[6], field="public kline close")
        if close_ms > observed_at_ms:
            continue
        candle_open = _decimal(row[1], field="candle open", positive=True)
        candle_high = _decimal(row[2], field="candle high", positive=True)
        candle_low = _decimal(row[3], field="candle low", positive=True)
        candle_close = _decimal(row[4], field="candle close", positive=True)
        base_volume = _decimal(row[5], field="candle base volume", non_negative=True)
        quote_volume = _decimal(row[7], field="candle quote volume", non_negative=True)
        if not (
            candle_low
            <= min(candle_open, candle_close)
            <= max(candle_open, candle_close)
            <= candle_high
        ):
            raise CandidatePaperRuntimeOperatorError("public completed candle is inconsistent")
        completed.append(
            (
                close_ms,
                candle_open,
                candle_high,
                candle_low,
                candle_close,
                base_volume,
                quote_volume,
            )
        )
    completed.sort(key=lambda item: item[0])
    if len({item[0] for item in completed}) != len(completed):
        raise CandidatePaperRuntimeOperatorError(
            "public completed candle timestamps are duplicated"
        )
    if len(completed) < 1440:
        raise CandidatePaperRuntimeOperatorError(
            "public klines must contain 1440 completed one-minute rows"
        )
    completed = completed[-1440:]
    if any(current[0] - previous[0] != 60_000 for previous, current in pairwise(completed)):
        raise CandidatePaperRuntimeOperatorError("public completed candle history contains a gap")
    latest = completed[-1]
    completed_close_ms = latest[0]
    if observed_at_ms - completed_close_ms > DEFAULT_MAX_SOURCE_AGE_MS:
        raise CandidatePaperRuntimeOperatorError("public completed candle is stale")

    total_base_volume = sum((item[5] for item in completed), Decimal("0"))
    total_quote_volume = sum((item[6] for item in completed), Decimal("0"))
    if total_base_volume <= 0 or total_quote_volume <= 0:
        raise CandidatePaperRuntimeOperatorError("public completed candle volume is empty")
    vwap = total_quote_volume / total_base_volume
    vwma = sum((item[4] * item[5] for item in completed), Decimal("0")) / total_base_volume

    atr_rows = completed[-15:]
    true_ranges = [
        max(
            current[2] - current[3],
            abs(current[2] - previous[4]),
            abs(current[3] - previous[4]),
        )
        for previous, current in pairwise(atr_rows)
    ]
    atr_ratio = sum(true_ranges, Decimal("0")) / Decimal(len(true_ranges)) / latest[4]

    closes = [item[4] for item in completed]
    returns = [current / previous - Decimal("1") for previous, current in pairwise(closes)]
    mean_return = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum(((value - mean_return) ** 2 for value in returns), Decimal("0")) / Decimal(
        len(returns)
    )
    volatility_ratio = variance.sqrt()
    trend_return_ratio = latest[4] / completed[0][1] - Decimal("1")
    wick_values: list[Decimal] = []
    for item in completed:
        candle_range = item[2] - item[3]
        wick_total = (item[2] - max(item[1], item[4])) + (min(item[1], item[4]) - item[3])
        wick_values.append(Decimal("0") if candle_range == 0 else wick_total / candle_range)
    wick_ratio = sum(wick_values, Decimal("0")) / Decimal(len(wick_values))

    mark_price = _decimal(
        premium.get("markPrice"),
        field="public mark price",
        positive=True,
    )
    bid = _decimal(book.get("bidPrice"), field="public bid", positive=True)
    ask = _decimal(book.get("askPrice"), field="public ask", positive=True)
    if ask < bid:
        raise CandidatePaperRuntimeOperatorError("public bid/ask spread is inverted")
    midpoint = (ask + bid) / Decimal("2")
    spread_bps = ((ask - bid) / midpoint) * Decimal("10000")
    open_interest_quantity = _decimal(
        open_interest.get("openInterest"),
        field="public open interest",
        non_negative=True,
    )
    funding_rate = _decimal(premium.get("lastFundingRate"), field="public funding rate")
    return PublicMarketSnapshot(
        symbol=normalized,
        observed_at_ms=observed_at_ms,
        decision_price=latest[4],
        completed_candle_close_ms=completed_close_ms,
        quote_volume_24h_usd=total_quote_volume,
        spread_bps=spread_bps,
        trend_return_ratio=trend_return_ratio,
        volatility_ratio=volatility_ratio,
        vwap=vwap,
        vwma=vwma,
        wick_ratio=wick_ratio,
        atr_ratio=atr_ratio,
        open_interest_usd=open_interest_quantity * mark_price,
        funding_rate=funding_rate,
    )


def _qualify_public_market_universe(
    universe: DynamicUniverseSnapshot,
    *,
    unavailable_symbols: tuple[str, ...],
) -> DynamicUniverseSnapshot:
    unavailable = {symbol.upper() for symbol in unavailable_symbols}
    decisions: list[UniverseInstrumentDecision] = []
    for decision in universe.decisions:
        symbol = decision.canonical_symbol.upper()
        if not decision.included:
            decisions.append(decision)
        elif symbol in unavailable:
            decisions.append(
                UniverseInstrumentDecision(
                    canonical_instrument_id=decision.canonical_instrument_id,
                    canonical_symbol=decision.canonical_symbol,
                    included=False,
                    reason_codes=("binance_usdm_public_market_unavailable",),
                )
            )
        else:
            decisions.append(
                UniverseInstrumentDecision(
                    canonical_instrument_id=decision.canonical_instrument_id,
                    canonical_symbol=decision.canonical_symbol,
                    included=True,
                    reason_codes=tuple(
                        sorted(
                            {
                                *decision.reason_codes,
                                "binance_usdm_public_market_available",
                            }
                        )
                    ),
                )
            )
    return DynamicUniverseSnapshot(
        schema_version=universe.schema_version,
        policy_version="wickhunter-liquid20-binance-usdm-public-v1",
        selected_at_ms=universe.selected_at_ms,
        decisions=tuple(decisions),
    )


def _runtime_policy() -> ShadowRuntimePolicy:
    return ShadowRuntimePolicy(
        policy_version="wickhunter-paper-runtime-v1",
        simulated_initial_equity_quote=Decimal("10000"),
        maximum_universe_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_source_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        minimum_healthy_sources=1,
        maximum_open_positions=4,
        maximum_drawdown_ratio=Decimal("0.20"),
        decision_history_limit=1000,
    )


def _risk_limits() -> WickHunterRiskLimits:
    return WickHunterRiskLimits(
        risk_policy_version="wickhunter-paper-risk-v1",
        maximum_base_risk_ratio=Decimal("0.02"),
        maximum_effective_exposure_ratio=Decimal("0.20"),
        maximum_leverage=Decimal("15"),
        maximum_dca_count=4,
        maximum_total_dca_risk_ratio=Decimal("0.04"),
        maximum_concurrent_positions=4,
        maximum_symbol_exposure_ratio=Decimal("0.20"),
        maximum_correlated_exposure_ratio=Decimal("0.40"),
        maximum_directional_exposure_ratio=Decimal("0.60"),
        maximum_daily_loss_ratio=Decimal("0.10"),
        maximum_drawdown_ratio=Decimal("0.20"),
        maximum_consecutive_losses=5,
        maximum_liquidation_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_candle_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_open_interest_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_funding_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_spread_bps=Decimal("50"),
        minimum_quote_volume_usd=Decimal("1000000"),
        minimum_confidence=Decimal("0"),
    )


def _current_equity(state: Any, policy: ShadowRuntimePolicy) -> Decimal:
    unrealized = sum(
        (position.unrealized_pnl_quote for position in state.positions),
        Decimal("0"),
    )
    equity = (
        policy.simulated_initial_equity_quote + state.cumulative_realized_pnl_quote + unrealized
    )
    return max(equity, Decimal("0.00000001"))


def _consecutive_losses(state: Any) -> int:
    streak = 0
    ordered = sorted(
        state.closed_positions,
        key=lambda position: (position.closed_at_ms, position.closed_position_id),
        reverse=True,
    )
    for position in ordered:
        if position.realized_pnl_quote < 0:
            streak += 1
        else:
            break
    return streak


def _runtime_risk_context(
    *,
    state: Any,
    policy: ShadowRuntimePolicy,
    parameters: Any,
    symbol: str,
    observed_at_ms: int,
    market: PublicMarketSnapshot,
    model_drift: DriftState,
    data_drift: DriftState,
    circuit_breaker_active: bool,
) -> WickHunterRiskContext:
    equity = _current_equity(state, policy)
    symbol_exposure = Decimal("0")
    total_exposure = Decimal("0")
    long_exposure = Decimal("0")
    short_exposure = Decimal("0")
    normalized_symbol = symbol.upper()
    for position in state.positions:
        exposure = position.mark_price * position.quantity / equity
        total_exposure += exposure
        if position.symbol.upper() == normalized_symbol:
            symbol_exposure += exposure
        if position.side is TradeDirection.LONG:
            long_exposure += exposure
        else:
            short_exposure += exposure

    candidate_exposure = (
        max(parameters.base_risk_ratio, parameters.dca_total_risk_ratio) * parameters.leverage
    )
    day_start_ms = observed_at_ms - 86_400_000
    gross_daily_loss = sum(
        (
            -position.realized_pnl_quote
            for position in state.closed_positions
            if day_start_ms <= position.closed_at_ms <= observed_at_ms
            and position.realized_pnl_quote < 0
        ),
        Decimal("0"),
    )
    streak = _consecutive_losses(state)
    loss_cooldown = None
    if streak >= _risk_limits().maximum_consecutive_losses:
        latest_loss_closed_at_ms = max(position.closed_at_ms for position in state.closed_positions)
        loss_cooldown = latest_loss_closed_at_ms + parameters.cooldown_ms
    symbol_closes = [
        position.closed_at_ms
        for position in state.closed_positions
        if position.symbol.upper() == normalized_symbol
    ]
    symbol_cooldown = None
    if symbol_closes:
        candidate = max(symbol_closes) + parameters.cooldown_ms
        if candidate > observed_at_ms:
            symbol_cooldown = candidate

    return WickHunterRiskContext(
        evaluated_at_ms=observed_at_ms,
        global_kill_switch_active=False,
        circuit_breaker_active=circuit_breaker_active,
        model_drift=model_drift,
        data_drift=data_drift,
        projected_concurrent_positions=len(state.positions) + 1,
        projected_symbol_exposure_ratio=symbol_exposure + candidate_exposure,
        projected_correlated_exposure_ratio=total_exposure + candidate_exposure,
        projected_directional_exposure_ratio=(
            max(long_exposure, short_exposure) + candidate_exposure
        ),
        daily_loss_ratio=(gross_daily_loss / policy.simulated_initial_equity_quote),
        drawdown_ratio=state.drawdown_ratio,
        consecutive_losses=streak,
        consecutive_loss_cooldown_until_ms=loss_cooldown,
        symbol_cooldown_until_ms=symbol_cooldown,
        setup_still_valid=True,
        dca_adverse_condition_met=True,
        dca_timing_condition_met=True,
        spread_bps=market.spread_bps,
        quote_volume_usd=market.quote_volume_24h_usd,
        candidate_paper_validation_authorized=False,
    )


def _atomic_health(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise CandidatePaperRuntimeOperatorError("health path cannot be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


@dataclass(slots=True)
class CandidatePaperRuntimeOperator:
    service: CandidatePaperRuntimeService
    liquid20_root_path: Path
    health_path: Path
    operator_commit: str
    public_market_base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL
    maximum_source_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS
    model_drift: DriftState = DriftState.HEALTHY
    data_drift: DriftState = DriftState.HEALTHY
    circuit_breaker_active: bool = False
    opener: OpenerDirector | None = None
    last_success_at_ms: int | None = None

    def __post_init__(self) -> None:
        if not GIT_SHA_RE.fullmatch(self.operator_commit):
            raise CandidatePaperRuntimeOperatorError(
                "operator commit must be an exact lowercase Git SHA"
            )
        if self.service.binding.request.mode is not BotMode.PAPER:
            raise CandidatePaperRuntimeOperatorError("runtime binding mode must be PAPER")
        _assert_regular_absolute(self.liquid20_root_path, field="Liquid20 input")
        if not self.health_path.is_absolute():
            raise CandidatePaperRuntimeOperatorError("health path must be absolute")
        if self.health_path.parent.is_symlink():
            raise CandidatePaperRuntimeOperatorError("health root cannot be a symlink")
        if self.maximum_source_age_ms < 1:
            raise CandidatePaperRuntimeOperatorError("maximum source age must be positive")
        assert_closed_authority_environment()

    def _compose_tick(
        self,
        *,
        liquid20: Liquid20Snapshot,
        markets: tuple[PublicMarketSnapshot, ...],
        observed_at_ms: int,
        unavailable_symbols: tuple[str, ...] = (),
    ) -> ShadowRuntimeTick:
        latest_state = self.service.runtime.state
        universe = _qualify_public_market_universe(
            liquid20.universe,
            unavailable_symbols=unavailable_symbols,
        )
        if not universe.selected_symbols:
            raise CandidatePaperRuntimeOperatorError(
                "public market universe contains no eligible Liquid20 symbols"
            )
        market_by_symbol = {item.symbol: item for item in markets}
        if len(market_by_symbol) != len(markets):
            raise CandidatePaperRuntimeOperatorError(
                "public market snapshots contain duplicate symbols"
            )
        required_market_symbols = {
            *universe.selected_symbols,
            *(position.symbol.upper() for position in latest_state.positions),
        }
        if set(market_by_symbol) != required_market_symbols:
            raise CandidatePaperRuntimeOperatorError(
                "public market symbols do not cover the universe and open positions"
            )

        market_wide_liquidation_intensity = _market_wide_liquidation_intensity(
            liquid20.events,
            decision_timestamp_ms=observed_at_ms,
            burst_window_ms=self.service.binding.parameters.burst_window_ms,
        )
        burst_start_ms = observed_at_ms - self.service.binding.parameters.burst_window_ms
        requests: list[ShadowDecisionRequest] = []
        for symbol in universe.selected_symbols:
            events = tuple(
                item
                for item in liquid20.events
                if item.symbol.upper() == symbol
                and burst_start_ms <= item.received_at_ms <= observed_at_ms
            )
            if not events:
                continue
            market = market_by_symbol[symbol]
            requests.append(
                ShadowDecisionRequest(
                    bot_instance=self.service.binding.request.bot_instance,
                    mode=self.service.binding.request.mode,
                    events=events,
                    market=market.market_context(
                        market_wide_liquidation_intensity=(market_wide_liquidation_intensity)
                    ),
                    history=liquid20.history_for(symbol),
                    source_states=liquid20.source_states,
                    universe=universe,
                    parameters=self.service.binding.parameters,
                    parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
                    hypothesis=StrategyHypothesis.REVERSAL,
                    scorer=self.service.binding.scorer,
                    signal_memory=SignalMemory(),
                    risk_limits=_risk_limits(),
                    risk_context=_runtime_risk_context(
                        state=latest_state,
                        policy=self.service.runtime.policy,
                        parameters=self.service.binding.parameters,
                        symbol=symbol,
                        observed_at_ms=observed_at_ms,
                        market=market,
                        model_drift=self.model_drift,
                        data_drift=self.data_drift,
                        circuit_breaker_active=self.circuit_breaker_active,
                    ),
                    dataset_hash=self.service.binding.request.dataset_hash,
                    code_sha=self.service.binding.request.code_sha,
                )
            )
        return ShadowRuntimeTick(
            observed_at_ms=observed_at_ms,
            universe=universe,
            decision_requests=tuple(requests),
            mark_prices=tuple(sorted((item.symbol, item.decision_price) for item in markets)),
            source_states=liquid20.source_states,
            model_drift=self.model_drift,
            data_drift=self.data_drift,
            validation_state="collecting",
            retraining_state="disabled",
        )

    def _health_payload(
        self,
        *,
        status: str,
        checked_at_ms: int,
        liquid20_snapshot_id: str | None,
        runtime_health: str,
        circuit_breaker_reasons: tuple[str, ...],
        error_code: str | None,
        error_message: str | None,
    ) -> dict[str, object]:
        if runtime_health not in {"healthy", "degraded", "fail_closed"}:
            raise CandidatePaperRuntimeOperatorError("runtime health is invalid")
        canonical_breaker_reasons = tuple(sorted(set(circuit_breaker_reasons)))
        state = self.service.runtime.state
        request = self.service.binding.request
        payload: dict[str, object] = {
            "schema_version": HEALTH_SCHEMA_VERSION,
            "status": status,
            "checked_at_ms": checked_at_ms,
            "last_success_at_ms": self.last_success_at_ms,
            "operator_commit": self.operator_commit,
            "binding_id": self.service.binding.binding_id,
            "run_id": request.run_id,
            "window_start_ms": request.window_start_ms,
            "window_end_ms": request.window_end_ms,
            "generation": state.generation,
            "last_observed_at_ms": state.last_observed_at_ms,
            "liquid20_snapshot_id": liquid20_snapshot_id,
            "runtime_health": runtime_health,
            "model_drift": self.model_drift.value,
            "data_drift": self.data_drift.value,
            "circuit_breaker_active": bool(canonical_breaker_reasons),
            "circuit_breaker_reasons": list(canonical_breaker_reasons),
            "error_code": error_code,
            "error_message": None if error_message is None else error_message[:240],
            **ZERO_AUTHORITY,
        }
        payload["health_sha256"] = canonical_sha256(payload)
        return payload

    def _fetch_public_market_snapshots(
        self,
        *,
        symbols: tuple[str, ...],
        observed_at_ms: int,
    ) -> tuple[tuple[PublicMarketSnapshot, ...], tuple[str, ...]]:
        def fetch(symbol: str) -> tuple[str, PublicMarketSnapshot | None]:
            try:
                snapshot = fetch_public_market_snapshot(
                    symbol=symbol,
                    observed_at_ms=observed_at_ms,
                    base_url=self.public_market_base_url,
                    opener=self.opener,
                )
            except _PublicMarketSymbolUnavailable as exc:
                if exc.symbol != symbol:
                    raise CandidatePaperRuntimeOperatorError(
                        "public market unavailable symbol identity mismatch"
                    ) from exc
                return symbol, None
            return symbol, snapshot

        if self.opener is not None or len(symbols) <= 2:
            results = tuple(fetch(symbol) for symbol in symbols)
        else:
            workers = min(MAX_PUBLIC_MARKET_WORKERS, len(symbols))
            with ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix="wickhunter-public-market",
            ) as executor:
                results = tuple(executor.map(fetch, symbols))
        snapshots = tuple(snapshot for _symbol, snapshot in results if snapshot is not None)
        unavailable = tuple(symbol for symbol, snapshot in results if snapshot is None)
        return snapshots, unavailable

    def run_once(self, *, observed_at_ms: int | None = None) -> int:
        now_ms = time.time_ns() // 1_000_000 if observed_at_ms is None else observed_at_ms
        request = self.service.binding.request
        if not request.window_start_ms <= now_ms < request.window_end_ms:
            raise CandidatePaperRuntimeOperatorError(
                "current time is outside the immutable activation window"
            )
        liquid20 = load_liquid20_snapshot(
            self.liquid20_root_path,
            now_ms=now_ms,
            maximum_age_ms=self.maximum_source_age_ms,
        )
        open_position_symbols = tuple(
            sorted({position.symbol.upper() for position in self.service.runtime.state.positions})
        )
        market_symbols = tuple(
            sorted(
                {
                    *liquid20.universe.selected_symbols,
                    *open_position_symbols,
                }
            )
        )
        markets, unavailable_symbols = self._fetch_public_market_snapshots(
            symbols=market_symbols,
            observed_at_ms=now_ms,
        )
        unavailable_open_positions = tuple(
            sorted(set(open_position_symbols) & set(unavailable_symbols))
        )
        if unavailable_open_positions:
            raise CandidatePaperRuntimeOperatorError(
                "open PAPER position lacks Binance USD-M public market context: "
                + ",".join(unavailable_open_positions)
            )
        tick = self._compose_tick(
            liquid20=liquid20,
            markets=markets,
            observed_at_ms=now_ms,
            unavailable_symbols=unavailable_symbols,
        )
        result = self.service.step(tick)
        breaker_reasons = set(result.snapshot.circuit_breaker_reasons)
        if self.circuit_breaker_active:
            breaker_reasons.add("operator_circuit_breaker_active")
        canonical_breaker_reasons = tuple(sorted(breaker_reasons))
        runtime_health = (
            "fail_closed" if canonical_breaker_reasons else result.snapshot.health.value
        )
        self.last_success_at_ms = now_ms
        _atomic_health(
            self.health_path,
            self._health_payload(
                status="healthy",
                checked_at_ms=now_ms,
                liquid20_snapshot_id=liquid20.snapshot_id,
                runtime_health=runtime_health,
                circuit_breaker_reasons=canonical_breaker_reasons,
                error_code=None,
                error_message=None,
            ),
        )
        return result.state.generation

    def publish_failure(self, error: BaseException, *, checked_at_ms: int) -> None:
        _atomic_health(
            self.health_path,
            self._health_payload(
                status="fail_closed",
                checked_at_ms=checked_at_ms,
                liquid20_snapshot_id=None,
                runtime_health="fail_closed",
                circuit_breaker_reasons=(),
                error_code=type(error).__name__,
                error_message=str(error),
            ),
        )

    def run_forever(self, *, poll_seconds: int) -> None:
        if not 60 <= poll_seconds <= 900:
            raise CandidatePaperRuntimeOperatorError("poll cadence must be within 60..900 seconds")
        while True:
            checked_at_ms = time.time_ns() // 1_000_000
            try:
                self.run_once(observed_at_ms=checked_at_ms)
            except Exception as exc:
                self.publish_failure(exc, checked_at_ms=checked_at_ms)
            time.sleep(poll_seconds)


def _boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("boolean value must be true or false")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persistent fail-closed WickHunter candidate PAPER operator"
    )
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--activation-root", type=Path, required=True)
    parser.add_argument("--journal-root", type=Path, required=True)
    parser.add_argument("--liquid20-root", type=Path, required=True)
    parser.add_argument("--health-root", type=Path, required=True)
    parser.add_argument("--operator-commit", required=True)
    parser.add_argument("--public-market-base-url", default=DEFAULT_PUBLIC_MARKET_BASE_URL)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--maximum-source-age-ms", type=int, default=DEFAULT_MAX_SOURCE_AGE_MS)
    parser.add_argument(
        "--model-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument(
        "--data-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument(
        "--circuit-breaker-active",
        type=_boolean,
        default=False,
    )
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    assert_closed_authority_environment()
    for path, field in (
        (args.candidate_root, "candidate root"),
        (args.activation_root, "activation root"),
        (args.journal_root, "journal root"),
        (args.liquid20_root, "Liquid20 root"),
        (args.health_root, "health root"),
    ):
        _assert_regular_absolute(
            path,
            field=field,
            must_exist=field not in {"journal root", "health root"},
        )
    if not args.liquid20_root.is_dir():
        raise CandidatePaperRuntimeOperatorError("Liquid20 root must be a regular directory")
    args.journal_root.mkdir(parents=True, exist_ok=True)
    args.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_candidate_paper_runtime_binding(
        candidate_root=args.candidate_root,
        activation_root=args.activation_root,
    )
    service = CandidatePaperRuntimeService(
        binding=binding,
        runtime_policy=_runtime_policy(),
        journal_root=args.journal_root,
    )
    operator = CandidatePaperRuntimeOperator(
        service=service,
        liquid20_root_path=args.liquid20_root,
        health_path=args.health_root / "health.json",
        operator_commit=args.operator_commit,
        public_market_base_url=args.public_market_base_url,
        maximum_source_age_ms=args.maximum_source_age_ms,
        model_drift=DriftState(args.model_drift),
        data_drift=DriftState(args.data_drift),
        circuit_breaker_active=args.circuit_breaker_active,
    )
    if args.once:
        operator.run_once()
        return 0
    operator.run_forever(poll_seconds=args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
