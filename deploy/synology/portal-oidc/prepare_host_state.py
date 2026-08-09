#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
import subprocess
import sys
from pathlib import Path

from docker_runtime_preflight import PreflightError, check_runtime


AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
SYNOLOGY_DOCKER_ROOT = Path("/volume1/docker")
HOST_MOUNT_ROOT = Path("/host-volume")
PORTAL_DATA_DIR = SYNOLOGY_DOCKER_ROOT / "freqtrade-portal-oidc/data"
PORTAL_UID = 10001
PORTAL_GID = 10001
HELPER_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=16m"  # noqa: S108


class PreparationError(RuntimeError):
    pass


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        lines = [
            line.strip()
            for stream in (result.stdout, result.stderr)
            for line in stream.splitlines()
            if line.strip()
        ]
        detail = " | ".join(lines[-5:]) if lines else "no output"
        raise PreparationError(
            f"command failed ({result.returncode}): {' '.join(command)}: {detail}"
        )
    return result


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _assert_secret_file(path: Path) -> None:
    if not path.is_file() or _mode(path) != 0o600:
        raise PreparationError(f"protected runtime file must have mode 0600: {path}")


def _compose_command(repo: Path) -> list[str]:
    runtime_env = AUTHENTIK_STATE_DIR / "runtime.env"
    _assert_secret_file(runtime_env)
    return [
        "docker",
        "compose",
        "--project-name",
        AUTHENTIK_PROJECT,
        "--env-file",
        str(runtime_env),
        "-f",
        str(repo / "deploy/synology/portal-authentik/compose.yml"),
    ]


def _helper_script() -> str:
    mounted_data_dir = HOST_MOUNT_ROOT / PORTAL_DATA_DIR.relative_to(SYNOLOGY_DOCKER_ROOT)
    return "\n".join(
        [
            "import os",
            "import stat",
            "from pathlib import Path",
            f"path = Path({str(mounted_data_dir)!r})",
            "path.mkdir(parents=True, exist_ok=True)",
            f"os.chown(path, {PORTAL_UID}, {PORTAL_GID})",
            "path.chmod(0o700)",
            "metadata = path.stat()",
            (f"if metadata.st_uid != {PORTAL_UID}: raise SystemExit('portal data uid mismatch')"),
            (f"if metadata.st_gid != {PORTAL_GID}: raise SystemExit('portal data gid mismatch')"),
            "if stat.S_IMODE(metadata.st_mode) != 0o700: "
            "raise SystemExit('portal data mode mismatch')",
        ]
    )


def _helper_run_args(image: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        HELPER_TMPFS,
        "--cap-drop",
        "ALL",
        "--cap-add",
        "CHOWN",
        "--cap-add",
        "DAC_OVERRIDE",
        "--cap-add",
        "FOWNER",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "32",
        "--memory",
        "64m",
        "--user",
        "0:0",
        "--mount",
        f"type=bind,src={SYNOLOGY_DOCKER_ROOT},dst={HOST_MOUNT_ROOT}",
        "--entrypoint",
        "python",
        image,
        "-c",
        _helper_script(),
    ]


def prepare(repo: Path) -> None:
    try:
        check_runtime()
    except PreflightError as exc:
        raise PreparationError(f"Synology Docker runtime preflight failed: {exc}") from exc

    compose = _compose_command(repo)
    server = _run([*compose, "ps", "-q", "server"]).stdout.strip()
    if not server:
        raise PreparationError("Authen­tik server container is unavailable")
    image = _run(["docker", "inspect", "--format", "{{.Config.Image}}", server]).stdout.strip()
    if not image:
        raise PreparationError("Authen­tik server image is unavailable")
    _run(_helper_run_args(image))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    prepare(Path(args.repository).resolve())
    print(f"prepared {PORTAL_DATA_DIR} for uid={PORTAL_UID} gid={PORTAL_GID} mode=0700")
    return 0


if __name__ == "__main__":
    sys.exit(main())
