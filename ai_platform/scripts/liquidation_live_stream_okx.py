from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from functools import partial
from pathlib import Path
from typing import Any

import websockets

from ai_platform.research.liquidations.contracts import LiquidationEvent
from ai_platform.research.liquidations.okx import (
    OkxInstrumentContract,
    parse_okx_instruments_response,
    parse_okx_liquidation_orders,
)
from ai_platform.research.liquidations.staging import (
    trading_credentials_present_in_environment,
)
from ai_platform.scripts.liquidation_binance_collector import trading_credentials_present
from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    EXPECTED_CONNECTION_EXCEPTIONS,
    OKX_SOURCE,
    AppendOnlyNdjsonWriter,
    LiveRunManager,
    _bounded_backoff_sleep,
    _fetch_json,
    _write_json_atomic_at,
    discover_binance_symbols,
    discover_bybit_symbols,
    redact_error,
    run_binance_source,
    run_bybit_source,
    validate_symbols,
)
from ai_platform.scripts.liquidation_okx_collector import (
    DEFAULT_OKX_ENDPOINT,
    DEFAULT_OKX_INSTRUMENTS_URL,
    build_instrument_snapshot,
)


OKX_INSTRUMENT_SNAPSHOT_FILE = "okx-swap-instruments-v1.json"
OKX_CREDENTIAL_ENVIRONMENT_NAMES = (
    "OKX_API_KEY",
    "OKX_API_SECRET",
    "OKX_SECRET_KEY",
    "OKX_PASSPHRASE",
)
REQUIRED_LIVE_SOURCES = frozenset((BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE))


def okx_credentials_present(environment: Mapping[str, str] | None = None) -> bool:
    values = environment if environment is not None else os.environ
    return any(values.get(name, "").strip() for name in OKX_CREDENTIAL_ENVIRONMENT_NAMES)


def _okx_subscription() -> str:
    return json.dumps(
        {
            "op": "subscribe",
            "args": [{"channel": "liquidation-orders", "instType": "SWAP"}],
        },
        separators=(",", ":"),
    )


def _is_okx_liquidation_payload(payload: Mapping[str, object]) -> bool:
    arg = payload.get("arg")
    return (
        isinstance(arg, dict)
        and str(arg.get("channel", "")) == "liquidation-orders"
        and str(arg.get("instType", "")).upper() == "SWAP"
        and isinstance(payload.get("data"), list)
    )


def discover_okx_instruments(
    *,
    url: str = DEFAULT_OKX_INSTRUMENTS_URL,
    maximum_symbols: int = 500,
    fetch_json: Callable[[str], Any] = _fetch_json,
    now_ms: Callable[[], int] | None = None,
) -> tuple[tuple[str, ...], dict[str, OkxInstrumentContract], dict[str, object]]:
    payload = fetch_json(url)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("invalid OKX instruments response")
    supported_rows: list[object] = []
    for row in payload["data"]:
        if not isinstance(row, dict):
            continue
        inst_id = str(row.get("instId", "")).strip().upper()
        base = inst_id.removesuffix("-USDT-SWAP")
        if (
            inst_id == f"{base}-USDT-SWAP"
            and base
            and str(row.get("instType", "")).upper() == "SWAP"
            and str(row.get("ctType", "")).lower() == "linear"
            and str(row.get("settleCcy", "")).upper() == "USDT"
            and str(row.get("ctValCcy", "")).upper() == base
            and str(row.get("ctMult", "")) == "1"
            and str(row.get("state", "")).lower() == "live"
        ):
            supported_rows.append(row)
    instruments = parse_okx_instruments_response(
        {"code": payload.get("code"), "data": supported_rows}
    )
    symbols = validate_symbols(
        [contract.canonical_symbol for contract in instruments.values()],
        maximum=maximum_symbols,
    )
    allowed = set(symbols)
    selected = {
        inst_id: contract
        for inst_id, contract in instruments.items()
        if contract.canonical_symbol in allowed
    }
    fetched_at_ms = (now_ms or (lambda: time.time_ns() // 1_000_000))()
    snapshot = build_instrument_snapshot(
        instruments=selected,
        instruments_url=url,
        fetched_at_ms=fetched_at_ms,
    )
    return symbols, selected, snapshot


class OkxLiveRunManager(LiveRunManager):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._last_event_at_ms: int | None = None
        self._last_event_received_at_ms: int | None = None
        self.sources[OKX_SOURCE].configured = True
        self._okx_instrument_snapshot: dict[str, object] | None = None
        self._startup_connected_sources: set[str] = set()
        self._startup_activation_complete = False

    def _state_payload(self) -> dict[str, object]:
        payload = super()._state_payload()
        payload["orders_submitted"] = 0
        return payload

    def _write_okx_snapshot(self, *, directory_fd: int | None = None) -> None:
        if self._okx_instrument_snapshot is not None:
            run_fd = directory_fd
            if run_fd is None:
                run_fd = self._require_fd(
                    self._run_root_fd,
                    label="Liquid20 active run root",
                )
            _write_json_atomic_at(
                run_fd,
                OKX_INSTRUMENT_SNAPSHOT_FILE,
                self._okx_instrument_snapshot,
            )

    def _start_new_run(self, now_ms: int) -> None:
        super()._start_new_run(now_ms)
        self._writers[OKX_SOURCE] = AppendOnlyNdjsonWriter(
            self.run_root / "okx-swap.ndjson",
            flush_interval_seconds=self._flush_interval_seconds,
            directory_fd=self._require_fd(self._run_root_fd, label="Liquid20 active run root"),
        )
        self._write_okx_snapshot()

    def _write_source_summaries(self, run_fd: int, payload: dict[str, object]) -> None:
        super()._write_source_summaries(run_fd, payload)
        sources = payload.get("sources")
        run_id = payload.get("run_id")
        run_state = payload.get("run_state")
        if not isinstance(sources, dict) or not isinstance(run_id, str):
            raise RuntimeError("Liquid20 OKX source summary payload is invalid")
        stats = sources.get(OKX_SOURCE)
        if not isinstance(stats, dict) or not isinstance(run_state, str):
            raise RuntimeError("Liquid20 OKX source summary state is invalid")
        source_payload = {
            "schema_version": 1,
            "source": {"id": OKX_SOURCE},
            "run_id": run_id,
            "run_state": run_state,
            "stats": stats,
            "trading_credentials_present": False,
            "execution_enabled": False,
            "orders_submitted": 0,
        }
        _write_json_atomic_at(run_fd, "okx-swap-summary.json", source_payload)
        self._write_okx_snapshot(directory_fd=run_fd)

    async def connected(self, source: str) -> None:
        async with self._lock:
            if source not in REQUIRED_LIVE_SOURCES:
                raise ValueError("unsupported live liquidation source")
            state = self.sources[source]
            state.last_heartbeat_at_ms = self._now_ms()
            state.latest_error = None
            if self._startup_activation_complete:
                state.connected = True
                await asyncio.to_thread(self._write_state)
                return

            self._startup_connected_sources.add(source)
            if self._startup_connected_sources != REQUIRED_LIVE_SOURCES:
                return

            activated_at_ms = self._now_ms()
            for item in self.sources.values():
                item.connected = True
                item.last_heartbeat_at_ms = activated_at_ms
                item.latest_error = None
            self._startup_activation_complete = True
            await asyncio.to_thread(self._write_state)

    async def disconnected(self, source: str, error: BaseException | str | None) -> None:
        async with self._lock:
            if source not in REQUIRED_LIVE_SOURCES:
                raise ValueError("unsupported live liquidation source")
            if not self._startup_activation_complete:
                self._startup_connected_sources.discard(source)
            state = self.sources[source]
            state.connected = False
            state.reconnect_count += 1
            state.last_heartbeat_at_ms = self._now_ms()
            planned = error == "subscription universe refresh"
            if not planned:
                state.error_count += 1
            state.latest_error = None if planned else redact_error(error)
            await asyncio.to_thread(self._write_state)

    async def set_okx_instruments(
        self,
        symbols: Sequence[str],
        snapshot: Mapping[str, object],
    ) -> None:
        normalized = validate_symbols(symbols, maximum=len(symbols) or 1)
        async with self._lock:
            self._okx_instrument_snapshot = dict(snapshot)
            self.sources[OKX_SOURCE].subscription_symbol_count = len(normalized)
            await asyncio.to_thread(self._write_state)

    async def append_event(self, event: LiquidationEvent) -> None:
        if event.source != OKX_SOURCE:
            await super().append_event(event)
            return
        async with self._lock:
            self._rotate_if_needed(self._now_ms())
            writer = self._writers[OKX_SOURCE]
            await asyncio.to_thread(writer.append, event)
            state = self.sources[OKX_SOURCE]
            state.events_written += 1
            state.observed_symbols.add(event.symbol)
            state.last_event_at_ms = event.occurred_at_ms
            state.last_event_received_at_ms = event.received_at_ms
            state.last_heartbeat_at_ms = self._now_ms()
            state.ingest_lag_ms = max(0, event.received_at_ms - event.occurred_at_ms)
            self._last_event_at_ms = max(self._last_event_at_ms or 0, event.occurred_at_ms)
            self._last_event_received_at_ms = max(
                self._last_event_received_at_ms or 0,
                event.received_at_ms,
            )


async def run_okx_source(  # noqa: C901
    manager: OkxLiveRunManager,
    stop_event: asyncio.Event,
    *,
    endpoint: str = DEFAULT_OKX_ENDPOINT,
    discovery: Callable[
        [], tuple[tuple[str, ...], dict[str, OkxInstrumentContract], dict[str, object]]
    ] = discover_okx_instruments,
    refresh_seconds: float = 3600.0,
    reconnect_max_seconds: float = 60.0,
) -> None:
    reconnect_delay = 1.0
    while not stop_event.is_set():
        try:
            symbols, instruments, snapshot = await asyncio.to_thread(discovery)
            allowed_symbols = frozenset(symbols)
            await manager.set_okx_instruments(symbols, snapshot)
            async with websockets.connect(
                endpoint,
                ping_interval=None,
                close_timeout=10,
                max_queue=10_000,
            ) as websocket:
                await websocket.send(_okx_subscription())
                await manager.connected(OKX_SOURCE)
                reconnect_delay = 1.0
                refresh_at = time.monotonic() + refresh_seconds
                while not stop_event.is_set() and time.monotonic() < refresh_at:
                    timeout = min(20.0, max(0.1, refresh_at - time.monotonic()))
                    try:
                        raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    except TimeoutError:
                        await websocket.send("ping")
                        await manager.source_heartbeat(OKX_SOURCE)
                        continue
                    if raw == "pong" or raw == b"pong":
                        await manager.source_heartbeat(OKX_SOURCE)
                        continue
                    received_at_ms = time.time_ns() // 1_000_000
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        await manager.parse_error(OKX_SOURCE, "OKX message is not an object")
                        continue
                    if payload.get("event") == "error":
                        raise ValueError(
                            f"OKX WebSocket error {payload.get('code', 'unknown')}: "
                            f"{str(payload.get('msg', 'subscription error'))[:200]}"
                        )
                    if _is_okx_liquidation_payload(payload):
                        try:
                            events = parse_okx_liquidation_orders(
                                payload,
                                received_at_ms=received_at_ms,
                                instruments=instruments,
                                allowed_symbols=symbols,
                            )
                        except (KeyError, TypeError, ValueError) as error:
                            await manager.parse_error(OKX_SOURCE, error)
                            continue
                        for event in events:
                            if event.symbol in allowed_symbols:
                                # The accepted isolated parser keeps its immutable source identity.
                                # The live integration maps only the emitted venue label to the
                                # public Liquid20 contract without rewriting accepted archives.
                                await manager.append_event(replace(event, source=OKX_SOURCE))
                    await manager.source_heartbeat(OKX_SOURCE)
        except asyncio.CancelledError:
            raise
        except EXPECTED_CONNECTION_EXCEPTIONS + (
            json.JSONDecodeError,
            TypeError,
            KeyError,
        ) as error:
            await manager.disconnected(OKX_SOURCE, error)
            await _bounded_backoff_sleep(reconnect_delay, stop_event)
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)
        else:
            await manager.disconnected(OKX_SOURCE, "subscription universe refresh")


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
    if (
        trading_credentials_present_in_environment()
        or trading_credentials_present()
        or okx_credentials_present()
    ):
        raise RuntimeError(
            "trading credentials are present; live data-only collector refuses to start"
        )

    manager = OkxLiveRunManager(
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

    bybit_discovery = partial(discover_bybit_symbols, maximum_symbols=maximum_symbols)
    binance_discovery = partial(discover_binance_symbols, maximum_symbols=maximum_symbols)
    okx_discovery = partial(discover_okx_instruments, maximum_symbols=maximum_symbols)
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
        asyncio.create_task(
            run_okx_source(
                manager,
                stop_event,
                discovery=okx_discovery,
                refresh_seconds=symbol_refresh_seconds,
            ),
            name="liquidations-okx-live",
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
        description="Run the continuous public three-source liquidation collector.",
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
