from __future__ import annotations

from typing import Any


def install(deploy: Any) -> None:  # noqa: C901 - deployment shim centralizes one cutover contract
    """Install rollback-safe PostgreSQL candidate cloning and authority cutover."""

    original_deploy = deploy.deploy
    original_current_database_mode = deploy._current_database_mode
    original_create_postgres_database = deploy._create_postgres_database
    original_quiesce_existing_portal = deploy._quiesce_existing_portal
    original_activate_candidate_runtime = deploy._activate_candidate_runtime
    original_promote_control = deploy._promote_control
    original_restore_previous_portal = deploy._restore_previous_portal
    original_drop_candidate_database = deploy._drop_candidate_database
    original_write_report = deploy._write_report

    state: dict[str, Any] = {
        "implementation_sha": None,
        "source_database": None,
        "candidate_database": None,
        "backup_sha256": None,
        "previous_runtime": {},
        "authority_switched": False,
        "authority_was_journaled": False,
        "authority_restore_failed": False,
        "candidate_quiesced_before_authority_restore": False,
        "candidate_retained_for_recovery": False,
    }

    def guarded_deploy(args: Any) -> int:
        state.update(
            {
                "implementation_sha": args.expected_repository_sha,
                "source_database": None,
                "candidate_database": None,
                "backup_sha256": None,
                "previous_runtime": {},
                "authority_switched": False,
                "authority_was_journaled": False,
                "authority_restore_failed": False,
                "candidate_quiesced_before_authority_restore": False,
                "candidate_retained_for_recovery": False,
            }
        )
        return int(original_deploy(args))

    def current_database_mode(
        runtime_env: dict[str, str],
        postgres_env: dict[str, str],
    ) -> tuple[str, str | None]:
        state["previous_runtime"] = dict(runtime_env)
        mode, database_name = original_current_database_mode(runtime_env, postgres_env)
        implementation_sha = state["implementation_sha"]
        if mode != "postgresql" or database_name is None or implementation_sha is None:
            return mode, database_name

        candidate_database = f"portal_candidate_{implementation_sha[:12]}"
        if database_name == candidate_database:
            return mode, database_name

        # A same-revision candidate while another database remains authoritative can be a
        # retained post-exposure recovery database from an earlier failed cutover. Never
        # delete or overwrite it automatically: explicit reconciliation must decide whether
        # it contains writes that need to be recovered before another attempt.
        if deploy._postgres_database_exists(candidate_database):
            raise deploy.DeploymentError(
                "PostgreSQL copy-on-write candidate already exists for this revision; "
                "reconcile the retained candidate before retrying deployment"
            )

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
            original_restore_previous_portal(previous, None, None)
            raise deploy.DeploymentError(
                "PostgreSQL copy-on-write candidate contract is incomplete"
            )

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
            original_drop_candidate_database(candidate_database)
            original_restore_previous_portal(previous, None, None)
            raise
        return previous

    def activate_candidate_runtime() -> None:
        if state["authority_switched"]:
            return
        original_activate_candidate_runtime()
        state["authority_switched"] = True
        state["authority_was_journaled"] = True

    def promote_control(candidate: str) -> str | None:
        # The candidate container has already started from runtime.candidate.env and is not
        # externally reachable. Journal the candidate database identity durably before the
        # first promotion step can expose a process that may accept writes.
        activate_candidate_runtime()
        return original_promote_control(candidate)

    def quiesce_candidate_before_authority_restore() -> None:
        if not state["authority_switched"]:
            return
        # The public web process is stopped first so no new externally-originated mutation can
        # reach the candidate control plane while rollback is changing durable database
        # authority. A host/process crash after either stop remains recovery-safe because
        # runtime.env still points at the candidate until both candidate processes are quiet.
        for container in (deploy.PORTAL_CONTAINER, deploy.CONTROL_CONTAINER):
            if deploy._container_running(container):
                deploy._run(["docker", "stop", container])
        state["candidate_quiesced_before_authority_restore"] = True

    def restore_runtime_authority() -> None:
        if not state["authority_switched"]:
            return
        previous_runtime = state["previous_runtime"]
        if not isinstance(previous_runtime, dict):
            raise deploy.DeploymentError("previous Portal runtime authority snapshot is invalid")
        try:
            if previous_runtime:
                deploy._write_env_atomic(deploy.PORTAL_RUNTIME_ENV, previous_runtime)
            elif deploy.PORTAL_RUNTIME_ENV.exists():
                deploy.PORTAL_RUNTIME_ENV.unlink()
        except Exception:
            state["authority_restore_failed"] = True
            raise
        state["authority_switched"] = False
        state["authority_restore_failed"] = False

    def restore_previous_portal(
        previous: dict[str, bool],
        control_backup: str | None,
        web_backup: str | None,
    ) -> None:
        # Keep candidate authority durable until the candidate processes are quiesced. After
        # that point restoring runtime.env is crash-safe: no process can continue writing the
        # candidate database while a future deploy sees the source database as authoritative.
        quiesce_candidate_before_authority_restore()
        restore_runtime_authority()
        original_restore_previous_portal(previous, control_backup, web_backup)

    def drop_candidate_database(database_name: str) -> None:
        # Once candidate authority was journaled, the candidate may have accepted writes. Even
        # after a clean rollback to the source database, deleting that candidate would make
        # those writes unrecoverable. Retain it and make a same-revision retry fail closed in
        # current_database_mode until an operator explicitly reconciles the two databases.
        if state["authority_was_journaled"]:
            state["candidate_retained_for_recovery"] = True
            return
        original_drop_candidate_database(database_name)

    def write_report(path: Any, report: dict[str, Any]) -> str:
        source_database = state["source_database"]
        candidate_database = state["candidate_database"]
        if source_database is not None:
            if candidate_database is None:
                raise deploy.DeploymentError(
                    "PostgreSQL copy-on-write recovery report is missing "
                    "candidate database identity"
                )
            recovery = report.setdefault("database_recovery", {})
            recovery.update(
                {
                    "pre_migration_backup_sha256": state["backup_sha256"],
                    "source_database": source_database,
                    "candidate_database": candidate_database,
                    "source_database_retained_for_rollback": True,
                    "authority_journaled_before_promotion": state["authority_was_journaled"],
                    "candidate_quiesced_before_authority_restore": state[
                        "candidate_quiesced_before_authority_restore"
                    ],
                    "candidate_database_retained_for_recovery": state[
                        "candidate_retained_for_recovery"
                    ],
                    "restore_authorized": False,
                }
            )
            database = report.get("database")
            if isinstance(database, dict):
                database.update(
                    {
                        "state_transition": "postgresql_copy_on_write",
                        "pre_migration_backup_sha256": state["backup_sha256"],
                        "source_database": source_database,
                        "candidate_database": candidate_database,
                        "source_database_retained_for_rollback": True,
                        "authority_journaled_before_promotion": state["authority_was_journaled"],
                        "candidate_quiesced_before_authority_restore": state[
                            "candidate_quiesced_before_authority_restore"
                        ],
                        "candidate_database_retained_for_recovery": state[
                            "candidate_retained_for_recovery"
                        ],
                    }
                )
        return str(original_write_report(path, report))

    deploy.deploy = guarded_deploy
    deploy._current_database_mode = current_database_mode
    deploy._create_postgres_database = create_postgres_database
    deploy._quiesce_existing_portal = quiesce_existing_portal
    deploy._activate_candidate_runtime = activate_candidate_runtime
    deploy._promote_control = promote_control
    deploy._restore_previous_portal = restore_previous_portal
    deploy._drop_candidate_database = drop_candidate_database
    deploy._write_report = write_report
