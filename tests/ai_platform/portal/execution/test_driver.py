from collections.abc import Sequence

import pytest

from ai_platform.portal.execution.driver import (
    CommandResult,
    DockerCliRuntimeDriver,
)
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


class _RecordingRunner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str]) -> CommandResult:
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError("unexpected command")
        return self.results.pop(0)


def test_docker_provision_creates_private_container_without_published_ports(tmp_path) -> None:
    runner = _RecordingRunner(
        CommandResult(returncode=1, stderr="Error: No such object: runtime-1"),
        CommandResult(returncode=0, stdout="container-id"),
    )
    driver = DockerCliRuntimeDriver(runner)
    spec = RuntimeContainerSpec(
        runtime_id="runtime-1",
        image="freqtradeorg/freqtrade:stable",
        workspace=tmp_path / "runtime-1",
        strategy_name="PortalStrategy",
        labels={
            "ai.portal.correlation_id": "correlation-1",
            "ai.portal.request_id": "request-1",
        },
    )

    state = driver.provision(spec)

    assert state is DriverRuntimeState.CREATED
    create = runner.calls[1]
    assert create[:4] == ("docker", "create", "--name", "runtime-1")
    assert "-p" not in create
    assert "--publish" not in create
    assert "--publish-all" not in create
    assert (
        f"type=bind,source={tmp_path / 'runtime-1'},target=/freqtrade/user_data"
        in create
    )
    assert "ai.portal.correlation_id=correlation-1" in create
    assert create[-5:] == (
        "trade",
        "--config",
        "/freqtrade/user_data/config.json",
        "--strategy",
        "PortalStrategy",
    )


def test_docker_start_unpauses_an_existing_paused_runtime() -> None:
    runner = _RecordingRunner(
        CommandResult(returncode=0, stdout="paused\n"),
        CommandResult(returncode=0),
    )
    driver = DockerCliRuntimeDriver(runner)

    state = driver.start("runtime-1")

    assert state is DriverRuntimeState.RUNNING
    assert runner.calls[-1] == ("docker", "unpause", "runtime-1")


def test_docker_pause_and_stop_are_idempotent_for_terminal_states() -> None:
    pause_runner = _RecordingRunner(CommandResult(returncode=0, stdout="paused\n"))
    stop_runner = _RecordingRunner(CommandResult(returncode=0, stdout="exited\n"))

    assert DockerCliRuntimeDriver(pause_runner).pause("runtime-1") is DriverRuntimeState.PAUSED
    assert DockerCliRuntimeDriver(stop_runner).stop("runtime-1") is DriverRuntimeState.STOPPED
    assert len(pause_runner.calls) == 1
    assert len(stop_runner.calls) == 1


def test_docker_unknown_state_fails_closed() -> None:
    runner = _RecordingRunner(CommandResult(returncode=0, stdout="mystery\n"))
    driver = DockerCliRuntimeDriver(runner)

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.inspect("runtime-1")

    assert exc_info.value.reason_code == "DOCKER_STATE_UNKNOWN"
