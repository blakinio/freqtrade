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
DOCKER_QUERY_TIMEOUT_SECONDS = 10
PROBE_CREATE_TIMEOUT_SECONDS = 60
PROBE_START_TIMEOUT_SECONDS = 60
PROBE_WAIT_TIMEOUT_SECONDS = 60
PROBE_REMOVE_TIMEOUT_SECONDS = 30


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


def _cleanup_probe(name: str, *, required: bool = False) -> None:
    try:
        result = _run(
            ["docker", "rm", "-f", name], timeout=PROBE_REMOVE_TIMEOUT_SECONDS
        )
    except PreflightError as exc:
        if required:
            raise PreflightError(
                "Docker daemon cannot remove the disposable container within the bounded timeout"
            ) from exc
        return
    if required and result.returncode != 0:
        raise PreflightError("Docker daemon cannot remove the disposable container")


def _run_probe_stage(
    stage: str, command: list[str], *, timeout: int
) -> subprocess.CompletedProcess[str]:
    try:
        result = _run(command, timeout=timeout)
    except PreflightError as exc:
        raise PreflightError(
            f"Docker daemon cannot {stage} a disposable container within the bounded timeout; "
            "recover Synology Container Manager before deployment"
        ) from exc
    if result.returncode != 0:
        raise PreflightError(f"Docker daemon cannot {stage} a disposable container")
    return result


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
    created = False
    probe_error: PreflightError | None = None
    try:
        _run_probe_stage(
            "create",
            [
                "docker",
                "create",
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
            timeout=PROBE_CREATE_TIMEOUT_SECONDS,
        )
        created = True
        _run_probe_stage(
            "start",
            ["docker", "start", name],
            timeout=PROBE_START_TIMEOUT_SECONDS,
        )
        wait = _run_probe_stage(
            "wait for",
            ["docker", "wait", name],
            timeout=PROBE_WAIT_TIMEOUT_SECONDS,
        )
        if wait.stdout.strip() != "0":
            raise PreflightError("disposable Docker runtime probe exited non-zero")
    except PreflightError as exc:
        probe_error = exc
    finally:
        try:
            _cleanup_probe(name, required=created)
        except PreflightError as cleanup_exc:
            if probe_error is None:
                probe_error = cleanup_exc
    if probe_error is not None:
        raise probe_error

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
