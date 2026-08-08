from __future__ import annotations

from typing import Any


def install(deploy: Any) -> None:
    """Install rollback-safe PostgreSQL candidate cloning on the protected deploy entrypoint."""

    original_deploy = deploy.deploy
    original_current_database_mode = deploy._current_database_mode
    original_create_postgres_database = deploy._create_postgres_database
    original_quiesce_existing_portal = deploy._quiesce_existing_portal
    original_write_report = deploy._write_report

    state: dict[str, Any] = {
        "implementation_sha": None,
        "source_database": None,
        "candidate_database": None,
        "backup_sha256": None,
    }

    def guarded_deploy(args: Any) -> int:
        state.update(
            {
                "implementation_sha": args.expected_repository_sha,
                "source_database": None,
                "candidate_database": None,
                "backup_sha256": None,
            }
        )
        return int(original_deploy(args))

    def current_database_mode(
        runtime_env: dict[str, str],
        postgres_env: dict[str, str],
    ) -> tuple[str, str | None]:
        mode, database_name = original_current_database_mode(runtime_env, postgres_env)
        implementation_sha = state["implementation_sha"]
        if mode != "postgresql" or database_name is None or implementation_sha is None:
            return mode, database_name

        candidate_database = f"portal_candidate_{implementation_sha[:12]}"
        if database_name == candidate_database:
            return mode, database_name

        state["source_database"] = database_name
        return "fresh", None

    def create_postgres_database(database_name: str) -> None:
        if state["source_database"] is None:
            original_create_postgres_database(database_name)
            return
        deploy._assert_database_name(database_name)
        state["candidate_database"] = database_name

    def quiesce_existing_portal() -> dict[str, bool]:
        previous = original_quiesce_existing_portal()
        source_database = state["source_database"]
        candidate_database = state["candidate_database"]
        implementation_sha = state["implementation_sha"]
        if source_database is None:
            return previous
        if candidate_database is None or implementation_sha is None:
            deploy._restore_previous_portal(previous, None, None)
            raise deploy.DeploymentError("PostgreSQL copy-on-write candidate contract is incomplete")

        try:
            state["backup_sha256"] = deploy._backup_postgres(
                source_database,
                implementation_sha,
            )
            deploy._run(
                [
                    "docker",
                    "exec",
                    deploy.PORTAL_POSTGRES_CONTAINER,
                    "psql",
                    "-U",
                    deploy.PORTAL_POSTGRES_USER,
                    "-d",
                    deploy.PORTAL_POSTGRES_ADMIN_DB,
                    "-c",
                    (
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        f"WHERE datname = '{source_database}' AND pid <> pg_backend_pid();"
                    ),
                ],
                sensitive=True,
            )
            deploy._run(
                [
                    "docker",
                    "exec",
                    deploy.PORTAL_POSTGRES_CONTAINER,
                    "createdb",
                    "-U",
                    deploy.PORTAL_POSTGRES_USER,
                    "-T",
                    source_database,
                    candidate_database,
                ],
                sensitive=True,
            )
            if not deploy._postgres_database_exists(candidate_database):
                raise deploy.DeploymentError("PostgreSQL copy-on-write candidate was not created")
        except Exception:
            deploy._drop_candidate_database(candidate_database)
            deploy._restore_previous_portal(previous, None, None)
            raise
        return previous

    def write_report(path: Any, report: dict[str, Any]) -> str:
        source_database = state["source_database"]
        if source_database is not None:
            recovery = report.setdefault("database_recovery", {})
            recovery.update(
                {
                    "pre_migration_backup_sha256": state["backup_sha256"],
                    "source_database_retained_for_rollback": True,
                    "restore_authorized": False,
                }
            )
            database = report.get("database")
            if isinstance(database, dict):
                database.update(
                    {
                        "state_transition": "postgresql_copy_on_write",
                        "pre_migration_backup_sha256": state["backup_sha256"],
                        "source_database_retained_for_rollback": True,
                    }
                )
        return str(original_write_report(path, report))

    deploy.deploy = guarded_deploy
    deploy._current_database_mode = current_database_mode
    deploy._create_postgres_database = create_postgres_database
    deploy._quiesce_existing_portal = quiesce_existing_portal
    deploy._write_report = write_report
