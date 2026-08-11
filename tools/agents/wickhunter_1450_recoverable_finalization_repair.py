from pathlib import Path


STREAM = Path("ai_platform/scripts/liquidation_live_stream.py")
OKX = Path("ai_platform/scripts/liquidation_live_stream_okx.py")
TESTS = Path("tests/ai_platform_integration/test_liquidation_live_restart_durability.py")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label} target mismatch: expected exactly one occurrence")
    return text.replace(old, new, 1)


def patch_stream() -> None:
    text = STREAM.read_text(encoding="utf-8")
    completion_old = '''            state["run_state"] = "completed"\n            state["data_mode"] = "historical"\n            state["completed_at_ms"] = self._now_ms()\n            state["completion_reason"] = "collector-restart"\n            _write_json_atomic_at(run_root_fd, RUN_STATE_FILE, state)\n'''
    completion_new = '''            state["run_state"] = "completed"\n            state["data_mode"] = "historical"\n            state["completed_at_ms"] = self._now_ms()\n            state["completion_reason"] = "collector-restart"\n            self._write_source_summaries(run_root_fd, state)\n            _write_json_atomic_at(run_root_fd, RUN_STATE_FILE, state)\n'''
    text = replace_once(text, completion_old, completion_new, label="restart completion")

    start = text.index('    def _write_state(self) -> None:\n')
    end = text.index('\n\ndef redact_error', start)
    old = text[start:end]
    for marker in (
        '_write_json_atomic_at(run_fd, RUN_STATE_FILE, payload)',
        'for source in (BYBIT_SOURCE, BINANCE_SOURCE):',
        '_write_json_atomic_at(live_fd, LIVE_STATE_FILE, pointer_payload)',
    ):
        if marker not in old:
            raise SystemExit(f"state writer semantic marker missing: {marker}")
    new = '''    def _write_source_summaries(\n        self, run_fd: int, payload: dict[str, object]\n    ) -> None:\n        sources = payload.get("sources")\n        run_id = payload.get("run_id")\n        run_state = payload.get("run_state")\n        if not isinstance(sources, dict) or not isinstance(run_id, str):\n            raise RuntimeError("Liquid20 source summary payload is invalid")\n        if not isinstance(run_state, str):\n            raise RuntimeError("Liquid20 run-state summary payload is invalid")\n        for source in (BYBIT_SOURCE, BINANCE_SOURCE):\n            stats = sources.get(source)\n            if not isinstance(stats, dict):\n                raise RuntimeError(f"Liquid20 {source} source summary payload is invalid")\n            source_payload = {\n                "schema_version": 1,\n                "source": {"id": source},\n                "run_id": run_id,\n                "run_state": run_state,\n                "stats": stats,\n                "trading_credentials_present": False,\n                "execution_enabled": False,\n            }\n            _write_json_atomic_at(run_fd, f"{source}-summary.json", source_payload)\n\n    def _write_state(self) -> None:\n        run_fd = self._require_fd(self._run_root_fd, label="Liquid20 active run root")\n        live_fd = self._require_fd(self._live_root_fd, label="Liquid20 live root")\n        for writer in self._writers.values():\n            if not writer.closed:\n                writer.flush()\n        payload = self._state_payload()\n        # Summaries are durable before run-state and pointer publication. A failed\n        # summary therefore leaves the prior active commit boundary recoverable.\n        self._write_source_summaries(run_fd, payload)\n        _write_json_atomic_at(run_fd, RUN_STATE_FILE, payload)\n        pointer_payload = {\n            "schema_version": 1,\n            "contract": LIVE_CONTRACT,\n            "active_run_id": self.run_id if self._run_state == "active" else None,\n            "collector_heartbeat_at_ms": payload["collector_heartbeat_at_ms"],\n            "state": payload,\n        }\n        _write_json_atomic_at(live_fd, LIVE_STATE_FILE, pointer_payload)\n'''
    text = text[:start] + new.rstrip("\n") + text[end:]
    STREAM.write_text(text, encoding="utf-8")


def patch_okx() -> None:
    text = OKX.read_text(encoding="utf-8")
    start = text.index('    def _write_okx_snapshot(self) -> None:\n')
    end = text.index('\n    def _start_new_run', start)
    old = text[start:end]
    if 'OKX_INSTRUMENT_SNAPSHOT_FILE' not in old or 'self._run_root_fd' not in old:
        raise SystemExit("OKX snapshot semantic target mismatch")
    new = '''    def _write_okx_snapshot(self, *, directory_fd: int | None = None) -> None:\n        if self._okx_instrument_snapshot is not None:\n            run_fd = directory_fd\n            if run_fd is None:\n                run_fd = self._require_fd(\n                    self._run_root_fd,\n                    label="Liquid20 active run root",\n                )\n            _write_json_atomic_at(\n                run_fd,\n                OKX_INSTRUMENT_SNAPSHOT_FILE,\n                self._okx_instrument_snapshot,\n            )\n'''
    text = text[:start] + new.rstrip("\n") + text[end:]

    start = text.index('    def _write_state(self) -> None:\n')
    end = text.index('\n    async def connected', start)
    old = text[start:end]
    if 'super()._write_state()' not in old or 'okx-swap-summary.json' not in old:
        raise SystemExit("OKX state writer semantic target mismatch")
    new = '''    def _write_source_summaries(\n        self, run_fd: int, payload: dict[str, object]\n    ) -> None:\n        super()._write_source_summaries(run_fd, payload)\n        sources = payload.get("sources")\n        run_id = payload.get("run_id")\n        run_state = payload.get("run_state")\n        if not isinstance(sources, dict) or not isinstance(run_id, str):\n            raise RuntimeError("Liquid20 OKX source summary payload is invalid")\n        stats = sources.get(OKX_SOURCE)\n        if not isinstance(stats, dict) or not isinstance(run_state, str):\n            raise RuntimeError("Liquid20 OKX source summary state is invalid")\n        source_payload = {\n            "schema_version": 1,\n            "source": {"id": OKX_SOURCE},\n            "run_id": run_id,\n            "run_state": run_state,\n            "stats": stats,\n            "trading_credentials_present": False,\n            "execution_enabled": False,\n            "orders_submitted": 0,\n        }\n        _write_json_atomic_at(run_fd, "okx-swap-summary.json", source_payload)\n        self._write_okx_snapshot(directory_fd=run_fd)\n'''
    text = text[:start] + new.rstrip("\n") + text[end:]
    OKX.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    if 'test_stop_okx_summary_failure_is_restart_recoverable' in text:
        raise SystemExit("recoverable finalization tests already present")
    marker = '\n\ndef test_restart_truncates_only_uncommitted_suffix_before_completion'
    if marker not in text:
        raise SystemExit("test insertion marker missing")
    addition = r'''


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

        persisted = json.loads(
            (old_run_root / "run-state-v1.json").read_text(encoding="utf-8")
        )
        pointer = json.loads(
            (tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8")
        )
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
        completed = json.loads(
            (old_run_root / "run-state-v1.json").read_text(encoding="utf-8")
        )
        assert completed["run_state"] == "completed"
        assert completed["completion_reason"] == "collector-restart"
        for source in (BYBIT_SOURCE, BINANCE_SOURCE, OKX_SOURCE):
            summary = json.loads(
                (old_run_root / f"{source}-summary.json").read_text(encoding="utf-8")
            )
            assert summary["run_id"] == old_run_id
            assert summary["run_state"] == "completed"
        new_pointer = json.loads(
            (tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8")
        )
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
            if (
                not failed
                and file_name == LIVE_STATE_FILE
                and payload.get("active_run_id") is None
            ):
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

        persisted = json.loads(
            (old_run_root / "run-state-v1.json").read_text(encoding="utf-8")
        )
        pointer = json.loads(
            (tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8")
        )
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
        new_pointer = json.loads(
            (tmp_path / "live" / LIVE_STATE_FILE).read_text(encoding="utf-8")
        )
        assert new_pointer["active_run_id"] == recovery.run_id
        await recovery.stop()

    asyncio.run(scenario())
'''
    TESTS.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


patch_stream()
patch_okx()
patch_tests()
