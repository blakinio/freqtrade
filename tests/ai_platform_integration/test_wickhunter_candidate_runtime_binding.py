from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import ai_platform.wickhunter.candidate_runtime_binding as runtime_binding
from ai_platform.wickhunter.candidate_activation import (
    VerifiedCandidateIdentity,
    VerifiedCandidatePackage,
)
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    StrategyHypothesis,
)
from ai_platform.wickhunter.lightgbm_scorer import (
    LightGBMAdvisoryScorer,
    LightGBMModelArtifact,
)
from ai_platform.wickhunter.paper_validation import (
    PaperValidationPolicy,
    build_paper_run_request,
    publish_paper_run_request,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
)
from ai_platform.wickhunter.risk import WickHunterRiskContext, WickHunterRiskLimits
from ai_platform.wickhunter.scoring import CandidateScorer
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.strategy import SignalMemory
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot


CREATED_AT_MS = 1_800_000_000_000
WINDOW_DURATION_MS = 86_700_000
CODE_SHA = "a" * 40
DATASET_HASH = "b" * 64
REPLAY_DATASET_HASH = "7" * 64
MODEL_HASH = "c" * 64
MODEL_ARTIFACT_SHA256 = "d" * 64


def _identity(tmp_path: Path) -> VerifiedCandidateIdentity:
    return VerifiedCandidateIdentity(
        package_id="1" * 64,
        manifest_sha256="2" * 64,
        source_commit_sha=CODE_SHA,
        evaluation_sha256=DATASET_HASH,
        parameter_version=INITIAL_COMPATIBILITY_PRIOR.parameter_version,
        parameter_hash=INITIAL_COMPATIBILITY_PRIOR.parameter_hash,
        model_version="wickhunter-lightgbm-candidate-v1",
        model_hash=MODEL_HASH,
        model_artifact_sha256=MODEL_ARTIFACT_SHA256,
        optimizer_result_id="3" * 64,
        comparison_report_id="4" * 64,
        rollback_model_version="wickhunter-rollback-model-v1",
        rollback_model_hash="5" * 64,
        rollback_parameter_version="wickhunter-rollback-parameters-v1",
        rollback_parameter_hash="6" * 64,
        candidate_root=tmp_path / "candidate",
    )


def _artifact(identity: VerifiedCandidateIdentity) -> LightGBMModelArtifact:
    value = SimpleNamespace(
        artifact_sha256=identity.model_artifact_sha256,
        model_version=identity.model_version,
        model_hash=identity.model_hash,
        parameter_version=identity.parameter_version,
        parameter_sha256=identity.parameter_hash,
        dataset_manifest_sha256=REPLAY_DATASET_HASH,
    )
    return cast(LightGBMModelArtifact, value)


def _activation(
    tmp_path: Path,
    identity: VerifiedCandidateIdentity,
    *,
    model_hash: str | None = None,
    rollback_model_hash: str | None = None,
) -> Path:
    policy = PaperValidationPolicy()
    request = build_paper_run_request(
        created_at_ms=CREATED_AT_MS,
        window_start_ms=CREATED_AT_MS,
        window_end_ms=CREATED_AT_MS + WINDOW_DURATION_MS,
        bot_instance="wickhunter-paper-v1",
        mode=BotMode.PAPER,
        model_version=identity.model_version,
        model_hash=model_hash or identity.model_hash,
        parameter_version=identity.parameter_version,
        parameter_hash=identity.parameter_hash,
        dataset_hash=identity.evaluation_sha256,
        code_sha=identity.source_commit_sha,
        rollback_model_version=identity.rollback_model_version,
        rollback_model_hash=(rollback_model_hash or identity.rollback_model_hash),
        rollback_parameter_version=identity.rollback_parameter_version,
        rollback_parameter_hash=identity.rollback_parameter_hash,
        wh08_consumer_version="wickhunter-portal-consumer-v1",
        policy=policy,
    )
    root = tmp_path / "activation"
    publish_paper_run_request(root, request=request, policy=policy)
    return root


def _risk_context(
    *,
    evaluated_at_ms: int = CREATED_AT_MS + 1_000,
    authorized: bool = False,
) -> WickHunterRiskContext:
    return WickHunterRiskContext(
        evaluated_at_ms=evaluated_at_ms,
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
        quote_volume_usd=Decimal("1"),
        candidate_paper_validation_authorized=authorized,
    )


def _shadow_request(
    *,
    decision_timestamp_ms: int = CREATED_AT_MS + 500,
    dataset_hash: str = DATASET_HASH,
    risk_context: WickHunterRiskContext | None = None,
) -> ShadowDecisionRequest:
    market = cast(
        MarketContextSnapshot,
        SimpleNamespace(
            symbol="BTCUSDT",
            decision_timestamp_ms=decision_timestamp_ms,
        ),
    )
    return ShadowDecisionRequest(
        bot_instance="wickhunter-paper-v1",
        mode=BotMode.PAPER,
        events=(),
        market=market,
        history=cast(LiquidationHistorySnapshot, object()),
        source_states=cast(tuple[LiquidationSourceState, ...], ()),
        universe=cast(DynamicUniverseSnapshot, object()),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        hypothesis=StrategyHypothesis.REVERSAL,
        scorer=cast(CandidateScorer, object()),
        signal_memory=cast(SignalMemory, object()),
        risk_limits=cast(WickHunterRiskLimits, object()),
        risk_context=risk_context or _risk_context(),
        dataset_hash=dataset_hash,
        code_sha=CODE_SHA,
    )


def _binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    activation_model_hash: str | None = None,
    activation_rollback_model_hash: str | None = None,
) -> runtime_binding.CandidatePaperRuntimeBinding:
    identity = _identity(tmp_path)
    artifact = _artifact(identity)
    package = VerifiedCandidatePackage(
        identity=identity,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        model_artifact=artifact,
    )
    scorer = cast(
        LightGBMAdvisoryScorer,
        SimpleNamespace(artifact=artifact),
    )
    monkeypatch.setattr(
        runtime_binding,
        "load_verified_candidate_package",
        lambda _root: package,
    )
    monkeypatch.setattr(
        runtime_binding,
        "LightGBMAdvisoryScorer",
        lambda _artifact: scorer,
    )
    return runtime_binding.build_candidate_paper_runtime_binding(
        candidate_root=identity.candidate_root,
        activation_root=_activation(
            tmp_path,
            identity,
            model_hash=activation_model_hash,
            rollback_model_hash=activation_rollback_model_hash,
        ),
    )


def test_verified_activation_binds_candidate_scorer_and_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(tmp_path, monkeypatch)
    request = _shadow_request()

    bound = binding.bind_request(request)

    assert bound.scorer is binding.scorer
    assert bound.parameters == INITIAL_COMPATIBILITY_PRIOR
    assert bound.parameter_bounds == DEFAULT_RESEARCH_BOUNDS
    assert bound.dataset_hash == REPLAY_DATASET_HASH
    assert binding.request.dataset_hash == DATASET_HASH
    assert bound.risk_context.candidate_paper_validation_authorized is True
    assert request.risk_context.candidate_paper_validation_authorized is False


def test_binding_rejects_activation_identity_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(
        runtime_binding.CandidateRuntimeBindingError,
        match="model_hash",
    ):
        _binding(tmp_path, monkeypatch, activation_model_hash="e" * 64)


def test_binding_rejects_rollback_identity_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(
        runtime_binding.CandidateRuntimeBindingError,
        match="rollback model_hash",
    ):
        _binding(
            tmp_path,
            monkeypatch,
            activation_rollback_model_hash="e" * 64,
        )


@pytest.mark.parametrize(
    ("shadow_request", "message"),
    (
        (
            _shadow_request(dataset_hash="f" * 64),
            "dataset identity",
        ),
        (
            _shadow_request(
                decision_timestamp_ms=CREATED_AT_MS + WINDOW_DURATION_MS,
                risk_context=_risk_context(evaluated_at_ms=CREATED_AT_MS + WINDOW_DURATION_MS),
            ),
            "outside the activation window",
        ),
        (
            _shadow_request(risk_context=_risk_context(authorized=True)),
            "already enabled",
        ),
    ),
)
def test_binding_rejects_unbound_or_pre_authorized_requests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    shadow_request: ShadowDecisionRequest,
    message: str,
) -> None:
    binding = _binding(tmp_path, monkeypatch)

    with pytest.raises(runtime_binding.CandidateRuntimeBindingError, match=message):
        binding.bind_request(shadow_request)


def test_binding_rejects_non_frozen_parameter_bounds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(tmp_path, monkeypatch)
    request = replace(
        _shadow_request(),
        parameter_bounds=replace(
            DEFAULT_RESEARCH_BOUNDS,
            maximum_event_age_ms=replace(
                DEFAULT_RESEARCH_BOUNDS.maximum_event_age_ms,
                maximum=299_999,
            ),
        ),
    )

    with pytest.raises(
        runtime_binding.CandidateRuntimeBindingError,
        match="frozen research bounds",
    ):
        binding.bind_request(request)
