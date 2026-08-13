from __future__ import annotations

import json
from collections.abc import Sequence

from ai_platform.portal.execution.driver import (
    CommandResult,
    DockerCliRuntimeDriver,
    DriverRuntimeState,
)


class _Runner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str], *, timeout_seconds: float | None = None) -> CommandResult:
        del timeout_seconds
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


def test_stop_retains_immutable_container_id_for_later_retirement() -> None:
    runner = _Runner(
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": "container-id",
                    "Config": {"Labels": {"ai.portal.runtime_id": "runtime-1"}},
                }
            ),
        ),
        CommandResult(0, stdout="running\n"),
        CommandResult(1),
        CommandResult(0),
    )
    driver = DockerCliRuntimeDriver(runner)
    driver._container_ids["runtime-1"] = "container-id"

    assert driver.stop("runtime-1") is DriverRuntimeState.STOPPED
    assert driver._container_ids["runtime-1"] == "container-id"
    assert runner.calls[-1] == ("docker", "stop", "container-id")
