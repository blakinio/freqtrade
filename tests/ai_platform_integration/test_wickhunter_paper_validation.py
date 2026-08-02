from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    ShadowStatus,
    SourceHealth,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import LabelOutcome
from ai_platform.wickhunter.paper_validation import (
    EXERCISE_SCHEMA_VERSION,
    PaperValidationError,
    PaperValidationOutcome,
    PaperValidationPolicy,
    SafetyExerciseEvidence,
    SafetyExerciseKind,
    build_paper_run_request,
    evaluate_paper_evidence,
    publish_paper_run_request,
    publish_paper_validation_package,
    verify_paper_run_request,
    verify_paper_validation_package,
)
from ai_platform.wickhunter.shadow_runtime import (
    PortalObservabilitySnapshot,
    ReplayShadowParityEvidence,
    RuntimeDecisionSummary,
    RuntimeHealth,
    RuntimeSourceStatus,
    SimulatedPosition,
)


MODEL_HASH = "1" * 64
PARAMETER_HASH = "2" * 64
DATASET_HASH = "3" * 64
CODE_SHA = "4" * 40
ROLLBACK_MODEL_HASH = "5" * 64
ROLLBACK_PARAMETER_HASH = "6" * 64
BOT_INSTANCE = "wickhunter-paper-1"


def _write_canonical_json(path, payload: dict[str, object]) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _refresh_derived_identity(
    payload: dict[str, object],
    identity_field: str,
) -> None:
    body = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", identity_field}
    }
    payload[identity_field] = canonical_sha256(
        {"schema_version": payload["schema_version"], "payload": body}
    )


def _refresh_manifest_and_checksums(destination, manifest_name: str) -> None:
    manifest_path = destination / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_names = [item[0] for item in manifest["artifacts"]]
    manifest["artifacts"] = [
        [name, hashlib.sha256((destination / name).read_bytes()).hexdigest()]
        for name in artifact_names
    ]
    manifest_body = {
        key: value
        for key, value in manifest.items()
        if key not in {"schema_version", "manifest_sha256"}
    }
    manifest["manifest_sha256"] = canonical_sha256(
        {"schema_version": manifest["schema_version"], "payload": manifest_body}
    )
    _write_canonical_json(manifest_path, manifest)
    indexed_names = [*artifact_names, manifest_name]
    checksum_text = "".join(
        f"{hashlib.sha256((destination / name).read_bytes()).hexdigest()}  {name}\n"
        for name in indexed_names
    )
    (destination / "artifact-sha256.txt").write_text(
        checksum_text,
        encoding="utf-8",
    )


def _policy(**overrides: object) -> PaperValidationPolicy:
    return PaperValidationPolicy(**overrides)  # type: ignore[arg-type]


def _request(policy: PaperValidationPolicy, *, window_end_ms: int | None = None):
    return build_paper_run_request(
        created_at_ms=100,
        window_start_ms=1_000,
        window_end_ms=(
            window_end_ms if window_end_ms is not None else 1_000 + policy.minimum_duration_ms
        ),
        bot_instance=BOT_INSTANCE,
        mode=BotMode.PAPER,
        model_version="wickhunter-lightgbm-v1",
        model_hash=MODEL_HASH,
        parameter_version="wickhunter-parameters-v1",
        parameter_hash=PARAMETER_HASH,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
        rollback_model_version="wickhunter-lightgbm-rollback-v1",
        rollback_model_hash=ROLLBACK_MODEL_HASH,
        rollback_parameter_version="wickhunter-parameters-rollback-v1",
        rollback_parameter_hash=ROLLBACK_PARAMETER_HASH,
        wh08_consumer_version="wickhunter-portal-observability-v1",
        policy=policy,
    )


def _snapshot(observed_at_ms: int, generation: int) -> PortalObservabilitySnapshot:
    allowed_id = canonical_sha256({"allowed": observed_at_ms})
    rejected_id = canonical_sha256({"rejected": observed_at_ms})
    return PortalObservabilitySnapshot(
        schema_version="wickhunter-portal-observability-snapshot-v1",
        snapshot_id=canonical_sha256({"snapshot": observed_at_ms}),
        bot_instance=BOT_INSTANCE,
        mode=BotMode.PAPER,
        health=RuntimeHealth.HEALTHY,
        observed_at_ms=observed_at_ms,
        universe_snapshot_hash=canonical_sha256({"universe": observed_at_ms}),
        dynamic_universe=("BTCUSDT",),
        source_freshness=(
            RuntimeSourceStatus(
                source="bybit-linear",
                health=SourceHealth.HEALTHY,
                observed_at_ms=observed_at_ms,
                last_received_at_ms=observed_at_ms - 10,
                age_ms=10,
                fresh=True,
            ),
        ),
        model_version="wickhunter-lightgbm-v1",
        model_hash=MODEL_HASH,
        parameter_version="wickhunter-parameters-v1",
        parameter_hash=PARAMETER_HASH,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
        decisions=(
            RuntimeDecisionSummary(
                shadow_decision_id=allowed_id,
                status=ShadowStatus.SIMULATED_ALLOWED,
                symbol="BTCUSDT",
                side=TradeDirection.LONG,
                candidate_id=canonical_sha256({"candidate": observed_at_ms}),
                score_id=canonical_sha256({"score": observed_at_ms}),
                risk_decision_id=canonical_sha256({"risk": observed_at_ms}),
                reason_codes=("risk_allowed",),
                observed_at_ms=observed_at_ms,
            ),
            RuntimeDecisionSummary(
                shadow_decision_id=rejected_id,
                status=ShadowStatus.SIMULATED_REJECTED,
                symbol="BTCUSDT",
                side=TradeDirection.SHORT,
                candidate_id=canonical_sha256({"candidate-rejected": observed_at_ms}),
                score_id=canonical_sha256({"score-rejected": observed_at_ms}),
                risk_decision_id=canonical_sha256({"risk-rejected": observed_at_ms}),
                reason_codes=("portfolio_heat_limit",),
                observed_at_ms=observed_at_ms,
            ),
        ),
        positions=(
            SimulatedPosition(
                position_id=canonical_sha256({"position": observed_at_ms}),
                trade_intent_id=canonical_sha256({"intent": observed_at_ms}),
                symbol="BTCUSDT",
                side=TradeDirection.LONG,
                opened_at_ms=observed_at_ms,
                entry_price=Decimal(100),
                mark_price=Decimal(101),
                quantity=Decimal(1),
                take_profit_price=Decimal(102),
                stop_loss_price=Decimal(99),
                model_version="wickhunter-lightgbm-v1",
                model_hash=MODEL_HASH,
                parameter_version="wickhunter-parameters-v1",
                parameter_hash=PARAMETER_HASH,
            ),
        ),
        cumulative_realized_pnl_quote=Decimal(generation),
        unrealized_pnl_quote=Decimal(1),
        simulated_equity_quote=Decimal(10000) + Decimal(generation),
        drawdown_ratio=Decimal("0.01"),
        retraining_state="idle",
        validation_state="candidate_only",
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        circuit_breaker_active=False,
        circuit_breaker_reasons=(),
        persistence_generation=generation,
        runtime_state_sha256=canonical_sha256({"state": observed_at_ms}),
    )


def _parity(snapshot: PortalObservabilitySnapshot) -> ReplayShadowParityEvidence:
    decision = snapshot.decisions[0]
    schema_version = "wickhunter-replay-shadow-parity-v1"
    label_id = canonical_sha256({"label": snapshot.observed_at_ms})
    payload = {
        "shadow_decision_id": decision.shadow_decision_id,
        "label_id": label_id,
        "symbol": "BTCUSDT",
        "side": TradeDirection.LONG.value,
        "decision_timestamp_ms": snapshot.observed_at_ms,
        "dataset_hash": DATASET_HASH,
        "code_sha": CODE_SHA,
        "take_profit_ratio": Decimal("0.02"),
        "stop_loss_ratio": Decimal("0.01"),
        "label_outcome": LabelOutcome.TAKE_PROFIT.value,
        "identities_match": True,
        "policy_match": True,
        "execution_authority_absent": True,
    }
    return ReplayShadowParityEvidence(
        schema_version=schema_version,
        parity_id=canonical_sha256({"schema_version": schema_version, "payload": payload}),
        shadow_decision_id=decision.shadow_decision_id,
        label_id=label_id,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=snapshot.observed_at_ms,
        dataset_hash=DATASET_HASH,
        code_sha=CODE_SHA,
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        label_outcome=LabelOutcome.TAKE_PROFIT,
        identities_match=True,
        policy_match=True,
        execution_authority_absent=True,
    )


def _exercises(
    run_id: str,
    snapshot_id: str,
    observed_at_ms: int,
) -> tuple[SafetyExerciseEvidence, ...]:
    reasons = {
        SafetyExerciseKind.CIRCUIT_BREAKER: "maximum_drawdown_exceeded",
        SafetyExerciseKind.MODEL_DRIFT: "model_drift_not_healthy",
        SafetyExerciseKind.RESTART_RECOVERY: "restart_state_hash_verified",
        SafetyExerciseKind.STALE_SOURCE: "source_unhealthy_or_stale:bybit-linear",
    }
    return tuple(
        SafetyExerciseEvidence(
            schema_version=EXERCISE_SCHEMA_VERSION,
            exercise_id=canonical_sha256({"exercise": kind.value, "run_id": run_id}),
            run_id=run_id,
            kind=kind,
            observed_at_ms=observed_at_ms,
            source_snapshot_id=snapshot_id,
            expected_reason=reasons[kind],
            observed_reasons=(reasons[kind],),
            passed=True,
            state_recovered=True,
        )
        for kind in sorted(SafetyExerciseKind, key=lambda item: item.value)
    )


def _accepted_inputs():
    policy = _policy()
    interval_ms = (policy.minimum_duration_ms + policy.minimum_snapshot_count - 2) // (
        policy.minimum_snapshot_count - 1
    )
    observed_at_values = tuple(
        1_000 + interval_ms * index for index in range(policy.minimum_snapshot_count)
    )
    request = _request(policy, window_end_ms=observed_at_values[-1])
    snapshots = tuple(_snapshot(value, index) for index, value in enumerate(observed_at_values, 1))
    parity = tuple(_parity(snapshot) for snapshot in snapshots)
    exercises = _exercises(
        request.run_id,
        snapshots[-1].snapshot_id,
        snapshots[-1].observed_at_ms,
    )
    return policy, request, snapshots, parity, exercises


def test_default_policy_requires_real_sustained_window() -> None:
    policy = PaperValidationPolicy()
    assert policy.minimum_duration_ms == 86_400_000
    assert policy.minimum_snapshot_count == 96


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"minimum_duration_ms": 86_399_999}, "minimum_duration_ms"),
        ({"minimum_snapshot_count": 95}, "minimum_snapshot_count"),
        ({"maximum_snapshot_gap_ms": 1_800_001}, "maximum_snapshot_gap_ms"),
        (
            {"minimum_fresh_source_ratio": Decimal("0.98")},
            "minimum_fresh_source_ratio",
        ),
        ({"maximum_drawdown_ratio": Decimal("0.21")}, "maximum_drawdown_ratio"),
        (
            {
                "required_exercises": tuple(
                    item
                    for item in sorted(SafetyExerciseKind, key=lambda value: value.value)
                    if item is not SafetyExerciseKind.STALE_SOURCE
                )
            },
            "required_exercises",
        ),
    ),
)
def test_terminal_policy_cannot_be_weakened(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(PaperValidationError, match=message):
        PaperValidationPolicy(**overrides)  # type: ignore[arg-type]


def test_activation_package_is_immutable_and_verified(tmp_path) -> None:
    policy = _policy()
    request = _request(policy)
    destination = tmp_path / "activation"
    result = publish_paper_run_request(destination, request=request, policy=policy)
    assert result == {"run_id": request.run_id, "verified": True}
    assert verify_paper_run_request(destination)["verified"] is True
    with pytest.raises(PaperValidationError, match="overwrite"):
        publish_paper_run_request(destination, request=request, policy=policy)


def test_activation_window_cannot_be_shorter_than_policy() -> None:
    policy = _policy()
    with pytest.raises(PaperValidationError, match="shorter than policy"):
        _request(policy, window_end_ms=5_000)


def test_activation_rejects_coordinated_weak_policy_rewrite(tmp_path) -> None:
    policy = _policy()
    request = _request(policy)
    destination = tmp_path / "activation-rewrite"
    publish_paper_run_request(destination, request=request, policy=policy)
    policy_payload = json.loads((destination / "policy.json").read_text(encoding="utf-8"))
    policy_payload["minimum_duration_ms"] = 1
    _write_canonical_json(destination / "policy.json", policy_payload)
    policy_sha256 = canonical_sha256(policy_payload)
    request_payload = json.loads((destination / "request.json").read_text(encoding="utf-8"))
    request_payload["policy_sha256"] = policy_sha256
    _refresh_derived_identity(request_payload, "run_id")
    _write_canonical_json(destination / "request.json", request_payload)
    manifest_path = destination / "activation-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["run_id"] = request_payload["run_id"]
    manifest["policy_sha256"] = policy_sha256
    _write_canonical_json(manifest_path, manifest)
    _refresh_manifest_and_checksums(destination, "activation-manifest.json")
    with pytest.raises(PaperValidationError, match="minimum_duration_ms"):
        verify_paper_run_request(destination)


def test_sustained_paper_evidence_creates_owner_review_package() -> None:
    policy, request, snapshots, parity, exercises = _accepted_inputs()
    result = evaluate_paper_evidence(
        request=request,
        policy=policy,
        snapshots=snapshots,
        parity_evidence=parity,
        safety_exercises=exercises,
    )
    assert result.report.outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW
    assert result.report.blocker_codes == ()
    assert result.candidate_review.eligible_for_owner_review
    assert result.candidate_review.owner_decision_required
    assert not result.candidate_review.automatic_promotion_enabled
    assert result.candidate_review.orders_submitted == 0
    assert not result.candidate_review.live_capital_authorized
    assert result.report.summary.snapshot_count == policy.minimum_snapshot_count
    assert result.report.summary.parity_count == policy.minimum_snapshot_count


def test_insufficient_window_remains_incomplete() -> None:
    policy, request, snapshots, parity, _old_exercises = _accepted_inputs()
    short_snapshots = snapshots[:-1]
    result = evaluate_paper_evidence(
        request=request,
        policy=policy,
        snapshots=short_snapshots,
        parity_evidence=parity[:-1],
        safety_exercises=_exercises(
            request.run_id,
            short_snapshots[-1].snapshot_id,
            short_snapshots[-1].observed_at_ms,
        ),
    )
    assert result.report.outcome is PaperValidationOutcome.INCOMPLETE
    assert "minimum_duration_not_met" in result.report.blocker_codes
    assert "minimum_snapshot_count_not_met" in result.report.blocker_codes
    assert not result.candidate_review.eligible_for_owner_review


def test_identity_mismatch_is_rejected() -> None:
    policy, request, snapshots, parity, exercises = _accepted_inputs()
    changed = replace(snapshots[0], model_hash="0" * 64)
    with pytest.raises(PaperValidationError, match="model_hash"):
        evaluate_paper_evidence(
            request=request,
            policy=policy,
            snapshots=(changed, *snapshots[1:]),
            parity_evidence=parity,
            safety_exercises=exercises,
        )


def test_missing_parity_and_exercises_remain_incomplete() -> None:
    policy, request, snapshots, parity, exercises = _accepted_inputs()
    result = evaluate_paper_evidence(
        request=request,
        policy=policy,
        snapshots=snapshots,
        parity_evidence=parity[:-1],
        safety_exercises=exercises[:-1],
    )
    assert "replay_shadow_parity_incomplete" in result.report.blocker_codes
    assert "required_safety_exercises_incomplete" in result.report.blocker_codes


def test_package_is_immutable_and_tamper_evident(tmp_path) -> None:
    policy, request, snapshots, parity, exercises = _accepted_inputs()
    destination = tmp_path / "paper-validation"
    result = publish_paper_validation_package(
        destination,
        request=request,
        policy=policy,
        snapshots=snapshots,
        parity_evidence=parity,
        safety_exercises=exercises,
    )
    verification = verify_paper_validation_package(destination)
    assert verification["verified"] is True
    assert verification["report_id"] == result.report.report_id
    with pytest.raises(PaperValidationError, match="overwrite"):
        publish_paper_validation_package(
            destination,
            request=request,
            policy=policy,
            snapshots=snapshots,
            parity_evidence=parity,
            safety_exercises=exercises,
        )
    report = json.loads((destination / "report.json").read_text(encoding="utf-8"))
    report["outcome"] = "ready_for_owner_review_modified"
    (destination / "report.json").write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(PaperValidationError, match="checksum"):
        verify_paper_validation_package(destination)


def test_package_rejects_coordinated_report_rewrite(tmp_path) -> None:
    policy, request, snapshots, parity, exercises = _accepted_inputs()
    destination = tmp_path / "paper-validation-rewrite"
    publish_paper_validation_package(
        destination,
        request=request,
        policy=policy,
        snapshots=snapshots,
        parity_evidence=parity,
        safety_exercises=exercises,
    )
    report_path = destination / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["outcome"] = "incomplete"
    report["blocker_codes"] = ["forged_blocker"]
    report["candidate_review_eligible"] = False
    _refresh_derived_identity(report, "report_id")
    _write_canonical_json(report_path, report)
    review_path = destination / "candidate-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["report_id"] = report["report_id"]
    review["eligible_for_owner_review"] = False
    _refresh_derived_identity(review, "package_id")
    _write_canonical_json(review_path, review)
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["report_id"] = report["report_id"]
    manifest["candidate_review_id"] = review["package_id"]
    _write_canonical_json(manifest_path, manifest)
    _refresh_manifest_and_checksums(destination, "manifest.json")
    with pytest.raises(PaperValidationError, match="report semantics mismatch"):
        verify_paper_validation_package(destination)


def test_live_request_is_forbidden() -> None:
    policy = _policy()
    with pytest.raises(PaperValidationError, match="shadow or paper"):
        build_paper_run_request(
            created_at_ms=100,
            window_start_ms=1_000,
            window_end_ms=1_000 + policy.minimum_duration_ms,
            bot_instance=BOT_INSTANCE,
            mode=BotMode.LIVE_BLOCKED,
            model_version="wickhunter-lightgbm-v1",
            model_hash=MODEL_HASH,
            parameter_version="wickhunter-parameters-v1",
            parameter_hash=PARAMETER_HASH,
            dataset_hash=DATASET_HASH,
            code_sha=CODE_SHA,
            rollback_model_version="rollback-model",
            rollback_model_hash=ROLLBACK_MODEL_HASH,
            rollback_parameter_version="rollback-parameters",
            rollback_parameter_hash=ROLLBACK_PARAMETER_HASH,
            wh08_consumer_version="wickhunter-portal-observability-v1",
            policy=policy,
        )
