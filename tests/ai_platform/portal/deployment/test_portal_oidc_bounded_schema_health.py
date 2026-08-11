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
    "portal_oidc_bounded_schema_lifecycle_health",
    MODULE_PATH,
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

CONTAINER_ID = "a" * 64
PROTECTED_ID = "e" * 64
REPLACEMENT_ID = "f" * 64


def _completed(command: list[str], *, returncode: int = 0, stdout: str = "") -> Any:
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def _state(
    *,
    exists: bool,
    running: bool,
    health: str,
    state: str,
    container_id: str = PROTECTED_ID,
) -> dict[str, object]:
    return {
        "exists": exists,
        "container_id": container_id if exists else None,
        "state": state,
        "running": running,
        "health": health,
    }


def _deploy_stub() -> SimpleNamespace:
    return SimpleNamespace(
        DeploymentError=RuntimeError,
        PORTAL_CONTAINER="freqtrade-portal-staging",
        CONTROL_CONTAINER="freqtrade-portal-control-plane",
        PORTAL_POSTGRES_CONTAINER="freqtrade-portal-postgresql",
    )


def _cleanup_call(deploy: SimpleNamespace, *, label: str) -> None:
    module._cleanup_with_protected_health(
        deploy,
        label=label,
        name="task-container",
        owner="task-owner",
        create_succeeded=True,
        container_id=CONTAINER_ID,
        cwd=None,
    )


def test_protected_service_snapshot_records_immutable_container_id(monkeypatch) -> None:
    deploy = _deploy_stub()
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[:3] == ["docker", "ps", "-aq"]:
            return _completed(command, stdout=f"{PROTECTED_ID}\n")
        if command[:3] == ["docker", "inspect", "--format"]:
            assert command[-1] == PROTECTED_ID
            return _completed(command, stdout="running|true|healthy\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    state = module._protected_service_state(
        deploy,
        "freqtrade-portal-postgresql",
        cwd=None,
    )

    assert state == _state(
        exists=True,
        running=True,
        health="healthy",
        state="running",
    )
    assert ["docker", "inspect", "--format", module.SERVICE_STATE_FORMAT, PROTECTED_ID] in calls


def test_cleanup_records_healthy_protected_service_non_regression(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True,
            running=False,
            health="healthy",
            state="exited",
        ),
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="healthy",
            state="running",
        ),
        "freqtrade-portal-staging": _state(
            exists=True,
            running=False,
            health="healthy",
            state="exited",
        ),
    }
    after = {name: dict(value) for name, value in before.items()}
    snapshots = iter((before, after))
    cleaned: list[tuple[str, str, str | None]] = []

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )

    def cleanup_owned(_deploy, name, owner, *, container_id, cwd):
        cleaned.append((name, owner, container_id))
        return container_id

    monkeypatch.setattr(module, "_cleanup_owned", cleanup_owned)

    _cleanup_call(deploy, label="schema-migrate")

    assert cleaned == [("task-container", "task-owner", CONTAINER_ID)]
    assert deploy._bounded_schema_cleanup_evidence == [
        {
            "workload": "schema-migrate",
            "task_container_name": "task-container",
            "task_container_id": CONTAINER_ID,
            "protected_before": before,
            "protected_after": after,
            "cleanup_complete": True,
            "protected_non_regression": True,
            "regressions": [],
            "verification_complete": True,
        }
    ]


def test_cleanup_fails_when_healthy_postgres_degrades(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="healthy",
            state="running",
        )
    }
    after = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=False,
            health="unhealthy",
            state="exited",
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_owned",
        lambda _deploy, name, owner, *, container_id, cwd: container_id,
    )

    with pytest.raises(RuntimeError, match="protected service health regressed"):
        _cleanup_call(deploy, label="state-transfer")

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["cleanup_complete"] is True
    assert evidence["protected_non_regression"] is False
    assert evidence["task_container_id"] == CONTAINER_ID
    assert evidence["regressions"] == [
        "freqtrade-portal-postgresql:stopped_running",
        "freqtrade-portal-postgresql:lost_healthy",
    ]


def test_cleanup_fails_when_protected_name_is_replaced_by_new_container(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="healthy",
            state="running",
            container_id=PROTECTED_ID,
        )
    }
    after = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="healthy",
            state="running",
            container_id=REPLACEMENT_ID,
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_owned",
        lambda _deploy, name, owner, *, container_id, cwd: container_id,
    )

    with pytest.raises(RuntimeError, match="protected service health regressed"):
        _cleanup_call(deploy, label="schema-check")

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["cleanup_complete"] is True
    assert evidence["protected_before"] == before
    assert evidence["protected_after"] == after
    assert evidence["regressions"] == ["freqtrade-portal-postgresql:identity_changed"]


def test_preexisting_unhealthy_stopped_service_is_recorded_not_repaired(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True,
            running=False,
            health="unhealthy",
            state="exited",
        )
    }
    after = {
        "freqtrade-portal-control-plane": _state(
            exists=True,
            running=False,
            health="unhealthy",
            state="exited",
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_owned",
        lambda _deploy, name, owner, *, container_id, cwd: container_id,
    )

    _cleanup_call(deploy, label="schema-check")

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["cleanup_complete"] is True
    assert evidence["protected_non_regression"] is True
    assert evidence["protected_before"] == before
    assert evidence["protected_after"] == after


def test_existing_stopped_service_may_not_disappear_during_cleanup(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True,
            running=False,
            health="none",
            state="exited",
        )
    }
    after = {
        "freqtrade-portal-control-plane": _state(
            exists=False,
            running=False,
            health="none",
            state="absent",
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_owned",
        lambda _deploy, name, owner, *, container_id, cwd: container_id,
    )

    with pytest.raises(RuntimeError, match="protected service health regressed"):
        _cleanup_call(deploy, label="schema-check")

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["cleanup_complete"] is True
    assert evidence["regressions"] == ["freqtrade-portal-control-plane:became_absent"]


def test_cleanup_failure_is_recorded_as_incomplete_verification(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    snapshots: Any = iter(({}, {}))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )

    def fail_cleanup(_deploy, name, owner, *, container_id, cwd):
        raise RuntimeError("cleanup failed")

    monkeypatch.setattr(module, "_cleanup_owned", fail_cleanup)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        _cleanup_call(deploy, label="schema-check")

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["cleanup_complete"] is False
    assert evidence["verification_complete"] is False
    assert evidence["protected_non_regression"] is False
    assert evidence["regressions"] == []


def test_starting_service_may_improve_to_healthy() -> None:
    before = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="starting",
            state="running",
        )
    }
    after = {
        "freqtrade-portal-postgresql": _state(
            exists=True,
            running=True,
            health="healthy",
            state="running",
        )
    }

    assert module._protected_service_regressions(before, after) == []


def test_install_persists_cleanup_health_and_task_identity_in_deployment_report() -> None:
    reports: list[dict[str, Any]] = []

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("run path is not used by this test")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        reports.append(dict(report))
        return "digest"

    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        _run=original_run,
        _write_report=original_write_report,
    )
    module.install(deploy)
    cleanup_evidence = {
        "workload": "schema-migrate",
        "task_container_name": "task-container",
        "task_container_id": CONTAINER_ID,
        "protected_before": {},
        "protected_after": {},
        "cleanup_complete": True,
        "protected_non_regression": True,
        "regressions": [],
        "verification_complete": True,
    }
    deploy._bounded_schema_cleanup_evidence.append(cleanup_evidence)

    report: dict[str, Any] = {"status": "success"}
    digest = deploy._write_report(Path("report.json"), report)

    assert digest == "digest"
    assert reports[-1]["bounded_schema_cleanup_evidence"] == [cleanup_evidence]
