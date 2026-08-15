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

CONTAINER_ID = "a" * 64
SECOND_CONTAINER_ID = "b" * 64


def _completed(
    command: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str | None = None,
) -> Any:
    if stderr is None:
        stderr = (
            "Error: No such object\n"
            if returncode != 0 and command[:2] == ["docker", "inspect"]
            else ""
        )
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


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


def _owner(label: str, token: str) -> str:
    return f"portal-oidc-bounded:{label}:{token}"


def test_schema_workload_uses_immutable_id_after_named_create(monkeypatch) -> None:
    deploy, delegated = _deploy_stub()
    calls: list[list[str]] = []
    exists = False
    token = "abc123def456"
    expected_owner = _owner("schema-migrate", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **_kwargs):
        nonlocal exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            exists = False
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
    owner_label = create[create.index("--label") + 1]
    assert name == f"portal-oidc-bounded-schema-migrate-{token}"
    assert owner_label == f"{module.OWNER_LABEL_KEY}={expected_owner}"
    assert ["docker", "start", CONTAINER_ID] in calls
    assert ["docker", "wait", CONTAINER_ID] in calls
    assert ["docker", "logs", CONTAINER_ID] in calls
    assert ["docker", "start", name] not in calls
    assert ["docker", "wait", name] not in calls
    assert ["docker", "logs", name] not in calls
    assert ["docker", "rm", "-f", CONTAINER_ID] in calls
    assert ["docker", "rm", "-f", name] not in calls
    assert not exists


def test_transfer_workload_is_bounded_by_same_lifecycle(monkeypatch) -> None:
    deploy, delegated = _deploy_stub()
    calls: list[list[str]] = []
    exists = False
    token = "123456abcdef"
    expected_owner = _owner("state-transfer", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **_kwargs):
        nonlocal exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            exists = False
            return _completed(command)
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
    assert f"portal-oidc-bounded-state-transfer-{token}" in create
    assert "--rm" not in create
    assert ["docker", "start", CONTAINER_ID] in calls
    assert ["docker", "wait", CONTAINER_ID] in calls
    assert ["docker", "logs", CONTAINER_ID] in calls
    assert ["docker", "rm", "-f", CONTAINER_ID] in calls


def test_wait_bounds_are_calibrated_per_workload() -> None:
    assert module._wait_timeout("schema-migrate") == 600
    assert module._wait_timeout("state-transfer") == 180
    assert module._wait_timeout("schema-check") == 180
    assert module._wait_timeout("schema-schema") == 300

    with pytest.raises(RuntimeError, match="no wait calibration"):
        module._wait_timeout("unreviewed-workload")


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


def test_unknown_inspect_failure_does_not_verify_identity_absent(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(
                command,
                returncode=1,
                stderr="Error response from daemon: context deadline exceeded\n",
            )
        if command[:2] == ["docker", "version"]:
            return _completed(command)
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="identity cleanup failed"):
        module._verify_container_id_absent(deploy, CONTAINER_ID, cwd=None)

    assert ["docker", "inspect", CONTAINER_ID] in calls
    assert ["docker", "version"] in calls


def test_preexisting_generated_name_collision_is_never_removed(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "0badc0ffee00")

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0)
        if command[:3] == ["docker", "ps", "-aq"]:
            return _completed(command, stdout="preexisting-container-id\n")
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        deploy._run(_schema_command(), sensitive=True)

    assert not any(command[:3] == ["docker", "rm", "-f"] for command in calls)
    assert not any(command[:2] == ["docker", "create"] for command in calls)


def test_nonzero_process_exit_is_secret_free_and_cleanup_is_verified(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    exists = False
    token = "feedfacecafe"
    expected_owner = _owner("schema-migrate", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **_kwargs):
        nonlocal exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            exists = False
            return _completed(command)
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
    assert ["docker", "rm", "-f", CONTAINER_ID] in calls
    assert not exists


def test_create_timeout_retries_owner_query_before_cleanup(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    identity_queries = 0
    exists = False
    token = "c0ffeec0ffee"
    expected_owner = _owner("schema-migrate", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **kwargs):
        nonlocal identity_queries, exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if command[:3] == ["docker", "inspect", "--format"]:
            identity_queries += 1
            if identity_queries == 1:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            exists = False
            return _completed(command)
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="schema-migrate:create"):
        deploy._run(_schema_command(), sensitive=True)

    assert identity_queries == 3
    assert ["docker", "rm", "-f", CONTAINER_ID] in calls
    assert not exists


def test_create_timeout_exhausts_owner_queries_without_unproven_remove(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    ownership_calls = 0
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "cafe0000cafe")

    def fake_run(command, **kwargs):
        nonlocal ownership_calls
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if command[:3] == ["docker", "inspect", "--format"]:
            ownership_calls += 1
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="workload and cleanup failed"):
        deploy._run(_schema_command(), sensitive=True)

    assert ownership_calls == module.OWNERSHIP_VERIFY_ATTEMPTS
    assert not any(command[:3] == ["docker", "rm", "-f"] for command in calls)


def test_create_race_never_removes_container_with_different_owner_label(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "facefeedcafe")

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            return _completed(command, returncode=1)
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(command, stdout=f"{SECOND_CONTAINER_ID}|different-owner\n")
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=1)
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="workload and cleanup failed"):
        deploy._run(_schema_command(), sensitive=True)

    assert not any(command[:3] == ["docker", "rm", "-f"] for command in calls)


def test_start_timeout_still_cleans_task_owned_container(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    calls: list[list[str]] = []
    exists = False
    token = "deadbeefcafe"
    expected_owner = _owner("schema-migrate", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **kwargs):
        nonlocal exists
        calls.append(list(command))
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:2] == ["docker", "start"]:
            assert command[2] == CONTAINER_ID
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            assert command[3] == CONTAINER_ID
            exists = False
            return _completed(command)
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="schema-migrate:start"):
        deploy._run(_schema_command(), sensitive=True)

    assert ["docker", "rm", "-f", CONTAINER_ID] in calls
    assert not exists


def test_cleanup_failure_overrides_success_and_fails_closed(monkeypatch) -> None:
    deploy, _delegated = _deploy_stub()
    exists = False
    token = "badc0ffee000"
    expected_owner = _owner("schema-migrate", token)
    module.install(deploy)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: token)

    def fake_run(command, **_kwargs):
        nonlocal exists
        if command[:2] == ["docker", "create"]:
            exists = True
            return _completed(command, stdout=f"{CONTAINER_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            return _completed(
                command,
                returncode=0 if exists else 1,
                stdout=f"{CONTAINER_ID}|{expected_owner}\n" if exists else "",
            )
        if command[:2] == ["docker", "inspect"]:
            return _completed(command, returncode=0 if exists else 1)
        if command[:3] == ["docker", "rm", "-f"]:
            return _completed(command, returncode=1)
        if command[:2] == ["docker", "wait"]:
            return _completed(command, stdout="0\n")
        if command[:2] == ["docker", "logs"]:
            return _completed(command, stdout='{"status":"ready"}\n')
        return _completed(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        deploy._run(_schema_command(), sensitive=True)

    assert exists


def test_deployment_entrypoint_installs_bounded_schema_lifecycle_after_build_guard() -> None:
    source = (DEPLOYMENT_DIR / "deploy_entrypoint.py").read_text(encoding="utf-8")

    assert 'DEPLOYMENT_DIR / "bounded_schema_lifecycle.py"' in source
    assert "bounded_schema.install(deploy)" in source
    assert source.index("_install_verified_build_timeout(deploy)") < source.index(
        "bounded_schema.install(deploy)"
    )
