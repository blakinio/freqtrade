from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec
from ai_platform.portal.runtime_supervisor import (
    InMemoryCommandJournal,
    RuntimeSupervisor,
    SqliteCommandJournal,
    SupervisorGeneration,
    SupervisorOperation,
    SupervisorOutcomeCode,
    SupervisorRequest,
)
from ai_platform.portal.runtime_supervisor.service import _KeyedLockRegistry


class Generations:
    def __init__(self, generation: SupervisorGeneration, active: str | None = None) -> None:
        self.generation = generation
        self.active = active

    def resolve(self, generation_id: str) -> SupervisorGeneration | None:
        return self.generation if generation_id == self.generation.generation_id else None

    def active_generation(self, tenant_id: str, bot_id: str) -> str | None:
        return self.active


class Driver:
    def __init__(
        self,
        state: DriverRuntimeState = DriverRuntimeState.MISSING,
        *,
        has_evidence: bool = True,
    ) -> None:
        self.state = state
        self.calls: list[str] = []
        self.has_evidence = has_evidence

    def inspect(self, runtime_id: str) -> DriverRuntimeState:
        self.calls.append("inspect")
        return self.state

    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:
        self.calls.append("provision")
        self.state = DriverRuntimeState.CREATED
        return self.state

    def start(self, runtime_id: str) -> DriverRuntimeState:
        self.calls.append("start")
        self.state = DriverRuntimeState.RUNNING
        return self.state

    def pause(self, runtime_id: str) -> DriverRuntimeState:
        self.calls.append("pause")
        self.state = DriverRuntimeState.PAUSED
        return self.state

    def stop(self, runtime_id: str) -> DriverRuntimeState:
        self.calls.append("stop")
        self.state = DriverRuntimeState.STOPPED
        return self.state

    def retire(self, runtime_id: str) -> DriverRuntimeState:
        self.calls.append("retire")
        self.state = DriverRuntimeState.MISSING
        return self.state

    def has_current_generation_evidence(self, runtime_id: str, spec: RuntimeContainerSpec) -> bool:
        return self.has_evidence


def generation(
    *, retired: bool = False, retirement_authorized: bool = False
) -> SupervisorGeneration:
    return SupervisorGeneration(
        "tenant-1",
        "bot-1",
        "gen-1",
        2,
        "a" * 64,
        7,
        retired,
        ExecutionMode.DRY_RUN,
        True,
        retirement_authorized,
        RuntimeContainerSpec(
            "runtime-1",
            "trusted@sha256:" + "b" * 64,
            Path("/trusted/config"),
            Path("/trusted/state"),
            "Strategy",
            {},
        ),
    )


def request(
    operation: SupervisorOperation = SupervisorOperation.ENSURE_RUNNING, **updates: object
) -> SupervisorRequest:
    values: dict[str, object] = {
        "tenant_id": "tenant-1",
        "bot_id": "bot-1",
        "generation_id": "gen-1",
        "generation_spec_digest": "a" * 64,
        "operation": operation,
        "command_id": uuid4(),
        "expected_generation_ordinal": 2,
        "expected_state_version": 7,
        "correlation_id": uuid4(),
    }
    values.update(updates)
    return SupervisorRequest.model_validate(values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("image", "evil:latest"),
        ("command", ["sh"]),
        ("mounts", ["/var/run/docker.sock"]),
        ("privileged", True),
        ("network_mode", "host"),
        ("ports", [80]),
        ("capabilities", ["SYS_ADMIN"]),
        ("devices", ["/dev/sda"]),
        ("environment", {"X": "Y"}),
    ],
)
def test_request_rejects_every_raw_engine_parameter(field: str, value: object) -> None:
    payload = request().model_dump()
    payload[field] = value
    with pytest.raises(ValidationError):
        SupervisorRequest.model_validate(payload)


def test_exact_binding_and_preconditions_fail_closed() -> None:
    service = RuntimeSupervisor(Generations(generation()), Driver(), InMemoryCommandJournal())
    assert (
        service.execute(request(tenant_id="other")).code
        is SupervisorOutcomeCode.GENERATION_NOT_FOUND
    )
    assert (
        service.execute(request(generation_spec_digest="b" * 64)).code
        is SupervisorOutcomeCode.GENERATION_SPEC_CONFLICT
    )
    assert (
        service.execute(request(expected_state_version=6)).code
        is SupervisorOutcomeCode.PRECONDITION_FAILED
    )


def test_retired_generation_cannot_be_provisioned_or_started() -> None:
    driver = Driver()
    service = RuntimeSupervisor(
        Generations(generation(retired=True)), driver, InMemoryCommandJournal()
    )
    assert service.execute(request()).code is SupervisorOutcomeCode.STALE_OR_RETIRED_GENERATION
    assert driver.calls == []


def test_non_paper_generation_fails_closed_before_engine_access() -> None:
    candidate = generation()
    candidate = SupervisorGeneration(
        **{
            **candidate.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
            "paper_authorized": False,
        }
    )
    driver = Driver()
    outcome = RuntimeSupervisor(Generations(candidate), driver, InMemoryCommandJournal()).execute(
        request()
    )
    assert outcome.code is SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED
    assert driver.calls == []


def test_conflicting_generation_fence_prevents_side_effect() -> None:
    driver = Driver()
    service = RuntimeSupervisor(
        Generations(generation(), active="gen-old"), driver, InMemoryCommandJournal()
    )
    assert service.execute(request()).code is SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE
    assert driver.calls == ["inspect"]


def test_supervisor_claims_active_generation_before_next_request() -> None:
    journal = InMemoryCommandJournal()
    driver = Driver()
    first = RuntimeSupervisor(Generations(generation()), driver, journal)
    assert first.execute(request()).accepted
    other = generation()
    other = SupervisorGeneration(
        **{**other.__dict__, "generation_id": "gen-2", "generation_ordinal": 3}
    )
    blocked = RuntimeSupervisor(Generations(other), driver, journal).execute(
        request(generation_id="gen-2", expected_generation_ordinal=3)
    )
    assert blocked.code is SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE


def test_replay_is_stable_and_conflicting_body_is_rejected() -> None:
    driver = Driver()
    service = RuntimeSupervisor(Generations(generation()), driver, InMemoryCommandJournal())
    original = request()
    first = service.execute(original)
    assert first.accepted and driver.calls == ["inspect", "provision", "start"]
    assert service.execute(original) == first
    assert driver.calls == ["inspect", "provision", "start"]
    conflict = original.model_copy(update={"operation": SupervisorOperation.ENSURE_STOPPED})
    assert service.execute(conflict).code is SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT
    assert driver.calls == ["inspect", "provision", "start"]


def test_sqlite_journal_survives_supervisor_restart(tmp_path: Path) -> None:
    driver = Driver()
    original = request()
    path = tmp_path / "supervisor-journal.sqlite3"
    first = RuntimeSupervisor(
        Generations(generation()), driver, SqliteCommandJournal(path)
    ).execute(original)
    recovered = RuntimeSupervisor(
        Generations(generation()), driver, SqliteCommandJournal(path)
    ).execute(original)
    assert recovered == first
    assert driver.calls == ["inspect", "provision", "start"]


def test_retryable_engine_failure_preserves_fingerprint_but_retries_outcome() -> None:
    class FlakyDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            if "failed" not in self.calls:
                self.calls.append("failed")
                from ai_platform.portal.execution.errors import RuntimeDriverError

                raise RuntimeDriverError("TRANSIENT", "transient")
            return super().start(runtime_id)

    driver = FlakyDriver(DriverRuntimeState.CREATED)
    original = request()
    service = RuntimeSupervisor(Generations(generation()), driver, InMemoryCommandJournal())
    assert service.execute(original).code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED
    conflict = original.model_copy(update={"operation": SupervisorOperation.ENSURE_STOPPED})
    assert service.execute(conflict).code is SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT
    assert service.execute(original).accepted


def test_sqlite_retryable_failure_preserves_replay_fingerprint_across_restart(
    tmp_path: Path,
) -> None:
    from ai_platform.portal.execution.errors import RuntimeDriverError

    class FailingDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            self.calls.append("failed")
            raise RuntimeDriverError("TRANSIENT", "transient")

    path = tmp_path / "retryable-fingerprint.sqlite3"
    original = request()
    first_driver = FailingDriver(DriverRuntimeState.CREATED)
    first = RuntimeSupervisor(
        Generations(generation()), first_driver, SqliteCommandJournal(path)
    ).execute(original)
    assert first.code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED

    second_driver = Driver(DriverRuntimeState.RUNNING)
    recovered = RuntimeSupervisor(
        Generations(generation()), second_driver, SqliteCommandJournal(path)
    )
    conflict = original.model_copy(update={"operation": SupervisorOperation.ENSURE_STOPPED})
    assert recovered.execute(conflict).code is SupervisorOutcomeCode.COMMAND_REPLAY_CONFLICT
    assert second_driver.calls == []


def test_pause_from_non_running_state_fails_without_driver_mutation() -> None:
    driver = Driver(DriverRuntimeState.STOPPED)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PAUSED))
    assert outcome.code is SupervisorOutcomeCode.INVALID_STATE_TRANSITION
    assert driver.calls == ["inspect"]


@pytest.mark.parametrize(
    "operation,initial,expected,calls",
    [
        (
            SupervisorOperation.ENSURE_PROVISIONED,
            DriverRuntimeState.MISSING,
            DriverRuntimeState.CREATED,
            ["inspect", "provision"],
        ),
        (
            SupervisorOperation.ENSURE_RUNNING,
            DriverRuntimeState.CREATED,
            DriverRuntimeState.RUNNING,
            ["inspect", "start"],
        ),
        (
            SupervisorOperation.ENSURE_PAUSED,
            DriverRuntimeState.RUNNING,
            DriverRuntimeState.PAUSED,
            ["inspect", "pause"],
        ),
        (
            SupervisorOperation.ENSURE_STOPPED,
            DriverRuntimeState.RUNNING,
            DriverRuntimeState.STOPPED,
            ["inspect", "stop"],
        ),
        (
            SupervisorOperation.ENSURE_RETIRED,
            DriverRuntimeState.STOPPED,
            DriverRuntimeState.MISSING,
            ["inspect", "retire"],
        ),
        (
            SupervisorOperation.INSPECT_GENERATION,
            DriverRuntimeState.RUNNING,
            DriverRuntimeState.RUNNING,
            ["inspect"],
        ),
    ],
)
def test_bounded_operations(
    operation: SupervisorOperation,
    initial: DriverRuntimeState,
    expected: DriverRuntimeState,
    calls: list[str],
) -> None:
    driver = Driver(initial)
    candidate = generation(retirement_authorized=operation is SupervisorOperation.ENSURE_RETIRED)
    outcome = RuntimeSupervisor(Generations(candidate), driver, InMemoryCommandJournal()).execute(
        request(operation)
    )
    assert outcome.accepted and outcome.state is expected
    assert driver.calls == calls


def test_restart_from_stopped_retires_and_reprovisions_exact_generation() -> None:
    driver = Driver(DriverRuntimeState.STOPPED)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.accepted and outcome.state is DriverRuntimeState.RUNNING
    assert driver.calls == ["inspect", "retire", "provision", "start"]


@pytest.mark.parametrize(
    ("operation", "expected", "calls"),
    [
        (
            SupervisorOperation.ENSURE_RUNNING,
            DriverRuntimeState.RUNNING,
            ["inspect", "stop", "retire", "provision", "start"],
        ),
        (
            SupervisorOperation.ENSURE_PROVISIONED,
            DriverRuntimeState.CREATED,
            ["inspect", "stop", "retire", "provision"],
        ),
    ],
)
def test_restart_from_starting_reconstructs_fail_closed(
    operation: SupervisorOperation,
    expected: DriverRuntimeState,
    calls: list[str],
) -> None:
    driver = Driver(DriverRuntimeState.STARTING)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(operation))
    assert outcome.accepted and outcome.state is expected
    assert driver.calls == calls


def test_running_generation_cannot_be_retired() -> None:
    driver = Driver(DriverRuntimeState.RUNNING)
    outcome = RuntimeSupervisor(
        Generations(generation(retirement_authorized=True)), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RETIRED))
    assert outcome.code is SupervisorOutcomeCode.INVALID_STATE_TRANSITION
    assert driver.calls == ["inspect"]


def test_retirement_requires_trusted_authorization() -> None:
    driver = Driver(DriverRuntimeState.STOPPED)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RETIRED))
    assert outcome.code is SupervisorOutcomeCode.RETIREMENT_NOT_AUTHORIZED
    assert driver.calls == []


def test_resume_from_paused_reconstructs_generation() -> None:
    driver = Driver(DriverRuntimeState.PAUSED)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.accepted
    assert driver.calls == ["inspect", "stop", "retire", "provision", "start"]


def test_provision_from_stopped_reconstructs_generation() -> None:
    driver = Driver(DriverRuntimeState.STOPPED)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect", "retire", "provision"]


def test_durable_local_claim_cannot_mask_provider_generation_conflict(tmp_path: Path) -> None:
    journal = SqliteCommandJournal(tmp_path / "journal.sqlite3")
    assert journal.claim_active("tenant-1", "bot-1", "gen-1")
    driver = Driver()
    outcome = RuntimeSupervisor(
        Generations(generation(), active="gen-other"), driver, journal
    ).execute(request())
    assert outcome.code is SupervisorOutcomeCode.CONFLICTING_GENERATION_ACTIVE
    assert driver.calls == ["inspect"]


def test_non_paper_runtime_remains_containable_and_inspectable() -> None:
    candidate = generation()
    candidate = SupervisorGeneration(
        **{
            **candidate.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
            "paper_authorized": False,
        }
    )

    inspect_driver = Driver(DriverRuntimeState.RUNNING)
    inspected = RuntimeSupervisor(
        Generations(candidate), inspect_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.INSPECT_GENERATION))
    assert inspected.accepted and inspected.state is DriverRuntimeState.RUNNING
    assert inspect_driver.calls == ["inspect"]

    stop_driver = Driver(DriverRuntimeState.RUNNING)
    stopped = RuntimeSupervisor(
        Generations(candidate), stop_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_STOPPED))
    assert stopped.accepted and stopped.state is DriverRuntimeState.STOPPED
    assert stop_driver.calls == ["inspect", "stop"]

    retirement_candidate = SupervisorGeneration(
        **{**candidate.__dict__, "retirement_authorized": True}
    )
    retire_driver = Driver(DriverRuntimeState.STOPPED)
    retired = RuntimeSupervisor(
        Generations(retirement_candidate), retire_driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RETIRED))
    assert retired.accepted and retired.state is DriverRuntimeState.MISSING
    assert retire_driver.calls == ["inspect", "retire"]


@pytest.mark.parametrize(
    "operation",
    [SupervisorOperation.ENSURE_PROVISIONED, SupervisorOperation.ENSURE_RUNNING],
)
def test_non_paper_runtime_cannot_create_exposure(operation: SupervisorOperation) -> None:
    candidate = generation()
    candidate = SupervisorGeneration(
        **{
            **candidate.__dict__,
            "execution_mode": ExecutionMode.SIMULATED,
            "paper_authorized": False,
        }
    )
    driver = Driver()
    outcome = RuntimeSupervisor(Generations(candidate), driver, InMemoryCommandJournal()).execute(
        request(operation)
    )
    assert outcome.code is SupervisorOutcomeCode.PAPER_AUTHORIZATION_REQUIRED
    assert driver.calls == []


def test_running_reconciliation_invokes_driver_reattestation() -> None:
    driver = Driver(DriverRuntimeState.RUNNING)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.accepted and outcome.state is DriverRuntimeState.RUNNING
    assert driver.calls == ["inspect", "start"]


def test_restart_observed_created_runtime_is_reconstructed() -> None:
    driver = Driver(DriverRuntimeState.CREATED, has_evidence=False)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect", "stop", "retire", "provision"]


def test_same_session_created_runtime_remains_idempotent() -> None:
    driver = Driver(DriverRuntimeState.CREATED, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect"]


def test_driver_reason_code_is_bounded_and_exception_text_is_not_exposed() -> None:
    from ai_platform.portal.execution.errors import RuntimeDriverError

    class FailingDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            self.calls.append("start")
            raise RuntimeDriverError("ISOLATION_ATTESTATION_FAILED", "/secret/path detail")

    driver = FailingDriver(DriverRuntimeState.RUNNING)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.code is SupervisorOutcomeCode.ENGINE_OPERATION_FAILED
    assert outcome.driver_reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert "/secret/path" not in outcome.model_dump_json()


def test_unbounded_driver_reason_code_is_sanitized() -> None:
    from ai_platform.portal.execution.errors import RuntimeDriverError

    class FailingDriver(Driver):
        def start(self, runtime_id: str) -> DriverRuntimeState:
            raise RuntimeDriverError("unsafe reason with detail", "secret")

    outcome = RuntimeSupervisor(
        Generations(generation()),
        FailingDriver(DriverRuntimeState.RUNNING),
        InMemoryCommandJournal(),
    ).execute(request(SupervisorOperation.ENSURE_RUNNING))
    assert outcome.driver_reason_code == "DRIVER_FAILURE_UNCLASSIFIED"


def test_keyed_lock_registry_serializes_same_key_and_releases_idle_entries() -> None:
    registry = _KeyedLockRegistry()
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()

    def first() -> None:
        with registry.hold("same-command"):
            first_entered.set()
            assert release_first.wait(2)

    def second() -> None:
        assert first_entered.wait(1)
        with registry.hold("same-command"):
            second_entered.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(first)
        second_future = pool.submit(second)
        assert first_entered.wait(1)
        assert not second_entered.wait(0.05)
        assert len(registry) == 1
        release_first.set()
        first_future.result(timeout=2)
        second_future.result(timeout=2)

    assert second_entered.is_set()
    assert len(registry) == 0


def test_command_lock_registry_does_not_retain_historical_command_ids() -> None:
    service = RuntimeSupervisor(Generations(generation()), Driver(), InMemoryCommandJournal())
    for _ in range(128):
        outcome = service.execute(request(SupervisorOperation.INSPECT_GENERATION))
        assert outcome.accepted
    assert len(service._command_locks) == 0


@pytest.mark.parametrize("initial", [DriverRuntimeState.RUNNING, DriverRuntimeState.PAUSED])
def test_restart_observed_active_runtime_reconstructs_before_provision_success(
    initial: DriverRuntimeState,
) -> None:
    driver = Driver(initial, has_evidence=False)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.CREATED
    assert driver.calls == ["inspect", "stop", "retire", "provision"]


def test_same_session_running_is_reattested_before_provision_success() -> None:
    driver = Driver(DriverRuntimeState.RUNNING, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.RUNNING
    assert driver.calls == ["inspect", "start"]


def test_same_session_paused_provision_remains_idempotent_with_exact_evidence() -> None:
    driver = Driver(DriverRuntimeState.PAUSED, has_evidence=True)
    outcome = RuntimeSupervisor(
        Generations(generation()), driver, InMemoryCommandJournal()
    ).execute(request(SupervisorOperation.ENSURE_PROVISIONED))
    assert outcome.accepted and outcome.state is DriverRuntimeState.PAUSED
    assert driver.calls == ["inspect"]
