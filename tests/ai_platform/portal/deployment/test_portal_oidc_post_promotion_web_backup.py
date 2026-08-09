from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
MODULE = ROOT / "deploy" / "synology" / "portal-oidc" / "postgresql_copy_on_write.py"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location("portal_postgresql_copy_on_write_guard", MODULE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_post_promotion_web_verification_failure_restores_new_backup_stopped() -> None:
    module = _load_module()
    portal = "freqtrade-portal-web"
    control = "freqtrade-portal-control-plane"
    backup = f"{portal}-backup-123"
    containers = {portal, control}
    backups: set[str] = set()
    commands: list[list[str]] = []

    def completed(command: list[str], stdout: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout, "")

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[:5] == ["docker", "ps", "-a", "--format", "{{.Names}}"]:
            names = sorted({*containers, *backups})
            return completed(command, "\n".join(names) + ("\n" if names else ""))
        if command[:2] == ["docker", "rename"]:
            old, new = command[2], command[3]
            backups.discard(old)
            containers.discard(old)
            containers.add(new)
            return completed(command)
        if command[:2] == ["docker", "start"]:
            raise AssertionError("restored web must remain stopped until outer authority rollback")
        return completed(command)

    def remove_container(name: str) -> None:
        containers.discard(name)

    def container_exists(name: str) -> bool:
        return name in containers or name in backups

    def failing_deploy_web(_image: str, _suffix: str) -> tuple[str | None, str]:
        containers.discard(portal)
        backups.add(backup)
        containers.add(portal)
        raise RuntimeError("post-promotion Market Evidence verification failed")

    previous = {
        "web_exists": True,
        "web_running": True,
        "control_exists": True,
        "control_running": True,
    }

    deploy = SimpleNamespace(
        deploy=lambda _args: 0,
        _current_database_mode=lambda _runtime, _postgres: ("legacy_sqlite", None),
        _create_postgres_database=lambda _database: None,
        _quiesce_existing_portal=lambda: dict(previous),
        _deploy_web=failing_deploy_web,
        _activate_candidate_runtime=lambda: None,
        _promote_control=lambda _candidate: None,
        _restore_previous_portal=lambda _previous, _control_backup, _web_backup: None,
        _drop_candidate_database=lambda _database: None,
        _write_report=lambda _path, _report: "digest",
        _container_exists=container_exists,
        _container_running=lambda name: name in containers,
        _remove_container=remove_container,
        _run=run,
        PORTAL_CONTAINER=portal,
        CONTROL_CONTAINER=control,
        DeploymentError=RuntimeError,
    )

    module.install(deploy)
    deploy._quiesce_existing_portal()

    try:
        deploy._deploy_web("portal-image", "abc")
    except RuntimeError as exc:
        assert "post-promotion Market Evidence verification failed" in str(exc)
    else:
        raise AssertionError("expected post-promotion verification failure")

    assert portal in containers
    assert backup not in backups
    assert ["docker", "rename", backup, portal] in commands
    assert not any(command[:2] == ["docker", "start"] for command in commands)
