from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import ai_platform.wickhunter.candidate_paper_runtime_parity_service as parity_service
from ai_platform.wickhunter.candidate_paper_runtime_service import CandidatePaperRuntimeService
from ai_platform.wickhunter.contracts import ShadowDecisionEvidence, ShadowStatus
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import (
    ReplayShadowParityEvidence,
    ShadowRuntimeStepResult,
    ShadowRuntimeTick,
)


def test_parity_service_replays_and_records_every_allowed_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = cast(
        ShadowDecisionRequest,
        SimpleNamespace(
            market=SimpleNamespace(symbol="BTCUSDT"),
            hypothesis=SimpleNamespace(value="reversal"),
        ),
    )
    original = cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id="1" * 64,
            status=ShadowStatus.SIMULATED_ALLOWED,
        ),
    )
    replayed = cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id=original.shadow_decision_id,
            status=ShadowStatus.SIMULATED_ALLOWED,
        ),
    )
    parity = cast(
        ReplayShadowParityEvidence,
        SimpleNamespace(parity_id="2" * 64),
    )
    result = cast(ShadowRuntimeStepResult, SimpleNamespace(decisions=(original,)))
    recorded: list[ReplayShadowParityEvidence] = []

    service = object.__new__(parity_service.CandidatePaperRuntimeParityService)
    service.binding = SimpleNamespace(bind_request=lambda item: item)
    service.runtime = SimpleNamespace(decision_evaluator=lambda _item: replayed)
    service.journal = SimpleNamespace(record_parity=recorded.append)

    monkeypatch.setattr(CandidatePaperRuntimeService, "step", lambda _self, _tick: result)
    monkeypatch.setattr(
        parity_service,
        "verify_runtime_replay_parity",
        lambda *, shadow_decision, replayed_decision: (
            parity
            if shadow_decision is original and replayed_decision is replayed
            else pytest.fail("unexpected replay pairing")
        ),
    )

    tick = cast(ShadowRuntimeTick, SimpleNamespace(decision_requests=(request,)))
    assert service.step(tick) is result
    assert recorded == [parity]


def test_parity_service_does_not_replay_rejected_decisions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = cast(
        ShadowDecisionRequest,
        SimpleNamespace(
            market=SimpleNamespace(symbol="BTCUSDT"),
            hypothesis=SimpleNamespace(value="reversal"),
        ),
    )
    rejected = cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id="3" * 64,
            status=ShadowStatus.SIMULATED_REJECTED,
        ),
    )
    result = cast(ShadowRuntimeStepResult, SimpleNamespace(decisions=(rejected,)))
    replay_calls: list[ShadowDecisionRequest] = []

    service = object.__new__(parity_service.CandidatePaperRuntimeParityService)
    service.binding = SimpleNamespace(bind_request=lambda item: item)
    service.runtime = SimpleNamespace(decision_evaluator=replay_calls.append)
    service.journal = SimpleNamespace(record_parity=lambda _value: pytest.fail("unexpected parity"))

    monkeypatch.setattr(CandidatePaperRuntimeService, "step", lambda _self, _tick: result)
    tick = cast(ShadowRuntimeTick, SimpleNamespace(decision_requests=(request,)))

    assert service.step(tick) is result
    assert replay_calls == []
