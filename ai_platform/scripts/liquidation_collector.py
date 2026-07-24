from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import websockets
from websockets.exceptions import WebSocketException

from ai_platform.research.liquidations.bybit import parse_bybit_all_liquidation
from ai_platform.research.liquidations.contracts import LiquidationEvent
from ai_platform.research.liquidations.staging import (
    DEFAULT_BYBIT_TIME_URL,
    ClockProbeResult,
    CollectorRunStats,
    build_collector_summary,
    probe_bybit_clock,
    trading_credentials_present_in_environment,
    write_json_atomic,
)


DEFAULT_BYBIT_ENDPOINT = "wss://stream.bybit.com/v5/public/linear"
EXPECTED_CONNECTION_EXCEPTIONS = (OSError, ValueError, WebSocketException)


class RecentEventIds:
    def __init__(self, maximum_size: int = 100_000) -> None:
        if maximum_size < 1:
            raise ValueError("maximum_size must be >= 1")
        self._maximum_size = maximum_size
        self._ordered: deque[str] = deque()
        self._values: set[str] = set()

    def add_if_new(self, event_id: str) -> bool:
        if event_id in self._values:
            return False
        self._values.add(event_id)
        self._ordered.append(event_id)
        if len(self._ordered) > self._maximum_size:
            removed = self._ordered.popleft()
            self._values.remove(removed)
        return True


def _subscription(symbols: Iterable[str]) -> str:
    topics = [f"allLiquidation.{symbol.strip().upper()}" for symbol in symbols]
    if not topics:
        raise ValueError("at least one symbol is required")
    return json.dumps({"op": "subscribe", "args": topics}, separators=(",", ":"))


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
            output.write(
                json.dumps(
                    event.as_json_dict(),
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def _process_payload(
    payload: Mapping[str, object],
    *,
    received_at_ms: int,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> tuple[LiquidationEvent, ...]:
    topic = str(payload.get("topic", ""))
    if not topic.startswith("allLiquidation."):
        stats.record_message(received_at_ms, message_kind="control")
        return ()

    stats.record_message(received_at_ms, message_kind="liquidation")
    try:
        events = parse_bybit_all_liquidation(
            payload,
            received_at_ms=received_at_ms,
        )
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
    received_at_ms: int,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> None:
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

    new_events = _process_payload(
        payload,
        received_at_ms=received_at_ms,
        recent_ids=recent_ids,
        stats=stats,
    )
    if new_events:
        await asyncio.to_thread(_append_events, output_path, new_events)


async def _receive_until_deadline(
    websocket: Any,
    *,
    deadline: float | None,
    output_path: Path,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> str:
    while True:
        if _duration_complete(deadline):
            return "completed_duration"

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
            if _duration_complete(deadline):
                return "completed_duration"
            continue

        await _process_raw_message(
            raw_message,
            output_path=output_path,
            received_at_ms=time.time_ns() // 1_000_000,
            recent_ids=recent_ids,
            stats=stats,
        )


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
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
            max_queue=10_000,
        ) as websocket:
            stats.connection_opened(time.time_ns() // 1_000_000)
            connection_opened = True
            await websocket.send(subscription)
            close_reason = await _receive_until_deadline(
                websocket,
                deadline=deadline,
                output_path=output_path,
                recent_ids=recent_ids,
                stats=stats,
            )
            return close_reason
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


async def _sleep_before_reconnect(
    reconnect_delay: float,
    *,
    deadline: float | None,
) -> None:
    remaining = _remaining_seconds(deadline)
    sleep_seconds = reconnect_delay
    if remaining is not None:
        sleep_seconds = min(sleep_seconds, remaining)
    await asyncio.sleep(max(0.0, sleep_seconds))


async def collect_bybit_liquidations(
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
    trading_credentials_present: bool = False,
) -> CollectorRunStats:
    if duration_seconds is not None and duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if reconnect_max_seconds <= 0:
        raise ValueError("reconnect_max_seconds must be > 0")

    output_initial_size_bytes = await asyncio.to_thread(
        _prepare_output_path,
        output_path,
        require_new_output=require_new_output,
    )
    normalized_symbols = tuple(
        dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
    )
    subscription = _subscription(normalized_symbols)
    recent_ids = RecentEventIds()
    reconnect_delay = 1.0
    started_at_ms = time.time_ns() // 1_000_000
    stats = CollectorRunStats(started_at_ms=started_at_ms)
    deadline = time.monotonic() + duration_seconds if duration_seconds is not None else None
    final_status = "stopped"

    try:
        while not _duration_complete(deadline):
            try:
                connection_status = await _collect_one_connection(
                    endpoint=endpoint,
                    subscription=subscription,
                    deadline=deadline,
                    output_path=output_path,
                    recent_ids=recent_ids,
                    stats=stats,
                )
                if connection_status == "completed_duration":
                    final_status = connection_status
                    break
            except asyncio.CancelledError:
                final_status = "cancelled"
                raise
            except EXPECTED_CONNECTION_EXCEPTIONS:
                if _duration_complete(deadline):
                    final_status = "completed_duration"
                    break

            await _sleep_before_reconnect(reconnect_delay, deadline=deadline)
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)

        if _duration_complete(deadline):
            final_status = "completed_duration"
    except asyncio.CancelledError:
        raise
    except Exception:
        final_status = "failed"
        raise
    finally:
        ended_at_ms = time.time_ns() // 1_000_000
        stats.finish(ended_at_ms, status=final_status)
        if summary_path is not None:
            effective_clock_probe = clock_probe or ClockProbeResult(
                checked_at_ms=started_at_ms,
                server_time_url=DEFAULT_BYBIT_TIME_URL,
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
                trading_credentials_present=trading_credentials_present,
            )
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
        description="Collect public Bybit liquidation events into canonical NDJSON.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        required=True,
        help="Bybit linear symbol such as BTCUSDT. Repeat for multiple symbols.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Append-only canonical NDJSON output path.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_BYBIT_ENDPOINT,
        help="Bybit public linear WebSocket endpoint.",
    )
    parser.add_argument(
        "--duration-seconds",
        type=_positive_float,
        help="Stop after this bounded duration. Omit for continuous collection.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Write a machine-readable run summary and output SHA-256.",
    )
    parser.add_argument(
        "--collector-commit",
        default=os.environ.get("GITHUB_SHA", "unknown"),
        help="Git commit recorded in the staging summary.",
    )
    parser.add_argument(
        "--require-new-output",
        action="store_true",
        help="Fail if the output file already contains data.",
    )
    parser.add_argument(
        "--clock-server-time-url",
        default=DEFAULT_BYBIT_TIME_URL,
        help="Public Bybit server-time endpoint used for the clock probe.",
    )
    parser.add_argument(
        "--clock-tolerance-ms",
        type=_non_negative_int,
        default=2_000,
        help="Maximum accepted absolute local/server clock skew.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in args.symbol))
    clock_probe = None
    if args.summary is not None:
        clock_probe = probe_bybit_clock(
            server_time_url=args.clock_server_time_url,
            tolerance_ms=args.clock_tolerance_ms,
        )
    asyncio.run(
        collect_bybit_liquidations(
            endpoint=args.endpoint,
            symbols=symbols,
            output_path=args.output,
            duration_seconds=args.duration_seconds,
            summary_path=args.summary,
            collector_commit=args.collector_commit,
            require_new_output=args.require_new_output,
            clock_probe=clock_probe,
            trading_credentials_present=trading_credentials_present_in_environment(),
        )
    )


if __name__ == "__main__":
    main()
