from __future__ import annotations

import re
import secrets
import subprocess
from pathlib import Path
from typing import Any, cast


CREATE_TIMEOUT_SECONDS = 240
START_TIMEOUT_SECONDS = 240
WAIT_TIMEOUT_SECONDS_BY_WORKLOAD = {
    "schema-migrate": 600,
    "state-transfer": 180,
    "schema-check": 180,
    "schema-schema": 300,
}
LOG_TIMEOUT_SECONDS = 90
REMOVE_TIMEOUT_SECONDS = 120
QUERY_TIMEOUT_SECONDS = 30
OWNERSHIP_VERIFY_ATTEMPTS = 3
OWNER_LABEL_KEY = "com.freqtrade.portal.bounded-owner"
OWNER_LABEL_FORMAT = f'{{{{ index .Config.Labels "{OWNER_LABEL_KEY}" }}}}'
_TARGET_MODULES = {
    "ai_platform.portal.database.cli",
    "ai_platform.portal.database.transfer",
}


def _target_module(command: list[str]) -> str | None:
    if command[:3] != ["docker", "run", "--rm"]:
        return None
    for index, value in enumerate(command[:-1]):
        if value == "-m" and command[index + 1] in _TARGET_MODULES:
            return command[index + 1]
    return None


def _workload_label(command: list[str], module: str) -> str:
    if module == "ai_platform.portal.database.transfer":
        return "state-transfer"
    module_index = command.index(module)
    operation = command[module_index + 1] if module_index + 1 < len(command) else "schema"
    if operation not in {"migrate", "check"}:
        operation = "schema"
    return f"schema-{operation}"


def _wait_timeout(label: str) -> int:
    try:
        return WAIT_TIMEOUT_SECONDS_BY_WORKLOAD[label]
    except KeyError as exc:
        raise RuntimeError(f"bounded Docker workload has no wait calibration: {label}") from exc


def _container_identity(label: str) -> tuple[str, str]:
    safe_label = re.sub(r"[^a-z0-9-]+", "-", label.lower()).strip("-") or "schema"
    token = secrets.token_hex(6)
    name = f"portal-oidc-bounded-{safe_label}-{token}"
    owner = f"portal-oidc-bounded:{safe_label}:{token}"
    return name, owner


def _run_bounded(
    command: list[str],
    *,
    cwd: Path | None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def _stage(
    deploy: Any,
    *,
    label: str,
    stage: str,
    command: list[str],
    cwd: Path | None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    try:
        result = _run_bounded(command, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise deploy.DeploymentError(
            f"sensitive Docker workload timed out: {label}:{stage}"
        ) from exc
    if result.returncode != 0:
        raise deploy.DeploymentError(f"sensitive Docker workload failed: {label}:{stage}")
    return result


def _verify_absent(deploy: Any, name: str, *, cwd: Path | None) -> None:
    exact_name_filter = f"name=^/{name}$"
    try:
        inspect = _run_bounded(
            ["docker", "inspect", name],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
        listed = _run_bounded(
            ["docker", "ps", "-aq", "--no-trunc", "--filter", exact_name_filter],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
        version = _run_bounded(
            ["docker", "version"],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise deploy.DeploymentError(
            "task-owned Docker workload cleanup could not be verified"
        ) from exc
    if (
        version.returncode != 0
        or listed.returncode != 0
        or bool(listed.stdout.strip())
        or inspect.returncode == 0
    ):
        raise deploy.DeploymentError("task-owned Docker workload cleanup failed")


def _cleanup_owned(deploy: Any, name: str, *, cwd: Path | None) -> None:
    try:
        _run_bounded(
            ["docker", "rm", "-f", name],
            cwd=cwd,
            timeout=REMOVE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        pass
    _verify_absent(deploy, name, cwd=cwd)


def _cleanup_ambiguous_create(
    deploy: Any,
    name: str,
    owner: str,
    *,
    cwd: Path | None,
) -> None:
    last_verification_error: Exception | None = None
    for _attempt in range(OWNERSHIP_VERIFY_ATTEMPTS):
        try:
            ownership = _run_bounded(
                ["docker", "inspect", "--format", OWNER_LABEL_FORMAT, name],
                cwd=cwd,
                timeout=QUERY_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            last_verification_error = exc
            continue

        if ownership.returncode == 0:
            if ownership.stdout.strip() != owner:
                raise deploy.DeploymentError(
                    "ambiguous Docker create produced a container not owned by this task"
                )
            _cleanup_owned(deploy, name, cwd=cwd)
            return

        try:
            _verify_absent(deploy, name, cwd=cwd)
            return
        except deploy.DeploymentError as exc:
            last_verification_error = exc

    raise deploy.DeploymentError(
        "ambiguous Docker create ownership could not be verified after bounded retries"
    ) from last_verification_error


def _run_sensitive_workload(
    deploy: Any,
    command: list[str],
    *,
    cwd: Path | None,
) -> subprocess.CompletedProcess[str]:
    module = _target_module(command)
    if module is None:
        raise deploy.DeploymentError("unsupported bounded Docker workload contract")
    label = _workload_label(command, module)
    name, owner = _container_identity(label)
    create_command = [
        "docker",
        "create",
        "--name",
        name,
        "--label",
        f"{OWNER_LABEL_KEY}={owner}",
        *command[3:],
    ]

    # A pre-existing collision is not task-owned and must fail closed without
    # mutation. The create itself carries an ownership label so an ambiguous
    # timeout/non-zero result can be cleaned only if the daemon proves that the
    # resulting exact-name container belongs to this invocation.
    _verify_absent(deploy, name, cwd=cwd)

    primary_error: Exception | None = None
    logs: subprocess.CompletedProcess[str] | None = None
    process_exit: str | None = None
    create_succeeded = False

    try:
        _stage(
            deploy,
            label=label,
            stage="create",
            command=create_command,
            cwd=cwd,
            timeout=CREATE_TIMEOUT_SECONDS,
        )
        create_succeeded = True
        _stage(
            deploy,
            label=label,
            stage="start",
            command=["docker", "start", name],
            cwd=cwd,
            timeout=START_TIMEOUT_SECONDS,
        )
        wait = _stage(
            deploy,
            label=label,
            stage="wait",
            command=["docker", "wait", name],
            cwd=cwd,
            timeout=_wait_timeout(label),
        )
        process_exit = wait.stdout.strip()
        logs = _stage(
            deploy,
            label=label,
            stage="logs",
            command=["docker", "logs", name],
            cwd=cwd,
            timeout=LOG_TIMEOUT_SECONDS,
        )
        if process_exit != "0":
            raise deploy.DeploymentError(f"sensitive Docker workload failed: {label}:process")
    except Exception as exc:
        primary_error = exc

    cleanup_error: Exception | None = None
    try:
        if create_succeeded:
            _cleanup_owned(deploy, name, cwd=cwd)
        else:
            _cleanup_ambiguous_create(deploy, name, owner, cwd=cwd)
    except Exception as exc:
        cleanup_error = exc

    if cleanup_error is not None:
        if primary_error is not None:
            raise deploy.DeploymentError(
                f"sensitive Docker workload and cleanup failed: {label}"
            ) from cleanup_error
        raise cleanup_error
    if primary_error is not None:
        raise primary_error
    if logs is None or process_exit != "0":
        raise deploy.DeploymentError(f"sensitive Docker workload produced no result: {label}")
    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout=logs.stdout,
        stderr="",
    )


def install(deploy: Any) -> None:
    """Bound only the sensitive Portal schema/transfer `docker run --rm` workloads."""

    original_run = deploy._run

    def guarded_run(
        command: list[str],
        *,
        cwd: Path | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        module = _target_module(command)
        if module is None or not sensitive or not check:
            return cast(
                subprocess.CompletedProcess[str],
                original_run(command, cwd=cwd, sensitive=sensitive, check=check),
            )
        return _run_sensitive_workload(deploy, command, cwd=cwd)

    deploy._run = guarded_run
