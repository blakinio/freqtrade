from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    CandidatePaperRuntimeOperatorError,
)
from ai_platform.wickhunter.candidate_paper_runtime_service import (
    CandidatePaperRuntimeServiceError,
)
from ai_platform.wickhunter.candidate_paper_runtime_supervisor import (
    CandidatePaperRuntimeEarlyFail,
    CandidatePaperRuntimeSupervisor,
    CandidatePaperRuntimeSupervisorError,
    CycleTelemetryStore,
)
from ai_platform.wickhunter.shadow_runtime_common import ShadowRuntimeError


OPERATOR_COMMIT = "a" * 40
BINDING_ID = "b" * 64
RUN_ID = "c" * 64


class _FakeJournal:
    def __init__(self, observed_at_ms: tuple[int, ...] = ()) -> None:
        self._observations = tuple(
            SimpleNamespace(observed_at_ms=value) for value in observed_at_ms
        )

    def observations(self) -> tuple[SimpleNamespace, ...]:
        return self._observations


class _FakeOperator:
    def __init__(
        self,
        *,
        observed_at_ms: tuple[int, ...] = (),
        failures_before_success: int = 0,
    ) -> None:
        binding = SimpleNamespace(
            binding_id=BINDING_ID,
            request=SimpleNamespace(run_id=RUN_ID),
            policy=SimpleNamespace(maximum_snapshot_gap_ms=1_800_000),
        )
        self.service = SimpleNamespace(
            binding=binding,
            journal=_FakeJournal(observed_at_ms),
        )
        self.operator_commit = OPERATOR_COMMIT
        self.failures_before_success = failures_before_success
        self.run_calls = 0
        self.failures: list[tuple[str, int]] = []

    def run_once(self, *, observed_at_ms: int) -> int:
        del observed_at_ms
        self.run_calls += 1
        if self.run_calls <= self.failures_before_success:
            raise CandidatePaperRuntimeOperatorError(f"transient-{self.run_calls}")
        return self.run_calls

    def publish_failure(self, error: BaseException, *, checked_at_ms: int) -> None:
        self.failures.append((type(error).__name__, checked_at_ms))


class _NestedShadowFailureOperator(_FakeOperator):
    def __init__(self, *, shadow_message: str) -> None:
        super().__init__()
        self.shadow_message = shadow_message

    def run_once(self, *, observed_at_ms: int) -> int:
        del observed_at_ms
        self.run_calls += 1
        if self.run_calls == 1:
            cause = ShadowRuntimeError(self.shadow_message)
            raise CandidatePaperRuntimeServiceError("candidate PAPER runtime step failed") from cause
        return self.run_calls


def _clock(*values: int):
    iterator = iter(values)
    return lambda: next(iterator)


def test_supervisor_retries_bounded_failures_and_persists_recovery(tmp_path) -> None:
    operator = _FakeOperator(failures_before_success=2)
    sleeps: list[float] = []
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,  # type: ignore[arg-type]
        state_root=tmp_path,
        sleep=sleeps.append,
        wall_clock_ms=_clock(1_000, 1_001, 1_002, 1_003, 1_004),
    )

    assert supervisor.run_cycle() is True
    assert operator.run_calls == 3
    assert sleeps == [5, 5]
    assert operator.failures == []

    payload = json.loads((tmp_path / "cycle-telemetry.json").read_text(encoding="utf-8"))
    assert payload["last_sequence"] == 1
    assert payload["records"][0]["attempt_count"] == 3
    assert payload["records"][0]["transient_failure_count"] == 2
    assert payload["records"][0]["outcome"] == "success"
    assert payload["records"][0]["generation"] == 3
    assert payload["live_capital_authorized"] is False
    assert payload["orders_submitted"] == 0


def test_supervisor_retries_only_nested_future_source_state_race(tmp_path) -> None:
    operator = _NestedShadowFailureOperator(
        shadow_message="source state is observed in the future"
    )
    sleeps: list[float] = []
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,  # type: ignore[arg-type]
        state_root=tmp_path,
        sleep=sleeps.append,
        wall_clock_ms=_clock(1_000, 1_001, 1_002, 1_003),
    )

    assert supervisor.run_cycle() is True
    assert operator.run_calls == 2
    assert sleeps == [5]
    assert operator.failures == []

    payload = json.loads((tmp_path / "cycle-telemetry.json").read_text(encoding="utf-8"))
    record = payload["records"][0]
    assert record["attempt_count"] == 2
    assert record["transient_failure_count"] == 1
    assert record["errors"][0]["code"] == "CandidatePaperRuntimeServiceError"
    assert record["errors"][0]["retryable"] is True
    assert record["outcome"] == "success"
    assert record["generation"] == 2


def test_supervisor_does_not_retry_other_nested_shadow_failures(tmp_path) -> None:
    operator = _NestedShadowFailureOperator(shadow_message="runtime identity mismatch")
    sleeps: list[float] = []
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,  # type: ignore[arg-type]
        state_root=tmp_path,
        sleep=sleeps.append,
        wall_clock_ms=_clock(1_000, 1_001, 1_002),
    )

    assert supervisor.run_cycle() is False
    assert operator.run_calls == 1
    assert sleeps == []
    assert operator.failures == [("CandidatePaperRuntimeServiceError", 1_002)]

    payload = json.loads((tmp_path / "cycle-telemetry.json").read_text(encoding="utf-8"))
    record = payload["records"][0]
    assert record["attempt_count"] == 1
    assert record["transient_failure_count"] == 1
    assert record["errors"][0]["retryable"] is False
    assert record["outcome"] == "fail_closed"
    assert record["generation"] is None


def test_supervisor_seals_irrecoverable_snapshot_gap_before_next_tick(tmp_path) -> None:
    operator = _FakeOperator(observed_at_ms=(1_000,))
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,  # type: ignore[arg-type]
        state_root=tmp_path,
        sleep=lambda _seconds: None,
        wall_clock_ms=lambda: 1_801_001,
    )

    with pytest.raises(CandidatePaperRuntimeEarlyFail):
        supervisor.run_cycle()

    assert operator.run_calls == 0
    assert operator.failures == [("CandidatePaperRuntimeEarlyFail", 1_801_001)]
    sentinel = json.loads((tmp_path / "early-fail.json").read_text(encoding="utf-8"))
    assert sentinel["blocker_code"] == "maximum_snapshot_gap_exceeded"
    assert sentinel["actual_gap_ms"] == 1_800_001
    assert sentinel["recoverable"] is False
    assert sentinel["live_capital_authorized"] is False
    assert sentinel["orders_submitted"] == 0


def test_supervisor_refuses_tampered_cycle_telemetry(tmp_path) -> None:
    path = tmp_path / "cycle-telemetry.json"
    store = CycleTelemetryStore(
        path=path,
        binding_id=BINDING_ID,
        run_id=RUN_ID,
        operator_commit=OPERATOR_COMMIT,
    )
    store.append(
        cycle_started_at_ms=1_000,
        cycle_completed_at_ms=1_010,
        attempt_count=1,
        outcome="success",
        generation=1,
        errors=[],
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"][0]["outcome"] = "fail_closed"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CandidatePaperRuntimeSupervisorError, match="self-hash mismatch"):
        CycleTelemetryStore(
            path=path,
            binding_id=BINDING_ID,
            run_id=RUN_ID,
            operator_commit=OPERATOR_COMMIT,
        )
