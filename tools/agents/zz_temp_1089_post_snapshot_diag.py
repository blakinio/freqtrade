from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

CONTROL_IMAGE = "sha256:0bd79c3bb178dba4073db9c1cb47cb22e7bc11eb32d133a28a97fd44658701fc"
DEPLOY_PATH = Path("deploy/synology/portal-oidc/deploy.py").resolve()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("diagnostic module spec unavailable")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def classify(text: str) -> str:
    lowered = text.lower()
    checks = (
        ("module", ("modulenotfounderror", "importerror", "no module named")),
        ("postgres_auth", ("password authentication failed", "authentication failed")),
        ("postgres_connect", ("connection refused", "could not translate host name", "operationalerror")),
        ("postgres_permission", ("permission denied", "insufficientprivilege")),
        ("target_nonempty", ("non-idempotent", "nonempty_table_counts", "contains portal business rows")),
        ("integrity", ("integrity", "quarantine")),
        ("sqlite_source", ("source-sqlite", "legacy sqlite")),
        ("schema", ("schemamigrationerror", "migration")),
        ("readonly", ("read-only", "readonly", "permissionerror")),
    )
    for category, needles in checks:
        if any(needle in lowered for needle in needles):
            return category
    return "unknown"


def main() -> int:
    deploy = load_module("portal_oidc_diagnostic_deploy", DEPLOY_PATH)
    original_subprocess_run = deploy.subprocess.run

    def timed_subprocess_run(*args, **kwargs):
        kwargs.setdefault("timeout", 60)
        return original_subprocess_run(*args, **kwargs)

    deploy.subprocess.run = timed_subprocess_run
    try:
        if deploy._docker_image_id(CONTROL_IMAGE) != CONTROL_IMAGE:
            raise RuntimeError("diagnostic exact control-plane image is unavailable")
        if not deploy._container_running(deploy.PORTAL_POSTGRES_CONTAINER):
            raise RuntimeError("diagnostic PostgreSQL container is not running")
        deploy._assert_secret_file(deploy.PORTAL_POSTGRES_ENV)
        postgres_env = deploy._read_env(deploy.PORTAL_POSTGRES_ENV)

        suffix = f"{int(time.time())}_{os.getpid()}"
        database_name = f"portal_diag_1089_{suffix}"
        deploy._assert_database_name(database_name)

        candidate_env = Path(deploy.PORTAL_RUNTIME_CANDIDATE_ENV)
        previous_candidate = candidate_env.read_bytes() if candidate_env.exists() else None
        previous_mode = (candidate_env.stat().st_mode & 0o777) if candidate_env.exists() else None

        stage = "setup"
        original_run = deploy._run

        def diagnostic_run(command, *, cwd=None, sensitive=False, check=True):
            nonlocal stage
            if not sensitive:
                try:
                    return original_run(command, cwd=cwd, sensitive=False, check=check)
                except subprocess.TimeoutExpired as exc:
                    print(f"DIAG_FAILURE stage={stage} category=timeout executable={Path(command[0]).name}")
                    raise deploy.DeploymentError(f"diagnostic stage timed out: {stage}") from exc
            try:
                result = original_run(command, cwd=cwd, sensitive=False, check=False)
            except subprocess.TimeoutExpired as exc:
                print(f"DIAG_FAILURE stage={stage} category=timeout executable={Path(command[0]).name}")
                raise deploy.DeploymentError(f"diagnostic stage timed out: {stage}") from exc
            if check and result.returncode != 0:
                combined = (result.stdout or "") + "\n" + (result.stderr or "")
                digest = hashlib.sha256(combined.encode("utf-8", errors="replace")).hexdigest()
                category = classify(combined)
                module = "none"
                if "-m" in command:
                    index = command.index("-m")
                    if index + 1 < len(command):
                        module = str(command[index + 1])
                print(
                    f"DIAG_FAILURE stage={stage} executable={Path(command[0]).name} "
                    f"module={module} rc={result.returncode} category={category} "
                    f"output_sha256={digest}"
                )
                raise deploy.DeploymentError(
                    f"diagnostic stage failed: {stage}; category={category}; rc={result.returncode}"
                )
            return result

        deploy._run = diagnostic_run
        created = False
        try:
            stage = "create_database"
            print(f"DIAG_ENTER stage={stage}")
            deploy._create_postgres_database(database_name)
            created = True
            database_url = deploy._postgres_database_url(database_name, postgres_env)
            deploy._write_env_atomic(candidate_env, {"PORTAL_DATABASE_URL": database_url})

            stage = "schema_migrate"
            print(f"DIAG_ENTER stage={stage}")
            migration = deploy._run_schema_command(CONTROL_IMAGE, "migrate")
            print(f"DIAG_PASS stage=schema_migrate status={migration.get('status')}")

            stage = "find_snapshot"
            print(f"DIAG_ENTER stage={stage}")
            helper = original_run(
                [
                    "docker", "run", "--rm", "--network", "none", "--read-only",
                    "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                    "--user", f"{deploy.PORTAL_UID}:{deploy.PORTAL_GID}",
                    "--mount", f"type=bind,src={deploy.PORTAL_LEGACY_BACKUP_DIR},dst=/legacy,readonly",
                    "--entrypoint", "/bin/sh", deploy.PORTAL_POSTGRES_IMAGE,
                    "-ec", "find /legacy -maxdepth 1 -type f -name 'portal-pre-postgresql-*.db' -printf '%T@ %f\\n' | sort -nr | head -n 1",
                ]
            )
            line = helper.stdout.strip()
            if not line or " " not in line:
                raise deploy.DeploymentError("diagnostic found no legacy snapshot")
            snapshot_name = line.split(" ", 1)[1].strip()
            if Path(snapshot_name).name != snapshot_name:
                raise deploy.DeploymentError("diagnostic snapshot name is unsafe")
            snapshot = Path(deploy.PORTAL_LEGACY_BACKUP_DIR) / snapshot_name
            print(f"DIAG_PASS stage=find_snapshot name={snapshot_name}")

            stage = "state_transfer"
            print(f"DIAG_ENTER stage={stage}")
            transfer = deploy._transfer_legacy_state(CONTROL_IMAGE, snapshot)
            print(
                f"DIAG_PASS stage=state_transfer status={transfer.get('status')} "
                f"rows_copied={transfer.get('rows_copied')}"
            )

            stage = "schema_check"
            print(f"DIAG_ENTER stage={stage}")
            check_report = deploy._run_schema_command(CONTROL_IMAGE, "check")
            print(f"DIAG_PASS stage=schema_check status={check_report.get('status')}")
            return 0
        finally:
            deploy._run = original_run
            if created:
                try:
                    deploy._drop_candidate_database(database_name)
                    print("DIAG_PASS stage=cleanup_database")
                except Exception as exc:
                    print(f"DIAG_FAILURE stage=cleanup_database type={type(exc).__name__}")
            if previous_candidate is None:
                candidate_env.unlink(missing_ok=True)
            else:
                candidate_env.write_bytes(previous_candidate)
                candidate_env.chmod(previous_mode or 0o600)
    finally:
        deploy.subprocess.run = original_subprocess_run


if __name__ == "__main__":
    raise SystemExit(main())
