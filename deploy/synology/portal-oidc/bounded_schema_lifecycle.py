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
CLEANUP_ATTEMPTS = 3
OWNERSHIP_VERIFY_ATTEMPTS = 3
OWNER_LABEL_KEY = "com.freqtrade.portal.bounded-owner"
OWNED_IDENTITY_FORMAT = f'{{{{.Id}}}}|{{{{ index .Config.Labels "{OWNER_LABEL_KEY}" }}}}'
SERVICE_STATE_FORMAT = (
    "{{.State.Status}}|{{.State.Running}}|"
    "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}"
)
PROTECTED_SERVICE_ATTRIBUTES = (
    "PORTAL_CONTAINER",
    "CONTROL_CONTAINER",
    "PORTAL_POSTGRES_CONTAINER",
)
_TARGET_MODULES = {
    "ai_platform.portal.database.cli",
    "ai_platform.portal.database.transfer",
}
_CONTAINER_ID_RE = re.compile(r"^[0-9a-f]{64}$")


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


def _parse_container_id(deploy: Any, value: str) -> str:
    container_id = value.strip()
    if not _CONTAINER_ID_RE.fullmatch(container_id):
        raise deploy.DeploymentError("Docker create returned an invalid container identity")
    return container_id


def _remember_cancellation(
    current: BaseException | None,
    candidate: BaseException,
) -> BaseException | None:
    if current is not None:
        return current
    if not isinstance(candidate, Exception):
        return candidate
    return None


def _raise_preserved_cancellation(
    cancellation: BaseException,
    cause: BaseException | None = None,
) -> None:
    if cause is not None and cause is not cancellation:
        raise cancellation from cause
    raise cancellation


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


def _inspect_owned_identity(
    deploy: Any,
    reference: str,
    *,
    cwd: Path | None,
) -> tuple[str, str] | None:
    try:
        inspected = _run_bounded(
            ["docker", "inspect", "--format", OWNED_IDENTITY_FORMAT, reference],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise deploy.DeploymentError("task-owned Docker identity query timed out") from exc
    if inspected.returncode != 0:
        return None
    container_id, separator, owner = inspected.stdout.strip().partition("|")
    if separator != "|" or not _CONTAINER_ID_RE.fullmatch(container_id):
        raise deploy.DeploymentError("task-owned Docker identity query returned invalid metadata")
    return container_id, owner


def _verify_container_id_absent(
    deploy: Any,
    container_id: str,
    *,
    cwd: Path | None,
) -> None:
    try:
        inspected = _run_bounded(
            ["docker", "inspect", container_id],
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
            "task-owned Docker identity cleanup could not be verified"
        ) from exc
    if version.returncode != 0 or inspected.returncode == 0:
        raise deploy.DeploymentError("task-owned Docker identity cleanup failed")


def _resolve_owned_cleanup_target(
    deploy: Any,
    name: str,
    owner: str,
    expected_id: str | None,
    *,
    cwd: Path | None,
) -> str | None:
    reference = expected_id or name
    identity = _inspect_owned_identity(deploy, reference, cwd=cwd)
    if identity is None:
        if expected_id is None:
            _verify_absent(deploy, name, cwd=cwd)
        else:
            _verify_container_id_absent(deploy, expected_id, cwd=cwd)
        return None

    current_id, current_owner = identity
    if current_owner != owner:
        raise deploy.DeploymentError("current Docker container identity is not owned by this task")
    if expected_id is not None and current_id != expected_id:
        raise deploy.DeploymentError(
            "current Docker container identity changed before task-owned cleanup"
        )
    return current_id


def _remove_owned_id_once(
    deploy: Any,
    container_id: str,
    *,
    cwd: Path | None,
) -> None:
    remove_error: BaseException | None = None
    try:
        removed = _run_bounded(
            ["docker", "rm", "-f", container_id],
            cwd=cwd,
            timeout=REMOVE_TIMEOUT_SECONDS,
        )
        if removed.returncode != 0:
            remove_error = deploy.DeploymentError("task-owned Docker identity removal failed")
    except subprocess.TimeoutExpired as exc:
        remove_error = exc

    try:
        _verify_container_id_absent(deploy, container_id, cwd=cwd)
    except deploy.DeploymentError as exc:
        cause = remove_error if remove_error is not None else exc
        raise deploy.DeploymentError(
            "task-owned Docker identity removal could not be verified"
        ) from cause


def _cleanup_owned(
    deploy: Any,
    name: str,
    owner: str,
    *,
    container_id: str | None,
    cwd: Path | None,
) -> str | None:
    expected_id = container_id
    cancellation: BaseException | None = None
    last_cleanup_error: BaseException | None = None
    for _attempt in range(CLEANUP_ATTEMPTS):
        try:
            target_id = _resolve_owned_cleanup_target(
                deploy,
                name,
                owner,
                expected_id,
                cwd=cwd,
            )
            if target_id is None:
                if cancellation is not None:
                    _raise_preserved_cancellation(cancellation, last_cleanup_error)
                return expected_id
            expected_id = target_id
            _remove_owned_id_once(deploy, expected_id, cwd=cwd)
            if cancellation is not None:
                _raise_preserved_cancellation(cancellation, last_cleanup_error)
            return expected_id
        except BaseException as exc:
            cancellation = _remember_cancellation(cancellation, exc)
            last_cleanup_error = exc

    if cancellation is not None:
        _raise_preserved_cancellation(cancellation, last_cleanup_error)
    raise deploy.DeploymentError(
        "task-owned Docker workload cleanup failed after bounded retries"
    ) from last_cleanup_error


def _cleanup_ambiguous_create(
    deploy: Any,
    name: str,
    owner: str,
    *,
    cwd: Path | None,
) -> str | None:
    cancellation: BaseException | None = None
    last_verification_error: BaseException | None = None
    for _attempt in range(OWNERSHIP_VERIFY_ATTEMPTS):
        try:
            identity = _inspect_owned_identity(deploy, name, cwd=cwd)
            if identity is not None:
                container_id, current_owner = identity
                if current_owner != owner:
                    ownership_error = deploy.DeploymentError(
                        "ambiguous Docker create produced a container not owned by this task"
                    )
                    if cancellation is not None:
                        _raise_preserved_cancellation(cancellation, ownership_error)
                    raise ownership_error
                try:
                    result = _cleanup_owned(
                        deploy,
                        name,
                        owner,
                        container_id=container_id,
                        cwd=cwd,
                    )
                except BaseException as exc:
                    if cancellation is not None and isinstance(exc, Exception):
                        _raise_preserved_cancellation(cancellation, exc)
                    raise
                if cancellation is not None:
                    _raise_preserved_cancellation(cancellation, last_verification_error)
                return result

            _verify_absent(deploy, name, cwd=cwd)
            if cancellation is not None:
                _raise_preserved_cancellation(cancellation, last_verification_error)
            return None
        except BaseException as exc:
            cancellation = _remember_cancellation(cancellation, exc)
            last_verification_error = exc
            if isinstance(exc, Exception) and not isinstance(exc, deploy.DeploymentError):
                raise

    if cancellation is not None:
        _raise_preserved_cancellation(cancellation, last_verification_error)
    raise deploy.DeploymentError(
        "ambiguous Docker create ownership could not be verified after bounded retries"
    ) from last_verification_error


def _protected_service_names(deploy: Any) -> tuple[str, ...]:
    names = {
        value
        for attribute in PROTECTED_SERVICE_ATTRIBUTES
        if isinstance((value := getattr(deploy, attribute, None)), str) and value
    }
    return tuple(sorted(names))


def _protected_service_state(
    deploy: Any,
    name: str,
    *,
    cwd: Path | None,
) -> dict[str, object]:
    exact_name_filter = f"name=^/{name}$"
    try:
        listed = _run_bounded(
            ["docker", "ps", "-aq", "--no-trunc", "--filter", exact_name_filter],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise deploy.DeploymentError("protected service health query timed out") from exc
    if listed.returncode != 0:
        raise deploy.DeploymentError("protected service inventory query failed")
    identifiers = [line.strip() for line in listed.stdout.splitlines() if line.strip()]
    if not identifiers:
        return {
            "exists": False,
            "container_id": None,
            "state": "absent",
            "running": False,
            "health": "none",
        }
    if len(identifiers) != 1:
        raise deploy.DeploymentError("protected service exact-name inventory is ambiguous")
    container_id = identifiers[0]
    if not _CONTAINER_ID_RE.fullmatch(container_id):
        raise deploy.DeploymentError("protected service inventory returned invalid identity")

    try:
        inspected = _run_bounded(
            ["docker", "inspect", "--format", SERVICE_STATE_FORMAT, container_id],
            cwd=cwd,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise deploy.DeploymentError("protected service health query timed out") from exc
    if inspected.returncode != 0:
        raise deploy.DeploymentError("protected service health inspection failed")
    state, separator, remainder = inspected.stdout.strip().partition("|")
    running, second_separator, health = remainder.partition("|")
    if separator != "|" or second_separator != "|" or running not in {"true", "false"}:
        raise deploy.DeploymentError(
            "protected service health inspection returned invalid metadata"
        )
    if not state or not health:
        raise deploy.DeploymentError(
            "protected service health inspection returned incomplete metadata"
        )
    return {
        "exists": True,
        "container_id": container_id,
        "state": state,
        "running": running == "true",
        "health": health,
    }


def _capture_protected_services(
    deploy: Any,
    *,
    cwd: Path | None,
) -> dict[str, dict[str, object]]:
    return {
        name: _protected_service_state(deploy, name, cwd=cwd)
        for name in _protected_service_names(deploy)
    }


def _protected_service_regressions(
    before: dict[str, dict[str, object]],
    after: dict[str, dict[str, object]],
) -> list[str]:
    regressions: list[str] = []
    for name, baseline in before.items():
        current = after.get(name)
        if current is None:
            regressions.append(f"{name}:unobserved")
            continue
        if baseline["exists"] is True and current["exists"] is not True:
            regressions.append(f"{name}:became_absent")
            continue
        if (
            baseline["exists"] is True
            and current["exists"] is True
            and baseline.get("container_id") != current.get("container_id")
        ):
            regressions.append(f"{name}:identity_changed")
            continue
        if baseline["running"] is True and current["running"] is not True:
            regressions.append(f"{name}:stopped_running")
        baseline_health = baseline["health"]
        current_health = current["health"]
        if baseline_health == "healthy" and current_health != "healthy":
            regressions.append(f"{name}:lost_healthy")
        elif baseline_health == "starting" and current_health not in {"starting", "healthy"}:
            regressions.append(f"{name}:starting_degraded")
    return regressions


def _record_cleanup_evidence(
    deploy: Any,
    *,
    label: str,
    name: str,
    container_id: str | None,
    before: dict[str, dict[str, object]] | None,
    after: dict[str, dict[str, object]] | None,
    regressions: list[str],
    cleanup_complete: bool,
    verification_complete: bool,
) -> None:
    evidence = getattr(deploy, "_bounded_schema_cleanup_evidence", None)
    if not isinstance(evidence, list):
        evidence = []
        deploy._bounded_schema_cleanup_evidence = evidence
    evidence.append(
        {
            "workload": label,
            "task_container_name": name,
            "task_container_id": container_id,
            "protected_before": before,
            "protected_after": after,
            "cleanup_complete": cleanup_complete,
            "protected_non_regression": verification_complete and not regressions,
            "regressions": regressions,
            "verification_complete": verification_complete,
        }
    )


def _cancellation_error(*errors: BaseException | None) -> BaseException | None:
    return next(
        (error for error in errors if error is not None and not isinstance(error, Exception)),
        None,
    )


def _prefer_cancellation(
    current: BaseException | None,
    candidate: BaseException,
) -> BaseException:
    if current is None:
        return candidate
    if isinstance(current, Exception) and not isinstance(candidate, Exception):
        return candidate
    return current


def _raise_cancellation_with_context(
    cancellation: BaseException,
    *errors: BaseException | None,
) -> None:
    cause = next(
        (error for error in errors if error is not None and error is not cancellation),
        None,
    )
    if cause is not None:
        raise cancellation from cause
    raise cancellation


def _cleanup_verified_after_error(
    deploy: Any,
    name: str,
    container_id: str | None,
    *,
    cwd: Path | None,
) -> bool:
    try:
        if container_id is not None:
            _verify_container_id_absent(deploy, container_id, cwd=cwd)
        else:
            _verify_absent(deploy, name, cwd=cwd)
    except (deploy.DeploymentError, subprocess.TimeoutExpired):
        return False
    return True


def _cleanup_with_protected_health(
    deploy: Any,
    *,
    label: str,
    name: str,
    owner: str,
    create_succeeded: bool,
    container_id: str | None,
    cwd: Path | None,
) -> None:
    before: dict[str, dict[str, object]] | None = None
    after: dict[str, dict[str, object]] | None = None
    cleaned_container_id = container_id
    health_error: BaseException | None = None
    cleanup_error: BaseException | None = None

    try:
        before = _capture_protected_services(deploy, cwd=cwd)
    except BaseException as exc:
        health_error = _prefer_cancellation(health_error, exc)

    try:
        if create_succeeded:
            cleaned_container_id = _cleanup_owned(
                deploy,
                name,
                owner,
                container_id=container_id,
                cwd=cwd,
            )
        else:
            cleaned_container_id = _cleanup_ambiguous_create(deploy, name, owner, cwd=cwd)
    except BaseException as exc:
        cleanup_error = exc
    finally:
        try:
            after = _capture_protected_services(deploy, cwd=cwd)
        except BaseException as exc:
            health_error = _prefer_cancellation(health_error, exc)

    cleanup_complete = cleanup_error is None
    if cleanup_error is not None and not isinstance(cleanup_error, Exception):
        cleanup_complete = _cleanup_verified_after_error(
            deploy,
            name,
            cleaned_container_id,
            cwd=cwd,
        )

    regressions = (
        _protected_service_regressions(before, after)
        if before is not None and after is not None
        else []
    )
    verification_complete = (
        health_error is None
        and cleanup_complete
        and before is not None
        and after is not None
    )
    _record_cleanup_evidence(
        deploy,
        label=label,
        name=name,
        container_id=cleaned_container_id,
        before=before,
        after=after,
        regressions=regressions,
        cleanup_complete=cleanup_complete,
        verification_complete=verification_complete,
    )

    cancellation = _cancellation_error(health_error, cleanup_error)
    if cancellation is not None:
        _raise_cancellation_with_context(cancellation, health_error, cleanup_error)
    if health_error is not None:
        if cleanup_error is not None:
            raise deploy.DeploymentError(
                "task-owned cleanup and protected service health verification failed"
            ) from health_error
        raise deploy.DeploymentError(
            "protected service health could not be verified around task-owned cleanup"
        ) from health_error
    if regressions:
        if cleanup_error is not None:
            raise deploy.DeploymentError(
                "task-owned cleanup failed and protected service health regressed"
            ) from cleanup_error
        raise deploy.DeploymentError("protected service health regressed during task-owned cleanup")
    if cleanup_error is not None:
        raise cleanup_error


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
    # mutation. Every destructive cleanup attempt re-reads the immutable ID and
    # invocation owner label, and all post-create execution targets the immutable
    # ID rather than whichever container may later reuse the generated name.
    _verify_absent(deploy, name, cwd=cwd)

    primary_error: BaseException | None = None
    cleanup_error: BaseException | None = None
    logs: subprocess.CompletedProcess[str] | None = None
    process_exit: str | None = None
    create_succeeded = False
    created_container_id: str | None = None

    try:
        created = _stage(
            deploy,
            label=label,
            stage="create",
            command=create_command,
            cwd=cwd,
            timeout=CREATE_TIMEOUT_SECONDS,
        )
        create_succeeded = True
        created_container_id = _parse_container_id(deploy, created.stdout)
        _stage(
            deploy,
            label=label,
            stage="start",
            command=["docker", "start", created_container_id],
            cwd=cwd,
            timeout=START_TIMEOUT_SECONDS,
        )
        wait = _stage(
            deploy,
            label=label,
            stage="wait",
            command=["docker", "wait", created_container_id],
            cwd=cwd,
            timeout=_wait_timeout(label),
        )
        process_exit = wait.stdout.strip()
        logs = _stage(
            deploy,
            label=label,
            stage="logs",
            command=["docker", "logs", created_container_id],
            cwd=cwd,
            timeout=LOG_TIMEOUT_SECONDS,
        )
        if process_exit != "0":
            raise deploy.DeploymentError(f"sensitive Docker workload failed: {label}:process")
    except BaseException as exc:
        primary_error = exc
    finally:
        try:
            _cleanup_with_protected_health(
                deploy,
                label=label,
                name=name,
                owner=owner,
                create_succeeded=create_succeeded,
                container_id=created_container_id,
                cwd=cwd,
            )
        except BaseException as exc:
            cleanup_error = exc

    cancellation = _cancellation_error(primary_error, cleanup_error)
    if cancellation is not None:
        _raise_cancellation_with_context(cancellation, primary_error, cleanup_error)
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
    original_write_report = getattr(deploy, "_write_report", None)
    deploy._bounded_schema_cleanup_evidence = []

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

    if callable(original_write_report):

        def write_report(path: Path, report: dict[str, Any]) -> str:
            report["bounded_schema_cleanup_evidence"] = list(
                deploy._bounded_schema_cleanup_evidence
            )
            return cast(str, original_write_report(path, report))

        deploy._write_report = write_report
