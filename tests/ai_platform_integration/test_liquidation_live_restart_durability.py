from __future__ import annotations

import asyncio
import json
import os
import stat
from pathlib import Path

import pytest

from ai_platform.scripts.liquidation_live_stream import (
    BINANCE_SOURCE,
    BYBIT_SOURCE,
    LIVE_STATE_FILE,
    OKX_SOURCE,
    LiveRunManager,
    _seal_committed_ndjson,
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


def test_seal_fsyncs_exact_committed_file_without_truncation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / f"{BINANCE_SOURCE}.ndjson"
    payload = b"{}\n"
    path.write_bytes(payload)
    fsync_calls: list[int] = []
    monkeypatch.setattr(
        "ai_platform.scripts.liquidation_live_stream.os.fsync",
        lambda fd: fsync_calls.append(fd),
    )

    _seal_committed_ndjson(path, committed_rows=1, source=BINANCE_SOURCE, allow_missing=False)

    assert fsync_calls
    assert path.read_bytes() == payload


def test_state_commit_rejects_replaced_canonical_source_inode(tmp_path: Path) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="7" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
        flush_interval_seconds=3600.0,
    )

    async def scenario() -> None:
        await manager.start()
        source_path = manager.run_root / f"{BYBIT_SOURCE}.ndjson"
        detached_path = manager.run_root / "bybit-linear-detached.ndjson"
        source_path.rename(detached_path)
        source_path.write_bytes(b"")
        writer = manager._writers[BYBIT_SOURCE]
        writer._handle.write("{}\n")
        writer._pending = 1
        manager.sources[BYBIT_SOURCE].events_written = 1

        with pytest.raises(RuntimeError, match="source file changed after writer anchoring"):
            manager._write_state()

        persisted = json.loads((manager.run_root / "run-state-v1.json").read_text(encoding="utf-8"))
        assert persisted["sources"][BYBIT_SOURCE]["events_written"] == 0
        assert source_path.read_bytes() == b""
        assert detached_path.read_bytes() == b"{}\n"
        await manager.stop()

    with pytest.raises(RuntimeError, match="source file changed after writer anchoring"):
        asyncio.run(scenario())


@pytest.mark.parametrize(
    ("field", "value"), [("schema_version", 2), ("contract", "foreign-live-contract-v2")]
)
def test_restart_rejects_foreign_pointer_contract_before_sealing(
    tmp_path: Path, field: str, value: object
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 2, OKX_SOURCE: 0},
    )
    pointer_path = tmp_path / "live" / LIVE_STATE_FILE
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer[field] = value
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    originals = {
        source: (old_run_root / f"{source}.ndjson").read_bytes()
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE)
    }
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="c" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match="previous live pointer contract is invalid"):
        asyncio.run(manager.start())
    for source, original in originals.items():
        assert (old_run_root / f"{source}.ndjson").read_bytes() == original
    persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    assert json.loads(pointer_path.read_text(encoding="utf-8"))["active_run_id"] == old_run_id


def test_restart_preflights_all_sources_before_any_truncation(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BYBIT_SOURCE: 2, BINANCE_SOURCE: 2, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    del state["sources"][BINANCE_SOURCE]["events_written"]
    state_path.write_text(json.dumps(state), encoding="utf-8")
    bybit_path = old_run_root / f"{BYBIT_SOURCE}.ndjson"
    original = bybit_path.read_bytes()
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="d" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match="binance-usdm events_written is missing"):
        asyncio.run(manager.start())
    assert bybit_path.read_bytes() == original
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


def test_restart_rejects_fifo_metadata_without_blocking(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    (live_root / "runs").mkdir(parents=True)
    os.mkfifo(live_root / LIVE_STATE_FILE)
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="6" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="previous live state path is not a regular file"):
        asyncio.run(manager.start())


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


def test_stop_closes_retained_runtime_directory_descriptors(tmp_path: Path) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="e" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        retained = [manager._live_root_fd, manager._runs_root_fd, manager._run_root_fd]
        assert all(isinstance(descriptor, int) for descriptor in retained)

        await manager.stop()

        assert manager._live_root_fd is None
        assert manager._runs_root_fd is None
        assert manager._run_root_fd is None
        for descriptor in retained:
            assert descriptor is not None
            with pytest.raises(OSError):
                os.fstat(descriptor)

        await manager.stop()

    asyncio.run(scenario())


def test_stop_closes_retained_runtime_directory_descriptors_on_state_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="f" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        retained = [manager._live_root_fd, manager._runs_root_fd, manager._run_root_fd]
        assert all(isinstance(descriptor, int) for descriptor in retained)

        def fail_state_write() -> None:
            raise RuntimeError("forced final state write failure")

        monkeypatch.setattr(manager, "_write_state", fail_state_write)
        with pytest.raises(RuntimeError, match="forced final state write failure"):
            await manager.stop()

        assert manager._live_root_fd is None
        assert manager._runs_root_fd is None
        assert manager._run_root_fd is None
        for descriptor in retained:
            assert descriptor is not None
            with pytest.raises(OSError):
                os.fstat(descriptor)

        await manager.stop()

    asyncio.run(scenario())


def test_start_failure_closes_all_runtime_descriptors_when_writer_close_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="1" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    captured: dict[str, object] = {}

    def fail_initial_state(self: LiveRunManager) -> None:
        captured["fds"] = [self._live_root_fd, self._runs_root_fd, self._run_root_fd]
        writers = list(self._writers.values())
        captured["writers"] = writers

        def fail_close() -> None:
            raise OSError("forced startup writer close failure")

        monkeypatch.setattr(writers[0], "close", fail_close)
        raise OSError("forced initial state failure")

    monkeypatch.setattr(LiveRunManager, "_write_state", fail_initial_state)
    with pytest.raises(OSError, match="forced initial state failure"):
        asyncio.run(manager.start())
    assert manager._writers == {}
    assert manager._live_root_fd is None
    assert manager._runs_root_fd is None
    assert manager._run_root_fd is None
    for descriptor in captured["fds"]:
        assert descriptor is not None
        with pytest.raises(OSError):
            os.fstat(descriptor)
    writers = captured["writers"]
    assert all(writer.closed for writer in writers[1:])


def test_stop_closes_all_runtime_descriptors_when_writer_close_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="e" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        retained = [manager._live_root_fd, manager._runs_root_fd, manager._run_root_fd]
        writers = list(manager._writers.values())

        def fail_close() -> None:
            raise OSError("forced writer close failure")

        monkeypatch.setattr(writers[0], "close", fail_close)
        with pytest.raises(OSError, match="forced writer close failure"):
            await manager.stop()
        assert manager._writers == {}
        assert manager._live_root_fd is None
        assert manager._runs_root_fd is None
        assert manager._run_root_fd is None
        for descriptor in retained:
            assert descriptor is not None
            with pytest.raises(OSError):
                os.fstat(descriptor)
        assert all(writer.closed for writer in writers[1:])

    asyncio.run(scenario())


def test_stop_okx_summary_failure_is_restart_recoverable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_platform.scripts.liquidation_live_stream_okx as okx_module

    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="1" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        old_run_id = manager.run_id
        old_run_root = manager.run_root
        retained = [manager._live_root_fd, manager._runs_root_fd, manager._run_root_fd]
        real_write = okx_module._write_json_atomic_at
        failed = False

        def fail_completed_okx_summary_once(
            directory_fd: int, file_name: str, payload: dict[str, object]
        ) -> None:
            nonlocal failed
            if (
                not failed
                and file_name == "okx-swap-summary.json"
                and payload.get("run_state") == "completed"
            ):
                failed = True
                raise RuntimeError("forced completed OKX summary failure")
            real_write(directory_fd, file_name, payload)

        monkeypatch.setattr(
            okx_module,
            "_write_json_atomic_at",
            fail_completed_okx_summary_once,
        )
        with pytest.raises(RuntimeError, match="forced completed OKX summary failure"):
            await manager.stop()

        persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
        pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
        assert persisted["run_state"] == "active"
        assert pointer["active_run_id"] == old_run_id
        assert manager._live_root_fd is None
        assert manager._runs_root_fd is None
        assert manager._run_root_fd is None
        for descriptor in retained:
            assert descriptor is not None
            with pytest.raises(OSError):
                os.fstat(descriptor)

        recovery = OkxLiveRunManager(
            data_root=tmp_path,
            collector_commit="2" * 40,
            host_id="synology-test",
            now_ms=lambda: 1_786_384_683_793,
        )
        await recovery.start()
        assert recovery.run_id != old_run_id
        completed = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
        assert completed["run_state"] == "completed"
        assert completed["completion_reason"] == "collector-restart"
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE):
            summary = json.loads(
                (old_run_root / f"{source}-summary.json").read_text(encoding="utf-8")
            )
            assert summary["run_id"] == old_run_id
            assert summary["run_state"] == "completed"
        new_pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
        assert new_pointer["active_run_id"] == recovery.run_id
        await recovery.stop()

    asyncio.run(scenario())


def test_stop_pointer_failure_leaves_coherent_history_for_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_platform.scripts.liquidation_live_stream as stream_module

    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="3" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        old_run_id = manager.run_id
        old_run_root = manager.run_root
        real_write = stream_module._write_json_atomic_at
        failed = False

        def fail_completed_pointer_once(
            directory_fd: int, file_name: str, payload: dict[str, object]
        ) -> None:
            nonlocal failed
            if not failed and file_name == LIVE_STATE_FILE and payload.get("active_run_id") is None:
                failed = True
                raise RuntimeError("forced completed pointer failure")
            real_write(directory_fd, file_name, payload)

        monkeypatch.setattr(
            stream_module,
            "_write_json_atomic_at",
            fail_completed_pointer_once,
        )
        with pytest.raises(RuntimeError, match="forced completed pointer failure"):
            await manager.stop()

        persisted = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
        pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
        assert persisted["run_state"] == "completed"
        assert pointer["active_run_id"] == old_run_id
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE):
            summary = json.loads(
                (old_run_root / f"{source}-summary.json").read_text(encoding="utf-8")
            )
            assert summary["run_state"] == "completed"

        recovery = OkxLiveRunManager(
            data_root=tmp_path,
            collector_commit="4" * 40,
            host_id="synology-test",
            now_ms=lambda: 1_786_384_683_793,
        )
        await recovery.start()
        assert recovery.run_id != old_run_id
        new_pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
        assert new_pointer["active_run_id"] == recovery.run_id
        await recovery.stop()

    asyncio.run(scenario())


def test_runtime_artifacts_preserve_shared_gid_modes(tmp_path: Path) -> None:
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="5" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    async def scenario() -> None:
        await manager.start()
        assert stat.S_IMODE(manager.run_root.stat().st_mode) == 0o750
        for path in (
            manager.run_root / "bybit-linear.ndjson",
            manager.run_root / "binance-usdm.ndjson",
            manager.run_root / "run-state-v1.json",
            manager.run_root / "bybit-linear-summary.json",
            manager.run_root / "binance-usdm-summary.json",
            tmp_path / "live" / LIVE_STATE_FILE,
        ):
            assert stat.S_IMODE(path.stat().st_mode) == 0o640, path
        await manager.stop()

    previous_umask = os.umask(0o027)
    try:
        asyncio.run(scenario())
    finally:
        os.umask(previous_umask)


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


def test_restart_revalidates_run_identity_before_completed_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BYBIT_SOURCE: 2, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
    )
    runs_root = tmp_path / "live" / "runs"
    detached_root = runs_root / "detached-old-run"
    replacement_root = runs_root / "replacement-old-run"
    replacement_root.mkdir()
    original_write_summaries = LiveRunManager._write_source_summaries

    def swap_before_completion(
        self: LiveRunManager, run_fd: int, payload: dict[str, object]
    ) -> None:
        original_write_summaries(self, run_fd, payload)
        old_run_root.rename(detached_root)
        replacement_root.rename(old_run_root)

    monkeypatch.setattr(LiveRunManager, "_write_source_summaries", swap_before_completion)
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="e" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match="runtime roots changed after anchoring"):
        asyncio.run(manager.start())
    state = json.loads((detached_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert state["run_state"] == "active"
    assert list(old_run_root.iterdir()) == []
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


@pytest.mark.parametrize(
    "field_name",
    ["execution_enabled", "trading_authorized", "trading_credentials_present"],
)
def test_restart_rejects_nonzero_authority_before_sealing(tmp_path: Path, field_name: str) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BYBIT_SOURCE: 2, BINANCE_SOURCE: 2, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state[field_name] = True
    state_path.write_text(json.dumps(state), encoding="utf-8")
    originals = {
        source: (old_run_root / f"{source}.ndjson").read_bytes()
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE)
    }
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="d" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match=f"previous live run must keep {field_name}=false"):
        asyncio.run(manager.start())
    for source, original in originals.items():
        assert (old_run_root / f"{source}.ndjson").read_bytes() == original
    assert json.loads(state_path.read_text(encoding="utf-8"))["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


def test_restart_rejects_oversized_committed_row_without_unbounded_read(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 0, OKX_SOURCE: 0},
    )
    source_path = old_run_root / f"{BYBIT_SOURCE}.ndjson"
    source_path.write_bytes(b"x" * (1024 * 1024 + 1) + b"\n")
    original = source_path.read_bytes()
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="c" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match="source row exceeds recovery bound"):
        asyncio.run(manager.start())
    assert source_path.read_bytes() == original
    state = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert state["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


def test_restart_revalidates_source_identity_before_completed_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BYBIT_SOURCE: 1, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
        actual_rows={BYBIT_SOURCE: 2, BINANCE_SOURCE: 1, OKX_SOURCE: 0},
    )
    source_path = old_run_root / f"{BYBIT_SOURCE}.ndjson"
    replacement = old_run_root / "replacement.ndjson"
    replacement.write_bytes(b"{}\n{}\n{}\n")
    original_write_summaries = LiveRunManager._write_source_summaries

    def swap_before_completion(
        self: LiveRunManager, run_fd: int, payload: dict[str, object]
    ) -> None:
        original_write_summaries(self, run_fd, payload)
        source_path.rename(old_run_root / "detached.ndjson")
        replacement.rename(source_path)

    monkeypatch.setattr(LiveRunManager, "_write_source_summaries", swap_before_completion)
    manager = LiveRunManager(
        data_root=tmp_path,
        collector_commit="f" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    with pytest.raises(RuntimeError, match="previous live source changed during recovery"):
        asyncio.run(manager.start())
    state = json.loads((old_run_root / "run-state-v1.json").read_text(encoding="utf-8"))
    assert state["run_state"] == "active"
    assert source_path.read_bytes() == b"{}\n{}\n{}\n"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


@pytest.mark.parametrize(
    ("field", "value"), [("schema_version", 2), ("contract", "foreign-live-contract-v2")]
)
def test_restart_rejects_foreign_run_contract_before_sealing(
    tmp_path: Path, field: str, value: object
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state[field] = value
    state_path.write_text(json.dumps(state), encoding="utf-8")
    source_path = old_run_root / f"{BINANCE_SOURCE}.ndjson"
    original = source_path.read_bytes()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="b" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="previous live run contract is invalid"):
        asyncio.run(manager.start())

    assert source_path.read_bytes() == original
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    assert persisted[field] == value
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id
    assert sorted(path.name for path in (tmp_path / "live" / "runs").iterdir()) == [old_run_id]


def test_restart_rejects_mismatched_state_run_id_before_sealing(tmp_path: Path) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["run_id"] = "liquid20-20260810T000000Z-2"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    source_path = old_run_root / f"{BINANCE_SOURCE}.ndjson"
    original = source_path.read_bytes()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="a" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="previous live run_id does not match active pointer"):
        asyncio.run(manager.start())

    assert source_path.read_bytes() == original
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    assert persisted["run_id"] == "liquid20-20260810T000000Z-2"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id
    assert sorted(path.name for path in (tmp_path / "live" / "runs").iterdir()) == [old_run_id]


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


@pytest.mark.parametrize("configured_value", ["__missing__", None, "false", 0])
def test_restart_rejects_malformed_configured_without_mutating_source(
    tmp_path: Path, configured_value: object
) -> None:
    old_run_id, old_run_root = _write_previous_active_run(
        tmp_path,
        committed_rows={BINANCE_SOURCE: 1, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
        actual_rows={BINANCE_SOURCE: 2, BYBIT_SOURCE: 0, OKX_SOURCE: 0},
    )
    state_path = old_run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if configured_value == "__missing__":
        del state["sources"][BINANCE_SOURCE]["configured"]
    else:
        state["sources"][BINANCE_SOURCE]["configured"] = configured_value
    state_path.write_text(json.dumps(state), encoding="utf-8")
    source_path = old_run_root / f"{BINANCE_SOURCE}.ndjson"
    original = source_path.read_bytes()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="c" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match="binance-usdm configured is invalid"):
        asyncio.run(manager.start())

    assert source_path.read_bytes() == original
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_state"] == "active"
    pointer = json.loads((tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8"))
    assert pointer["active_run_id"] == old_run_id


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


@pytest.mark.parametrize("component", ["live", "runs"])
def test_start_rejects_symlinked_runtime_root_before_any_write(
    tmp_path: Path, component: str
) -> None:
    external = tmp_path / f"external-{component}"
    external.mkdir()
    if component == "live":
        (tmp_path / "live").symlink_to(external, target_is_directory=True)
        expected = "Liquid20 live root is not a regular directory"
    else:
        live_root = tmp_path / "live"
        live_root.mkdir()
        (live_root / "runs").symlink_to(external, target_is_directory=True)
        expected = "Liquid20 runs root is not a regular directory"
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="b" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )

    with pytest.raises(RuntimeError, match=expected):
        asyncio.run(manager.start())

    assert list(external.iterdir()) == []


def test_seal_anchors_source_to_open_run_directory_after_path_swap(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    source_path = run_root / f"{BINANCE_SOURCE}.ndjson"
    source_path.write_text('{"row":1}\n{"row":2}\n', encoding="utf-8")
    external_root = tmp_path / "external"
    external_root.mkdir()
    external_source = external_root / f"{BINANCE_SOURCE}.ndjson"
    external_payload = b'{"external":1}\n{"external":2}\n'
    external_source.write_bytes(external_payload)
    run_root_fd = os.open(
        run_root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    archived_root = tmp_path / "archived-run"
    try:
        run_root.rename(archived_root)
        run_root.symlink_to(external_root, target_is_directory=True)
        _seal_committed_ndjson(
            run_root / f"{BINANCE_SOURCE}.ndjson",
            committed_rows=1,
            source=BINANCE_SOURCE,
            allow_missing=False,
            directory_fd=run_root_fd,
        )
    finally:
        os.close(run_root_fd)

    assert external_source.read_bytes() == external_payload
    assert (archived_root / f"{BINANCE_SOURCE}.ndjson").read_text(encoding="utf-8") == (
        '{"row":1}\n'
    )


def test_new_run_creation_fails_closed_after_runs_path_swap(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    runs_root = live_root / "runs"
    external_root = tmp_path / "external-runs"
    external_root.mkdir()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="d" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    anchored_runs = live_root / "runs-anchored"

    def swap_runs_path_after_fd_open() -> None:
        runs_root.rename(anchored_runs)
        runs_root.symlink_to(external_root, target_is_directory=True)

    manager._complete_previous_active_run = swap_runs_path_after_fd_open  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="Liquid20 runtime roots changed after anchoring"):
        asyncio.run(manager.start())

    assert list(external_root.iterdir()) == []
    assert not (live_root / LIVE_STATE_FILE).exists()
    created_runs = list(anchored_runs.iterdir())
    assert len(created_runs) == 1
    created = created_runs[0]
    assert created.is_dir()
    assert (created / "bybit-linear.ndjson").is_file()
    assert (created / "binance-usdm.ndjson").is_file()
    assert (created / "okx-swap.ndjson").is_file()
    assert not (created / "run-state-v1.json").exists()


def test_new_run_creation_fails_closed_after_live_path_swap(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    external_root = tmp_path / "external-live"
    external_root.mkdir()
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="c" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    anchored_live = tmp_path / "live-anchored"

    def swap_live_path_after_fd_open() -> None:
        live_root.rename(anchored_live)
        live_root.symlink_to(external_root, target_is_directory=True)

    manager._complete_previous_active_run = swap_live_path_after_fd_open  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="Liquid20 runtime roots changed after anchoring"):
        asyncio.run(manager.start())

    assert list(external_root.iterdir()) == []
    assert not (external_root / LIVE_STATE_FILE).exists()
    created_runs = list((anchored_live / "runs").iterdir())
    assert len(created_runs) == 1
    assert not (created_runs[0] / "run-state-v1.json").exists()


def test_new_run_creation_fails_closed_after_active_run_path_swap(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    manager = OkxLiveRunManager(
        data_root=tmp_path,
        collector_commit="e" * 40,
        host_id="synology-test",
        now_ms=lambda: 1_786_384_683_792,
    )
    original_start_new_run = manager._start_new_run
    detached_run: Path | None = None

    def start_and_swap_active_run(now_ms: int) -> None:
        nonlocal detached_run
        original_start_new_run(now_ms)
        canonical_run = manager.run_root
        detached_run = canonical_run.with_name(f"{canonical_run.name}-anchored")
        canonical_run.rename(detached_run)
        canonical_run.mkdir(mode=0o750)

    manager._start_new_run = start_and_swap_active_run  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="Liquid20 runtime roots changed after anchoring"):
        asyncio.run(manager.start())
    assert detached_run is not None
    assert list(manager.run_root.iterdir()) == []
    assert not (live_root / LIVE_STATE_FILE).exists()
    assert (detached_run / "bybit-linear.ndjson").is_file()
    assert (detached_run / "binance-usdm.ndjson").is_file()
    assert (detached_run / "okx-swap.ndjson").is_file()
    assert not (detached_run / "run-state-v1.json").exists()


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
