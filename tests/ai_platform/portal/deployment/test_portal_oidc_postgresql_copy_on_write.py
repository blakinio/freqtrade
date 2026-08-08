from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "postgresql_copy_on_write.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_postgresql_copy_on_write", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_existing_postgresql_is_cloned_after_quiesce_before_migration() -> None:
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
    deploy._quiesce_existing_portal = lambda: events.append("quiesce") or {
        "web_exists": True,
        "web_running": True,
        "control_exists": True,
        "control_running": True,
    }
    deploy._backup_postgres = lambda database_name, sha: events.append(
        ("backup", database_name, sha)
    ) or "backup-sha256"
    deploy._postgres_database_exists = lambda database_name: database_name in databases
    deploy._drop_candidate_database = lambda database_name: (
        events.append(("drop", database_name)),
        databases.discard(database_name),
    )
    deploy._restore_previous_portal = lambda previous, control_backup, web_backup: events.append(
        ("restore", previous, control_backup, web_backup)
    )

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
        if isinstance(event, tuple)
        and event[0] == "run"
        and "createdb" in event[1]
    )
    assert createdb_event[1][-2:] == (
        "portal_candidate_oldoldold",
        "portal_candidate_aaaaaaaaaaaa",
    )
    assert events.index("quiesce") < events.index(("backup", "portal_candidate_oldoldold", "a" * 40))
    assert captured_report["database"] == {
        "state_transition": "postgresql_copy_on_write",
        "pre_migration_backup_sha256": "backup-sha256",
        "source_database_retained_for_rollback": True,
    }
    assert captured_report["database_recovery"] == {
        "pre_migration_backup_sha256": "backup-sha256",
        "source_database_retained_for_rollback": True,
        "restore_authorized": False,
    }


def test_same_revision_database_is_reused_without_copy_on_write() -> None:
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

    def original_deploy(_args):
        observed["mode"] = deploy._current_database_mode({}, {})
        return 0

    deploy.deploy = original_deploy
    module.install(deploy)

    assert deploy.deploy(args) == 0
    assert observed["mode"] == ("postgresql", active_database)
