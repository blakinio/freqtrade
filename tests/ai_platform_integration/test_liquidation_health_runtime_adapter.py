from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from ai_platform.scripts import liquidation_health_runtime_adapter as adapter
from ai_platform.scripts import liquidation_live_health as health


def test_container_observation_reads_pointer_and_disk_without_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert kwargs["check"] is False
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 15
        source = kwargs["input"]
        assert isinstance(source, str)
        if "live-state-v1.json" in source:
            stdout = '{"contract":"liquidation-live-state-v1","state":{"run_state":"active"}}\n'
        else:
            stdout = '{"free":300,"total":1000,"used":700}\n'
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(adapter.subprocess, "run", run)

    pointer = adapter.read_live_pointer_from_container("liquid20-live")
    disk = adapter.disk_snapshot_from_container("liquid20-live")

    assert pointer == {
        "contract": "liquidation-live-state-v1",
        "state": {"run_state": "active"},
    }
    assert disk == {"total": 1000, "used": 700, "free": 300}
    assert calls == [
        ["docker", "exec", "--interactive", "liquid20-live", "python", "-"],
        ["docker", "exec", "--interactive", "liquid20-live", "python", "-"],
    ]


def test_runtime_adapter_falls_back_to_container_and_tolerates_disabled_issues(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(health, "read_live_pointer", lambda _root: None)
    monkeypatch.setattr(
        health,
        "disk_snapshot",
        lambda _root: {"total": 0, "used": 0, "free": 0},
    )

    def disabled_issues(*_args: Any, **_kwargs: Any) -> str:
        raise RuntimeError(
            "GitHub API POST /repos/blakinio/freqtrade/issues failed: 410 "
            '{"message":"Issues has been disabled in this repository."}'
        )

    monkeypatch.setattr(health, "reconcile_alert_issue", disabled_issues)
    monkeypatch.setattr(
        adapter,
        "read_live_pointer_from_container",
        lambda name: {
            "contract": "liquidation-live-state-v1",
            "state": {"run_state": "active", "container": name},
        },
    )
    monkeypatch.setattr(
        adapter,
        "disk_snapshot_from_container",
        lambda name: {"total": 1000, "used": 400, "free": 600} if name else {},
    )

    restore = adapter.install_runtime_adapter("liquid20-live")
    try:
        assert health.read_live_pointer(tmp_path) == {
            "contract": "liquidation-live-state-v1",
            "state": {"run_state": "active", "container": "liquid20-live"},
        }
        assert health.disk_snapshot(tmp_path) == {
            "total": 1000,
            "used": 400,
            "free": 600,
        }
        assert health.reconcile_alert_issue(object(), "blakinio/freqtrade", {}) == "unavailable"
    finally:
        restore()


def test_scripts_package_activates_adapter_only_for_health_workflow() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    package_init = (repository_root / "ai_platform" / "scripts" / "__init__.py").read_text(
        encoding="utf-8"
    )

    assert 'os.environ.get("GITHUB_WORKFLOW") == "Liquidations Live Health"' in package_init
    assert 'os.environ.get("LIQUID20_CONTAINER_NAME")' in package_init
    assert "install_runtime_adapter(container_name)" in package_init
