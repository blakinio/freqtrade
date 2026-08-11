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
SPEC = importlib.util.spec_from_file_location("portal_oidc_bounded_schema_lifecycle", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _completed(command: list[str], *, returncode: int = 0, stdout: str = "") -> Any:
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def _schema_command(operation: str = "migrate") -> list[str]:
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
        operation,
    ]


def _transfer_command() -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "portal_oidc_public",
        "--read-only",
        "--env-file",
        "/state/runtime.candidate.env",
        "--mount",
        "type=bind,src=/backup,dst=/legacy,readonly",
        "--entrypoint",
        "python",
        "sha256:approved",
        "-m",
        "ai_platform.portal.database.transfer",
        "--source-sqlite",
        "/legacy/snapshot.db",
    ]


def _deploy_stub() -> tuple[SimpleNamespace, list[tuple[object, ...]]]:
    delegated: list[tuple[object, ...]] = []

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        delegated.append((tuple(command), cwd, sensitive, check))
        return _completed(command, stdout="delegated\n")

    deploy = SimpleNamespace(DeploymentError=RuntimeError, _run=original_run)
    return deploy, delegated


def test_schema_workload_uses_named_split_lifecycle_and_returns_logs(monkeypatch) -> None:
    deploy, delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "abc123def456")

    def fake_run(command, *, cwd=None, check=False, text=True, capture_output=True, timeout=None):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "version"]:
            return _completed(command)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = deploy._run(_schema_command(), sensitive=True)

    assert result.returncode == 0
    assert result.stdout == '{"status":"ready"}\n'
    assert delegated == []
    assert not any(command[:2] == ["docker", "run"] for command in calls)
    create = next(command for command in calls if command[:2] == ["docker", "create"])
    name = create[create.index("--name") + 1]
    assert name == "portal-oidc-bounded-schema-migrate-abc123def456"
    assert ["docker", "start", name] in calls
    assert ["docker", "wait", name] in calls
    assert ["docker", "logs", name] in calls
    assert ["docker", "rm", "-f", name] in calls


def test_transfer_workload_is_bounded_by_same_lifecycle(monkeypatch) -> None:
    deploy, delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "123456abcdef")

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"transferred","integrity":"clean"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = deploy._run(_transfer_command(), sensitive=True)

    assert result.returncode == 0
    assert "transferred" in result.stdout
    assert delegated == []
    create = next(command for command in calls if command[:2] == ["docker", "create"])
    assert "portal-oidc-bounded-state-transfer-123456abcdef" in create
    assert "--rm" not in create


def test_non_target_and_check_false_commands_delegate(monkeypatch) -> None:
    deploy, delegated = _deploy_stub()
    module.install(deploy)

    def unexpected_run(*_args, **_kwargs):
        raise AssertionError("bounded subprocess path should not be used")

    monkeypatch.setattr(module.subprocess, "run", unexpected_run)

    deploy._run(["docker", "run", "--rm", "alpine:3.23", "true"], sensitive=True)
    deploy._run(_schema_command("check"), sensitive=True, check=False)

    assert len(delegated) == 2
    assert delegated[0][2:] == (True, True)
    assert delegated[1][2:] == (True, False)


def test_nonzero_process_exit_is_secret_free_and_cleanup_is_verified(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "feedfacecafe")

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="7\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout="TOP_SECRET_TOKEN\n")
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc_info:
        deploy._run(_schema_command(), sensitive=True)

    message = str(exc_info.value)
    assert "schema-migrate:process" in message
    assert "TOP_SECRET_TOKEN" not in message
    assert any(command[:3] == ["docker", "rm", "-f"] for command in calls)
    assert sum(command[:2] == ["docker", "inspect"] for command in calls) >= 2


def test_start_timeout_still_cleans_task_owned_container(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "deadbeefcafe")

    def fake_run(command, **kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "start"]:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="schema-migrate:start"):
        deploy._run(_schema_command(), sensitive=True)

    assert any(command[:3] == ["docker", "rm", "-f"] for command in calls)


def test_cleanup_failure_overrides_success_and_fails_closed(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    inspect_calls = 0
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "badc0ffee000")

    def fake_run(command, **_kwargs):
        nonlocal inspect_calls
        if command[:2] == ["docker", "inspect"]:
            inspect_calls += 1
            return _completed(command, returncode=1 if inspect_calls == 1 else 0)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        deploy._run(_schema_command(), sensitive=True)


def test_deployment_entrypoint_installs_bounded_schema_lifecycle_after_build_guard() -> None:
    source = (DEPLOYMENT_DIR / "deploy_entrypoint.py").read_text(encoding="utf-8")

    assert 'DEPLOYMENT_DIR / "bounded_schema_lifecycle.py"' in source
    assert "bounded_schema.install(deploy)" in source
    assert source.index("_install_verified_build_timeout(deploy)") < source.index(
        "bounded_schema.install(deploy)"
    )
