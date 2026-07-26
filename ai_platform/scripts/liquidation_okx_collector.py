from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

import websockets
from websockets.exceptions import WebSocketException

from ai_platform.research.liquidations.contracts import LiquidationEvent, integer_value
from ai_platform.research.liquidations.okx import (
    OKX_USDT_SWAP_SOURCE,
    OkxInstrumentContract,
    parse_okx_instruments_response,
    parse_okx_liquidation_orders,
)
from ai_platform.research.liquidations.staging import (
    ClockProbeResult,
    CollectorRunStats,
    build_collector_summary,
    sha256_file,
    trading_credentials_present_in_environment,
    write_json_atomic,
)
from ai_platform.scripts.liquidation_collector import RecentEventIds


DEFAULT_OKX_ENDPOINT = "wss://ws.okx.com:8443/ws/v5/public"
DEFAULT_OKX_TIME_URL = "https://www.okx.com/api/v5/public/time"
DEFAULT_OKX_INSTRUMENTS_URL = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
EXPECTED_CONNECTION_EXCEPTIONS = (OSError, ValueError, WebSocketException)
OKX_CREDENTIAL_ENVIRONMENT_NAMES = (
    "OKX_API_KEY",
    "OKX_API_SECRET",
    "OKX_SECRET_KEY",
    "OKX_PASSPHRASE",
)


def _subscription() -> str:
    return json.dumps(
        {
            "op": "subscribe",
            "args": [{"channel": "liquidation-orders", "instType": "SWAP"}],
        },
        separators=(",", ":"),
    )


def _validated_https_url(url: str, *, field: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTPS URL")
    return url


def _load_public_json(url: str, *, timeout_seconds: float) -> Mapping[str, object]:
    validated_url = _validated_https_url(url, field="public_url")
    request = urllib.request.Request(  # noqa: S310
        validated_url,
        headers={"User-Agent": "freqtrade-liquidation-research/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("OKX public response must be an object")
    return payload


def parse_okx_server_time_response(
    payload: Mapping[str, object],
    *,
    request_started_at_ms: int,
    request_ended_at_ms: int,
    tolerance_ms: int,
    server_time_url: str = DEFAULT_OKX_TIME_URL,
) -> ClockProbeResult:
    if request_ended_at_ms < request_started_at_ms:
        raise ValueError("request_ended_at_ms must be >= request_started_at_ms")
    if tolerance_ms < 0:
        raise ValueError("tolerance_ms must be >= 0")
    if str(payload.get("code", "")) != "0":
        raise ValueError("OKX server-time response code must be 0")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("OKX server-time response must contain exactly one data row")
    server_time_ms = integer_value(data[0].get("ts"), field="data[0].ts")
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


def probe_okx_clock(
    *,
    server_time_url: str = DEFAULT_OKX_TIME_URL,
    tolerance_ms: int = 2_000,
    timeout_seconds: float = 10.0,
) -> ClockProbeResult:
    request_started_at_ms = time.time_ns() // 1_000_000
    try:
        payload = _load_public_json(server_time_url, timeout_seconds=timeout_seconds)
        request_ended_at_ms = time.time_ns() // 1_000_000
        return parse_okx_server_time_response(
            payload,
            request_started_at_ms=request_started_at_ms,
            request_ended_at_ms=request_ended_at_ms,
            tolerance_ms=tolerance_ms,
            server_time_url=server_time_url,
        )
    except (OSError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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


def fetch_okx_instruments(
    *,
    symbols: Sequence[str],
    instruments_url: str = DEFAULT_OKX_INSTRUMENTS_URL,
    timeout_seconds: float = 10.0,
) -> dict[str, OkxInstrumentContract]:
    payload = _load_public_json(instruments_url, timeout_seconds=timeout_seconds)
    return parse_okx_instruments_response(payload, requested_symbols=symbols)


def build_instrument_snapshot(
    *,
    instruments: Mapping[str, OkxInstrumentContract],
    instruments_url: str,
    fetched_at_ms: int,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "snapshot_type": "okx_public_swap_instruments",
        "source": OKX_USDT_SWAP_SOURCE,
        "fetched_at_ms": fetched_at_ms,
        "endpoint": instruments_url,
        "contracts": [instruments[inst_id].as_json_dict() for inst_id in sorted(instruments)],
        "normalization_policy": {
            "supported_contract_type": "linear",
            "supported_settle_currency": "USDT",
            "required_contract_multiplier": "1",
            "quantity_formula": "base_quantity = contracts * ctVal",
            "notional_formula": "notional_usd = base_quantity * bankruptcy_price",
        },
    }


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


def _is_liquidation_payload(payload: Mapping[str, object]) -> bool:
    arg = payload.get("arg")
    return (
        isinstance(arg, dict)
        and str(arg.get("channel", "")) == "liquidation-orders"
        and isinstance(payload.get("data"), list)
    )


def _process_payload(
    payload: Mapping[str, object],
    *,
    received_at_ms: int,
    instruments: Mapping[str, OkxInstrumentContract],
    allowed_symbols: Sequence[str],
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> tuple[LiquidationEvent, ...]:
    if payload.get("event") == "error":
        code = str(payload.get("code", "unknown"))
        message = str(payload.get("msg", "subscription error"))[:200]
        raise ValueError(f"OKX WebSocket error {code}: {message}")
    if not _is_liquidation_payload(payload):
        stats.record_message(received_at_ms, message_kind="control")
        return ()

    stats.record_message(received_at_ms, message_kind="liquidation")
    try:
        events = parse_okx_liquidation_orders(
            payload,
            received_at_ms=received_at_ms,
            instruments=instruments,
            allowed_symbols=allowed_symbols,
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


async def _process_raw_message(
    raw_message: str | bytes,
    *,
    output_path: Path,
    instruments: Mapping[str, OkxInstrumentContract],
    allowed_symbols: Sequence[str],
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> None:
    received_at_ms = time.time_ns() // 1_000_000
    if raw_message == "pong" or raw_message == b"pong":
        stats.record_message(received_at_ms, message_kind="control")
        return
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
        instruments=instruments,
        allowed_symbols=allowed_symbols,
        recent_ids=recent_ids,
        stats=stats,
    )
    if events:
        await asyncio.to_thread(_append_events, output_path, events)


def _remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _duration_complete(deadline: float | None) -> bool:
    remaining = _remaining_seconds(deadline)
    return remaining is not None and remaining <= 0


async def _collect_one_connection(
    *,
    endpoint: str,
    subscription: str,
    deadline: float | None,
    output_path: Path,
    instruments: Mapping[str, OkxInstrumentContract],
    allowed_symbols: Sequence[str],
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> str:
    connection_opened = False
    close_reason = "connection_closed"
    disconnected = False
    try:
        async with websockets.connect(
            endpoint,
            ping_interval=None,
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
                receive_timeout = 20.0
                if remaining is not None:
                    receive_timeout = min(receive_timeout, max(0.1, remaining))
                try:
                    raw_message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=receive_timeout,
                    )
                except TimeoutError:
                    if _duration_complete(deadline):
                        close_reason = "completed_duration"
                        return close_reason
                    await websocket.send("ping")
                    continue
                await _process_raw_message(
                    raw_message,
                    output_path=output_path,
                    instruments=instruments,
                    allowed_symbols=allowed_symbols,
                    recent_ids=recent_ids,
                    stats=stats,
                )
    except asyncio.CancelledError:
        close_reason = "cancelled"
        raise
    except EXPECTED_CONNECTION_EXCEPTIONS:
        close_reason = "connection_error"
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


def _validated_collection_symbols(
    symbols: Sequence[str],
    instruments: Mapping[str, OkxInstrumentContract],
) -> tuple[str, ...]:
    normalized = tuple(
        dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
    )
    if not normalized:
        raise ValueError("at least one symbol is required")
    selected = {item.canonical_symbol for item in instruments.values()}
    missing = sorted(set(normalized) - selected)
    if missing:
        raise ValueError(f"missing OKX instrument metadata for: {', '.join(missing)}")
    return normalized


async def _persist_instrument_snapshot(
    *,
    instruments: Mapping[str, OkxInstrumentContract],
    instruments_url: str,
    instrument_metadata_path: Path,
) -> str:
    snapshot = build_instrument_snapshot(
        instruments=instruments,
        instruments_url=instruments_url,
        fetched_at_ms=time.time_ns() // 1_000_000,
    )
    await asyncio.to_thread(write_json_atomic, instrument_metadata_path, snapshot)
    return await asyncio.to_thread(sha256_file, instrument_metadata_path)


async def _run_collection_loop(
    *,
    endpoint: str,
    symbols: tuple[str, ...],
    instruments: Mapping[str, OkxInstrumentContract],
    output_path: Path,
    deadline: float | None,
    reconnect_max_seconds: float,
    recent_ids: RecentEventIds,
    stats: CollectorRunStats,
) -> str:
    reconnect_delay = 1.0
    while not _duration_complete(deadline):
        try:
            status = await _collect_one_connection(
                endpoint=endpoint,
                subscription=_subscription(),
                deadline=deadline,
                output_path=output_path,
                instruments=instruments,
                allowed_symbols=symbols,
                recent_ids=recent_ids,
                stats=stats,
            )
            if status == "completed_duration":
                return status
        except asyncio.CancelledError:
            raise
        except EXPECTED_CONNECTION_EXCEPTIONS:
            if _duration_complete(deadline):
                return "completed_duration"
        remaining = _remaining_seconds(deadline)
        sleep_seconds = reconnect_delay if remaining is None else min(reconnect_delay, remaining)
        await asyncio.sleep(max(0.0, sleep_seconds))
        reconnect_delay = min(reconnect_delay * 2.0, reconnect_max_seconds)
    return "completed_duration" if _duration_complete(deadline) else "stopped"


def _okx_summary(
    *,
    stats: CollectorRunStats,
    endpoint: str,
    symbols: tuple[str, ...],
    output_path: Path,
    output_initial_size_bytes: int,
    collector_commit: str,
    clock_probe: ClockProbeResult,
    credentials_present: bool,
    instrument_metadata_path: Path,
    instruments_url: str,
    metadata_sha256: str,
    instrument_count: int,
) -> dict[str, object]:
    summary = build_collector_summary(
        stats=stats,
        endpoint=endpoint,
        symbols=symbols,
        output_path=output_path,
        output_initial_size_bytes=output_initial_size_bytes,
        collector_commit=collector_commit,
        clock_probe=clock_probe,
        trading_credentials_present=credentials_present,
    )
    source = summary["source"]
    if not isinstance(source, dict):
        raise TypeError("collector summary source must be an object")
    source["id"] = OKX_USDT_SWAP_SOURCE
    source["semantics"] = {
        "stream": "liquidation-orders",
        "subscription_scope": "all SWAP instruments with local canonical-symbol filtering",
        "price": "bankruptcy price (bkPx)",
        "raw_quantity": "contract count (sz)",
        "normalized_quantity": "base quantity using frozen public ctVal metadata",
        "status": "shadow_only_not_in_liquid20_v1",
    }
    summary["instrument_metadata"] = {
        "file_name": instrument_metadata_path.name,
        "endpoint": instruments_url,
        "sha256": metadata_sha256,
        "contract_count": instrument_count,
    }
    return summary


async def _write_okx_summary(
    *,
    summary_path: Path | None,
    stats: CollectorRunStats,
    endpoint: str,
    symbols: tuple[str, ...],
    output_path: Path,
    output_initial_size_bytes: int,
    collector_commit: str,
    clock_probe: ClockProbeResult | None,
    credentials_present: bool,
    instrument_metadata_path: Path,
    instruments_url: str,
    metadata_sha256: str,
    instrument_count: int,
    started_at_ms: int,
) -> None:
    if summary_path is None:
        return
    effective_clock_probe = clock_probe or ClockProbeResult(
        checked_at_ms=started_at_ms,
        server_time_url=DEFAULT_OKX_TIME_URL,
        round_trip_ms=None,
        absolute_skew_ms=None,
        tolerance_ms=2_000,
        synchronized=None,
        error="clock probe not supplied",
    )
    summary = _okx_summary(
        stats=stats,
        endpoint=endpoint,
        symbols=symbols,
        output_path=output_path,
        output_initial_size_bytes=output_initial_size_bytes,
        collector_commit=collector_commit,
        clock_probe=effective_clock_probe,
        credentials_present=credentials_present,
        instrument_metadata_path=instrument_metadata_path,
        instruments_url=instruments_url,
        metadata_sha256=metadata_sha256,
        instrument_count=instrument_count,
    )
    await asyncio.to_thread(write_json_atomic, summary_path, summary)


async def collect_okx_liquidations(
    *,
    endpoint: str,
    symbols: tuple[str, ...],
    instruments: Mapping[str, OkxInstrumentContract],
    instruments_url: str,
    instrument_metadata_path: Path,
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
    normalized_symbols = _validated_collection_symbols(symbols, instruments)
    output_initial_size_bytes = await asyncio.to_thread(
        _prepare_output_path,
        output_path,
        require_new_output=require_new_output,
    )
    metadata_sha256 = await _persist_instrument_snapshot(
        instruments=instruments,
        instruments_url=instruments_url,
        instrument_metadata_path=instrument_metadata_path,
    )

    recent_ids = RecentEventIds()
    started_at_ms = time.time_ns() // 1_000_000
    stats = CollectorRunStats(started_at_ms=started_at_ms)
    deadline = time.monotonic() + duration_seconds if duration_seconds is not None else None
    final_status = "stopped"
    try:
        final_status = await _run_collection_loop(
            endpoint=endpoint,
            symbols=normalized_symbols,
            instruments=instruments,
            output_path=output_path,
            deadline=deadline,
            reconnect_max_seconds=reconnect_max_seconds,
            recent_ids=recent_ids,
            stats=stats,
        )
    except asyncio.CancelledError:
        final_status = "cancelled"
        raise
    except Exception:
        final_status = "failed"
        raise
    finally:
        stats.finish(time.time_ns() // 1_000_000, status=final_status)
        await _write_okx_summary(
            summary_path=summary_path,
            stats=stats,
            endpoint=endpoint,
            symbols=normalized_symbols,
            output_path=output_path,
            output_initial_size_bytes=output_initial_size_bytes,
            collector_commit=collector_commit,
            clock_probe=clock_probe,
            credentials_present=credentials_present,
            instrument_metadata_path=instrument_metadata_path,
            instruments_url=instruments_url,
            metadata_sha256=metadata_sha256,
            instrument_count=len(instruments),
            started_at_ms=started_at_ms,
        )
    return stats


def trading_credentials_present() -> bool:
    if trading_credentials_present_in_environment():
        return True
    return any(os.environ.get(name, "").strip() for name in OKX_CREDENTIAL_ENVIRONMENT_NAMES)


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
        description="Collect public OKX USDT swap liquidation orders into canonical NDJSON.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        required=True,
        help="Canonical symbol such as BTCUSDT. Repeat for multiple symbols.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--instrument-metadata", type=Path, required=True)
    parser.add_argument("--endpoint", default=DEFAULT_OKX_ENDPOINT)
    parser.add_argument("--instruments-url", default=DEFAULT_OKX_INSTRUMENTS_URL)
    parser.add_argument("--duration-seconds", type=_positive_float)
    parser.add_argument(
        "--collector-commit",
        default=os.environ.get("GITHUB_SHA", "unknown"),
    )
    parser.add_argument("--require-new-output", action="store_true")
    parser.add_argument("--clock-server-time-url", default=DEFAULT_OKX_TIME_URL)
    parser.add_argument("--clock-tolerance-ms", type=_non_negative_int, default=2_000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in args.symbol))
    credentials_present = trading_credentials_present()
    if credentials_present:
        raise SystemExit("refusing to run with exchange or Freqtrade trading credentials")
    instruments = fetch_okx_instruments(
        symbols=symbols,
        instruments_url=args.instruments_url,
    )
    clock_probe = probe_okx_clock(
        server_time_url=args.clock_server_time_url,
        tolerance_ms=args.clock_tolerance_ms,
    )
    asyncio.run(
        collect_okx_liquidations(
            endpoint=args.endpoint,
            symbols=symbols,
            instruments=instruments,
            instruments_url=args.instruments_url,
            instrument_metadata_path=args.instrument_metadata,
            output_path=args.output,
            duration_seconds=args.duration_seconds,
            summary_path=args.summary,
            collector_commit=args.collector_commit,
            require_new_output=args.require_new_output,
            clock_probe=clock_probe,
            credentials_present=credentials_present,
        )
    )


if __name__ == "__main__":
    main()
