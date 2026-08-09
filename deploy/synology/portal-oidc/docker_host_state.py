from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, cast


SYNOLOGY_DOCKER_ROOT = Path("/volume1/docker")
HOST_MOUNT_ROOT = Path("/host-volume")
PORTAL_STATE_MOUNT = Path("/portal-state")
HELPER_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=32m"  # noqa: S108
PREPARE_MARKER = "__PORTAL_DOCKER_HOST_STATE_PREPARED__"
SQLITE_MARKER = "__PORTAL_DOCKER_HOST_SQLITE__"
POSTGRES_MARKER = "__PORTAL_DOCKER_HOST_POSTGRES__"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _portal_relative_path(deploy: Any) -> Path:
    data_dir = Path(deploy.PORTAL_DATA_DIR)
    try:
        relative = data_dir.relative_to(SYNOLOGY_DOCKER_ROOT)
    except ValueError as exc:
        raise deploy.DeploymentError(
            "Portal data directory is outside the canonical Synology Docker root"
        ) from exc
    if relative != Path("freqtrade-portal-oidc/data"):
        raise deploy.DeploymentError("Portal data directory differs from the frozen host path")
    return relative


def _base_helper_args(deploy: Any, *, network: str, mount_root: bool) -> list[str]:
    args = [
        "docker",
        "run",
        "--rm",
        "--network",
        network,
        "--read-only",
        "--tmpfs",
        HELPER_TMPFS,
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "64",
        "--memory",
        "256m",
    ]
    if mount_root:
        args.extend(
            [
                "--cap-add",
                "CHOWN",
                "--cap-add",
                "DAC_OVERRIDE",
                "--cap-add",
                "FOWNER",
                "--user",
                "0:0",
                "--mount",
                f"type=bind,src={SYNOLOGY_DOCKER_ROOT},dst={HOST_MOUNT_ROOT}",
            ]
        )
    else:
        args.extend(
            [
                "--user",
                f"{deploy.PORTAL_UID}:{deploy.PORTAL_GID}",
                "--mount",
                f"type=bind,src={deploy.PORTAL_DATA_DIR},dst={PORTAL_STATE_MOUNT}",
            ]
        )
    return args


def _prepare_script(deploy: Any) -> str:
    relative = _portal_relative_path(deploy)
    mounted = HOST_MOUNT_ROOT / relative
    project_dir = mounted.parent
    backup_dirs = [
        mounted,
        mounted / "legacy-backups",
        mounted / "postgres-backups",
    ]
    lines = [
        "set -eu",
        f"project={str(project_dir)!r}",
        'if [ -L "$project" ]; then exit 21; fi',
        'mkdir -p "$project"',
        'if [ ! -d "$project" ] || [ -L "$project" ]; then exit 22; fi',
    ]
    for index, path in enumerate(backup_dirs, start=1):
        variable = f"path{index}"
        unsafe_exit = 30 + index
        invalid_exit = 40 + index
        lines.extend(
            [
                f"{variable}={str(path)!r}",
                f'if [ -L "${variable}" ]; then exit {unsafe_exit}; fi',
                f'mkdir -p "${variable}"',
                (
                    f'if [ ! -d "${variable}" ] || [ -L "${variable}" ]; '
                    f"then exit {invalid_exit}; fi"
                ),
                f'chown {deploy.PORTAL_UID}:{deploy.PORTAL_GID} "${variable}"',
                f'chmod 700 "${variable}"',
                (
                    f'test "$(stat -c %u:%g:%a "${variable}")" = '
                    f'"{deploy.PORTAL_UID}:{deploy.PORTAL_GID}:700"'
                ),
            ]
        )
    lines.append(f"printf '%s\\n' {PREPARE_MARKER!r}")
    return "\n".join(lines)


def _prepare_docker_host_state(deploy: Any) -> None:
    Path(deploy.PORTAL_STATE_DIR).mkdir(parents=True, exist_ok=True)
    command = [
        *_base_helper_args(deploy, network="none", mount_root=True),
        "--entrypoint",
        "/bin/sh",
        deploy.PORTAL_POSTGRES_IMAGE,
        "-ec",
        _prepare_script(deploy),
    ]
    result = cast(subprocess.CompletedProcess[str], deploy._run(command))
    if PREPARE_MARKER not in result.stdout.splitlines():
        raise deploy.DeploymentError("Docker-host Portal state preparation returned no marker")


def _snapshot_script(filename: str) -> str:
    return f"""
import hashlib
import json
import sqlite3
import stat
from pathlib import Path

root = Path({str(PORTAL_STATE_MOUNT)!r})
source_path = root / "portal.db"
backup_dir = root / "legacy-backups"
destination = backup_dir / {filename!r}

if source_path.is_symlink() or not source_path.is_file():
    raise SystemExit("legacy Portal SQLite database is missing or unsafe")
backup_stat = backup_dir.lstat()
if not stat.S_ISDIR(backup_stat.st_mode) or stat.S_ISLNK(backup_stat.st_mode):
    raise SystemExit("legacy backup directory is unsafe")
if destination.exists() or destination.is_symlink():
    raise SystemExit("legacy snapshot destination already exists")

source_uri = f"file:{{source_path}}?mode=ro"
with sqlite3.connect(source_uri, uri=True) as source, sqlite3.connect(destination) as target:
    source.backup(target)
    check = target.execute("PRAGMA integrity_check").fetchone()
    if check is None or check[0] != "ok":
        raise SystemExit("legacy Portal SQLite snapshot failed integrity_check")

destination.chmod(0o600)
digest = hashlib.sha256()
with destination.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(
    {SQLITE_MARKER!r}
    + json.dumps({{"filename": destination.name, "sha256": digest.hexdigest()}}, sort_keys=True)
)
""".strip()


def _snapshot_legacy_sqlite(
    deploy: Any,
    control_image: str,
    implementation_sha: str,
) -> tuple[Path, str]:
    if not control_image:
        raise deploy.DeploymentError(
            "exact control-plane image is unavailable for Docker-host SQLite snapshot"
        )
    filename = f"portal-pre-postgresql-{implementation_sha[:12]}-{int(time.time())}.db"
    command = [
        *_base_helper_args(deploy, network="none", mount_root=False),
        "--entrypoint",
        "python",
        control_image,
        "-c",
        _snapshot_script(filename),
    ]
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(command, sensitive=True),
    )
    payload_text = next(
        (
            line.removeprefix(SQLITE_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(SQLITE_MARKER)
        ),
        None,
    )
    if payload_text is None:
        raise deploy.DeploymentError("Docker-host SQLite snapshot returned no marker")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise deploy.DeploymentError("Docker-host SQLite snapshot returned invalid JSON") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("filename") != filename
        or not isinstance(payload.get("sha256"), str)
        or SHA256_PATTERN.fullmatch(payload["sha256"]) is None
    ):
        raise deploy.DeploymentError("Docker-host SQLite snapshot returned invalid metadata")
    return Path(deploy.PORTAL_LEGACY_BACKUP_DIR) / filename, payload["sha256"]


def _postgres_backup_script() -> str:
    backup_dir = PORTAL_STATE_MOUNT / "postgres-backups"
    return "\n".join(
        [
            "set -eu",
            f"backup_dir={str(backup_dir)!r}",
            'if [ -L "$backup_dir" ] || [ ! -d "$backup_dir" ]; then exit 51; fi',
            'case "$BACKUP_NAME" in (*[!A-Za-z0-9._-]*|"") exit 52 ;; esac',
            'case "$TARGET_DATABASE" in (*[!A-Za-z0-9_]*|"") exit 53 ;; esac',
            'destination="$backup_dir/$BACKUP_NAME"',
            'if [ -e "$destination" ] || [ -L "$destination" ]; then exit 54; fi',
            "umask 077",
            'export PGPASSWORD="$POSTGRES_PASSWORD"',
            (
                'pg_dump --host="$PORTAL_POSTGRES_ALIAS" --port=5432 '
                '--username="$POSTGRES_USER" --dbname="$TARGET_DATABASE" '
                '--format=custom --file="$destination"'
            ),
            "unset PGPASSWORD",
            'chmod 600 "$destination"',
            'digest="$(sha256sum "$destination" | awk \'{print $1}\')"',
            (f'printf \'%s%s|%s\\n\' {POSTGRES_MARKER!r} "$BACKUP_NAME" "$digest"'),
        ]
    )


def _backup_postgres(
    deploy: Any,
    database_name: str,
    implementation_sha: str,
) -> str:
    deploy._assert_database_name(database_name)
    filename = f"portal-{implementation_sha[:12]}-{int(time.time())}.backup"
    command = [
        *_base_helper_args(deploy, network=deploy.PORTAL_NETWORK, mount_root=False),
        "--env-file",
        str(deploy.PORTAL_POSTGRES_ENV),
        "--env",
        f"TARGET_DATABASE={database_name}",
        "--env",
        f"BACKUP_NAME={filename}",
        "--env",
        f"PORTAL_POSTGRES_ALIAS={deploy.PORTAL_POSTGRES_ALIAS}",
        "--entrypoint",
        "/bin/sh",
        deploy.PORTAL_POSTGRES_IMAGE,
        "-ec",
        _postgres_backup_script(),
    ]
    result = cast(
        subprocess.CompletedProcess[str],
        deploy._run(command, sensitive=True),
    )
    marker = next(
        (
            line.removeprefix(POSTGRES_MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(POSTGRES_MARKER)
        ),
        None,
    )
    if marker is None:
        raise deploy.DeploymentError("Docker-host PostgreSQL backup returned no marker")
    returned_name, separator, digest = marker.partition("|")
    if separator != "|" or returned_name != filename or SHA256_PATTERN.fullmatch(digest) is None:
        raise deploy.DeploymentError("Docker-host PostgreSQL backup returned invalid metadata")
    return digest


def install(deploy: Any) -> None:
    original_build_images = deploy._build_images
    state: dict[str, str] = {}

    def build_images(repo: Path, implementation_sha: str) -> tuple[str, str, str, str]:
        result = cast(
            tuple[str, str, str, str],
            original_build_images(repo, implementation_sha),
        )
        control_image = result[0]
        if not control_image:
            raise deploy.DeploymentError("exact control-plane image build returned no tag")
        state["control_image"] = control_image
        return result

    def prepare_host_state() -> None:
        _prepare_docker_host_state(deploy)

    def snapshot_legacy_sqlite(implementation_sha: str) -> tuple[Path, str]:
        return _snapshot_legacy_sqlite(
            deploy,
            state.get("control_image", ""),
            implementation_sha,
        )

    def backup_postgres(database_name: str, implementation_sha: str) -> str:
        return _backup_postgres(deploy, database_name, implementation_sha)

    deploy._build_images = build_images
    deploy._prepare_host_state = prepare_host_state
    deploy._snapshot_legacy_sqlite = snapshot_legacy_sqlite
    deploy._backup_postgres = backup_postgres
