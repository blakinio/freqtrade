from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide, LiquidationEvent
from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    LIVE_STATE_FILE,
)
from ai_platform.scripts.liquidation_live_stream_okx import (
    OKX_INSTRUMENT_SNAPSHOT_FILE,
    OKX_SOURCE,
    OkxLiveRunManager,
    discover_okx_instruments,
)
from ai_platform.scripts.liquidation_operational_health import REQUIRED_SOURCES


ROOT = Path(__file__).resolve().parents[2]


def _instrument_row(
    inst_id: str,
    *,
    ct_val: str = "0.01",
    ct_mult: str = "1",
    settle: str = "USDT",
    contract_type: str = "linear",
    state: str = "live",
) -> dict[str, object]:
    return {
        "instType": "SWAP",
        "instId": inst_id,
        "ctVal": ct_val,
        "ctMult": ct_mult,
        "ctValCcy": inst_id.split("-")[0],
        "settleCcy": settle,
        "ctType": contract_type,
        "state": state,
    }


def _event(source: str, event_id: str, occurred_at_ms: int) -> LiquidationEvent:
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=event_id,
        symbol="BTCUSDT",
        liquidated_position_side=LiquidatedPositionSide.LONG,
        occurred_at_ms=occurred_at_ms,
        received_at_ms=occurred_at_ms + 20,
        price=Decimal("70000"),
        quantity=Decimal("0.01"),
        notional_usd=Decimal("700"),
        raw_side="sell:long",
    )


def _read(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_okx_live_discovery_filters_to_supported_public_usdt_swaps() -> None:
    payload = {
        "code": "0",
        "data": [
            _instrument_row("BTC-USDT-SWAP"),
            _instrument_row("ETH-USDT-SWAP", ct_val="0.1"),
            _instrument_row("DOGE-USDT-SWAP", ct_mult="10"),
            _instrument_row("BTC-USD-SWAP", settle="BTC", contract_type="inverse"),
            _instrument_row("XRP-USDT-SWAP", state="suspend"),
        ],
    }

    symbols, instruments, snapshot = discover_okx_instruments(
        fetch_json=lambda _url: payload,
        maximum_symbols=10,
        now_ms=lambda: 1_750_000_000_000,
    )

    assert symbols == ("BTCUSDT", "ETHUSDT")
    assert set(instruments) == {"BTC-USDT-SWAP", "ETH-USDT-SWAP"}
    assert snapshot["snapshot_type"] == "okx_public_swap_instruments"
    assert snapshot["fetched_at_ms"] == 1_750_000_000_000


def test_okx_live_manager_registers_separate_state_files_and_zero_orders(tmp_path: Path) -> None:
    now = [1_784_956_800_000]
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="d" * 40,
        host_id="synology-test",
        now_ms=lambda: now[0],
        flush_interval_seconds=0.01,
    )

    async def scenario() -> None:
        await manager.start()
        await manager.set_okx_instruments(
            ("BTCUSDT", "ETHUSDT"),
            {
                "schema_version": 1,
                "snapshot_type": "okx_public_swap_instruments",
                "source": "okx-usdt-swap",
                "fetched_at_ms": now[0],
                "endpoint": "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
                "contracts": [],
                "normalization_policy": {},
            },
        )
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)
        await manager.connected(OKX_SOURCE)
        await manager.append_event(_event(OKX_SOURCE, "okx-1", now[0] - 20))
        await manager.heartbeat()

        state = _read(tmp_path / "live" / LIVE_STATE_FILE)["state"]
        assert isinstance(state, dict)
        sources = state["sources"]
        assert isinstance(sources, dict)
        assert set(sources) == {BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE}
        okx = sources[OKX_SOURCE]
        assert isinstance(okx, dict)
        assert okx["configured"] is True
        assert okx["connected"] is True
        assert okx["subscription_symbol_count"] == 2
        assert okx["events_written"] == 1
        assert okx["observed_symbol_count"] == 1
        assert okx["parse_error_count"] == 0
        assert okx["ingest_lag_ms"] == 20
        assert state["orders_submitted"] == 0

        output = manager.run_root / "okx-swap.ndjson"
        assert output.read_text(encoding="utf-8").count("\n") == 1
        assert '"source":"okx-swap"' in output.read_text(encoding="utf-8")
        assert (manager.run_root / OKX_INSTRUMENT_SNAPSHOT_FILE).is_file()
        summary = _read(manager.run_root / "okx-swap-summary.json")
        assert summary["orders_submitted"] == 0
        assert summary["trading_credentials_present"] is False
        assert summary["execution_enabled"] is False
        await manager.stop()

    asyncio.run(scenario())


def test_okx_failure_does_not_rewrite_other_source_state(tmp_path: Path) -> None:
    now = [1_784_956_800_000]
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="e" * 40,
        host_id="synology-test",
        now_ms=lambda: now[0],
    )

    async def scenario() -> None:
        await manager.start()
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)
        await manager.connected(OKX_SOURCE)
        await manager.disconnected(OKX_SOURCE, "connection token=sensitive")
        state = _read(manager.run_root / "run-state-v1.json")
        sources = state["sources"]
        assert isinstance(sources, dict)
        assert sources[BYBIT_SOURCE]["connected"] is True
        assert sources[BINANCE_SOURCE]["connected"] is True
        assert sources[OKX_SOURCE]["connected"] is False
        assert sources[OKX_SOURCE]["reconnect_count"] == 1
        assert "sensitive" not in str(sources[OKX_SOURCE]["latest_error"])
        await manager.stop()

    asyncio.run(scenario())


def test_old_disabled_okx_live_state_migrates_to_new_active_run(tmp_path: Path) -> None:
    old_run_id = "liquid20-20260729T000000Z-0"
    old_root = tmp_path / "live" / "runs" / old_run_id
    old_root.mkdir(parents=True)
    (old_root / f"{BYBIT_SOURCE}.ndjson").write_text("", encoding="utf-8")
    (old_root / f"{BINANCE_SOURCE}.ndjson").write_text("", encoding="utf-8")
    old_state = {
        "schema_version": 1,
        "contract": "liquidation-live-state-v1",
        "run_id": old_run_id,
        "run_state": "active",
        "data_mode": "live",
        "collector_started_at_ms": 1_784_870_400_000,
        "collector_heartbeat_at_ms": 1_784_870_405_000,
        "last_event_at_ms": None,
        "last_event_received_at_ms": None,
        "completed_at_ms": None,
        "completion_reason": None,
        "collector_commit": "f" * 40,
        "host_id": "old",
        "execution_enabled": False,
        "trading_authorized": False,
        "trading_credentials_present": False,
        "sources": {
            BYBIT_SOURCE: {"configured": True, "events_written": 0},
            BINANCE_SOURCE: {"configured": True, "events_written": 0},
            OKX_SOURCE: {"configured": False, "events_written": 0},
        },
    }
    (old_root / "run-state-v1.json").write_text(json.dumps(old_state), encoding="utf-8")
    (tmp_path / "live" / LIVE_STATE_FILE).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract": "liquidation-live-state-v1",
                "active_run_id": old_run_id,
                "collector_heartbeat_at_ms": old_state["collector_heartbeat_at_ms"],
                "state": old_state,
            }
        ),
        encoding="utf-8",
    )

    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="1" * 40,
        host_id="new",
        now_ms=lambda: 1_784_956_800_000,
    )

    async def scenario() -> None:
        await manager.start()
        completed = _read(old_root / "run-state-v1.json")
        assert completed["run_state"] == "completed"
        assert completed["completion_reason"] == "collector-restart"
        current = _read(tmp_path / "live" / LIVE_STATE_FILE)["state"]
        assert isinstance(current, dict)
        assert current["sources"][OKX_SOURCE]["configured"] is True
        assert current["orders_submitted"] == 0
        assert manager.run_id != old_run_id
        await manager.stop()

    asyncio.run(scenario())


def test_operational_portal_and_deployment_contracts_require_okx() -> None:
    assert REQUIRED_SOURCES == (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE)

    entrypoint = (ROOT / "deploy/synology/liquid20/live-entrypoint.sh").read_text(encoding="utf-8")
    verify = (ROOT / "deploy/synology/liquid20/verify-okx-live.sh").read_text(encoding="utf-8")
    portal_reader = (ROOT / "ai_platform/portal/web/lib/liquidations/reader.ts").read_text(
        encoding="utf-8"
    )
    portal_ui = (
        ROOT / "ai_platform/portal/web/components/liquidations-live-dashboard.tsx"
    ).read_text(encoding="utf-8")

    assert "liquidation_live_stream_okx" in entrypoint
    for credential in ("OKX_API_KEY", "OKX_API_SECRET", "OKX_SECRET_KEY", "OKX_PASSPHRASE"):
        assert credential in entrypoint
    assert "orders_submitted" in verify
    assert "okx-swap.ndjson" in verify
    assert '"okx-swap"' in portal_reader
    assert "OKX SWAP" in portal_ui
    assert "Błędy parsera" in portal_ui
    assert '<option value="okx-swap">OKX SWAP</option>' in portal_ui


def test_portal_has_no_direct_okx_or_collector_network_connection() -> None:
    portal_root = ROOT / "ai_platform" / "portal" / "web"
    inspected = [
        portal_root / "lib/liquidations/reader.ts",
        portal_root / "lib/liquidations/live-reader.ts",
        portal_root / "components/liquidations-live-dashboard.tsx",
        portal_root / "app/api/market/liquidations/_shared.ts",
    ]
    contents = "\n".join(path.read_text(encoding="utf-8") for path in inspected)
    assert "wss://ws.okx.com" not in contents
    assert "api/v5/public/instruments" not in contents
    assert "WebSocket(" not in contents
    assert "/api/market/liquidations" in contents


def test_daily_rotation_resets_reconnect_counter_with_new_epoch(tmp_path: Path) -> None:
    now = [1_785_801_599_000]
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="2" * 40,
        host_id="synology-test",
        now_ms=lambda: now[0],
        flush_interval_seconds=0.01,
    )

    async def scenario() -> None:
        await manager.start()
        await manager.connected(BYBIT_SOURCE)
        await manager.connected(BINANCE_SOURCE)
        await manager.connected(OKX_SOURCE)
        for _ in range(3):
            await manager.disconnected(OKX_SOURCE, "transient network failure")
            await manager.connected(OKX_SOURCE)

        before = _read(tmp_path / "live" / LIVE_STATE_FILE)["state"]
        assert before["sources"][OKX_SOURCE]["reconnect_count"] == 3

        now[0] = 1_785_801_601_000
        await manager.heartbeat()

        after = _read(tmp_path / "live" / LIVE_STATE_FILE)["state"]
        assert after["run_id"].startswith("liquid20-20260804T000000Z-")
        assert after["collector_started_at_ms"] == now[0]
        assert after["sources"][OKX_SOURCE]["connected"] is True
        assert after["sources"][OKX_SOURCE]["reconnect_count"] == 0
        await manager.stop()

    asyncio.run(scenario())
