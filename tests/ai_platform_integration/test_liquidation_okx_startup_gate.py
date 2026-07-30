from __future__ import annotations

import asyncio
import json
from pathlib import Path

from ai_platform.scripts.liquidation_live_stream import BINANCE_SOURCE, BYBIT_SOURCE, OKX_SOURCE
from ai_platform.scripts.liquidation_live_stream_okx import OkxLiveRunManager


def _state(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_initial_readiness_waits_for_binance_bybit_and_okx(tmp_path: Path) -> None:
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="a" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_784_956_800_000,
    )

    async def scenario() -> None:
        await manager.start()
        await manager.set_subscription(BYBIT_SOURCE, ("BTCUSDT",))
        await manager.set_subscription(BINANCE_SOURCE, ("BTCUSDT",))
        await manager.set_okx_instruments(
            ("BTCUSDT",),
            {
                "schema_version": 1,
                "snapshot_type": "okx_public_swap_instruments",
                "source": "okx-usdt-swap",
                "fetched_at_ms": 1_784_956_800_000,
                "endpoint": "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
                "contracts": [],
                "normalization_policy": {},
            },
        )
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)

        pending = _state(manager.run_root / "run-state-v1.json")
        sources = pending["sources"]
        assert isinstance(sources, dict)
        assert sources[BYBIT_SOURCE]["connected"] is False
        assert sources[BINANCE_SOURCE]["connected"] is False
        assert sources[OKX_SOURCE]["connected"] is False

        await manager.connected(OKX_SOURCE)
        ready = _state(manager.run_root / "run-state-v1.json")
        sources = ready["sources"]
        assert isinstance(sources, dict)
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE):
            assert sources[source]["configured"] is True
            assert sources[source]["connected"] is True
            assert sources[source]["subscription_symbol_count"] == 1
        await manager.stop()

    asyncio.run(scenario())
