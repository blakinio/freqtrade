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

CONTAINER_ID = "c" * 64
REPLACEMENT_ID = "d" * 64


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
    exists = False
    token = "cancelcafe00"
    owner = f"portal-oidc-bounded:schema-migrate:{token}"
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **_kwargs):
        nonlocal exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:2] == ["docker", "wait"]:
            raise KeyboardInterrupt
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            exists = False
            return _completed(command)
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(KeyboardInterrupt):
        deploy._run(_schema_command(), sensitive=True)

    assert ["docker", "rm", "-f", CONTAINER_ID] in calls
    assert not any(command[:2] == ["docker", "logs"] for command in calls)
    assert not exists


def test_owned_cleanup_retries_after_ambiguous_remove_timeout(monkeypatch) -> None:
    deploy = _deploy_stub()
    calls: list[list[str]] = []
    exists = False
    remove_calls = 0
    token = "removebeef00"
    owner = f"portal-oidc-bounded:schema-migrate:{token}"
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **kwargs):
        nonlocal exists, remove_calls
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{owner}\n" if exists else "",
            )
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            remove_calls += 1
            if remove_calls == 1:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            exists = False
            return _completed(command)
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = deploy._run(_schema_command(), sensitive=True)

    assert result.returncode == 0
    assert remove_calls == 2
    assert not exists
    assert sum(command[:3] == ["docker", "rm", "-f"] for command in calls) == 2


def test_name_reuse_after_remove_timeout_never_removes_replacement(monkeypatch) -> None:
    deploy = _deploy_stub()
    calls: list[list[str]] = []
    original_exists = False
    replacement_exists = False
    remove_calls = 0
    token = "reusebeef000"
    owner = f"portal-oidc-bounded:schema-migrate:{token}"
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **kwargs):
        nonlocal original_exists, replacement_exists, remove_calls
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            original_exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            reference = command[-1]
            if reference == CONTAINER_ID:
                return _completed(
                    command,
                    returncode=0 if original_exists else 1,
                    stdout=f"{CONTAINER_ID}|{owner}\n" if original_exists else "",
                )
            if replacement_exists:
                return _completed(command, stdout=f"{REPLACEMENT_ID}|foreign-owner\n")
            return _completed(command, returncode=1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            remove_calls += 1
            if remove_calls == 1:
                original_exists = False
                replacement_exists = True
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            raise AssertionError("replacement must never be targeted by cleanup")
        if command[:2] == ["docker", "inspect"]:
            reference = command[-1]
            if reference == CONTAINER_ID:
                return _completed(command, returncode=0 if original_exists else 1)
            return _completed(command, returncode=0 if replacement_exists else 1)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = deploy._run(_schema_command(), sensitive=True)

    assert result.returncode == 0
    assert remove_calls == 1
    assert not original_exists
    assert replacement_exists
    assert ["docker", "rm", "-f", REPLACEMENT_ID] not in calls
