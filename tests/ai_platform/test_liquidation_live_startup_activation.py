from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable

from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    OKX_SOURCE,
)
from ai_platform.scripts.liquidation_live_stream_okx import OkxLiveRunManager


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


def _run(operation: Callable[[], object]) -> None:
    asyncio.run(operation())  # type: ignore[misc]


def test_startup_activation_defers_partial_state_writes(tmp_path: Path) -> None:
    writes: list[dict[str, bool]] = []
    manager = _manager(tmp_path, writes)

    async def scenario() -> None:
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)
        assert writes == []
        assert all(state.connected is False for state in manager.sources.values())

        await manager.connected(OKX_SOURCE)

    _run(scenario)

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

    _run(scenario)

    assert len(writes) == 2
    assert all(writes[-1].values())
    assert all(state.connected is True for state in manager.sources.values())
