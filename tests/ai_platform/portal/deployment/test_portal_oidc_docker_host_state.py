from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-oidc"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_docker_host_state",
    DEPLOYMENT / "docker_host_state.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def deploy_module(tmp_path: Path, run):
    def assert_database_name(name: str) -> None:
        if not name.startswith("portal_candidate_"):
            raise RuntimeError("invalid database")

    return SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        PORTAL_STATE_DIR=tmp_path / "runner-state",
        PORTAL_DATA_DIR=Path("/volume1/docker/freqtrade-portal-oidc/data"),
        PORTAL_LEGACY_BACKUP_DIR=Path(
            "/volume1/docker/freqtrade-portal-oidc/data/legacy-backups"
        ),
        PORTAL_POSTGRES_ENV=tmp_path / "postgres.env",
        PORTAL_POSTGRES_IMAGE=(
            "docker.io/library/postgres:16.13-alpine3.23@sha256:" + "1" * 64
        ),
        PORTAL_POSTGRES_ALIAS="portal-postgresql",
        PORTAL_NETWORK="portal_oidc_public",
        PORTAL_UID=10001,
        PORTAL_GID=10001,
        _assert_database_name=assert_database_name,
    )


def test_prepare_state_uses_docker_host_namespace_not_runner_volume1(
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"{module.PREPARE_MARKER}\n",
            stderr="",
        )

    deploy = deploy_module(tmp_path, run)
    module._prepare_docker_host_state(deploy)

    assert deploy.PORTAL_STATE_DIR.is_dir()
    assert len(calls) == 1
    command = calls[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--mount") + 1] == (
        "type=bind,src=/volume1/docker,dst=/host-volume"
    )
    assert command[command.index("--user") + 1] == "0:0"
    assert "--privileged" not in command
    assert "/var/run/docker.sock" not in " ".join(command)
    script = command[-1]
    assert "/host-volume/freqtrade-portal-oidc/data" in script
    assert "legacy-backups" in script
    assert "postgres-backups" in script
    assert "10001:10001:700" in script


def test_sqlite_snapshot_is_created_inside_docker_host_bind(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.time, "time", lambda: 123456)
    sha = "a" * 40
    filename = "portal-pre-postgresql-aaaaaaaaaaaa-123456.db"
    digest = "b" * 64
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(command: list[str], **kwargs):
        calls.append((command, kwargs))
        payload = json.dumps(
            {"filename": filename, "sha256": digest},
            sort_keys=True,
        )
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"{module.SQLITE_MARKER}{payload}\n",
            stderr="",
        )

    deploy = deploy_module(tmp_path, run)
    snapshot, actual_digest = module._snapshot_legacy_sqlite(
        deploy,
        "local/freqtrade-portal-control-plane:aaaaaaaaaaaa",
        sha,
    )

    assert snapshot == deploy.PORTAL_LEGACY_BACKUP_DIR / filename
    assert actual_digest == digest
    command, kwargs = calls[0]
    assert kwargs["sensitive"] is True
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--mount") + 1] == (
        "type=bind,src=/volume1/docker/freqtrade-portal-oidc/data,dst=/portal-state"
    )
    assert command[command.index("--user") + 1] == "10001:10001"
    assert command[command.index("--entrypoint") + 1] == "python"
    assert "local/freqtrade-portal-control-plane:aaaaaaaaaaaa" in command
    script = command[-1]
    assert 'root / "portal.db"' in script
    assert "source_path.is_symlink()" in script
    assert "sqlite3.connect" in script
    assert "source.backup(target)" in script
    assert "PRAGMA integrity_check" in script


def test_postgres_backup_is_written_to_docker_host_without_secret_cli_value(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.time, "time", lambda: 654321)
    sha = "c" * 40
    database = "portal_candidate_cccccccccccc"
    filename = "portal-cccccccccccc-654321.backup"
    digest = "d" * 64
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(command: list[str], **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"{module.POSTGRES_MARKER}{filename}|{digest}\n",
            stderr="",
        )

    deploy = deploy_module(tmp_path, run)
    deploy.PORTAL_POSTGRES_ENV.write_text(
        "POSTGRES_USER=portal\nPOSTGRES_PASSWORD=do-not-place-on-cli\n",
        encoding="utf-8",
    )

    assert module._backup_postgres(deploy, database, sha) == digest

    command, kwargs = calls[0]
    assert kwargs["sensitive"] is True
    assert command[command.index("--network") + 1] == "portal_oidc_public"
    assert command[command.index("--mount") + 1] == (
        "type=bind,src=/volume1/docker/freqtrade-portal-oidc/data,dst=/portal-state"
    )
    env_file_index = command.index("--env-file")
    assert command[env_file_index + 1] == str(deploy.PORTAL_POSTGRES_ENV)
    assert "do-not-place-on-cli" not in " ".join(command)
    assert f"TARGET_DATABASE={database}" in command
    assert f"BACKUP_NAME={filename}" in command
    script = command[-1]
    assert 'export PGPASSWORD="$POSTGRES_PASSWORD"' in script
    assert "pg_dump" in script
    assert "sha256sum" in script


def test_install_captures_exact_control_image_and_entrypoint_wires_bridge(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.time, "time", lambda: 111)
    digest = "e" * 64
    filename = "portal-pre-postgresql-eeeeeeeeeeee-111.db"
    calls: list[list[str]] = []

    def run(command: list[str], **_kwargs):
        calls.append(command)
        if module.SQLITE_MARKER in command[-1]:
            payload = json.dumps(
                {"filename": filename, "sha256": digest},
                sort_keys=True,
            )
            stdout = f"{module.SQLITE_MARKER}{payload}\n"
        else:
            stdout = f"{module.PREPARE_MARKER}\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = deploy_module(tmp_path, run)

    def build_images(_repo: Path, _sha: str):
        return (
            "local/control:eeeeeeeeeeee",
            "sha256:control",
            "local/web:eeeeeeeeeeee",
            "sha256:web",
        )

    def unexpected_snapshot(_sha: str):
        raise AssertionError("runner-filesystem snapshot must be replaced")

    def unexpected_backup(_db: str, _sha: str):
        raise AssertionError("runner-filesystem backup must be replaced")

    def unexpected_prepare() -> None:
        raise AssertionError("runner-filesystem host prepare must be replaced")

    deploy._build_images = build_images
    deploy._snapshot_legacy_sqlite = unexpected_snapshot
    deploy._backup_postgres = unexpected_backup
    deploy._prepare_host_state = unexpected_prepare

    module.install(deploy)
    deploy._build_images(Path("/repo"), "e" * 40)
    snapshot, actual_digest = deploy._snapshot_legacy_sqlite("e" * 40)

    assert snapshot.name == filename
    assert actual_digest == digest
    assert "local/control:eeeeeeeeeeee" in calls[-1]

    entrypoint = (DEPLOYMENT / "deploy_entrypoint.py").read_text(encoding="utf-8")
    assert 'DEPLOYMENT_DIR / "docker_host_state.py"' in entrypoint
    assert "docker_host_state.install(deploy)" in entrypoint


def test_noncanonical_portal_host_path_is_rejected(tmp_path: Path) -> None:
    deploy = deploy_module(tmp_path, lambda *_args, **_kwargs: None)
    deploy.PORTAL_DATA_DIR = Path("/tmp/portal-data")

    with pytest.raises(RuntimeError, match="canonical Synology Docker root"):
        module._portal_relative_path(deploy)
