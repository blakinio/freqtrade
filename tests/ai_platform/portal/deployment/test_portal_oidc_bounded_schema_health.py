from __future__ import annotations

import importlib.util
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


def _state(*, exists: bool, running: bool, health: str, state: str) -> dict[str, object]:
    return {
        "exists": exists,
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


def test_cleanup_records_healthy_protected_service_non_regression(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True, running=False, health="healthy", state="exited"
        ),
        "freqtrade-portal-postgresql": _state(
            exists=True, running=True, health="healthy", state="running"
        ),
        "freqtrade-portal-staging": _state(
            exists=True, running=False, health="healthy", state="exited"
        ),
    }
    after = {name: dict(value) for name, value in before.items()}
    snapshots = iter((before, after))
    cleaned: list[str] = []

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_owned",
        lambda _deploy, name, *, cwd: cleaned.append(name),
    )

    module._cleanup_with_protected_health(
        deploy,
        label="schema-migrate",
        name="task-container",
        owner="task-owner",
        create_succeeded=True,
        cwd=None,
    )

    assert cleaned == ["task-container"]
    assert deploy._bounded_schema_cleanup_evidence == [
        {
            "workload": "schema-migrate",
            "protected_before": before,
            "protected_after": after,
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
            exists=True, running=True, health="healthy", state="running"
        )
    }
    after = {
        "freqtrade-portal-postgresql": _state(
            exists=True, running=False, health="unhealthy", state="exited"
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(module, "_cleanup_owned", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="protected service health regressed"):
        module._cleanup_with_protected_health(
            deploy,
            label="state-transfer",
            name="task-container",
            owner="task-owner",
            create_succeeded=True,
            cwd=None,
        )

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["protected_non_regression"] is False
    assert evidence["regressions"] == [
        "freqtrade-portal-postgresql:stopped_running",
        "freqtrade-portal-postgresql:lost_healthy",
    ]


def test_preexisting_unhealthy_stopped_service_is_recorded_not_repaired(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True, running=False, health="unhealthy", state="exited"
        )
    }
    after = {
        "freqtrade-portal-control-plane": _state(
            exists=True, running=False, health="unhealthy", state="exited"
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(module, "_cleanup_owned", lambda *_args, **_kwargs: None)

    module._cleanup_with_protected_health(
        deploy,
        label="schema-check",
        name="task-container",
        owner="task-owner",
        create_succeeded=True,
        cwd=None,
    )

    evidence = deploy._bounded_schema_cleanup_evidence[-1]
    assert evidence["protected_non_regression"] is True
    assert evidence["protected_before"] == before
    assert evidence["protected_after"] == after


def test_existing_stopped_service_may_not_disappear_during_cleanup(monkeypatch) -> None:
    deploy = _deploy_stub()
    deploy._bounded_schema_cleanup_evidence = []
    before = {
        "freqtrade-portal-control-plane": _state(
            exists=True, running=False, health="none", state="exited"
        )
    }
    after = {
        "freqtrade-portal-control-plane": _state(
            exists=False, running=False, health="none", state="absent"
        )
    }
    snapshots = iter((before, after))

    monkeypatch.setattr(
        module,
        "_capture_protected_services",
        lambda _deploy, *, cwd: next(snapshots),
    )
    monkeypatch.setattr(module, "_cleanup_owned", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="protected service health regressed"):
        module._cleanup_with_protected_health(
            deploy,
            label="schema-check",
            name="task-container",
            owner="task-owner",
            create_succeeded=True,
            cwd=None,
        )

    assert deploy._bounded_schema_cleanup_evidence[-1]["regressions"] == [
        "freqtrade-portal-control-plane:became_absent"
    ]


def test_starting_service_may_improve_to_healthy() -> None:
    before = {
        "freqtrade-portal-postgresql": _state(
            exists=True, running=True, health="starting", state="running"
        )
    }
    after = {
        "freqtrade-portal-postgresql": _state(
            exists=True, running=True, health="healthy", state="running"
        )
    }

    assert module._protected_service_regressions(before, after) == []


def test_install_persists_cleanup_health_evidence_in_deployment_report() -> None:
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
    deploy._bounded_schema_cleanup_evidence.append(
        {
            "workload": "schema-migrate",
            "protected_before": {},
            "protected_after": {},
            "protected_non_regression": True,
            "regressions": [],
            "verification_complete": True,
        }
    )

    report: dict[str, Any] = {"status": "success"}
    digest = deploy._write_report(Path("report.json"), report)

    assert digest == "digest"
    assert reports[-1]["bounded_schema_cleanup_evidence"] == [
        {
            "workload": "schema-migrate",
            "protected_before": {},
            "protected_after": {},
            "protected_non_regression": True,
            "regressions": [],
            "verification_complete": True,
        }
    ]
