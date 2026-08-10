from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    LIVE_STATE_FILE,
    OKX_SOURCE,
    LiveRunManager,
)
from ai_platform.scripts.liquidation_live_stream_okx import OkxLiveRunManager


def _write_previous_active_run(
    data_root: Path,
    *,
    committed_rows: dict[str, int],
    actual_rows: dict[str, int],
) -> tuple[str, Path]:
    run_id = "liquid20-20260810T000000Z-1"
    run_root = data_root / "live" / "runs" / run_id
    run_root.mkdir(parents=True)
    sources = {
        source: {
            "configured": True,
            "connected": True,
            "events_written": committed_rows.get(source, 0),
        }
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE)
    }
    state = {
        "schema_version": 1,
        "contract": "liquidation-live-state-v1",
        "run_id": run_id,
        "run_state": "active",
        "data_mode": "live",
        "collector_started_at_ms": 1_786_362_979_860,
        "collector_heartbeat_at_ms": 1_786_382_100_000,
        "completed_at_ms": None,
        "completion_reason": None,
        "collector_commit": "1" * 40,
        "host_id": "synology-test",
        "execution_enabled": False,
        "trading_authorized": False,
        "trading_credentials_present": False,
        "orders_submitted": 0,
        "sources": sources,
    }
    (run_root / "run-state-v1.json").write_text(json.dumps(state), encoding="utf-8")
    (data_root / "live" / LIVE_STATE_FILE).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract": "liquidation-live-state-v1",
                "active_run_id": run_id,
                "collector_heartbeat_at_ms": state["collector_heartbeat_at_ms"],
                "state": state,
            }
        ),
        encoding="utf-8",
    )
    for source, count in actual_rows.items():
        (run_root / f"{source}.ndjson").write_bytes(b"{}\n" * count)
    return run_id, run_root


def test_state_commit_flushes_pending_ndjson_before_events_written(tmp_path: Path) -> None:
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="8" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
        flush_interval_seconds=3600.0,
    )

    async def scenario() -> None:
        await manager.start()
        writer = manager._writers[BINANCE_SOURCE]
        writer._handle.write("{}\\n")
        writer._pending = 1
        manager.sources[BINANCE_SOURCE].events_written = 1

        manager._write_state()

        assert writer._pending == 0
        assert (manager.run_root / f"{BINANCE_SOURCE}.ndjson").read_bytes() == b"{}\\n"
        state = json.loads((manager.run_root / "run-state-v1.json").read_text(encoding="utf-8"))
        assert state["sources"][BINANCE_SOURCE]["events_written"] == 1
        await manager.stop()

    asyncio.run(scenario())


def test_restart_truncates_only_uncommitted_suffix_before_completion(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 7, BYBIT_SOURCE: 2, OKX_SOURCE: 0},
    )
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="2" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        assert manager.run_id != old_run_id
        await manager.stop()

    asyncio.run(scenario())

    completed = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert completed["run_state"] == "completed"
    assert completed["completion_reason"] == "collector-restart"
    assert (old_run_root / f"{BINANCE_SOURCE}.ndjson").read_bytes() == b"{}\n" * 2
    assert (old_run_root / f"{BYBIT_SOURCE}.ndjson").read_bytes() == b"{}\n"
    assert (old_run_root / f"{OKX_SOURCE}.ndjson").read_bytes() == b""


def test_restart_rejects_missing_events_written_without_mutating_source(
    tmp_path: Path,
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    del state["sources"][BINANCE_SOURCE]["events_written"]
    state_path.write_text(json.dumps(state), encoding="utf-8")
    original = (old_run_root / f"{BINANCE_SOURCE}.ndjson").read_bytes()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="9" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="binance-usdm events_written is missing"):
        asyncio.run(manager.start())

    assert (old_run_root / f"{BINANCE_SOURCE}.ndjson").read_bytes() == original
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id
    assert sorted(path.name for path in (tmp_path / "live" / "runs").iterdir()) == [old_run_id]


def test_restart_rejects_missing_configured_zero_row_source(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    (old_run_root / f"{OKX_SOURCE}.ndjson").unlink()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="5" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="okx-swap source file is missing"):
        asyncio.run(manager.start())

    persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


def test_restart_allows_missing_unconfigured_zero_row_source(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    (old_run_root / f"{OKX_SOURCE}.ndjson").unlink()
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["sources"][OKX_SOURCE]["configured"] = False
    state["sources"][OKX_SOURCE]["connected"] = False
    state_path.write_text(json.dumps(state), encoding="utf-8")
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="6" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        assert manager.run_id != old_run_id
        await manager.stop()

    asyncio.run(scenario())
    completed = json.loads(state_path.read_text(encoding="utf-8"))
    assert completed["run_state"] == "completed"
    assert completed["completion_reason"] == "collector-restart"


def test_restart_rejects_incomplete_source_state_set(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    del state["sources"][OKX_SOURCE]
    state_path.write_text(json.dumps(state), encoding="utf-8")
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="7" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="previous live source set is invalid"):
        asyncio.run(manager.start())

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


def test_restart_rejects_symlinked_run_root_without_mutating_external_target(
    tmp_path: Path,
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    external_root = tmp_path / "external-run"
    old_run_root.rename(external_root)
    old_run_root.symlink_to(external_root, target_is_directory=True)
    external_source = external_root / f"{BINANCE_SOURCE}.ndjson"
    original = external_source.read_bytes()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="a" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="previous live run root is not a regular directory"):
        asyncio.run(manager.start())

    assert external_source.read_bytes() == original
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id
    assert old_run_root.is_symlink()


def test_restart_rejects_dangling_symlink_even_with_zero_committed_rows(
    tmp_path: Path,
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 0, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    okx_path = old_run_root / f"{OKX_SOURCE}.ndjson"
    okx_path.unlink()
    okx_path.symlink_to(old_run_root / "missing-okx.ndjson")
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="4" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="okx-swap source path is not a regular file"):
        asyncio.run(manager.start())

    persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id
    assert sorted(path.name for path in (tmp_path / "live" / "runs").iterdir()) == [old_run_id]


def test_restart_fails_closed_when_committed_rows_are_missing(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="3" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(
        RuntimeError, match="binance-usdm source file has fewer rows than committed"
    ):
        asyncio.run(manager.start())

    persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    assert (
        json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))[
            "active_run_id"
        ]
        == old_run_id
    )
    assert sorted(path.name for path in (tmp_path / "live" / "runs").iterdir()) == [old_run_id]
