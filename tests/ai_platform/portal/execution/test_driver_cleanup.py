from __future__ import annotations

from collections.abc import Sequence

import pytest

from ai_platform.portal.execution.driver import (
    CommandResult,
    DockerCliRuntimeDriver,
    ExternalIsolationCapabilities,
)
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.isolation import RuntimeIsolationPlan


class _Runner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str]) -> CommandResult:
        self.calls.append(tuple(args))
        return self.result


class _CleanupAttestor:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.cleaned: list[tuple[str, str]] = []

    def capabilities(self) -> ExternalIsolationCapabilities:
        return ExternalIsolationCapabilities()

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: object) -> None:
        del plan, state_path

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan, network_name, runtime_id

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: object) -> None:
        del plan, state_path

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan, network_name, runtime_id

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        self.cleaned.append((network_name, runtime_id))
        if self.error is not None:
            raise self.error


def test_cleanup_attempts_network_after_container_remove_failure() -> None:
    runner = _Runner(CommandResult(1, stderr="daemon unavailable"))
    attestor = _CleanupAttestor(error=RuntimeError("nft cleanup failed"))
    driver = DockerCliRuntimeDriver(runner, external_attestor=attestor)
    driver._attested.add("runtime-1")
    driver._released.add("runtime-1")
    driver._fingerprints["runtime-1"] = "fingerprint"
    driver._networks["runtime-1"] = "portal-net-1"
    driver._container_ids["runtime-1"] = "container-id-1"

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver._cleanup_failed_runtime("runtime-1", "portal-net-1")

    assert exc_info.value.reason_code == "RUNTIME_CLEANUP_FAILED"
    assert runner.calls == [("docker", "rm", "-f", "container-id-1")]
    assert attestor.cleaned == [("portal-net-1", "runtime-1")]
    assert "runtime-1" not in driver._attested
    assert "runtime-1" not in driver._released
    assert "runtime-1" not in driver._fingerprints
    assert "runtime-1" not in driver._networks
    assert driver._container_ids["runtime-1"] == "container-id-1"


def test_cleanup_treats_missing_container_as_idempotent_success() -> None:
    runner = _Runner(CommandResult(1, stderr="Error: No such container: container-id-1"))
    attestor = _CleanupAttestor()
    driver = DockerCliRuntimeDriver(runner, external_attestor=attestor)
    driver._container_ids["runtime-1"] = "container-id-1"

    driver._cleanup_failed_runtime("runtime-1", "portal-net-1")

    assert runner.calls == [("docker", "rm", "-f", "container-id-1")]
    assert attestor.cleaned == [("portal-net-1", "runtime-1")]
    assert "runtime-1" not in driver._container_ids
