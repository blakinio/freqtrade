from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


PREFLIGHT_PATH = Path("deploy/synology/portal-oidc/docker_runtime_preflight.py")


def _load_preflight() -> ModuleType:
    spec = importlib.util.spec_from_file_location("portal_docker_runtime_preflight_test", PREFLIGHT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _completed(command: list[str], returncode: int = 0, stdout: str = "ok\n") -> Any:
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def test_runtime_preflight_proves_disposable_container_start(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_preflight()
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, timeout: int) -> Any:
        commands.append(command)
        if command[:3] == ["docker", "info", "--format"]:
            return _completed(command, stdout="27.5.1\n")
        return _completed(command)

    monkeypatch.setattr(module, "_run", fake_run)

    result = module.check_runtime()

    assert result == {
        "status": "ready",
        "disposable_container_start": True,
        "network_mode": "none",
        "secret_values_recorded": False,
        "live_capital_authorized": False,
    }
    assert any(command[:2] == ["docker", "run"] for command in commands)
    assert any("--network" in command and "none" in command for command in commands)


def test_runtime_preflight_fails_closed_when_container_start_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_preflight()

    def fake_run(command: list[str], *, timeout: int) -> Any:
        if command[:3] == ["docker", "info", "--format"]:
            return _completed(command, stdout="27.5.1\n")
        if command[:3] == ["docker", "image", "inspect"]:
            return _completed(command)
        if command[:2] == ["docker", "run"]:
            raise module.PreflightError("docker runtime command timed out")
        return _completed(command)

    monkeypatch.setattr(module, "_run", fake_run)

    with pytest.raises(module.PreflightError, match="recover Synology Container Manager"):
        module.check_runtime()


def test_runtime_preflight_output_remains_secret_free(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_preflight()
    monkeypatch.setattr(
        module,
        "check_runtime",
        lambda: {
            "status": "ready",
            "disposable_container_start": True,
            "network_mode": "none",
            "secret_values_recorded": False,
            "live_capital_authorized": False,
        },
    )

    assert module.main() == 0
