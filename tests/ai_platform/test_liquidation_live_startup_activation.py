from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType

if importlib.util.find_spec("websockets") is None:
    websockets_stub = ModuleType("websockets")
    websockets_exceptions_stub = ModuleType("websockets.exceptions")

    class WebSocketException(Exception):
        pass

    websockets_exceptions_stub.__dict__["WebSocketException"] = WebSocketException
    websockets_stub.__dict__["exceptions"] = websockets_exceptions_stub
    sys.modules["websockets"] = websockets_stub
    sys.modules["websockets.exceptions"] = websockets_exceptions_stub

live_stream = importlib.import_module("ai_platform.scripts.liquidation_live_stream")
okx_stream = importlib.import_module("ai_platform.scripts.liquidation_live_stream_okx")
BINANCE_SOURCE = live_stream.BINANCE_SOURCE
BYBIT_SOURCE = live_stream.BYBIT_SOURCE
OKX_SOURCE = live_stream.OKX_SOURCE
OkxLiveRunManager = okx_stream.OkxLiveRunManager

COLLECTOR_COMMIT = "a" * 40


def _manager(tmp_path: Path, writes: list[dict[str, bool]]) -> OkxLiveRunManager:
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit=COLLECTOR_COMMIT,
        host_id="test-host",
        now_ms=lambda: 1_000,
    )

    def record_write() -> None:
        writes.append({source: state.connected for source, state in manager.sources.items()})

    manager._write_state = record_write  # type: ignore[method-assign]
    return manager


def test_startup_activation_defers_partial_state_writes(tmp_path: Path) -> None:
    writes: list[dict[str, bool]] = []
    manager = _manager(tmp_path, writes)

    async def scenario() -> None:
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)
        assert writes == []
        assert all(state.connected is False for state in manager.sources.values())

        await manager.connected(OKX_SOURCE)

    asyncio.run(scenario())

    assert writes == [
        {
            BYBIT_SOURCE: True,
            BINANCE_SOURCE: True,
            OKX_SOURCE: True,
        }
    ]
    assert all(state.connected is True for state in manager.sources.values())


def test_preactivation_disconnect_discards_stale_source_atomically(tmp_path: Path) -> None:
    writes: list[dict[str, bool]] = []
    manager = _manager(tmp_path, writes)

    async def scenario() -> None:
        await manager.connected(BYBIT_SOURCE)
        await manager.disconnected(BYBIT_SOURCE, "socket closed")
        await manager.connected(BINANCE_SOURCE)
        await manager.connected(OKX_SOURCE)

        assert len(writes) == 1
        assert all(state.connected is False for state in manager.sources.values())
        assert manager.sources[BYBIT_SOURCE].reconnect_count == 1
        assert manager.sources[BYBIT_SOURCE].error_count == 1

        await manager.connected(BYBIT_SOURCE)

    asyncio.run(scenario())

    assert len(writes) == 2
    assert all(writes[-1].values())
    assert all(state.connected is True for state in manager.sources.values())
