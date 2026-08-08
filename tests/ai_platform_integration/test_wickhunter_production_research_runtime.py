from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import ai_platform.wickhunter.production_research_runtime as research
from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateAction,
    DriftState,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    ShadowDecisionEvidence,
    ShadowStatus,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
)
from ai_platform.wickhunter.risk import WickHunterRiskContext, WickHunterRiskLimits
from ai_platform.wickhunter.scoring import CandidateScorer
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime_common import ShadowRuntimePolicy
from ai_platform.wickhunter.strategy import SignalMemory
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot

CREATED_AT_MS = 1_800_000_000_000
CODE_SHA = "a" * 40
DATASET_HASH = "b" * 64
MODEL_HASH = "c" * 64
MODEL_ARTIFACT_SHA256 = "d" * 64
MANIFEST_SHA256 = "e" * 64
PARAMETER_HASH = INITIAL_COMPATIBILITY_PRIOR.parameter_hash
PACKAGE_ID = "wickhunter-h900-test-package"


def _identity() -> research.ProductionResearchRunIdentity:
    return research.ProductionResearchRunIdentity(
        schema_version=research.RESEARCH_IDENTITY_SCHEMA,
        run_id=research.canonical_sha256({"package": PACKAGE_ID}),
        bot_instance="wickhunter-wh09-production-research",
        mode=BotMode.SHADOW,
        package_id=PACKAGE_ID,
        package_manifest_sha256=MANIFEST_SHA256,
        model_artifact_sha256=MODEL_ARTIFACT_SHA256,
        model_version="wickhunter-lightgbm-test",
        model_hash=MODEL_HASH,
        parameter_version=INITIAL_COMPATIBILITY_PRIOR.parameter_version,
        parameter_hash=PARAMETER_HASH,
        dataset_hash=DATASET_HASH,
        model_source_commit=CODE_SHA,
        no_trade_confidence=Decimal("0.60"),
        outcome_horizon_ms=900_000,
    )


def _journal_request() -> ShadowDecisionRequest:
    return cast(
        ShadowDecisionRequest,
        SimpleNamespace(
            market=SimpleNamespace(
                symbol="BTCUSDT",
                decision_timestamp_ms=CREATED_AT_MS,
                decision_price=Decimal("100"),
                completed_candle_close_ms=CREATED_AT_MS - 1,
                metrics=(),
            ),
            hypothesis=StrategyHypothesis.REVERSAL,
        ),
    )


def _journal_evidence() -> ShadowDecisionEvidence:
    return cast(
        ShadowDecisionEvidence,
        SimpleNamespace(
            shadow_decision_id="3" * 64,
            status=ShadowStatus.SIMULATED_REJECTED,
            candidate=SimpleNamespace(
                candidate_id="1" * 64,
                action=CandidateAction.ENTER,
                side=TradeDirection.LONG,
                reason_codes=("candidate_ready",),
            ),
            score=SimpleNamespace(score_id="2" * 64, confidence=Decimal("0.333333")),
            risk_decision=SimpleNamespace(reason_codes=("MODEL_NOT_APPROVED",)),
            feature_hash="4" * 64,
            created_at_ms=CREATED_AT_MS,
        ),
    )


def test_journal_records_no_trade_and_delays_h900_outcome(tmp_path: Path) -> None:
    journal = research.ProductionResearchJournal(tmp_path / "journal", _identity())
    request = _journal_request()
    evidence = _journal_evidence()
    trace = research.ResearchScoreTrace(
        score_id="2" * 64,
        raw_probability=Decimal("0.331543"),
        calibrated_confidence=Decimal("0.333333"),
    )
    assert journal.record_decisions(
        requests=(request,),
        decisions=(evidence,),
        traces={trace.score_id: trace},
        operator_commit=CODE_SHA,
    ) == 1
    decision_path = journal.root / "decisions" / f"{evidence.shadow_decision_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["final_decision"] == "NO_TRADE"
    assert decision["raw_probability"] == "0.331543"
    assert decision["calibrated_confidence"] == "0.333333"
    assert decision["above_no_trade_confidence"] is False
    assert decision["execution_enabled"] is False
    assert decision["orders_submitted"] == 0

    assert journal.materialize_due_outcomes(
        observed_at_ms=CREATED_AT_MS + 899_999,
        mark_prices={"BTCUSDT": Decimal("110")},
        operator_commit=CODE_SHA,
    ) == 0
    assert journal.materialize_due_outcomes(
        observed_at_ms=CREATED_AT_MS + 900_000,
        mark_prices={"BTCUSDT": Decimal("110")},
        operator_commit=CODE_SHA,
    ) == 1
    outcome = json.loads(
        (journal.root / "outcomes" / f"{evidence.shadow_decision_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert outcome["observation_delay_ms"] == 0
    assert outcome["directional_return_ratio"] == "0.10000000"
    assert outcome["positive_outcome"] is True
    assert outcome["deterministic_replay_equivalent"] is False
    assert outcome["execution_enabled"] is False
    assert outcome["orders_submitted"] == 0
    assert journal.materialize_due_outcomes(
        observed_at_ms=CREATED_AT_MS + 960_000,
        mark_prices={"BTCUSDT": Decimal("120")},
        operator_commit=CODE_SHA,
    ) == 0


def test_journal_rejects_tampered_immutable_decision(tmp_path: Path) -> None:
    journal = research.ProductionResearchJournal(tmp_path / "journal", _identity())
    evidence = _journal_evidence()
    trace = research.ResearchScoreTrace(
        score_id="2" * 64,
        raw_probability=Decimal("0.331543"),
        calibrated_confidence=Decimal("0.333333"),
    )
    journal.record_decisions(
        requests=(_journal_request(),),
        decisions=(evidence,),
        traces={trace.score_id: trace},
        operator_commit=CODE_SHA,
    )
    path = journal.root / "decisions" / f"{evidence.shadow_decision_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["calibrated_confidence"] = "0.99"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(research.ProductionResearchRuntimeError, match="self-hash mismatch"):
        journal.materialize_due_outcomes(
            observed_at_ms=CREATED_AT_MS + 900_000,
            mark_prices={"BTCUSDT": Decimal("110")},
            operator_commit=CODE_SHA,
        )


def _risk_context(*, authorized: bool = False) -> WickHunterRiskContext:
    return WickHunterRiskContext(
        evaluated_at_ms=CREATED_AT_MS,
        global_kill_switch_active=False,
        circuit_breaker_active=False,
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        projected_concurrent_positions=0,
        projected_symbol_exposure_ratio=Decimal("0"),
        projected_correlated_exposure_ratio=Decimal("0"),
        projected_directional_exposure_ratio=Decimal("0"),
        daily_loss_ratio=Decimal("0"),
        drawdown_ratio=Decimal("0"),
        consecutive_losses=0,
        consecutive_loss_cooldown_until_ms=None,
        symbol_cooldown_until_ms=None,
        setup_still_valid=True,
        dca_adverse_condition_met=True,
        dca_timing_condition_met=True,
        spread_bps=Decimal("0"),
        quote_volume_usd=Decimal("1000000"),
        candidate_paper_validation_authorized=authorized,
    )


def _shadow_request(*, authorized: bool = False, mode: BotMode = BotMode.SHADOW) -> ShadowDecisionRequest:
    return ShadowDecisionRequest(
        bot_instance="wickhunter-wh09-production-research",
        mode=mode,
        events=(),
        market=cast(
            MarketContextSnapshot,
            SimpleNamespace(symbol="BTCUSDT", decision_timestamp_ms=CREATED_AT_MS),
        ),
        history=cast(LiquidationHistorySnapshot, object()),
        source_states=cast(tuple[LiquidationSourceState, ...], ()),
        universe=cast(DynamicUniverseSnapshot, object()),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        hypothesis=StrategyHypothesis.REVERSAL,
        scorer=cast(CandidateScorer, object()),
        signal_memory=cast(SignalMemory, object()),
        risk_limits=cast(WickHunterRiskLimits, object()),
        risk_context=_risk_context(authorized=authorized),
        dataset_hash="f" * 64,
        code_sha="f" * 40,
    )


def _fake_package(*, threshold: Decimal = Decimal("0.60")) -> SimpleNamespace:
    identity = SimpleNamespace(
        package_id=PACKAGE_ID,
        manifest_sha256=MANIFEST_SHA256,
        source_commit_sha=CODE_SHA,
        model_artifact_sha256=MODEL_ARTIFACT_SHA256,
        model_version="wickhunter-lightgbm-test",
        model_hash=MODEL_HASH,
        parameter_version=INITIAL_COMPATIBILITY_PRIOR.parameter_version,
        parameter_hash=PARAMETER_HASH,
    )
    artifact = SimpleNamespace(
        training_policy=SimpleNamespace(no_trade_confidence=threshold),
        parameter_sha256=PARAMETER_HASH,
        dataset_manifest_sha256=DATASET_HASH,
        model_version=identity.model_version,
        model_hash=identity.model_hash,
    )
    return SimpleNamespace(
        identity=identity,
        model_artifact=artifact,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
    )


def _binding(monkeypatch: pytest.MonkeyPatch, *, threshold: Decimal = Decimal("0.60")) -> research.ProductionResearchRuntimeBinding:
    package = _fake_package(threshold=threshold)
    monkeypatch.setattr(research, "load_verified_candidate_package", lambda _root: package)
    monkeypatch.setattr(
        research,
        "LightGBMAdvisoryScorer",
        lambda artifact: cast(research.LightGBMAdvisoryScorer, SimpleNamespace(artifact=artifact)),
    )
    return research.build_production_research_runtime_binding(
        model_root=Path("/tmp/model"),
        expected_package_id=PACKAGE_ID,
        expected_manifest_sha256=MANIFEST_SHA256,
        expected_model_artifact_sha256=MODEL_ARTIFACT_SHA256,
        expected_model_hash=MODEL_HASH,
        expected_parameter_hash=PARAMETER_HASH,
    )


def test_binding_stays_shadow_and_never_enables_paper_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    binding = _binding(monkeypatch)
    bound = binding.bind_request(_shadow_request())
    assert bound.mode is BotMode.SHADOW
    assert bound.risk_context.candidate_paper_validation_authorized is False
    assert bound.scorer is binding.scorer
    assert bound.dataset_hash == DATASET_HASH
    assert bound.code_sha == CODE_SHA
    with pytest.raises(
        research.ProductionResearchRuntimeError,
        match="cannot inherit candidate PAPER authorization",
    ):
        binding.bind_request(_shadow_request(authorized=True))
    with pytest.raises(research.ProductionResearchRuntimeError, match="mode must be SHADOW"):
        binding.bind_request(_shadow_request(mode=BotMode.RESEARCH))


def test_binding_rejects_threshold_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(research.ProductionResearchRuntimeError, match="frozen 0.60"):
        _binding(monkeypatch, threshold=Decimal("0.59"))


def test_service_restores_persisted_shadow_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binding = _binding(monkeypatch)
    policy = ShadowRuntimePolicy(
        policy_version="test-research-runtime-v1",
        simulated_initial_equity_quote=Decimal("10000"),
        maximum_universe_age_ms=300_000,
        maximum_source_age_ms=300_000,
        minimum_healthy_sources=1,
        maximum_open_positions=4,
        maximum_drawdown_ratio=Decimal("0.20"),
        decision_history_limit=1000,
    )
    first = research.ProductionResearchRuntimeService.create(
        binding=binding,
        journal_root=tmp_path / "journal",
        operator_commit=CODE_SHA,
        policy=policy,
    )
    first.journal.runtime_store.save(first.runtime.state)
    second = research.ProductionResearchRuntimeService.create(
        binding=binding,
        journal_root=tmp_path / "journal",
        operator_commit=CODE_SHA,
        policy=policy,
    )
    assert second.runtime.state == first.runtime.state
    assert second.runtime.state.mode is BotMode.SHADOW
