from __future__ import annotations

from uuid import uuid4

from ai_platform.portal.execution.runtime import DriverRuntimeState
from ai_platform.portal.runtime_supervisor import (
    SupervisorOperation,
    SupervisorOutcome,
    SupervisorOutcomeCode,
    SupervisorRequest,
)
from ai_platform.portal.runtime_supervisor.service import RuntimeSupervisor


def _request(**updates: object) -> SupervisorRequest:
    values: dict[str, object] = {
        "tenant_id": "tenant-1",
        "bot_id": "bot-1",
        "generation_id": "generation-1",
        "generation_spec_digest": "a" * 64,
        "operation": SupervisorOperation.INSPECT_GENERATION,
        "command_id": uuid4(),
        "expected_generation_ordinal": 2,
        "expected_state_version": 7,
        "correlation_id": uuid4(),
        "causation_id": uuid4(),
    }
    values.update(updates)
    return SupervisorRequest.model_validate(values)


def _outcome(request: SupervisorRequest) -> SupervisorOutcome:
    return RuntimeSupervisor._outcome(
        request,
        SupervisorOutcomeCode.OBSERVED,
        True,
        DriverRuntimeState.RUNNING,
        7,
    )


def test_outcome_echoes_and_serializes_full_authoritative_request_binding() -> None:
    request = _request()
    outcome = _outcome(request)

    assert outcome.expected_generation_ordinal == request.expected_generation_ordinal
    assert outcome.expected_state_version == request.expected_state_version
    assert outcome.correlation_id == request.correlation_id
    assert outcome.causation_id == request.causation_id

    recovered = SupervisorOutcome.model_validate_json(outcome.model_dump_json())
    assert recovered == outcome


def test_evidence_digest_changes_for_each_new_request_binding_field() -> None:
    request = _request()
    baseline = _outcome(request).evidence_digest

    variants = [
        request.model_copy(update={"expected_generation_ordinal": 3}),
        request.model_copy(update={"expected_state_version": 8}),
        request.model_copy(update={"correlation_id": uuid4()}),
        request.model_copy(update={"causation_id": uuid4()}),
    ]

    assert all(_outcome(candidate).evidence_digest != baseline for candidate in variants)
