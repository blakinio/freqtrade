from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def run(self, args: Sequence[str]) -> CommandResult: ...


class SubprocessCommandRunner:
    def run(self, args: Sequence[str]) -> CommandResult:
        completed = subprocess.run(
            list(args),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


class DockerCliRuntimeDriver:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner or SubprocessCommandRunner()

    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:
        current = self.inspect(spec.runtime_id)
        if current is not DriverRuntimeState.MISSING:
            return current

        args: list[str] = [
            "docker",
            "create",
            "--name",
            spec.runtime_id,
            "--restart",
            "no",
        ]
        for key, value in sorted(spec.labels.items()):
            args.extend(("--label", f"{key}={value}"))
        args.extend(
            (
                "--mount",
                f"type=bind,source={spec.workspace},target=/freqtrade/user_data",
                spec.image,
                "trade",
                "--config",
                "/freqtrade/user_data/config.json",
                "--strategy",
                spec.strategy_name,
            )
        )
        self._require_success(args, "DOCKER_CREATE_FAILED")
        return DriverRuntimeState.CREATED

    def start(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.RUNNING:
            return current
        if current is DriverRuntimeState.PAUSED:
            self._require_success(("docker", "unpause", runtime_id), "DOCKER_UNPAUSE_FAILED")
            return DriverRuntimeState.RUNNING
        if current in {DriverRuntimeState.CREATED, DriverRuntimeState.STOPPED}:
            self._require_success(("docker", "start", runtime_id), "DOCKER_START_FAILED")
            return DriverRuntimeState.RUNNING
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def pause(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.PAUSED:
            return current
        if current is DriverRuntimeState.RUNNING:
            self._require_success(("docker", "pause", runtime_id), "DOCKER_PAUSE_FAILED")
            return DriverRuntimeState.PAUSED
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def stop(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.STOPPED:
            return current
        if current in {DriverRuntimeState.RUNNING, DriverRuntimeState.PAUSED}:
            self._require_success(("docker", "stop", runtime_id), "DOCKER_STOP_FAILED")
            return DriverRuntimeState.STOPPED
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def inspect(self, runtime_id: str) -> DriverRuntimeState:
        result = self._runner.run(
            (
                "docker",
                "inspect",
                "--format",
                "{{.State.Status}}",
                runtime_id,
            )
        )
        if result.returncode != 0:
            if "no such object" in result.stderr.lower():
                return DriverRuntimeState.MISSING
            raise RuntimeDriverError(
                "DOCKER_INSPECT_FAILED",
                result.stderr.strip() or "docker inspect failed",
            )

        state = result.stdout.strip().lower()
        mapping = {
            "created": DriverRuntimeState.CREATED,
            "restarting": DriverRuntimeState.STARTING,
            "running": DriverRuntimeState.RUNNING,
            "paused": DriverRuntimeState.PAUSED,
            "exited": DriverRuntimeState.STOPPED,
            "dead": DriverRuntimeState.STOPPED,
        }
        try:
            return mapping[state]
        except KeyError as exc:
            raise RuntimeDriverError(
                "DOCKER_STATE_UNKNOWN",
                f"unsupported docker runtime state: {state or '<empty>'}",
            ) from exc

    def _require_success(self, args: Sequence[str], reason_code: str) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise RuntimeDriverError(
                reason_code,
                result.stderr.strip() or f"command failed: {args[1]}",
            )
