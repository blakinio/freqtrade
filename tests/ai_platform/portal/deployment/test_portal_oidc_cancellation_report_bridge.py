from __future__ import annotations

import copy
import importlib.util
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


def _deploy_stub(*, interrupt: BaseException) -> tuple[SimpleNamespace, list[dict[str, Any]], list[str]]:
    reports: list[dict[str, Any]] = []
    rollback: list[str] = []
    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        REQUEST_ID="portal-authentik-public-oidc-20260801-v1",
        _bounded_schema_cleanup_evidence=[
            {
                "workload": "schema-migrate",
                "task_container_name": "task-container",
                "task_container_id": "a" * 64,
                "protected_non_regression": True,
                "verification_complete": True,
            }
        ],
    )

    def original_run(command, *, cwd=None, sensitive=False, check=True):
        raise interrupt

    def original_write_report(path: Path, report: dict[str, Any]) -> str:
        report["bounded_schema_cleanup_evidence"] = list(
            deploy._bounded_schema_cleanup_evidence
        )
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
        try:
            deploy._run(["docker", "wait", "task-container"], sensitive=True)
        except Exception as exc:
            rollback.append("performed")
            report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            deploy._write_report(Path(args.report), report)
            return 1
        raise AssertionError("test fixture expected a failure")

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
    assert reports[0]["cancellation"] == {
        "type": "KeyboardInterrupt",
        "propagated_after_report": True,
    }
    assert reports[0]["bounded_schema_cleanup_evidence"] == [
        {
            "workload": "schema-migrate",
            "task_container_name": "task-container",
            "task_container_id": "a" * 64,
            "protected_non_regression": True,
            "verification_complete": True,
        }
    ]
    assert reports[0]["secret_values_recorded"] is False
    assert reports[0]["live_capital_authorized"] is False


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
