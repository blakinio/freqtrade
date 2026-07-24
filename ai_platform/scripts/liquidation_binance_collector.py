from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.request
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import websockets
from websockets.exceptions import WebSocketException

from ai_platform.research.liquidations.binance import parse_binance_force_order
from ai_platform.research.liquidations.contracts import LiquidationEvent, integer_value
from ai_platform.research.liquidations.staging import (
    ClockProbeResult,
    CollectorRunStats,
    build_collector_summary,
    trading_credentials_present_in_environment,
    write_json_atomic,
)
from ai_platform.scripts.liquidation_collector import RecentEventIds


DEFAULT_BINANCE_ENDPOINT = "wss://fstream.binance.com/market/ws"
DEFAULT_BINANCE_TIME_URL = "https://fapi.binance.com/fapi/v1/time"
EXPECTED_CONNECTION_EXCEPTIONS = (OSError, ValueError, WebSocketException)
BINANCE_CREDENTIAL_ENVIRONMENT_NAMES = (
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "BINANCE_SECRET_KEY",
)


def _subscription(symbols: Iterable[str]) -> str:
    streams = [f"{symbol.strip().lower()}@forceOrder" for symbol in symbols if symbol.strip()]
    if not streams:
        raise ValueError("at least one symbol is required")
    return json.dumps(
        {"method": "SUBSCRIBE", "params": streams, "id": 1},
        separators=(",", ":"),
    )


def _prepare_output_path(output_path: Path, *, require_new_output: bool) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    initial_size = output_path.stat().st_size if output_path.exists() else 0
    if require_new_output and initial_size != 0:
        raise FileExistsError(f"staging output already contains data: {output_path}")
    output_path.touch(exist_ok=True)
    return initial_size


def _append_events(output_path: Path, events: Sequence[LiquidationEvent]) -> None:
    with output_path.open("a", encoding="utf-8") as output:
        for event in events:
            output.write(json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True))
            output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def _is_force_order_payload(payload: Mapping[str, object]) -> bool:
    if str(payload.get("e", "")) == "forceOrder":
        return True
    wrapped = payload.get("data")
    return isinstance(wrapped, dict) and str(wrapped.get("e", "")) == "forceOrder"


def _process_payload(
    payload: Mapping[str, object],
    *,
    received_at_ms: int,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> tuple[LiquidationEvent, ...]:
    if not _is_force_order_payload(payload):
        stats.record_message(received_at_ms, message_kind="control")
        return ()

    stats.record_message(received_at_ms, message_kind="liquidation")
    try:
        events = parse_binance_force_order(payload, received_at_ms=received_at_ms)
    except (KeyError, TypeError, ValueError):
        stats.parse_failures += 1
        return ()

    new_events = tuple(event for event in events if recent_ids.add_if_new(event.source_event_id))
    stats.record_events(
        events,
        written_count=len(new_events),
        duplicates=len(events) - len(new_events),
    )
    return new_events


def parse_binance_server_time_response(
    payload: Mapping[str, object],
    *,
    request_started_at_ms: int,
    request_ended_at_ms: int,
    tolerance_ms: int,
    server_time_url: str = DEFAULT_BINANCE_TIME_URL,
) -> ClockProbeResult:
    if request_ended_at_ms < request_started_at_ms:
        raise ValueError("request_ended_at_ms must be >= request_started_at_ms")
    if tolerance_ms < 0:
        raise ValueError("tolerance_ms must be >= 0")
    server_time_ms = integer_value(payload["serverTime"], field="serverTime")
    midpoint_ms = request_started_at_ms + (request_ended_at_ms - request_started_at_ms) // 2
    skew_ms = abs(server_time_ms - midpoint_ms)
    return ClockProbeResult(
        checked_at_ms=request_ended_at_ms,
        server_time_url=server_time_url,
        round_trip_ms=request_ended_at_ms - request_started_at_ms,
        absolute_skew_ms=skew_ms,
        tolerance_ms=tolerance_ms,
        synchronized=skew_ms <= tolerance_ms,
    )


def probe_binance_clock(
    *,
    server_time_url: str = DEFAULT_BINANCE_TIME_URL,
    tolerance_ms: int = 2_000,
    timeout_seconds: float = 10.0,
) -> ClockProbeResult:
    request_started_at_ms = time.time_ns() // 1_000_000
    try:
        request = urllib.request.Request(
            server_time_url,
            headers={"User-Agent": "freqtrade-liquidation-research/1"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = json.loads(response.read())
        request_ended_at_ms = time.time_ns() // 1_000_000
        if not isinstance(payload, dict):
            raise TypeError("Binance server-time response must be an object")
        return parse_binance_server_time_response(
            payload,
            request_started_at_ms=request_started_at_ms,
            request_ended_at_ms=request_ended_at_ms,
            tolerance_ms=tolerance_ms,
            server_time_url=server_time_url,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        request_ended_at_ms = time.time_ns() // 1_000_000
        return ClockProbeResult(
            checked_at_ms=request_ended_at_ms,
            server_time_url=server_time_url,
            round_trip_ms=request_ended_at_ms - request_started_at_ms,
            absolute_skew_ms=None,
            tolerance_ms=tolerance_ms,
            synchronized=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def trading_credentials_present() -> bool:
    if trading_credentials_present_in_environment():
        return True
    return any(os.environ.get(name, "").strip() for name in BINANCE_CREDENTIAL_ENVIRONMENT_NAMES)


def _remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _duration_complete(deadline: float | None) -> bool:
    remaining = _remaining_seconds(deadline)
    return remaining is not None and remaining <= 0


async def _process_raw_message(
    raw_message: str | bytes,
    *,
    output_path: Path,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> None:
    received_at_ms = time.time_ns() // 1_000_000
    try:
        payload = json.loads(raw_message)
    except (UnicodeDecodeError, json.JSONDecodeError):
        stats.record_message(received_at_ms, message_kind="malformed")
        stats.parse_failures += 1
        return
    if not isinstance(payload, dict):
        stats.record_message(received_at_ms, message_kind="malformed")
        stats.parse_failures += 1
        return

    events = _process_payload(
        payload,
        received_at_ms=received_at_ms,
        recent_ids=recent_ids,
        stats=stats,
    )
    if events:
        await asyncio.to_thread(_append_events, output_path, events)


async def _collect_one_connection(
    *,
    endpoint: str,
    subscription: str,
    deadline: float | None,
    output_path: Path,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> str:
    connection_opened = False
    close_reason = "connection_closed"
    disconnected = False
    try:
        async with websockets.connect(
            endpoint,
            ping_interval=180,
            ping_timeout=600,
            close_timeout=10,
            max_queue=10_000,
        ) as websocket:
            stats.connection_opened(time.time_ns() // 1_000_000)
            connection_opened = True
            await websocket.send(subscription)
            while True:
                if _duration_complete(deadline):
                    close_reason = "completed_duration"
                    return close_reason
                remaining = _remaining_seconds(deadline)
                receive_timeout = 30.0
                if remaining is not None:
                    receive_timeout = min(receive_timeout, max(0.1, remaining))
                try:
                    raw_message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=receive_timeout,
                    )
                except TimeoutError:
                    continue
                await _process_raw_message(
                    raw_message,
                    output_path=output_path,
                    recent_ids=recent_ids,
                    stats=stats,
                )
    except asyncio.CancelledError:
        close_reason = "cancelled"
        raise
    except EXPECTED_CONNECTION_EXCEPTIONS as exc:
        close_reason = type(exc).__name__
        disconnected = True
        if not connection_opened:
            stats.record_connection_failure()
        raise
    finally:
        if connection_opened:
            stats.connection_closed(
                time.time_ns() // 1_000_000,
                reason=close_reason,
                disconnected=disconnected,
            )


async def collect_binance_liquidations(
    *,
    endpoint: str,
    symbols: tuple[str, ...],
    output_path: Path,
    reconnect_max_seconds: float = 30.0,
    duration_seconds: float | None = None,
    summary_path: Path | None = None,
    collector_commit: str = "unknown",
    require_new_output: bool = False,
    clock_probe: ClockProbeResult | None = None,
    credentials_present: bool = False,
) -> CollectorRunStats:
    if duration_seconds is not None and duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if reconnect_max_seconds <= 0:
        raise ValueError("reconnect_max_seconds must be > 0")

    normalized_symbols = tuple(
        dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
    )
    subscription = _subscription(normalized_symbols)
    output_initial_size_bytes = await asyncio.to_thread(
        _prepare_output_path,
        output_path,
        require_new_output=require_new_output,
    )
    recent_ids = RecentEventIds()
    started_at_ms = time.time_ns() // 1_000_000
    stats = CollectorRunStats(started_at_ms=started_at_ms)
    deadline = time.monotonic() + duration_seconds if duration_seconds is not None else None
    reconnect_delay = 1.0
    final_status = "stopped"

    try:
        while not _duration_complete(deadline):
            try:
                status = await _collect_one_connection(
                    endpoint=endpoint,
                    subscription=subscription,
                    deadline=deadline,
                    output_path=output_path,
                    recent_ids=recent_ids,
                    stats=stats,
                )
                if status == "completed_duration":
                    final_status = status
                    break
            except asyncio.CancelledError:
                final_status = "cancelled"
                raise
            except EXPECTED_CONNECTION_EXCEPTIONS:
                if _duration_complete(deadline):
                    final_status = "completed_duration"
                    break
            remaining = _remaining_seconds(deadline)
            sleep_seconds = (
                reconnect_delay if remaining is None else min(reconnect_delay, remaining)
            )
            await asyncio.sleep(max(0.0, sleep_seconds))
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)
        if _duration_complete(deadline):
            final_status = "completed_duration"
    except asyncio.CancelledError:
        raise
    except Exception:
        final_status = "failed"
        raise
    finally:
        stats.finish(time.time_ns() // 1_000_000, status=final_status)
        if summary_path is not None:
            effective_clock_probe = clock_probe or ClockProbeResult(
                checked_at_ms=started_at_ms,
                server_time_url=DEFAULT_BINANCE_TIME_URL,
                round_trip_ms=None,
                absolute_skew_ms=None,
                tolerance_ms=2_000,
                synchronized=None,
                error="clock probe not supplied",
            )
            summary = build_collector_summary(
                stats=stats,
                endpoint=endpoint,
                symbols=normalized_symbols,
                output_path=output_path,
                output_initial_size_bytes=output_initial_size_bytes,
                collector_commit=collector_commit,
                clock_probe=effective_clock_probe,
                trading_credentials_present=credentials_present,
            )
            summary["source"] = "binance-usdm"
            summary["source_semantics"] = {
                "stream": "forceOrder",
                "coverage": "latest liquidation per symbol within each 1000ms window",
            }
            await asyncio.to_thread(write_json_atomic, summary_path, summary)
    return stats


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect public Binance USD-M liquidation events into canonical NDJSON.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        required=True,
        help="Binance USD-M symbol such as BTCUSDT. Repeat for multiple symbols.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default=DEFAULT_BINANCE_ENDPOINT)
    parser.add_argument("--duration-seconds", type=_positive_float)
    parser.add_argument("--summary", type=Path)
    parser.add_argument(
        "--collector-commit",
        default=os.environ.get("GITHUB_SHA", "unknown"),
    )
    parser.add_argument("--require-new-output", action="store_true")
    parser.add_argument("--clock-server-time-url", default=DEFAULT_BINANCE_TIME_URL)
    parser.add_argument("--clock-tolerance-ms", type=_non_negative_int, default=2_000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in args.symbol))
    clock_probe = None
    if args.summary is not None:
        clock_probe = probe_binance_clock(
            server_time_url=args.clock_server_time_url,
            tolerance_ms=args.clock_tolerance_ms,
        )
    asyncio.run(
        collect_binance_liquidations(
            endpoint=args.endpoint,
            symbols=symbols,
            output_path=args.output,
            duration_seconds=args.duration_seconds,
            summary_path=args.summary,
            collector_commit=args.collector_commit,
            require_new_output=args.require_new_output,
            clock_probe=clock_probe,
            credentials_present=trading_credentials_present(),
        )
    )


if __name__ == "__main__":
    main()
