from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from collections import deque
from collections.abc import Iterable, Sequence
from pathlib import Path

import websockets
from websockets.exceptions import WebSocketException

from ai_platform.research.liquidations.bybit import parse_bybit_all_liquidation
from ai_platform.research.liquidations.contracts import LiquidationEvent


DEFAULT_BYBIT_ENDPOINT = "wss://stream.bybit.com/v5/public/linear"


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


def _prepare_output_path(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


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


async def collect_bybit_liquidations(
    *,
    endpoint: str,
    symbols: tuple[str, ...],
    output_path: Path,
    reconnect_max_seconds: float = 30.0,
) -> None:
    await asyncio.to_thread(_prepare_output_path, output_path)
    subscription = _subscription(symbols)
    recent_ids = RecentEventIds()
    reconnect_delay = 1.0

    while True:
        try:
            async with websockets.connect(
                endpoint,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_queue=10_000,
            ) as websocket:
                await websocket.send(subscription)
                reconnect_delay = 1.0
                async for raw_message in websocket:
                    received_at_ms = time.time_ns() // 1_000_000
                    payload = json.loads(raw_message)
                    if not isinstance(payload, dict):
                        continue
                    topic = str(payload.get("topic", ""))
                    if not topic.startswith("allLiquidation."):
                        continue
                    events = parse_bybit_all_liquidation(
                        payload,
                        received_at_ms=received_at_ms,
                    )
                    new_events = tuple(
                        event
                        for event in events
                        if recent_ids.add_if_new(event.source_event_id)
                    )
                    if new_events:
                        await asyncio.to_thread(_append_events, output_path, new_events)
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError, json.JSONDecodeError, WebSocketException):
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)


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
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in args.symbol))
    asyncio.run(
        collect_bybit_liquidations(
            endpoint=args.endpoint,
            symbols=symbols,
            output_path=args.output,
        )
    )


if __name__ == "__main__":
    main()
