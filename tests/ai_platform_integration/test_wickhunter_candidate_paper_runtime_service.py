from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from ai_platform.wickhunter.candidate_paper_runtime_service import (
    GENERATION_SCHEMA_VERSION,
    CandidatePaperRuntimeService,
    CandidatePaperRuntimeServiceError,
)
from ai_platform.wickhunter.candidate_runtime_binding import (
    CandidatePaperRuntimeBinding,
)
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    LiquidationSourceState,
    ShadowDecisionEvidence,
    ShadowStatus,
    SourceHealth,
    StrategyHypothesis,
)
from ai_platform.wickhunter.paper_validation import (
    PaperValidationPolicy,
    build_paper_run_request,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import (
    ShadowRuntimePolicy,
    ShadowRuntimeTick,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


START_MS = 1_800_000_000_000
CODE_SHA = "a" * 40
DATASET_HASH = "b" * 64
MODEL_HASH = "c" * 64
PARAMETER_HASH = "d" * 64
ROLLBACK_MODEL_HASH = "e" * 64
ROLLBACK_PARAMETER_HASH = "f" * 64


def _paper_policy() -> PaperValidationPolicy:
    return PaperValidationPolicy()


def _runtime_policy(*, policy_version: str = "runtime-v1") -> ShadowRuntimePolicy:
    return ShadowRuntimePolicy(
        policy_version=policy_version,
        simulated_initial_equity_quote=Decimal("1000"),
        maximum_universe_age_ms=60_000,
        maximum_source_age_ms=60_000,
        minimum_healthy_sources=1,
        maximum_open_positions=2,
        maximum_drawdown_ratio=Decimal("0.10"),
    )


def _binding() -> CandidatePaperRuntimeBinding:
    policy = _paper_policy()
    request = build_paper_run_request(
        created_at_ms=START_MS,
        window_start_ms=START_MS,
        window_end_ms=START_MS + 86_700_000,
        bot_instance="wickhunter-paper-v1",
        mode=BotMode.PAPER,
        model_version="wickhunter-model-v1",
        model_hash=MODEL_HASH,
        parameter_version="wickhunter-parameters-v1",
        parameter_hash=PARAMETER_HASH,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
        rollback_model_version="wickhunter-rollback-model-v1",
        rollback_model_hash=ROLLBACK_MODEL_HASH,
        rollback_parameter_version="wickhunter-rollback-parameters-v1",
        rollback_parameter_hash=ROLLBACK_PARAMETER_HASH,
        wh08_consumer_version="wickhunter-portal-consumer-v1",
        policy=policy,
    )
    identity = SimpleNamespace(
        package_id="1" * 64,
        manifest_sha256="2" * 64,
    )
    binding = SimpleNamespace(
        binding_id="3" * 64,
        request=request,
        policy=policy,
        identity=identity,
    )
    binding.bind_request = lambda request_value: request_value
    return cast(CandidatePaperRuntimeBinding, binding)


def _universe(observed_at_ms: int) -> DynamicUniverseSnapshot:
    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version="paper-test-v1",
        selected_at_ms=observed_at_ms,
        decisions=(
            UniverseInstrumentDecision(
                canonical_instrument_id="perpetual:BTCUSDT",
                canonical_symbol="BTCUSDT",
                included=True,
                reason_codes=("eligible",),
            ),
        ),
    )


def _request(
    observed_at_ms: int,
    universe: DynamicUniverseSnapshot,
) -> ShadowDecisionRequest:
    return cast(
        ShadowDecisionRequest,
        SimpleNamespace(
            mode=BotMode.PAPER,
            bot_instance="wickhunter-paper-v1",
            hypothesis=StrategyHypothesis.REVERSAL,
            universe=universe,
            market=SimpleNamespace(
                symbol="BTCUSDT",
                decision_timestamp_ms=observed_at_ms,
            ),
        ),
    )


def _tick(observed_at_ms: int, *, include_decision: bool = True) -> ShadowRuntimeTick:
    universe = _universe(observed_at_ms)
    requests = (_request(observed_at_ms, universe),) if include_decision else ()
    return ShadowRuntimeTick(
        observed_at_ms=observed_at_ms,
        universe=universe,
        decision_requests=requests,
        mark_prices=(("BTCUSDT", Decimal("100")),),
        source_states=(
            LiquidationSourceState(
                source="binance-usdm",
                health=SourceHealth.HEALTHY,
                coverage_available=True,
                last_received_at_ms=observed_at_ms,
                observed_at_ms=observed_at_ms,
            ),
        ),
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        validation_state="collecting",
        retraining_state="disabled",
    )


def _evaluator(request: ShadowDecisionRequest) -> ShadowDecisionEvidence:
    universe = request.universe
    created_at_ms = request.market.decision_timestamp_ms
    decision_id = canonical_sha256(
        {
            "kind": "paper-test-no-candidate",
            "created_at_ms": created_at_ms,
            "universe": universe.snapshot_hash,
        }
    )
    return ShadowDecisionEvidence(
        schema_version="wickhunter-shadow-decision-v1",
        shadow_decision_id=decision_id,
        status=ShadowStatus.NO_CANDIDATE,
        mode=BotMode.PAPER,
        universe_snapshot_hash=universe.snapshot_hash,
        feature_hash=None,
        candidate=None,
        score=None,
        trade_intent=None,
        risk_decision=None,
        created_at_ms=created_at_ms,
    )


def _service(
    root: Path,
    *,
    runtime_policy: ShadowRuntimePolicy | None = None,
) -> CandidatePaperRuntimeService:
    return CandidatePaperRuntimeService(
        binding=_binding(),
        runtime_policy=runtime_policy or _runtime_policy(),
        journal_root=root,
        decision_evaluator=_evaluator,
    )


def test_journal_recovers_and_continues_contiguous_generations(tmp_path: Path) -> None:
    root = (tmp_path / "paper-journal").resolve()
    service = _service(root)

    first = service.step(_tick(START_MS + 1_000))
    assert first.state.generation == 1
    assert first.snapshot.model_hash == MODEL_HASH
    assert len(service.journal.observations()) == 1

    recovered = _service(root)
    assert recovered.runtime.state.generation == 1
    second = recovered.step(_tick(START_MS + 2_000))

    assert second.state.generation == 2
    assert [item.persistence_generation for item in recovered.journal.observations()] == [1, 2]
    assert (root / "generations" / "00000000000000000001").is_dir()
    assert (root / "generations" / "00000000000000000002").is_dir()


def test_identity_seed_allows_observation_without_directional_decision(tmp_path: Path) -> None:
    root = (tmp_path / "empty-decision-journal").resolve()
    service = _service(root)

    result = service.step(_tick(START_MS + 1_000, include_decision=False))
    observation = service.journal.observations()[0]

    assert result.state.model_hash == MODEL_HASH
    assert observation.model_hash == MODEL_HASH
    assert observation.decision_count == 0
    assert observation.allowed_decision_ids == ()
    assert observation.risk_rejection_decision_ids == ()
    assert observation.ignored_decision_ids == ()


def test_recovery_rejects_runtime_policy_substitution(tmp_path: Path) -> None:
    root = (tmp_path / "policy-journal").resolve()
    service = _service(root)
    service.step(_tick(START_MS + 1_000))

    with pytest.raises(
        CandidatePaperRuntimeServiceError,
        match="journal identity",
    ):
        _service(root, runtime_policy=_runtime_policy(policy_version="runtime-v2"))


def test_tampering_is_detected_before_recovery(tmp_path: Path) -> None:
    root = (tmp_path / "tampered-journal").resolve()
    service = _service(root)
    service.step(_tick(START_MS + 1_000))
    observation_path = root / "generations" / "00000000000000000001" / "paper-observation.json"
    observation_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        CandidatePaperRuntimeServiceError,
        match="checksum mismatch",
    ):
        _service(root)


def _rewrite_generation_manifest_field(
    generation_root: Path,
    *,
    field: str,
    value: object,
) -> None:
    manifest_path = generation_root / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload[field] = value
    body = {
        key: item
        for key, item in payload.items()
        if key not in {"schema_version", "manifest_sha256"}
    }
    payload["manifest_sha256"] = canonical_sha256(
        {"schema_version": GENERATION_SCHEMA_VERSION, "payload": body}
    )
    manifest_path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    index_path = generation_root / "artifact-sha256.txt"
    lines = [
        f"{digest}  manifest.json" if line.endswith("  manifest.json") else line
        for line in index_path.read_text(encoding="utf-8").splitlines()
    ]
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("previous_manifest_sha256", "9" * 64, "generation chain identity"),
        ("runtime_policy_sha256", "8" * 64, "runtime policy identity"),
        ("observation_sha256", "7" * 64, "observation identity"),
    ),
)
def test_recovery_rejects_generation_manifest_identity_substitution(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    root = (tmp_path / f"manifest-{field}").resolve()
    service = _service(root)
    service.step(_tick(START_MS + 1_000))
    service.step(_tick(START_MS + 2_000))
    generation_root = root / "generations" / "00000000000000000002"
    _rewrite_generation_manifest_field(
        generation_root,
        field=field,
        value=value,
    )

    with pytest.raises(CandidatePaperRuntimeServiceError, match=message):
        _service(root)


def test_finalize_refuses_before_prospective_window_elapsed(tmp_path: Path) -> None:
    root = (tmp_path / "early-finalize-journal").resolve()
    service = _service(root)
    service.step(_tick(START_MS + 1_000))

    with pytest.raises(
        CandidatePaperRuntimeServiceError,
        match="window has not elapsed",
    ):
        service.journal.finalize(
            (tmp_path / "final").resolve(),
            finalized_at_ms=START_MS + 10_000,
        )
