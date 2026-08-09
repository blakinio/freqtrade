from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "postgresql_copy_on_write.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_partial_quiesce_recovery", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_partial_quiesce_failure_restores_pre_stop_runtime() -> None:
    web = "freqtrade-portal-web"
    control = "freqtrade-portal-control-plane"
    running = {web: True, control: True}
    restored: list[dict[str, bool]] = []

    def original_quiesce() -> dict[str, bool]:
        running[web] = False
        raise RuntimeError("synthetic control stop failure")

    def original_restore(previous, control_backup, web_backup) -> None:
        assert control_backup is None
        assert web_backup is None
        restored.append(dict(previous))
        running[web] = previous["web_running"]
        running[control] = previous["control_running"]

    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        PORTAL_CONTAINER=web,
        CONTROL_CONTAINER=control,
        deploy=lambda _args: 0,
        _current_database_mode=lambda _runtime, _postgres: ("fresh", None),
        _create_postgres_database=lambda _database: None,
        _quiesce_existing_portal=original_quiesce,
        _activate_candidate_runtime=lambda: None,
        _promote_control=lambda _candidate: None,
        _restore_previous_portal=original_restore,
        _drop_candidate_database=lambda _database: None,
        _write_report=lambda _path, _report: "report-sha256",
        _container_exists=lambda container: container in running,
        _container_running=lambda container: running[container],
    )

    module.install(deploy)

    with pytest.raises(RuntimeError, match="synthetic control stop failure"):
        deploy._quiesce_existing_portal()

    assert running == {web: True, control: True}
    assert restored == [
        {
            "web_exists": True,
            "web_running": True,
            "control_exists": True,
            "control_running": True,
        }
    ]
