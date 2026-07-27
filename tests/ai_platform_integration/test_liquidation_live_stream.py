from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide, LiquidationEvent
from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    LIVE_STATE_FILE,
    RUN_STATE_FILE,
    LiveRunManager,
    discover_binance_symbols,
    discover_bybit_symbols,
    redact_error,
)


def event(
    source: str,
    event_id: str,
    occurred_at_ms: int,
    symbol: str = "XRPUSDT",
) -> LiquidationEvent:
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=event_id,
        symbol=symbol,
        liquidated_position_side=LiquidatedPositionSide.LONG,
        occurred_at_ms=occurred_at_ms,
        received_at_ms=occurred_at_ms + 25,
        price=Decimal("1.25"),
        quantity=Decimal("40"),
        notional_usd=Decimal("50"),
        raw_side="Sell",
    )


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_live_manager_advances_heartbeat_appends_and_rotates_without_mutating_old_data(
    tmp_path: Path,
) -> None:
    now = [1_784_956_800_000]
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="a" * 40,
        host_id="synology-test",
        now_ms=lambda: now[0],
        flush_interval_seconds=0.01,
    )

    async def scenario() -> None:
        await manager.start()
        first_run_id = manager.run_id
        first_run_root = manager.run_root
        initial = read_json(tmp_path / "live" / LIVE_STATE_FILE)
        initial_state = initial["state"]
        assert isinstance(initial_state, dict)
        assert initial_state["run_state"] == "active"
        assert initial_state["last_event_at_ms"] is None

        now[0] += 5_000
        await manager.heartbeat()
        heartbeat = read_json(tmp_path / "live" / LIVE_STATE_FILE)
        heartbeat_state = heartbeat["state"]
        assert isinstance(heartbeat_state, dict)
        assert heartbeat_state["collector_heartbeat_at_ms"] == now[0]
        assert heartbeat_state["last_event_at_ms"] is None

        await manager.connected(BYBIT_SOURCE)
        await manager.append_event(event(BYBIT_SOURCE, "event-1", now[0] - 25))
        await manager.heartbeat()
        first_bytes = (first_run_root / "bybit-linear.ndjson").read_bytes()
        assert first_bytes.endswith(b"\n")
        assert b'"source_event_id":"event-1"' in first_bytes

        now[0] += 24 * 60 * 60 * 1_000
        await manager.heartbeat()
        assert manager.run_id != first_run_id
        assert (first_run_root / "bybit-linear.ndjson").read_bytes() == first_bytes
        completed = read_json(first_run_root / RUN_STATE_FILE)
        assert completed["run_state"] == "completed"
        assert completed["completion_reason"] == "daily-rotation"
        current = read_json(tmp_path / "live" / LIVE_STATE_FILE)
        assert current["active_run_id"] == manager.run_id
        assert (manager.run_root / "bybit-linear.ndjson").is_file()
        await manager.stop()

    asyncio.run(scenario())


def test_disconnect_reconnect_state_is_counted_and_errors_are_redacted(tmp_path: Path) -> None:
    now = [1_784_956_800_000]
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="b" * 40,
        host_id="synology-test",
        now_ms=lambda: now[0],
    )

    async def scenario() -> None:
        await manager.start()
        await manager.connected(BINANCE_SOURCE)
        await manager.disconnected(
            BINANCE_SOURCE,
            "wss://user:pass@example.invalid/ws?token=secret-value",
        )
        disconnected = read_json(manager.run_root / RUN_STATE_FILE)
        sources = disconnected["sources"]
        assert isinstance(sources, dict)
        binance = sources[BINANCE_SOURCE]
        assert isinstance(binance, dict)
        assert binance["connected"] is False
        assert binance["reconnect_count"] == 1
        assert binance["error_count"] == 1
        assert "secret-value" not in str(binance["latest_error"])
        assert "[redacted]" in str(binance["latest_error"])

        now[0] += 1_000
        await manager.connected(BINANCE_SOURCE)
        reconnected = read_json(manager.run_root / RUN_STATE_FILE)
        sources = reconnected["sources"]
        assert isinstance(sources, dict)
        binance = sources[BINANCE_SOURCE]
        assert isinstance(binance, dict)
        assert binance["connected"] is True
        assert binance["reconnect_count"] == 1
        assert binance["latest_error"] is None
        await manager.stop()

    asyncio.run(scenario())


def test_dynamic_symbol_discovery_is_validated_and_bounded() -> None:
    bybit_pages = iter(
        [
            {
                "retCode": 0,
                "result": {
                    "list": [
                        {
                            "symbol": "XRPUSDT",
                            "status": "Trading",
                            "quoteCoin": "USDT",
                            "contractType": "LinearPerpetual",
                        },
                        {
                            "symbol": "BTCUSD",
                            "status": "Trading",
                            "quoteCoin": "USD",
                            "contractType": "InversePerpetual",
                        },
                    ],
                    "nextPageCursor": "next",
                },
            },
            {
                "retCode": 0,
                "result": {
                    "list": [
                        {
                            "symbol": "ADAUSDT",
                            "status": "Trading",
                            "quoteCoin": "USDT",
                            "contractType": "LinearPerpetual",
                        }
                    ],
                    "nextPageCursor": "",
                },
            },
        ]
    )
    assert discover_bybit_symbols(fetch_json=lambda _url: next(bybit_pages)) == (
        "ADAUSDT",
        "XRPUSDT",
    )

    binance_payload = {
        "symbols": [
            {
                "symbol": "DOGEUSDT",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "ETHUSDT_240927",
                "status": "TRADING",
                "contractType": "CURRENT_QUARTER",
                "quoteAsset": "USDT",
            },
        ]
    }
    assert discover_binance_symbols(fetch_json=lambda _url: binance_payload) == ("DOGEUSDT",)
    with pytest.raises(ValueError, match="maximum must be"):
        discover_binance_symbols(maximum_symbols=0, fetch_json=lambda _url: binance_payload)


def test_live_state_contract_contains_no_trading_authority(tmp_path: Path) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="c" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_784_956_800_000,
    )

    async def scenario() -> None:
        await manager.start()
        payload = read_json(manager.run_root / RUN_STATE_FILE)
        assert payload["execution_enabled"] is False
        assert payload["trading_authorized"] is False
        assert payload["trading_credentials_present"] is False
        serialized = json.dumps(payload).lower()
        assert "api_key" not in serialized
        assert "api_secret" not in serialized
        await manager.stop()

    asyncio.run(scenario())


def test_error_redaction_is_bounded() -> None:
    error = redact_error("https://user:password@example.invalid/path?signature=abc")
    assert error is not None
    assert "password" not in error
    assert "signature=abc" not in error
    assert len(error) <= 500
