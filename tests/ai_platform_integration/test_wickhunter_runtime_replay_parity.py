from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest

import ai_platform.wickhunter.shadow_runtime_snapshot as runtime_snapshot
from ai_platform.wickhunter.contracts import (
    RiskOutcome,
    ShadowDecisionEvidence,
    ShadowStatus,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import LabelOutcome
from ai_platform.wickhunter.shadow_runtime import ShadowRuntimeError


DATASET_HASH = "d" * 64
CODE_SHA = "a" * 40
ORIGINAL_SHA = "1" * 64
REPLAY_SHA = "2" * 64
PARITY_SHA = "3" * 64


def _allowed(*, shadow_decision_id: str = "4" * 64) -> ShadowDecisionEvidence:
    candidate = SimpleNamespace(
        candidate_id="5" * 64,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=2_000_000,
    )
    intent = SimpleNamespace(
        trade_intent_id="6" * 64,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
        requested_base_risk_ratio=Decimal("0.001"),
        requested_leverage=Decimal("1"),
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        dca_plan=SimpleNamespace(maximum_total_risk_ratio=Decimal("0.001")),
    )
    risk = SimpleNamespace(
        risk_decision_id="7" * 64,
        outcome=RiskOutcome.ALLOW,
        reason_codes=("risk_allowed",),
    )
    return cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id=shadow_decision_id,
            status=ShadowStatus.SIMULATED_ALLOWED,
            candidate=candidate,
            trade_intent=intent,
            risk_decision=risk,
        ),
    )


def test_runtime_replay_parity_records_exact_allowed_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _allowed()
    replayed = _allowed()

    def digest(value: object) -> str:
        if value is original:
            return ORIGINAL_SHA
        if value is replayed:
            return ORIGINAL_SHA
        return PARITY_SHA

    monkeypatch.setattr(runtime_snapshot, "canonical_sha256", digest)

    evidence = runtime_snapshot.verify_runtime_replay_parity(
        shadow_decision=original,
        replayed_decision=replayed,
    )

    assert evidence.shadow_decision_id == original.shadow_decision_id
    assert evidence.label_id == ORIGINAL_SHA
    assert evidence.label_outcome is LabelOutcome.MISSING_ENTRY
    assert evidence.dataset_hash == DATASET_HASH
    assert evidence.code_sha == CODE_SHA
    assert evidence.identities_match is True
    assert evidence.policy_match is True
    assert evidence.execution_authority_absent is True


def test_runtime_replay_parity_rejects_non_identical_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _allowed()
    replayed = _allowed()

    def digest(value: object) -> str:
        if value is original:
            return ORIGINAL_SHA
        if value is replayed:
            return REPLAY_SHA
        return PARITY_SHA

    monkeypatch.setattr(runtime_snapshot, "canonical_sha256", digest)

    with pytest.raises(ShadowRuntimeError, match="parity evidence is not accepted"):
        runtime_snapshot.verify_runtime_replay_parity(
            shadow_decision=original,
            replayed_decision=replayed,
        )
