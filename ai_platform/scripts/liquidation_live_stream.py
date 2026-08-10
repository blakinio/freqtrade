from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import websockets
from websockets.exceptions import WebSocketException

from ai_platform.research.liquidations.binance import parse_binance_force_order
from ai_platform.research.liquidations.bybit import parse_bybit_all_liquidation
from ai_platform.research.liquidations.contracts import LiquidationEvent
from ai_platform.research.liquidations.staging import (
    trading_credentials_present_in_environment,
    write_json_atomic,
)
from ai_platform.scripts.liquidation_binance_collector import trading_credentials_present


LIVE_CONTRACT = "liquidation-live-state-v1"
LIVE_STATE_FILE = "live-state-v1.json"
RUN_STATE_FILE = "run-state-v1.json"
BYBIT_SOURCE = "bybit-linear"
BINANCE_SOURCE = "binance-usdm"
OKX_SOURCE = "okx-swap"
RUN_ID_PATTERN = re.compile(r"^liquid20-\d{8}T\d{6}Z-\d+$")
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,24}$")
DEFAULT_BYBIT_ENDPOINT = "wss://stream.bybit.com/v5/public/linear"
DEFAULT_BYBIT_INSTRUMENTS_URL = "https://api.bybit.com/v5/market/instruments-info"
DEFAULT_BINANCE_ENDPOINT = "wss://fstream.binance.com/market/ws"
DEFAULT_BINANCE_EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
EXPECTED_CONNECTION_EXCEPTIONS = (OSError, ValueError, WebSocketException)
REDACTED = "[redacted]"


@dataclass(slots=True)
class SourceState:
    configured: bool
    connected: bool = False
    last_event_at_ms: int | None = None
    last_event_received_at_ms: int | None = None
    last_heartbeat_at_ms: int | None = None
    reconnect_count: int = 0
    observed_symbols: set[str] = field(default_factory=set)
    subscription_symbol_count: int = 0
    latest_error: str | None = None
    ingest_lag_ms: int | None = None
    events_written: int = 0
    error_count: int = 0
    parse_error_count: int = 0

    def as_json_dict(self) -> dict[str, object]:
        return {
            "configured": self.configured,
            "connected": self.connected,
            "last_event_at_ms": self.last_event_at_ms,
            "last_event_received_at_ms": self.last_event_received_at_ms,
            "last_heartbeat_at_ms": self.last_heartbeat_at_ms,
            "ingest_lag_ms": self.ingest_lag_ms,
            "reconnect_count": self.reconnect_count,
            "observed_symbol_count": len(self.observed_symbols),
            "subscription_symbol_count": self.subscription_symbol_count,
            "events_written": self.events_written,
            "error_count": self.error_count,
            "parse_error_count": self.parse_error_count,
            "latest_error": self.latest_error,
        }


class AppendOnlyNdjsonWriter:
    def __init__(
        self,
        path: Path,
        *,
        flush_interval_seconds: float = 1.0,
        flush_event_count: int = 100,
    ) -> None:
        if flush_interval_seconds <= 0:
            raise ValueError("flush_interval_seconds must be > 0")
        if flush_event_count < 1:
            raise ValueError("flush_event_count must be >= 1")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._handle = path.open("a", encoding="utf-8")
        self._flush_interval_seconds = flush_interval_seconds
        self._flush_event_count = flush_event_count
        self._pending = 0
        self._last_flush = time.monotonic()

    def append(self, event: LiquidationEvent) -> None:
        line = json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True)
        self._handle.write(line)
        self._handle.write("\n")
        self._pending += 1
        if (
            self._pending >= self._flush_event_count
            or time.monotonic() - self._last_flush >= self._flush_interval_seconds
        ):
            self.flush()

    def flush(self) -> None:
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._pending = 0
        self._last_flush = time.monotonic()

    @property
    def closed(self) -> bool:
        return self._handle.closed

    def close(self) -> None:
        if not self.closed:
            self.flush()
            self._handle.close()


def _seal_committed_ndjson(
    path: Path, *, committed_rows: int, source: str, allow_missing: bool
) -> None:
    if (
        isinstance(committed_rows, bool)
        or not isinstance(committed_rows, int)
        or committed_rows < 0
    ):
        raise RuntimeError(f"previous {source} events_written is invalid")
    if path.is_symlink():
        raise RuntimeError(f"previous {source} source path is not a regular file")
    if not path.exists():
        if allow_missing and committed_rows == 0:
            return
        if committed_rows == 0:
            raise RuntimeError(f"previous {source} source file is missing")
        raise RuntimeError(f"previous {source} source file is missing committed rows")
    if not path.is_file():
        raise RuntimeError(f"previous {source} source path is not a regular file")

    with path.open("r+b") as handle:
        committed_end = 0
        for _ in range(committed_rows):
            row = handle.readline()
            if not row or not row.endswith(b"\n") or not row.strip():
                raise RuntimeError(f"previous {source} source file has fewer rows than committed")
            committed_end = handle.tell()
        if handle.read(1):
            handle.truncate(committed_end)
            handle.flush()
            os.fsync(handle.fileno())


class LiveRunManager:
    def __init__(
        self,
        *,
        data_root: Path,
        collector_commit: str,
        host_id: str,
        now_ms: Callable[[], int] | None = None,
        flush_interval_seconds: float = 1.0,
    ) -> None:
        if not re.fullmatch(r"[0-9a-fA-F]{40}", collector_commit):
            raise ValueError("collector_commit must be a 40-character Git SHA")
        self.live_root = data_root / "live"
        self.runs_root = self.live_root / "runs"
        self.collector_commit = collector_commit.lower()
        self.host_id = host_id
        self._now_ms = now_ms or (lambda: time.time_ns() // 1_000_000)
        self._flush_interval_seconds = flush_interval_seconds
        self._lock = asyncio.Lock()
        self._run_id: str | None = None
        self._run_root: Path | None = None
        self._collector_started_at_ms: int | None = None
        self._completed_at_ms: int | None = None
        self._run_state = "active"
        self._completion_reason: str | None = None
        self._rotation_day: str | None = None
        self._last_event_at_ms: int | None = None
        self._last_event_received_at_ms: int | None = None
        self._writers: dict[str, AppendOnlyNdjsonWriter] = {}
        self.sources = {
            BYBIT_SOURCE: SourceState(configured=True),
            BINANCE_SOURCE: SourceState(configured=True),
            OKX_SOURCE: SourceState(configured=False),
        }

    @property
    def run_id(self) -> str:
        if self._run_id is None:
            raise RuntimeError("live run has not started")
        return self._run_id

    @property
    def run_root(self) -> Path:
        if self._run_root is None:
            raise RuntimeError("live run has not started")
        return self._run_root

    async def start(self) -> None:
        async with self._lock:
            self.runs_root.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(self._complete_previous_active_run)
            self._start_new_run(self._now_ms())
            await asyncio.to_thread(self._write_state)

    async def heartbeat(self) -> None:
        async with self._lock:
            self._rotate_if_needed(self._now_ms())
            await asyncio.to_thread(self._write_state)

    async def set_subscription(self, source: str, symbols: Sequence[str]) -> None:
        normalized = validate_symbols(symbols, maximum=len(symbols) or 1)
        async with self._lock:
            self.sources[source].subscription_symbol_count = len(normalized)
            await asyncio.to_thread(self._write_state)

    async def connected(self, source: str) -> None:
        async with self._lock:
            state = self.sources[source]
            state.connected = True
            state.last_heartbeat_at_ms = self._now_ms()
            state.latest_error = None
            await asyncio.to_thread(self._write_state)

    async def source_heartbeat(self, source: str) -> None:
        async with self._lock:
            state = self.sources[source]
            if state.connected:
                state.last_heartbeat_at_ms = self._now_ms()

    async def disconnected(self, source: str, error: BaseException | str | None) -> None:
        async with self._lock:
            state = self.sources[source]
            state.connected = False
            state.reconnect_count += 1
            state.last_heartbeat_at_ms = self._now_ms()
            planned = error == "subscription universe refresh"
            if not planned:
                state.error_count += 1
            state.latest_error = None if planned else redact_error(error)
            await asyncio.to_thread(self._write_state)

    async def parse_error(self, source: str, error: BaseException | str) -> None:
        async with self._lock:
            state = self.sources[source]
            state.parse_error_count += 1
            state.error_count += 1
            state.latest_error = redact_error(error)

    async def append_event(self, event: LiquidationEvent) -> None:
        if event.source not in (BYBIT_SOURCE, BINANCE_SOURCE):
            raise ValueError("unsupported live liquidation source")
        async with self._lock:
            self._rotate_if_needed(self._now_ms())
            writer = self._writers[event.source]
            await asyncio.to_thread(writer.append, event)
            state = self.sources[event.source]
            state.events_written += 1
            state.observed_symbols.add(event.symbol)
            state.last_event_at_ms = event.occurred_at_ms
            state.last_event_received_at_ms = event.received_at_ms
            state.last_heartbeat_at_ms = self._now_ms()
            state.ingest_lag_ms = max(0, event.received_at_ms - event.occurred_at_ms)
            self._last_event_at_ms = max(self._last_event_at_ms or 0, event.occurred_at_ms)
            self._last_event_received_at_ms = max(
                self._last_event_received_at_ms or 0, event.received_at_ms
            )

    async def stop(self, *, reason: str = "collector-stopped") -> None:
        async with self._lock:
            if self._run_id is None:
                return
            self._run_state = "completed"
            self._completion_reason = reason
            self._completed_at_ms = self._now_ms()
            for state in self.sources.values():
                state.connected = False
            for writer in self._writers.values():
                await asyncio.to_thread(writer.close)
            await asyncio.to_thread(self._write_state)
            self._writers.clear()

    def _complete_previous_active_run(self) -> None:
        pointer = self.live_root / LIVE_STATE_FILE
        if not pointer.exists() or pointer.is_symlink():
            return
        try:
            payload = json.loads(pointer.read_text(encoding="utf-8"))
            run_id = payload.get("active_run_id")
            if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
                return
            run_root = self.runs_root / run_id
            state_path = run_root / RUN_STATE_FILE
            if not state_path.is_file() or state_path.is_symlink():
                return
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return
        if state.get("run_state") != "active":
            return

        sources = state.get("sources")
        if not isinstance(sources, dict):
            raise RuntimeError("previous live source state is invalid")
        expected_sources = {BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE}
        if set(sources) != expected_sources:
            raise RuntimeError("previous live source set is invalid")
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE):
            source_state = sources[source]
            if not isinstance(source_state, dict):
                raise RuntimeError(f"previous {source} source state is invalid")
            committed_rows = source_state.get("events_written", 0)
            allow_missing = (
                source_state.get("configured") is not True
                and source_state.get("last_event_received_at_ms") is None
            )
            _seal_committed_ndjson(
                run_root / f"{source}.ndjson",
                committed_rows=committed_rows,
                source=source,
                allow_missing=allow_missing,
            )

        state["run_state"] = "completed"
        state["data_mode"] = "historical"
        state["completed_at_ms"] = self._now_ms()
        state["completion_reason"] = "collector-restart"
        write_json_atomic(state_path, state)

    def _start_new_run(self, now_ms: int) -> None:
        instant = datetime.fromtimestamp(now_ms / 1000, tz=UTC)
        day = instant.strftime("%Y%m%d")
        base = f"liquid20-{day}T000000Z"
        attempt = 0
        while (self.runs_root / f"{base}-{attempt}").exists():
            attempt += 1
        run_id = f"{base}-{attempt}"
        run_root = self.runs_root / run_id
        run_root.mkdir(parents=False, exist_ok=False)
        self._run_id = run_id
        self._run_root = run_root
        self._collector_started_at_ms = now_ms
        self._completed_at_ms = None
        self._run_state = "active"
        self._completion_reason = None
        self._rotation_day = day
        self._last_event_at_ms = None
        self._last_event_received_at_ms = None
        self._writers = {
            BYBIT_SOURCE: AppendOnlyNdjsonWriter(
                run_root / "bybit-linear.ndjson",
                flush_interval_seconds=self._flush_interval_seconds,
            ),
            BINANCE_SOURCE: AppendOnlyNdjsonWriter(
                run_root / "binance-usdm.ndjson",
                flush_interval_seconds=self._flush_interval_seconds,
            ),
        }
        for state in self.sources.values():
            state.connected = False
            state.last_event_at_ms = None
            state.last_event_received_at_ms = None
            state.last_heartbeat_at_ms = now_ms if state.configured else None
            state.reconnect_count = 0
            state.observed_symbols.clear()
            state.subscription_symbol_count = 0
            state.latest_error = None
            state.ingest_lag_ms = None
            state.events_written = 0
            state.error_count = 0
            state.parse_error_count = 0

    def _rotate_if_needed(self, now_ms: int) -> None:
        day = datetime.fromtimestamp(now_ms / 1000, tz=UTC).strftime("%Y%m%d")
        if day == self._rotation_day:
            return
        connection_state = {
            source: (
                state.connected,
                state.last_heartbeat_at_ms,
                state.subscription_symbol_count,
            )
            for source, state in self.sources.items()
        }
        self._run_state = "completed"
        self._completion_reason = "daily-rotation"
        self._completed_at_ms = now_ms
        for writer in self._writers.values():
            writer.close()
        self._write_state()
        self._start_new_run(now_ms)
        # Reconnect and error counters are scoped to the new run epoch created above.
        # Carrying them across rotation would divide an old cumulative count by a new uptime.
        for source, values in connection_state.items():
            connected, heartbeat_at_ms, subscription_count = values
            state = self.sources[source]
            state.connected = connected
            state.last_heartbeat_at_ms = heartbeat_at_ms
            state.subscription_symbol_count = subscription_count
        self._write_state()

    def _state_payload(self) -> dict[str, object]:
        heartbeat_at_ms = self._now_ms()
        return {
            "schema_version": 1,
            "contract": LIVE_CONTRACT,
            "run_id": self.run_id,
            "run_state": self._run_state,
            "data_mode": "live" if self._run_state == "active" else "historical",
            "collector_started_at_ms": self._collector_started_at_ms,
            "collector_heartbeat_at_ms": heartbeat_at_ms,
            "last_event_at_ms": self._last_event_at_ms,
            "last_event_received_at_ms": self._last_event_received_at_ms,
            "completed_at_ms": self._completed_at_ms,
            "completion_reason": self._completion_reason,
            "collector_commit": self.collector_commit,
            "host_id": self.host_id,
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "sources": {source: state.as_json_dict() for source, state in self.sources.items()},
        }

    def _write_state(self) -> None:
        for writer in self._writers.values():
            if not writer.closed:
                writer.flush()
        payload = self._state_payload()
        write_json_atomic(self.run_root / RUN_STATE_FILE, payload)
        for source in (BYBIT_SOURCE, BINANCE_SOURCE):
            source_payload = {
                "schema_version": 1,
                "source": {"id": source},
                "run_id": self.run_id,
                "run_state": self._run_state,
                "stats": self.sources[source].as_json_dict(),
                "trading_credentials_present": False,
                "execution_enabled": False,
            }
            write_json_atomic(self.run_root / f"{source}-summary.json", source_payload)
        pointer_payload = {
            "schema_version": 1,
            "contract": LIVE_CONTRACT,
            "active_run_id": self.run_id if self._run_state == "active" else None,
            "collector_heartbeat_at_ms": payload["collector_heartbeat_at_ms"],
            "state": payload,
        }
        write_json_atomic(self.live_root / LIVE_STATE_FILE, pointer_payload)


def redact_error(error: BaseException | str | None) -> str | None:
    if error is None:
        return None
    text = str(error)
    text = re.sub(
        r"(?i)(api[_-]?key|secret|token|password)=([^\s&]+)",
        rf"\1={REDACTED}",
        text,
    )
    text = re.sub(r"(?i)(wss?|https?)://([^/@\s]+)@", r"\1://[redacted]@", text)
    text = re.sub(
        r"([?&](?:signature|token|key|secret)=)[^&\s]+",
        rf"\1{REDACTED}",
        text,
    )
    if isinstance(error, BaseException):
        return f"{type(error).__name__}: {text}"[:500]
    return text[:500]


def validate_symbols(symbols: Sequence[str], *, maximum: int) -> tuple[str, ...]:
    if maximum < 1:
        raise ValueError("maximum must be >= 1")
    normalized = tuple(
        sorted(
            {
                symbol.strip().upper()
                for symbol in symbols
                if isinstance(symbol, str) and SYMBOL_PATTERN.fullmatch(symbol.strip().upper())
            }
        )
    )
    if not normalized:
        raise ValueError("symbol discovery returned no valid symbols")
    if len(normalized) > maximum:
        raise ValueError(f"symbol discovery exceeded configured maximum of {maximum}")
    return normalized


def _fetch_json(
    url: str,
    *,
    timeout_seconds: float = 15.0,
    maximum_bytes: int = 8_000_000,
) -> Any:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("symbol discovery URL must use HTTPS")
    request = urllib.request.Request(  # noqa: S310
        url,
        headers={"User-Agent": "freqtrade-liquidations-live/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        payload = response.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise ValueError("symbol discovery response exceeded the bounded size limit")
    return json.loads(payload)


def discover_bybit_symbols(
    *,
    url: str = DEFAULT_BYBIT_INSTRUMENTS_URL,
    maximum_symbols: int = 500,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> tuple[str, ...]:
    symbols: list[str] = []
    cursor = ""
    for _ in range(10):
        query = {"category": "linear", "limit": "1000"}
        if cursor:
            query["cursor"] = cursor
        payload = fetch_json(f"{url}?{urllib.parse.urlencode(query)}")
        if not isinstance(payload, dict) or payload.get("retCode") != 0:
            raise ValueError("invalid Bybit instruments response")
        result = payload.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("list"), list):
            raise ValueError("invalid Bybit instruments result")
        for item in result["list"]:
            if not isinstance(item, dict):
                continue
            if (
                item.get("status") == "Trading"
                and item.get("quoteCoin") == "USDT"
                and item.get("contractType") == "LinearPerpetual"
            ):
                symbols.append(str(item.get("symbol", "")))
        cursor = str(result.get("nextPageCursor", ""))
        if not cursor:
            break
    return validate_symbols(symbols, maximum=maximum_symbols)


def discover_binance_symbols(
    *,
    url: str = DEFAULT_BINANCE_EXCHANGE_INFO_URL,
    maximum_symbols: int = 500,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> tuple[str, ...]:
    payload = fetch_json(url)
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise ValueError("invalid Binance exchangeInfo response")
    symbols = [
        str(item.get("symbol", ""))
        for item in payload["symbols"]
        if isinstance(item, dict)
        and item.get("status") == "TRADING"
        and item.get("contractType") == "PERPETUAL"
        and item.get("quoteAsset") == "USDT"
    ]
    return validate_symbols(symbols, maximum=maximum_symbols)


def _bybit_subscriptions(
    symbols: Sequence[str],
    *,
    batch_size: int = 100,
) -> tuple[str, ...]:
    if batch_size < 1 or batch_size > 100:
        raise ValueError("Bybit subscription batch_size must be between 1 and 100")
    topics = [f"allLiquidation.{symbol}" for symbol in symbols]
    return tuple(
        json.dumps(
            {"op": "subscribe", "args": topics[index : index + batch_size]},
            separators=(",", ":"),
        )
        for index in range(0, len(topics), batch_size)
    )


def _binance_subscription() -> str:
    return json.dumps(
        {"method": "SUBSCRIBE", "params": ["!forceOrder@arr"], "id": 1},
        separators=(",", ":"),
    )


async def _bounded_backoff_sleep(delay: float, stop_event: asyncio.Event) -> None:
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=delay)
    except TimeoutError:
        return


async def run_bybit_source(  # noqa: C901
    manager: LiveRunManager,
    stop_event: asyncio.Event,
    *,
    endpoint: str = DEFAULT_BYBIT_ENDPOINT,
    discovery: Callable[[], tuple[str, ...]] = discover_bybit_symbols,
    refresh_seconds: float = 3600.0,
    reconnect_max_seconds: float = 60.0,
) -> None:
    reconnect_delay = 1.0
    while not stop_event.is_set():
        try:
            symbols = await asyncio.to_thread(discovery)
            await manager.set_subscription(BYBIT_SOURCE, symbols)
            subscriptions = _bybit_subscriptions(symbols)
            async with websockets.connect(
                endpoint,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_queue=10_000,
            ) as websocket:
                for subscription in subscriptions:
                    await websocket.send(subscription)
                await manager.connected(BYBIT_SOURCE)
                reconnect_delay = 1.0
                refresh_at = time.monotonic() + refresh_seconds
                while not stop_event.is_set() and time.monotonic() < refresh_at:
                    timeout = min(10.0, max(0.1, refresh_at - time.monotonic()))
                    try:
                        raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    except TimeoutError:
                        await manager.source_heartbeat(BYBIT_SOURCE)
                        continue
                    received_at_ms = time.time_ns() // 1_000_000
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        await manager.parse_error(
                            BYBIT_SOURCE,
                            "Bybit message is not an object",
                        )
                        continue
                    if str(payload.get("topic", "")).startswith("allLiquidation."):
                        try:
                            events = parse_bybit_all_liquidation(
                                payload,
                                received_at_ms=received_at_ms,
                            )
                        except (KeyError, TypeError, ValueError) as error:
                            await manager.parse_error(BYBIT_SOURCE, error)
                            continue
                        for event in events:
                            if event.symbol in symbols:
                                await manager.append_event(event)
                    await manager.source_heartbeat(BYBIT_SOURCE)
        except asyncio.CancelledError:
            raise
        except EXPECTED_CONNECTION_EXCEPTIONS + (
            json.JSONDecodeError,
            TypeError,
            KeyError,
        ) as error:
            await manager.disconnected(BYBIT_SOURCE, error)
            await _bounded_backoff_sleep(reconnect_delay, stop_event)
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)
        else:
            await manager.disconnected(BYBIT_SOURCE, "subscription universe refresh")


async def run_binance_source(
    manager: LiveRunManager,
    stop_event: asyncio.Event,
    *,
    endpoint: str = DEFAULT_BINANCE_ENDPOINT,
    discovery: Callable[[], tuple[str, ...]] = discover_binance_symbols,
    refresh_seconds: float = 3600.0,
    reconnect_max_seconds: float = 60.0,
) -> None:
    reconnect_delay = 1.0
    while not stop_event.is_set():
        try:
            symbols = await asyncio.to_thread(discovery)
            allowed_symbols = frozenset(symbols)
            await manager.set_subscription(BINANCE_SOURCE, symbols)
            async with websockets.connect(
                endpoint,
                ping_interval=180,
                ping_timeout=600,
                close_timeout=10,
                max_queue=10_000,
            ) as websocket:
                await websocket.send(_binance_subscription())
                await manager.connected(BINANCE_SOURCE)
                reconnect_delay = 1.0
                refresh_at = time.monotonic() + refresh_seconds
                while not stop_event.is_set() and time.monotonic() < refresh_at:
                    timeout = min(10.0, max(0.1, refresh_at - time.monotonic()))
                    try:
                        raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    except TimeoutError:
                        await manager.source_heartbeat(BINANCE_SOURCE)
                        continue
                    received_at_ms = time.time_ns() // 1_000_000
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        await manager.parse_error(
                            BINANCE_SOURCE,
                            "Binance message is not an object",
                        )
                        continue
                    try:
                        events = parse_binance_force_order(
                            payload,
                            received_at_ms=received_at_ms,
                        )
                    except (KeyError, TypeError, ValueError) as error:
                        if "forceOrder" in str(payload):
                            await manager.parse_error(BINANCE_SOURCE, error)
                        events = ()
                    for event in events:
                        if event.symbol in allowed_symbols:
                            await manager.append_event(event)
                    await manager.source_heartbeat(BINANCE_SOURCE)
        except asyncio.CancelledError:
            raise
        except EXPECTED_CONNECTION_EXCEPTIONS + (
            json.JSONDecodeError,
            TypeError,
            KeyError,
        ) as error:
            await manager.disconnected(BINANCE_SOURCE, error)
            await _bounded_backoff_sleep(reconnect_delay, stop_event)
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)
        else:
            await manager.disconnected(BINANCE_SOURCE, "subscription universe refresh")


async def run_live_collector(
    *,
    data_root: Path,
    collector_commit: str,
    host_id: str,
    heartbeat_seconds: float = 5.0,
    symbol_refresh_seconds: float = 3600.0,
    maximum_symbols: int = 500,
) -> None:
    if heartbeat_seconds <= 0:
        raise ValueError("heartbeat_seconds must be > 0")
    if symbol_refresh_seconds < 60:
        raise ValueError("symbol_refresh_seconds must be >= 60")
    if maximum_symbols < 1 or maximum_symbols > 1000:
        raise ValueError("maximum_symbols must be between 1 and 1000")
    if trading_credentials_present_in_environment() or trading_credentials_present():
        raise RuntimeError(
            "trading credentials are present; live data-only collector refuses to start"
        )

    manager = LiveRunManager(
        data_root=data_root,
        collector_commit=collector_commit,
        host_id=host_id,
    )
    await manager.start()
    stop_event = asyncio.Event()

    async def heartbeat_loop() -> None:
        while not stop_event.is_set():
            await manager.heartbeat()
            await _bounded_backoff_sleep(heartbeat_seconds, stop_event)

    bybit_discovery = partial(
        discover_bybit_symbols,
        maximum_symbols=maximum_symbols,
    )
    binance_discovery = partial(
        discover_binance_symbols,
        maximum_symbols=maximum_symbols,
    )
    tasks = [
        asyncio.create_task(
            run_bybit_source(
                manager,
                stop_event,
                discovery=bybit_discovery,
                refresh_seconds=symbol_refresh_seconds,
            ),
            name="liquidations-bybit-live",
        ),
        asyncio.create_task(
            run_binance_source(
                manager,
                stop_event,
                discovery=binance_discovery,
                refresh_seconds=symbol_refresh_seconds,
            ),
            name="liquidations-binance-live",
        ),
        asyncio.create_task(heartbeat_loop(), name="liquidations-heartbeat"),
    ]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        raise
    finally:
        stop_event.set()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await manager.stop()


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def _bounded_symbol_count(value: str) -> int:
    parsed = int(value)
    if parsed < 1 or parsed > 1000:
        raise argparse.ArgumentTypeError("value must be between 1 and 1000")
    return parsed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the continuous public liquidation live/shadow collector.",
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--collector-commit", required=True)
    parser.add_argument("--host-id", default="synology-01")
    parser.add_argument("--heartbeat-seconds", type=_positive_float, default=5.0)
    parser.add_argument("--symbol-refresh-seconds", type=_positive_float, default=3600.0)
    parser.add_argument("--maximum-symbols", type=_bounded_symbol_count, default=500)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    asyncio.run(
        run_live_collector(
            data_root=args.data_root,
            collector_commit=args.collector_commit,
            host_id=args.host_id,
            heartbeat_seconds=args.heartbeat_seconds,
            symbol_refresh_seconds=args.symbol_refresh_seconds,
            maximum_symbols=args.maximum_symbols,
        )
    )


if __name__ == "__main__":
    main()
