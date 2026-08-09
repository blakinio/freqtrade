#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys


POSTGRES_IMAGE = (
    "docker.io/library/postgres:16.13-alpine3.23@sha256:"
    "57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777"
)
PROBE_TIMEOUT_SECONDS = 20
DOCKER_QUERY_TIMEOUT_SECONDS = 10


class PreflightError(RuntimeError):
    pass


def _run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise PreflightError("docker runtime command timed out") from exc


def _ensure_probe_image() -> None:
    inspect = _run(
        ["docker", "image", "inspect", POSTGRES_IMAGE],
        timeout=DOCKER_QUERY_TIMEOUT_SECONDS,
    )
    if inspect.returncode == 0:
        return
    pull = _run(["docker", "pull", POSTGRES_IMAGE], timeout=120)
    if pull.returncode != 0:
        raise PreflightError("pinned Docker runtime probe image is unavailable")


def _cleanup_probe(name: str) -> None:
    try:
        _run(["docker", "rm", "-f", name], timeout=DOCKER_QUERY_TIMEOUT_SECONDS)
    except PreflightError:
        pass


def check_runtime() -> dict[str, object]:
    info = _run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        timeout=DOCKER_QUERY_TIMEOUT_SECONDS,
    )
    if info.returncode != 0 or not info.stdout.strip():
        raise PreflightError("Docker daemon is unavailable")

    _ensure_probe_image()
    name = f"portal-oidc-runtime-preflight-{os.getpid()}"
    _cleanup_probe(name)
    try:
        probe = _run(
            [
                "docker",
                "run",
                "--rm",
                "--name",
                name,
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--entrypoint",
                "/bin/true",
                POSTGRES_IMAGE,
            ],
            timeout=PROBE_TIMEOUT_SECONDS,
        )
        if probe.returncode != 0:
            raise PreflightError("Docker daemon cannot start a disposable container")
    except PreflightError as exc:
        _cleanup_probe(name)
        if "timed out" in str(exc):
            raise PreflightError(
                "Docker daemon cannot start a disposable container within the bounded timeout; "
                "recover Synology Container Manager before deployment"
            ) from exc
        raise
    finally:
        _cleanup_probe(name)

    return {
        "status": "ready",
        "disposable_container_start": True,
        "network_mode": "none",
        "secret_values_recorded": False,
        "live_capital_authorized": False,
    }


def main() -> int:
    try:
        result = check_runtime()
    except PreflightError as exc:
        print(f"Docker runtime preflight failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
