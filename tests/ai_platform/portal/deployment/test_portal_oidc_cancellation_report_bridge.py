from __future__ import annotations

import copy
import importlib.util
import json
import os
import signal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT_DIR = ROOT / "deploy" / "synology" / "portal-oidc"
MODULE_PATH = DEPLOYMENT_DIR / "cancellation_report_bridge.py"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_cancellation_report_bridge_test",
    MODULE_PATH,
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _cleanup_evidence() -> list[dict[str, Any]]:
    return [
        {
            "workload": "schema-migrate",
            "task_container_name": "task-container",
            "task_container_id": "a" * 64,
            "cleanup_complete": True,
            "protected_non_regression": True,
            "verification_complete": True,
        }
    ]


def _deploy_stub(
    *,
    interrupt: BaseException,
    report_status: str = "failed",
) -> tuple[SimpleNamespace, list[dict[str, Any]], list[str]]:
    reports: list[dict[str, Any]] = []
    rollback: list[str] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise interrupt

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        report["bounded_schema_cleanup_evidence"] = list(deploy._bounded_schema_cleanup_evidence)
        reports.append(copy.deepcopy(report))
        return "digest"

    def original_deploy(args: Any) -> int:
        report: dict[str, Any] = {
            "schema_version": 2,
            "request_id": deploy.REQUEST_ID,
            "implementation_sha": args.expected_repository_sha,
            "status": report_status,
            "secret_values_recorded": False,
            "live_capital_authorized": False,
        }
        try:
            deploy._run(["docker", "wait", "task-container"], sensitive=True)
        except RuntimeError as exc:
            rollback.append("performed")
            report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            deploy._write_report(Path(args.report), report)
            return 1
        raise AssertionError("test fixture expected a failure")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    return deploy, reports, rollback


def _pure_python_sigint_stub() -> tuple[SimpleNamespace, list[dict[str, Any]], list[str]]:
    reports: list[dict[str, Any]] = []
    rollback: list[str] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("pure-Python SIGINT test must not pass through _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        report["bounded_schema_cleanup_evidence"] = list(deploy._bounded_schema_cleanup_evidence)
        reports.append(copy.deepcopy(report))
        return "digest"

    def original_deploy(args: Any) -> int:
        report: dict[str, Any] = {
            "schema_version": 2,
            "request_id": deploy.REQUEST_ID,
            "implementation_sha": args.expected_repository_sha,
            "status": "failed",
            "secret_values_recorded": False,
            "live_capital_authorized": False,
        }
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)
        try:
            handler(signal.SIGINT, None)
        except RuntimeError as exc:
            rollback.append("performed")
            report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            deploy._write_report(Path(args.report), report)
            return 1
        raise AssertionError("installed SIGINT handler must fail into canonical rollback")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    return deploy, reports, rollback


def test_keyboard_interrupt_is_reported_after_canonical_rollback_then_reraised(tmp_path) -> None:
    interrupt = KeyboardInterrupt()
    deploy, reports, rollback = _deploy_stub(interrupt=interrupt)
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="a" * 40,
    )

    with pytest.raises(KeyboardInterrupt) as exc_info:
        deploy.deploy(args)

    assert exc_info.value is interrupt
    assert rollback == ["performed"]
    assert len(reports) == 1
    assert reports[0]["status"] == "failed"
    assert reports[0]["cancellation"] == {
        "type": "KeyboardInterrupt",
        "propagated_after_report": True,
    }
    assert reports[0]["bounded_schema_cleanup_evidence"] == _cleanup_evidence()
    assert reports[0]["secret_values_recorded"] is False
    assert reports[0]["live_capital_authorized"] is False


def test_pure_python_sigint_routes_through_canonical_rollback_and_restores_handler(
    tmp_path,
) -> None:
    deploy, reports, rollback = _pure_python_sigint_stub()
    previous_handler = signal.getsignal(signal.SIGINT)
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="d" * 40,
    )

    with pytest.raises(KeyboardInterrupt):
        deploy.deploy(args)

    assert rollback == ["performed"]
    assert len(reports) == 1
    assert reports[0]["status"] == "failed"
    assert reports[0]["cancellation"] == {
        "type": "KeyboardInterrupt",
        "propagated_after_report": True,
    }
    assert reports[0]["bounded_schema_cleanup_evidence"] == _cleanup_evidence()
    assert signal.getsignal(signal.SIGINT) == previous_handler


def test_post_activation_success_report_is_failed_before_cancellation_propagates(tmp_path) -> None:
    interrupt = KeyboardInterrupt()
    deploy, reports, rollback = _deploy_stub(
        interrupt=interrupt,
        report_status="success",
    )
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="c" * 40,
    )

    with pytest.raises(KeyboardInterrupt) as exc_info:
        deploy.deploy(args)

    assert exc_info.value is interrupt
    assert rollback == ["performed"]
    assert len(reports) == 1
    assert reports[0]["status"] == "failed"
    assert reports[0]["cancellation"]["type"] == "KeyboardInterrupt"
    assert reports[0]["bounded_schema_cleanup_evidence"]


def test_ordinary_exception_is_not_reclassified_as_cancellation(tmp_path) -> None:
    deploy, reports, rollback = _deploy_stub(interrupt=RuntimeError("ordinary failure"))
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="b" * 40,
    )

    assert deploy.deploy(args) == 1
    assert rollback == ["performed"]
    assert len(reports) == 1
    assert "cancellation" not in reports[0]


def test_entrypoint_installs_cancellation_bridge_after_runtime_wrappers() -> None:
    source = (DEPLOYMENT_DIR / "deploy_entrypoint.py").read_text(encoding="utf-8")

    assert 'DEPLOYMENT_DIR / "cancellation_report_bridge.py"' in source
    assert "cancellation_bridge.install(deploy)" in source
    assert source.index("copy_on_write.install(deploy)") < source.index(
        "cancellation_bridge.install(deploy)"
    )


def test_pure_python_sigterm_routes_through_canonical_rollback(tmp_path) -> None:
    reports: list[dict[str, Any]] = []
    rollback: list[str] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("pure-Python SIGTERM test must not pass through _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        report["bounded_schema_cleanup_evidence"] = list(deploy._bounded_schema_cleanup_evidence)
        reports.append(copy.deepcopy(report))
        return "digest"

    def original_deploy(args: Any) -> int:
        report = {
            "schema_version": 2,
            "request_id": deploy.REQUEST_ID,
            "implementation_sha": args.expected_repository_sha,
            "status": "failed",
            "secret_values_recorded": False,
            "live_capital_authorized": False,
        }
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        try:
            handler(signal.SIGTERM, None)
        except RuntimeError as exc:
            rollback.append("performed")
            report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            deploy._write_report(Path(args.report), report)
            return 1
        raise AssertionError("installed SIGTERM handler must enter canonical rollback")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    previous_handler = signal.getsignal(signal.SIGTERM)
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="e" * 40,
    )

    with pytest.raises(SystemExit) as exc_info:
        deploy.deploy(args)

    assert exc_info.value.code == 128 + signal.SIGTERM
    assert rollback == ["performed"]
    assert len(reports) == 1
    assert reports[0]["status"] == "failed"
    assert reports[0]["cancellation"]["type"] == "SystemExit"
    assert reports[0]["bounded_schema_cleanup_evidence"] == _cleanup_evidence()
    assert signal.getsignal(signal.SIGTERM) == previous_handler


def test_late_sigint_preserves_existing_canonical_report(tmp_path) -> None:
    reports: list[dict[str, Any]] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("late SIGINT test must not pass through _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        report["bounded_schema_cleanup_evidence"] = list(deploy._bounded_schema_cleanup_evidence)
        path.write_text(json.dumps(report), encoding="utf-8")
        reports.append(copy.deepcopy(report))
        return "digest"

    def original_deploy(args: Any) -> int:
        report = {
            "schema_version": 2,
            "request_id": deploy.REQUEST_ID,
            "implementation_sha": args.expected_repository_sha,
            "status": "success",
            "secret_values_recorded": False,
            "live_capital_authorized": False,
            "portal": {"health": "healthy", "api_mode": True},
            "authentik": {"issuer_verified": True},
            "database": {"revision": "20260809_04_runtime_isolation_binding"},
            "recovery": {"restart_verified": True},
        }
        deploy._write_report(Path(args.report), report)
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)
        handler(signal.SIGINT, None)
        raise AssertionError("late SIGINT must not return")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    module.install(deploy)
    args = SimpleNamespace(
        report=str(tmp_path / "report.json"),
        expected_repository_sha="f" * 40,
    )

    with pytest.raises(KeyboardInterrupt):
        deploy.deploy(args)

    assert len(reports) == 2
    final = reports[-1]
    assert final["status"] == "failed"
    assert final["portal"] == {"health": "healthy", "api_mode": True}
    assert final["authentik"] == {"issuer_verified": True}
    assert final["database"] == {"revision": "20260809_04_runtime_isolation_binding"}
    assert final["recovery"] == {"restart_verified": True}
    assert final["cancellation"]["type"] == "KeyboardInterrupt"
    assert final["failure"]["type"] == "CancellationRecoveryError"
    assert final["bounded_schema_cleanup_evidence"] == _cleanup_evidence()


def test_early_sigint_does_not_republish_stale_report(tmp_path) -> None:
    reports: list[dict[str, Any]] = []
    report_path = tmp_path / "report.json"
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("early SIGINT test must not pass through _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        path.write_text(json.dumps(report), encoding="utf-8")
        reports.append(copy.deepcopy(report))
        return "digest"

    def original_deploy(args: Any) -> int:
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)
        handler(signal.SIGINT, None)
        raise AssertionError("early SIGINT must not return")

    stale = {
        "schema_version": 2,
        "request_id": deploy.REQUEST_ID,
        "implementation_sha": "1" * 40,
        "status": "success",
        "portal": {"health": "stale"},
        "database": {"revision": "stale"},
        "recovery": {"restart_verified": True},
    }
    report_path.write_text(json.dumps(stale), encoding="utf-8")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    module.install(deploy)
    args = SimpleNamespace(
        report=str(report_path),
        expected_repository_sha="1" * 40,
    )

    with pytest.raises(KeyboardInterrupt):
        deploy.deploy(args)

    assert len(reports) == 1
    final = reports[0]
    assert final["status"] == "failed"
    assert final["implementation_sha"] == "1" * 40
    assert final["cancellation"]["type"] == "KeyboardInterrupt"
    assert final["failure"]["type"] == "CancellationRecoveryError"
    assert "portal" not in final
    assert "database" not in final
    assert "recovery" not in final


def test_sigint_after_report_bytes_preserves_current_report(tmp_path) -> None:
    reports: list[dict[str, Any]] = []
    report_path = tmp_path / "report.json"
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("post-write SIGINT test must not pass through _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        path.write_text(json.dumps(report), encoding="utf-8")
        reports.append(copy.deepcopy(report))
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)
        handler(signal.SIGINT, None)
        raise AssertionError("SIGINT after report bytes must not return")

    def original_deploy(args: Any) -> int:
        report = {
            "schema_version": 2,
            "request_id": deploy.REQUEST_ID,
            "implementation_sha": args.expected_repository_sha,
            "status": "success",
            "secret_values_recorded": False,
            "live_capital_authorized": False,
            "portal": {"health": "healthy", "api_mode": True},
            "database": {"revision": "20260809_04_runtime_isolation_binding"},
            "recovery": {"restart_verified": True},
        }
        deploy._write_report(report_path, report)
        raise AssertionError("post-write SIGINT must interrupt deploy")

    stale = {
        "schema_version": 2,
        "request_id": deploy.REQUEST_ID,
        "implementation_sha": "2" * 40,
        "status": "success",
        "portal": {"health": "stale"},
    }
    report_path.write_text(json.dumps(stale), encoding="utf-8")

    deploy._run = original_run
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    module.install(deploy)
    args = SimpleNamespace(
        report=str(report_path),
        expected_repository_sha="2" * 40,
    )

    with pytest.raises(KeyboardInterrupt):
        deploy.deploy(args)

    assert len(reports) == 2
    final = reports[-1]
    assert final["status"] == "failed"
    assert final["portal"] == {"health": "healthy", "api_mode": True}
    assert final["database"] == {"revision": "20260809_04_runtime_isolation_binding"}
    assert final["recovery"] == {"restart_verified": True}
    assert final["cancellation"]["type"] == "KeyboardInterrupt"
    assert final["failure"]["type"] == "CancellationRecoveryError"


def test_overlapping_same_report_invocation_fails_before_deploy(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "request_id": "portal-authentik-public-oidc-20260801-v1",
                "implementation_sha": "3" * 40,
                "status": "success",
                "portal": {"health": "first-invocation"},
            }
        ),
        encoding="utf-8",
    )
    first = SimpleNamespace(
        DeploymentError=RuntimeError,
        _portal_report_lock_fd=None,
        _portal_current_report_path=None,
    )
    second = SimpleNamespace(
        DeploymentError=RuntimeError,
        _portal_report_lock_fd=None,
        _portal_current_report_path=None,
    )
    args = SimpleNamespace(report=str(report_path))

    module._reserve_current_report_path(first, args)
    module._clear_current_report_path(first, args)
    report_path.write_text(
        json.dumps({"status": "success", "portal": {"health": "first-invocation"}}),
        encoding="utf-8",
    )
    try:
        with pytest.raises(RuntimeError, match="already owned by another invocation"):
            module._reserve_current_report_path(second, args)
        assert json.loads(report_path.read_text(encoding="utf-8"))["portal"] == {
            "health": "first-invocation"
        }
        assert second._portal_current_report_path is None
        assert second._portal_report_lock_fd is None
    finally:
        module._release_current_report_lock(first)

    module._reserve_current_report_path(second, args)
    try:
        module._clear_current_report_path(second, args)
        assert second._portal_current_report_path == report_path.resolve()
        assert not report_path.exists()
    finally:
        module._release_current_report_lock(second)


def test_lock_contention_fails_before_installing_termination_handlers(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    first = SimpleNamespace(
        DeploymentError=RuntimeError,
        _portal_report_lock_fd=None,
        _portal_current_report_path=None,
    )
    args = SimpleNamespace(
        report=str(report_path),
        expected_repository_sha="4" * 40,
    )
    module._reserve_current_report_path(first, args)
    report_path.write_text(
        json.dumps({"status": "success", "portal": {"health": "first"}}),
        encoding="utf-8",
    )

    deploy_calls: list[str] = []
    reports: list[dict[str, Any]] = []
    second = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise AssertionError("lock contention must not enter _run")

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        reports.append(copy.deepcopy(report))
        path.write_text(json.dumps(report), encoding="utf-8")
        return "digest"

    def original_deploy(_args: Any) -> int:
        deploy_calls.append("entered")
        return 0

    second._run = original_run
    second._write_report = original_write_report
    second.deploy = original_deploy
    previous_sigint = signal.getsignal(signal.SIGINT)
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    module.install(second)
    try:
        with pytest.raises(RuntimeError, match="already owned by another invocation"):
            second.deploy(args)
        assert deploy_calls == []
        assert reports == []
        assert signal.getsignal(signal.SIGINT) == previous_sigint
        assert signal.getsignal(signal.SIGTERM) == previous_sigterm
        assert json.loads(report_path.read_text(encoding="utf-8"))["portal"] == {"health": "first"}
    finally:
        module._release_current_report_lock(first)


def test_sigterm_during_stale_report_clear_persists_cancellation_and_releases_lock(
    tmp_path, monkeypatch
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps({"status": "success", "portal": {"health": "stale"}}))
    reports: list[dict[str, Any]] = []
    deploy_calls: list[str] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        reports.append(copy.deepcopy(report))
        path.write_text(json.dumps(report), encoding="utf-8")
        return "digest"

    def original_deploy(_args: Any) -> int:
        deploy_calls.append("entered")
        return 0

    original_unlink = Path.unlink

    def interrupting_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == report_path:
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
        original_unlink(path, *args, **kwargs)

    deploy._run = lambda *args, **kwargs: None
    deploy._write_report = original_write_report
    deploy.deploy = original_deploy
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    module.install(deploy)
    monkeypatch.setattr(Path, "unlink", interrupting_unlink)
    args = SimpleNamespace(
        report=str(report_path),
        expected_repository_sha="5" * 40,
    )

    with pytest.raises(SystemExit) as exc_info:
        deploy.deploy(args)

    assert exc_info.value.code == 128 + signal.SIGTERM
    assert deploy_calls == []
    assert reports[-1]["status"] == "failed"
    assert reports[-1]["cancellation"]["type"] == "SystemExit"
    assert reports[-1]["implementation_sha"] == "5" * 40
    assert "portal" not in reports[-1]
    assert deploy._portal_report_lock_fd is None
    assert signal.getsignal(signal.SIGTERM) == previous_sigterm

    contender = SimpleNamespace(
        DeploymentError=RuntimeError,
        _portal_report_lock_fd=None,
        _portal_current_report_path=None,
    )
    module._reserve_current_report_path(contender, args)
    module._release_current_report_lock(contender)


@pytest.mark.parametrize("transition", ["after_lock", "restore_handoff"])
def test_sigterm_is_bridged_across_handler_transitions(tmp_path, monkeypatch, transition) -> None:
    report_path = tmp_path / "report.json"
    reports: list[dict[str, Any]] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=_cleanup_evidence(),
    )

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        reports.append(copy.deepcopy(report))
        path.write_text(json.dumps(report), encoding="utf-8")
        return "digest"

    deploy._run = lambda *args, **kwargs: None
    deploy._write_report = original_write_report
    deploy.deploy = lambda _args: 0
    module.install(deploy)
    restore_states: list[bool] = []
    if transition == "after_lock":
        original_reserve = module._reserve_current_report_path

        def reserve_then_cancel(current_deploy: Any, current_args: Any) -> None:
            original_reserve(current_deploy, current_args)
            os.kill(os.getpid(), signal.SIGTERM)

        monkeypatch.setattr(module, "_reserve_current_report_path", reserve_then_cancel)
    else:
        original_restore = module._restore_termination_handlers

        def observe_restore(previous_handlers: dict[int, Any]) -> None:
            restore_states.append(deploy._portal_termination_handlers_active)
            original_restore(previous_handlers)

        monkeypatch.setattr(module, "_restore_termination_handlers", observe_restore)

    previous_sigint = signal.getsignal(signal.SIGINT)
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    args = SimpleNamespace(
        report=str(report_path),
        expected_repository_sha="6" * 40,
    )
    if transition == "after_lock":
        with pytest.raises(SystemExit) as exc_info:
            deploy.deploy(args)
        assert exc_info.value.code == 128 + signal.SIGTERM
        assert reports[-1]["status"] == "failed"
        assert reports[-1]["cancellation"]["type"] == "SystemExit"
    else:
        assert deploy.deploy(args) == 0
        assert restore_states == [False]
    assert deploy._portal_report_lock_fd is None
    assert signal.getsignal(signal.SIGINT) == previous_sigint
    assert signal.getsignal(signal.SIGTERM) == previous_sigterm
