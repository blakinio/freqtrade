from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT_DIR = ROOT / "deploy" / "synology" / "portal-oidc"
MODULE_PATH = DEPLOYMENT_DIR / "bounded_schema_lifecycle.py"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_bounded_schema_lifecycle_cancellation",
    MODULE_PATH,
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _completed(command: list[str], *, returncode: int = 0, stdout: str = "") -> Any:
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def _schema_command() -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "portal_oidc_public",
        "--read-only",
        "--env-file",
        "/state/runtime.candidate.env",
        "--entrypoint",
        "python",
        "sha256:approved",
        "-m",
        "ai_platform.portal.database.cli",
        "migrate",
    ]


def _deploy_stub() -> SimpleNamespace:
    def original_run(command, *, cwd=None, sensitive=False, check=True):
        return _completed(command, stdout="delegated\n")

    return SimpleNamespace(DeploymentError=RuntimeError, _run=original_run)


def test_keyboard_interrupt_runs_owned_cleanup_before_reraise(monkeypatch) -> None:
    deploy = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "cancelcafe00")

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "wait"]:
            raise KeyboardInterrupt
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(KeyboardInterrupt):
        deploy._run(_schema_command(), sensitive=True)

    expected_name = "portal-oidc-bounded-schema-migrate-cancelcafe00"
    assert ["docker", "rm", "-f", expected_name] in calls
    assert not any(command[:2] == ["docker", "logs"] for command in calls)


def test_owned_cleanup_retries_after_ambiguous_remove_timeout(monkeypatch) -> None:
    deploy = _deploy_stub()
    calls: list[list[str]] = []
    created = False
    remove_calls = 0
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "removebeef00")

    def fake_run(command, **kwargs):
        nonlocal created, remove_calls
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            created = True
            return _completed(command)
        if command[:3] == ["docker", "rm", "-f"]:
            remove_calls += 1
            if remove_calls == 1:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            created = False
            return _completed(command)
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if created else 1)
        if command[:3] == ["docker", "ps", "-aq"]:
            return _completed(command, stdout="task-container\n" if created else "")
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = deploy._run(_schema_command(), sensitive=True)

    assert result.returncode == 0
    assert remove_calls == 2
    assert not created
    assert sum(command[:3] == ["docker", "rm", "-f"] for command in calls) == 2
