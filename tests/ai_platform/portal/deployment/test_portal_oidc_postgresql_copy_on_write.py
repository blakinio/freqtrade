from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "postgresql_copy_on_write.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_postgresql_copy_on_write", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _cutover_stubs(deploy: SimpleNamespace, tmp_path: Path) -> None:
    deploy.PORTAL_RUNTIME_ENV = tmp_path / "runtime.env"
    deploy.PORTAL_CONTAINER = "freqtrade-portal-web"
    deploy.CONTROL_CONTAINER = "freqtrade-portal-control-plane"
    deploy._container_running = lambda _container: False
    deploy._activate_candidate_runtime = lambda: None
    deploy._promote_control = lambda _candidate: None
    deploy._write_env_atomic = lambda path, values: path.write_text(
        "\n".join(f"{name}={value}" for name, value in sorted(values.items())) + "\n",
        encoding="utf-8",
    )


def test_existing_postgresql_is_cloned_after_quiesce_before_migration(tmp_path: Path) -> None:
    events: list[object] = []
    captured_report: dict[str, object] = {}
    databases = {"portal_candidate_oldoldold"}
    runtime_env = {"PORTAL_DATABASE_URL": "postgresql://active"}
    postgres_env = {"POSTGRES_PASSWORD": "synthetic"}
    args = SimpleNamespace(expected_repository_sha="a" * 40)

    deploy = SimpleNamespace()
    deploy.DeploymentError = RuntimeError
    deploy.PORTAL_POSTGRES_CONTAINER = "portal-postgresql"
    deploy.PORTAL_POSTGRES_USER = "portal"
    deploy.PORTAL_POSTGRES_ADMIN_DB = "portal_admin"
    deploy._assert_database_name = lambda database_name: events.append(("validate", database_name))
    deploy._current_database_mode = lambda _runtime, _postgres: (
        "postgresql",
        "portal_candidate_oldoldold",
    )
    deploy._create_postgres_database = lambda database_name: events.append(
        ("unexpected-direct-create", database_name)
    )

    def quiesce_existing_portal() -> dict[str, bool]:
        events.append("quiesce")
        return {
            "web_exists": True,
            "web_running": True,
            "control_exists": True,
            "control_running": True,
        }

    deploy._quiesce_existing_portal = quiesce_existing_portal

    def backup_postgres(database_name: str, sha: str) -> str:
        events.append(("backup", database_name, sha))
        return "backup-sha256"

    deploy._backup_postgres = backup_postgres
    deploy._postgres_database_exists = lambda database_name: database_name in databases

    def drop_candidate_database(database_name: str) -> None:
        events.append(("drop", database_name))
        databases.discard(database_name)

    deploy._drop_candidate_database = drop_candidate_database

    def restore_previous_portal(previous, control_backup, web_backup) -> None:
        events.append(("restore", previous, control_backup, web_backup))

    deploy._restore_previous_portal = restore_previous_portal

    def run(command, *, sensitive=False, **_kwargs):
        events.append(("run", tuple(command), sensitive))
        if "createdb" in command:
            databases.add(command[-1])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    deploy._run = run

    def write_report(_path, report):
        captured_report.update(report)
        events.append("write-report")
        return "report-sha256"

    deploy._write_report = write_report
    _cutover_stubs(deploy, tmp_path)

    def original_deploy(_args):
        mode, database_name = deploy._current_database_mode(runtime_env, postgres_env)
        assert mode == "fresh"
        assert database_name is None
        candidate = f"portal_candidate_{_args.expected_repository_sha[:12]}"
        assert candidate not in databases
        deploy._create_postgres_database(candidate)
        deploy._quiesce_existing_portal()
        assert candidate in databases
        deploy._write_report(
            Path("report.json"),
            {
                "status": "success",
                "database": {"state_transition": "fresh_postgresql"},
            },
        )
        return 0

    deploy.deploy = original_deploy
    module.install(deploy)

    assert deploy.deploy(args) == 0
    assert "quiesce" in events
    assert ("backup", "portal_candidate_oldoldold", "a" * 40) in events
    assert not any(
        isinstance(event, tuple) and event[0] == "unexpected-direct-create" for event in events
    )
    createdb_event = next(
        event
        for event in events
        if isinstance(event, tuple) and event[0] == "run" and "createdb" in event[1]
    )
    assert createdb_event[1][-2:] == (
        "portal_candidate_oldoldold",
        "portal_candidate_aaaaaaaaaaaa",
    )
    assert events.index("quiesce") < events.index(
        ("backup", "portal_candidate_oldoldold", "a" * 40)
    )
    assert captured_report["database"] == {
        "state_transition": "postgresql_copy_on_write",
        "pre_migration_backup_sha256": "backup-sha256",
        "source_database": "portal_candidate_oldoldold",
        "candidate_database": "portal_candidate_aaaaaaaaaaaa",
        "source_database_retained_for_rollback": True,
        "authority_journaled_before_promotion": False,
        "candidate_quiesced_before_authority_restore": False,
        "candidate_database_retained_for_recovery": False,
    }
    assert captured_report["database_recovery"] == {
        "pre_migration_backup_sha256": "backup-sha256",
        "source_database": "portal_candidate_oldoldold",
        "candidate_database": "portal_candidate_aaaaaaaaaaaa",
        "source_database_retained_for_rollback": True,
        "authority_journaled_before_promotion": False,
        "candidate_quiesced_before_authority_restore": False,
        "candidate_database_retained_for_recovery": False,
        "restore_authorized": False,
    }


def test_authority_is_journaled_before_promotion_and_exposed_candidate_is_retained_on_rollback(
    tmp_path: Path,
) -> None:
    args = SimpleNamespace(expected_repository_sha="c" * 40)
    old_runtime = {"PORTAL_DATABASE_URL": "postgresql://old-authority"}
    runtime_path = tmp_path / "runtime.env"
    candidate_path = tmp_path / "runtime.candidate.env"
    runtime_path.write_text("PORTAL_DATABASE_URL=postgresql://old-authority\n", encoding="utf-8")
    candidate_path.write_text(
        "PORTAL_DATABASE_URL=postgresql://candidate-authority\n",
        encoding="utf-8",
    )
    events: list[str] = []
    databases = {"portal_candidate_oldoldold"}
    captured_report: dict[str, object] = {}
    running = {
        "freqtrade-portal-web": True,
        "freqtrade-portal-control-plane": True,
    }

    def database_exists(database_name: str) -> bool:
        return database_name in databases

    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        PORTAL_POSTGRES_CONTAINER="portal-postgresql",
        PORTAL_POSTGRES_USER="portal",
        PORTAL_POSTGRES_ADMIN_DB="portal_admin",
        PORTAL_RUNTIME_ENV=runtime_path,
        PORTAL_CONTAINER="freqtrade-portal-web",
        CONTROL_CONTAINER="freqtrade-portal-control-plane",
        _current_database_mode=lambda _runtime, _postgres: (
            "postgresql",
            "portal_candidate_oldoldold",
        ),
        _create_postgres_database=lambda _database_name: None,
        _quiesce_existing_portal=lambda: {
            "web_exists": True,
            "web_running": True,
            "control_exists": True,
            "control_running": True,
        },
        _assert_database_name=lambda _database_name: None,
        _backup_postgres=lambda _database_name, _sha: "backup-sha256",
        _postgres_database_exists=database_exists,
        _container_running=lambda container: running[container],
    )

    def drop_candidate_database(database_name: str) -> None:
        events.append("drop-candidate")
        databases.discard(database_name)

    deploy._drop_candidate_database = drop_candidate_database

    def run(command, **_kwargs):
        if "createdb" in command:
            databases.add(command[-1])
        if command[:2] == ["docker", "stop"]:
            container = command[2]
            events.append(f"stop:{container}")
            running[container] = False
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    deploy._run = run

    def activate_candidate_runtime() -> None:
        events.append("journal-candidate-authority")
        candidate_path.replace(runtime_path)

    deploy._activate_candidate_runtime = activate_candidate_runtime

    def promote_control(_candidate: str) -> str:
        assert runtime_path.read_text(encoding="utf-8") == (
            "PORTAL_DATABASE_URL=postgresql://candidate-authority\n"
        )
        events.append("promote-control")
        return "control-backup"

    deploy._promote_control = promote_control

    def write_env_atomic(path: Path, values: dict[str, str]) -> None:
        assert not any(running.values())
        events.append("restore-runtime-authority")
        path.write_text(
            "\n".join(f"{name}={value}" for name, value in sorted(values.items())) + "\n",
            encoding="utf-8",
        )

    deploy._write_env_atomic = write_env_atomic

    def restore_previous_portal(_previous, _control_backup, _web_backup) -> None:
        assert not any(running.values())
        assert runtime_path.read_text(encoding="utf-8") == (
            "PORTAL_DATABASE_URL=postgresql://old-authority\n"
        )
        events.append("restore-old-containers")

    deploy._restore_previous_portal = restore_previous_portal

    def write_report(_path, report):
        captured_report.update(report)
        return "report-sha256"

    deploy._write_report = write_report

    def original_deploy(_args) -> int:
        mode, database_name = deploy._current_database_mode(old_runtime, {})
        assert mode == "fresh"
        assert database_name is None
        candidate = "portal_candidate_cccccccccccc"
        deploy._create_postgres_database(candidate)
        previous = deploy._quiesce_existing_portal()
        assert candidate in databases
        deploy._promote_control("control-candidate")
        deploy._activate_candidate_runtime()
        assert events.count("journal-candidate-authority") == 1
        deploy._restore_previous_portal(previous, "control-backup", "web-backup")
        deploy._drop_candidate_database(candidate)
        deploy._write_report(Path("report.json"), {"status": "failure", "database": {}})
        return 1

    deploy.deploy = original_deploy
    module.install(deploy)

    assert deploy.deploy(args) == 1
    assert events.index("journal-candidate-authority") < events.index("promote-control")
    assert events.index("stop:freqtrade-portal-web") < events.index(
        "stop:freqtrade-portal-control-plane"
    )
    assert events.index("stop:freqtrade-portal-control-plane") < events.index(
        "restore-runtime-authority"
    )
    assert events.index("restore-runtime-authority") < events.index("restore-old-containers")
    assert "drop-candidate" not in events
    assert "portal_candidate_cccccccccccc" in databases
    recovery = captured_report["database_recovery"]
    assert isinstance(recovery, dict)
    assert recovery["authority_journaled_before_promotion"] is True
    assert recovery["candidate_quiesced_before_authority_restore"] is True
    assert recovery["candidate_database_retained_for_recovery"] is True
    assert runtime_path.read_text(encoding="utf-8") == (
        "PORTAL_DATABASE_URL=postgresql://old-authority\n"
    )


def test_retry_fails_closed_when_same_revision_candidate_is_retained(tmp_path: Path) -> None:
    args = SimpleNamespace(expected_repository_sha="c" * 40)
    active_database = "portal_candidate_oldoldold"
    retained_candidate = "portal_candidate_cccccccccccc"

    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        PORTAL_POSTGRES_CONTAINER="portal-postgresql",
        PORTAL_POSTGRES_USER="portal",
        PORTAL_POSTGRES_ADMIN_DB="portal_admin",
        _current_database_mode=lambda _runtime, _postgres: ("postgresql", active_database),
        _create_postgres_database=lambda _database_name: None,
        _quiesce_existing_portal=lambda: {},
        _write_report=lambda _path, _report: "report-sha256",
        _assert_database_name=lambda _database_name: None,
        _backup_postgres=lambda _database_name, _sha: "backup-sha256",
        _run=lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
        _postgres_database_exists=lambda database_name: database_name == retained_candidate,
        _drop_candidate_database=lambda _database_name: None,
        _restore_previous_portal=lambda *_args: None,
    )
    _cutover_stubs(deploy, tmp_path)

    def original_deploy(_args):
        deploy._current_database_mode({}, {})
        return 0

    deploy.deploy = original_deploy
    module.install(deploy)

    with pytest.raises(RuntimeError, match="reconcile the retained candidate"):
        deploy.deploy(args)


def test_same_revision_database_is_reused_without_copy_on_write(tmp_path: Path) -> None:
    args = SimpleNamespace(expected_repository_sha="b" * 40)
    active_database = "portal_candidate_bbbbbbbbbbbb"
    observed: dict[str, object] = {}

    deploy = SimpleNamespace(
        DeploymentError=RuntimeError,
        PORTAL_POSTGRES_CONTAINER="portal-postgresql",
        PORTAL_POSTGRES_USER="portal",
        PORTAL_POSTGRES_ADMIN_DB="portal_admin",
        _current_database_mode=lambda _runtime, _postgres: ("postgresql", active_database),
        _create_postgres_database=lambda _database_name: None,
        _quiesce_existing_portal=lambda: {},
        _write_report=lambda _path, _report: "report-sha256",
        _assert_database_name=lambda _database_name: None,
        _backup_postgres=lambda _database_name, _sha: "backup-sha256",
        _run=lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
        _postgres_database_exists=lambda _database_name: True,
        _drop_candidate_database=lambda _database_name: None,
        _restore_previous_portal=lambda *_args: None,
    )
    _cutover_stubs(deploy, tmp_path)

    def original_deploy(_args):
        observed["mode"] = deploy._current_database_mode({}, {})
        return 0

    deploy.deploy = original_deploy
    module.install(deploy)

    assert deploy.deploy(args) == 0
    assert observed["mode"] == ("postgresql", active_database)
