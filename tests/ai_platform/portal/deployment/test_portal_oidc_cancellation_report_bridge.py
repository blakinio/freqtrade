from __future__ import annotations

import copy
import importlib.util
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
