"""Deterministic research-only ensemble ranking from immutable OOS evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Literal

SchemaVersion = Literal["1.0.0"]
MetricsScope = Literal["oos_trading", "training_only"]
LifecycleState = Literal["experimental", "candidate", "validated"]


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    candidate_id: str
    model_version_id: str
    experiment_id: str
    experiment_result_hash: str
    validation_report_hash: str
    feature_registry_identity: str
    config_identity: str
    data_identity: str
    routing_evidence_hash: str
    oos_timerange: str
    oos_profit: Decimal | None
    oos_stability: Decimal | None
    max_abs_correlation: Decimal | None
    drawdown_contribution: Decimal | None
    calibration_error: Decimal | None
    trade_count: int
    validation_passed: bool
    evidence_immutable: bool
    research_only: bool
    order_submission_performed: bool
    metrics_scope: MetricsScope
    lifecycle_state: LifecycleState = "candidate"
    schema_version: SchemaVersion = "1.0.0"
    protected_holdout_used: bool = False


@dataclass(frozen=True, slots=True)
class RankingManifest:
    manifest_id: str
    feature_registry_identity: str
    config_identity: str
    data_identity: str
    routing_evidence_hash: str
    candidates: tuple[CandidateEvidence, ...]
    schema_version: SchemaVersion = "1.0.0"
    protected_holdout_used: bool = False
    selected_model: str | None = None


@dataclass(frozen=True, slots=True)
class RankingPolicy:
    policy_id: str
    minimum_oos_trades: int = 20
    profit_weight: Decimal = Decimal("1.0")
    correlation_penalty_weight: Decimal = Decimal("0.20")
    instability_penalty_weight: Decimal = Decimal("0.20")
    drawdown_penalty_weight: Decimal = Decimal("0.25")
    calibration_penalty_weight: Decimal = Decimal("0.15")
    score_quantum: Decimal = Decimal("0.000001")
    schema_version: SchemaVersion = "1.0.0"


@dataclass(frozen=True, slots=True)
class CandidateRanking:
    candidate_id: str
    model_version_id: str
    eligible: bool
    score: Decimal | None
    oos_profit_component: Decimal | None
    correlation_penalty: Decimal | None
    instability_penalty: Decimal | None
    drawdown_penalty: Decimal | None
    calibration_penalty: Decimal | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RankingEvidence:
    manifest_hash: str
    evidence_hash: str
    policy_id: str
    policy_hash: str
    manifest_id: str
    feature_registry_identity: str
    config_identity: str
    data_identity: str
    explanation_version: SchemaVersion
    rankings: tuple[CandidateRanking, ...]
    proposed_candidates: tuple[str, ...]
    selected_model: None = None
    promotion_authorized: Literal[False] = False
    execution_authorized: Literal[False] = False
    risk_core_bypassed: Literal[False] = False
    active_model_mutated: Literal[False] = False


def rank_candidates(manifest: RankingManifest, policy: RankingPolicy) -> RankingEvidence:
    """Score candidates without selecting or promoting an active model."""

    common: set[str] = set()
    if not manifest.manifest_id.strip():
        common.add("MANIFEST_ID_MISSING")
    if not policy.policy_id.strip():
        common.add("POLICY_ID_MISSING")
    if manifest.protected_holdout_used:
        common.add("PROTECTED_HOLDOUT_FORBIDDEN")
    if manifest.selected_model is not None:
        common.add("SELECTED_MODEL_MUST_REMAIN_NULL")
    if policy.minimum_oos_trades < 1:
        common.add("MINIMUM_OOS_TRADES_INVALID")
    weights = _weights(policy, common)
    duplicate_ids = {
        item
        for item, count in Counter(
            candidate.candidate_id for candidate in manifest.candidates
        ).items()
        if count > 1
    }

    rows: list[CandidateRanking] = []
    for candidate in sorted(
        manifest.candidates,
        key=lambda item: (item.candidate_id, item.model_version_id),
    ):
        reasons = set(common)
        if candidate.candidate_id in duplicate_ids:
            reasons.add("AMBIGUOUS_CANDIDATE_ID")
        _identity_guards(candidate, manifest, reasons)
        _safety_guards(candidate, policy, reasons)
        profit = _decimal(candidate.oos_profit)
        stability = _bounded(candidate.oos_stability)
        correlation = _bounded(candidate.max_abs_correlation)
        drawdown = _bounded(candidate.drawdown_contribution)
        calibration = _bounded(candidate.calibration_error)
        if profit is None:
            reasons.add("OOS_PROFIT_MISSING_OR_INVALID")
        if stability is None:
            reasons.add("OOS_STABILITY_MISSING_OR_INVALID")
        if correlation is None:
            reasons.add("CORRELATION_MISSING_OR_INVALID")
        if drawdown is None:
            reasons.add("DRAWDOWN_CONTRIBUTION_MISSING_OR_INVALID")
        if calibration is None:
            reasons.add("CALIBRATION_MISSING_OR_INVALID")

        components: tuple[
            Decimal | None,
            Decimal | None,
            Decimal | None,
            Decimal | None,
            Decimal | None,
        ]
        score: Decimal | None = None
        if (
            not reasons
            and weights is not None
            and profit is not None
            and stability is not None
            and correlation is not None
            and drawdown is not None
            and calibration is not None
        ):
            profit_component = _quantize(profit * weights[0], policy.score_quantum)
            correlation_penalty = _quantize(correlation * weights[1], policy.score_quantum)
            instability_penalty = _quantize(
                (Decimal(1) - stability) * weights[2], policy.score_quantum
            )
            drawdown_penalty = _quantize(drawdown * weights[3], policy.score_quantum)
            calibration_penalty = _quantize(calibration * weights[4], policy.score_quantum)
            score = _quantize(
                profit_component
                - correlation_penalty
                - instability_penalty
                - drawdown_penalty
                - calibration_penalty,
                policy.score_quantum,
            )
            components = (
                profit_component,
                correlation_penalty,
                instability_penalty,
                drawdown_penalty,
                calibration_penalty,
            )
        else:
            components = (None, None, None, None, None)
        rows.append(
            CandidateRanking(
                candidate_id=candidate.candidate_id,
                model_version_id=candidate.model_version_id,
                eligible=not reasons,
                score=score,
                oos_profit_component=components[0],
                correlation_penalty=components[1],
                instability_penalty=components[2],
                drawdown_penalty=components[3],
                calibration_penalty=components[4],
                reason_codes=tuple(sorted(reasons)),
            )
        )

    eligible = [row for row in rows if row.eligible and row.score is not None]
    eligible.sort(key=_eligible_key)
    rejected = sorted((row for row in rows if not row.eligible), key=lambda row: row.candidate_id)
    ordered = tuple(eligible + rejected)
    proposed = tuple(row.candidate_id for row in eligible)
    manifest_hash = _manifest_hash(manifest)
    policy_hash = _policy_hash(policy)
    evidence_hash = _sha(
        {
            "manifest_hash": manifest_hash,
            "policy_id": policy.policy_id,
            "policy_hash": policy_hash,
            "rankings": [_ranking_payload(row) for row in ordered],
            "proposed_candidates": proposed,
            "selected_model": None,
            "promotion_authorized": False,
            "execution_authorized": False,
            "risk_core_bypassed": False,
            "active_model_mutated": False,
        }
    )
    return RankingEvidence(
        manifest_hash=manifest_hash,
        evidence_hash=evidence_hash,
        policy_id=policy.policy_id,
        policy_hash=policy_hash,
        manifest_id=manifest.manifest_id,
        feature_registry_identity=manifest.feature_registry_identity,
        config_identity=manifest.config_identity,
        data_identity=manifest.data_identity,
        explanation_version="1.0.0",
        rankings=ordered,
        proposed_candidates=proposed,
    )


def _identity_guards(
    candidate: CandidateEvidence,
    manifest: RankingManifest,
    reasons: set[str],
) -> None:
    for name, value in (
        ("CANDIDATE_ID", candidate.candidate_id),
        ("MODEL_VERSION_ID", candidate.model_version_id),
        ("EXPERIMENT_ID", candidate.experiment_id),
        ("EXPERIMENT_RESULT_HASH", candidate.experiment_result_hash),
        ("VALIDATION_REPORT_HASH", candidate.validation_report_hash),
        ("FEATURE_REGISTRY_IDENTITY", candidate.feature_registry_identity),
        ("CONFIG_IDENTITY", candidate.config_identity),
        ("DATA_IDENTITY", candidate.data_identity),
        ("ROUTING_EVIDENCE_HASH", candidate.routing_evidence_hash),
    ):
        if not value.strip():
            reasons.add(f"{name}_MISSING")
    if not _sha256(candidate.experiment_result_hash):
        reasons.add("EXPERIMENT_RESULT_HASH_INVALID")
    if not _sha256(candidate.validation_report_hash):
        reasons.add("VALIDATION_REPORT_HASH_INVALID")
    if not _sha256(candidate.routing_evidence_hash):
        reasons.add("ROUTING_EVIDENCE_HASH_INVALID")
    if candidate.feature_registry_identity != manifest.feature_registry_identity:
        reasons.add("FEATURE_REGISTRY_IDENTITY_MISMATCH")
    if candidate.config_identity != manifest.config_identity:
        reasons.add("CONFIG_IDENTITY_MISMATCH")
    if candidate.data_identity != manifest.data_identity:
        reasons.add("DATA_IDENTITY_MISMATCH")
    if candidate.routing_evidence_hash != manifest.routing_evidence_hash:
        reasons.add("ROUTING_EVIDENCE_IDENTITY_MISMATCH")


def _safety_guards(
    candidate: CandidateEvidence,
    policy: RankingPolicy,
    reasons: set[str],
) -> None:
    if candidate.protected_holdout_used:
        reasons.add("PROTECTED_HOLDOUT_FORBIDDEN")
    timerange = _timerange(candidate.oos_timerange)
    if timerange is None:
        reasons.add("OOS_TIMERANGE_INVALID")
    elif _protected(timerange):
        reasons.add("PROTECTED_HOLDOUT_TIMERANGE_FORBIDDEN")
    if not candidate.validation_passed:
        reasons.add("VALIDATION_REQUIRED")
    if not candidate.evidence_immutable:
        reasons.add("IMMUTABLE_EVIDENCE_REQUIRED")
    if not candidate.research_only:
        reasons.add("RESEARCH_ONLY_EVIDENCE_REQUIRED")
    if candidate.order_submission_performed:
        reasons.add("ORDER_SUBMISSION_EVIDENCE_FORBIDDEN")
    if candidate.metrics_scope != "oos_trading":
        reasons.add("OOS_TRADING_METRICS_REQUIRED")
    if candidate.trade_count < policy.minimum_oos_trades:
        reasons.add("INSUFFICIENT_OOS_TRADES")
    if candidate.lifecycle_state not in {"experimental", "candidate", "validated"}:
        reasons.add("LIFECYCLE_STATE_NOT_RESEARCH_ONLY")


def _weights(
    policy: RankingPolicy,
    reasons: set[str],
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal] | None:
    values = (
        _decimal(policy.profit_weight),
        _decimal(policy.correlation_penalty_weight),
        _decimal(policy.instability_penalty_weight),
        _decimal(policy.drawdown_penalty_weight),
        _decimal(policy.calibration_penalty_weight),
    )
    if any(value is None or value < 0 for value in values):
        reasons.add("RANKING_POLICY_WEIGHT_INVALID")
        return None
    quantum = _decimal(policy.score_quantum)
    if quantum is None or quantum <= 0:
        reasons.add("RANKING_SCORE_QUANTUM_INVALID")
        return None
    profit, correlation, instability, drawdown, calibration = values
    assert profit is not None
    assert correlation is not None
    assert instability is not None
    assert drawdown is not None
    assert calibration is not None
    return profit, correlation, instability, drawdown, calibration


def _manifest_hash(manifest: RankingManifest) -> str:
    candidates = sorted((_candidate_payload(item) for item in manifest.candidates), key=_canonical)
    return _sha(
        {
            "schema_version": manifest.schema_version,
            "manifest_id": manifest.manifest_id,
            "feature_registry_identity": manifest.feature_registry_identity,
            "config_identity": manifest.config_identity,
            "data_identity": manifest.data_identity,
            "routing_evidence_hash": manifest.routing_evidence_hash,
            "candidates": candidates,
            "protected_holdout_used": manifest.protected_holdout_used,
            "selected_model": manifest.selected_model,
        }
    )


def _candidate_payload(item: CandidateEvidence) -> dict[str, object]:
    return {
        "schema_version": item.schema_version,
        "candidate_id": item.candidate_id,
        "model_version_id": item.model_version_id,
        "experiment_id": item.experiment_id,
        "experiment_result_hash": item.experiment_result_hash,
        "validation_report_hash": item.validation_report_hash,
        "feature_registry_identity": item.feature_registry_identity,
        "config_identity": item.config_identity,
        "data_identity": item.data_identity,
        "routing_evidence_hash": item.routing_evidence_hash,
        "oos_timerange": item.oos_timerange,
        "oos_profit": None if item.oos_profit is None else str(item.oos_profit),
        "oos_stability": None if item.oos_stability is None else str(item.oos_stability),
        "max_abs_correlation": (
            None if item.max_abs_correlation is None else str(item.max_abs_correlation)
        ),
        "drawdown_contribution": (
            None if item.drawdown_contribution is None else str(item.drawdown_contribution)
        ),
        "calibration_error": (
            None if item.calibration_error is None else str(item.calibration_error)
        ),
        "trade_count": item.trade_count,
        "validation_passed": item.validation_passed,
        "evidence_immutable": item.evidence_immutable,
        "research_only": item.research_only,
        "order_submission_performed": item.order_submission_performed,
        "metrics_scope": item.metrics_scope,
        "lifecycle_state": item.lifecycle_state,
        "protected_holdout_used": item.protected_holdout_used,
    }


def _ranking_payload(row: CandidateRanking) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "model_version_id": row.model_version_id,
        "eligible": row.eligible,
        "score": None if row.score is None else str(row.score),
        "oos_profit_component": (
            None if row.oos_profit_component is None else str(row.oos_profit_component)
        ),
        "correlation_penalty": (
            None if row.correlation_penalty is None else str(row.correlation_penalty)
        ),
        "instability_penalty": (
            None if row.instability_penalty is None else str(row.instability_penalty)
        ),
        "drawdown_penalty": (None if row.drawdown_penalty is None else str(row.drawdown_penalty)),
        "calibration_penalty": (
            None if row.calibration_penalty is None else str(row.calibration_penalty)
        ),
        "reason_codes": row.reason_codes,
    }


def _policy_hash(policy: RankingPolicy) -> str:
    return _sha(
        {
            "schema_version": policy.schema_version,
            "policy_id": policy.policy_id,
            "minimum_oos_trades": policy.minimum_oos_trades,
            "profit_weight": str(policy.profit_weight),
            "correlation_penalty_weight": str(policy.correlation_penalty_weight),
            "instability_penalty_weight": str(policy.instability_penalty_weight),
            "drawdown_penalty_weight": str(policy.drawdown_penalty_weight),
            "calibration_penalty_weight": str(policy.calibration_penalty_weight),
            "score_quantum": str(policy.score_quantum),
        }
    )


def _decimal(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _bounded(value: Decimal | None) -> Decimal | None:
    parsed = _decimal(value)
    return parsed if parsed is not None and Decimal(0) <= parsed <= Decimal(1) else None


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


def _eligible_key(row: CandidateRanking) -> tuple[Decimal, str]:
    assert row.score is not None
    return -row.score, row.candidate_id


def _timerange(value: str) -> tuple[date, date] | None:
    parts = value.split("-", maxsplit=1)
    if len(parts) != 2 or any(len(part) != 8 or not part.isdigit() for part in parts):
        return None
    try:
        start = date(int(parts[0][:4]), int(parts[0][4:6]), int(parts[0][6:]))
        end = date(int(parts[1][:4]), int(parts[1][4:6]), int(parts[1][6:]))
    except ValueError:
        return None
    return None if end < start else (start, end)


def _protected(timerange: tuple[date, date]) -> bool:
    start, end = timerange
    return start <= date(2026, 9, 30) and end >= date(2026, 8, 1)


def _sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()
