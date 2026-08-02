from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import BotMode, DriftState, ShadowStatus, TradeDirection
from ai_platform.wickhunter.deterministic_replay import LabelOutcome
from ai_platform.wickhunter.shadow_runtime import (
    PortalObservabilitySnapshot,
    ReplayShadowParityEvidence,
    ShadowRuntimeError,
)


POLICY_SCHEMA_VERSION = "wickhunter-paper-validation-policy-v1"
REQUEST_SCHEMA_VERSION = "wickhunter-paper-run-request-v1"
ACTIVATION_SCHEMA_VERSION = "wickhunter-paper-activation-manifest-v1"
OBSERVATION_SCHEMA_VERSION = "wickhunter-paper-observation-v1"
EXERCISE_SCHEMA_VERSION = "wickhunter-paper-safety-exercise-v1"
REPORT_SCHEMA_VERSION = "wickhunter-paper-validation-report-v1"
REVIEW_SCHEMA_VERSION = "wickhunter-paper-candidate-review-v1"
MANIFEST_SCHEMA_VERSION = "wickhunter-paper-validation-manifest-v1"
POLICY_NAME = "policy.json"
REQUEST_NAME = "request.json"
ACTIVATION_MANIFEST_NAME = "activation-manifest.json"
OBSERVATIONS_NAME = "observations.jsonl"
PARITY_NAME = "replay-shadow-parity.jsonl"
EXERCISES_NAME = "safety-exercises.jsonl"
REPORT_NAME = "report.json"
REVIEW_NAME = "candidate-review.json"
MANIFEST_NAME = "manifest.json"
CHECKSUM_INDEX_NAME = "artifact-sha256.txt"


class PaperValidationError(RuntimeError):
    """Raised when WH-09 evidence is malformed, unsafe, mutable or inconsistent."""


class PaperValidationOutcome(StrEnum):
    READY_FOR_OWNER_REVIEW = "ready_for_owner_review"
    INCOMPLETE = "incomplete"


class SafetyExerciseKind(StrEnum):
    CIRCUIT_BREAKER = "circuit_breaker"
    MODEL_DRIFT = "model_drift"
    RESTART_RECOVERY = "restart_recovery"
    STALE_SOURCE = "stale_source"


def _text(value: object, *, field: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise PaperValidationError(f"{field} must be non-empty")
    return normalized


def _sha256(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise PaperValidationError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _git_sha(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 40 or any(char not in "0123456789abcdef" for char in normalized):
        raise PaperValidationError(f"{field} must be a lowercase 40-character Git SHA")
    return normalized


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise PaperValidationError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaperValidationError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise PaperValidationError(f"{field} must be finite")
    return parsed


def _assert_zero_authority(payload: Mapping[str, object], *, field: str) -> None:
    unsafe = (
        bool(payload.get("protected_holdout_accessed", False))
        or bool(payload.get("automatic_promotion_enabled", False))
        or bool(payload.get("trading_credentials_present", False))
        or bool(payload.get("order_adapter_present", False))
        or bool(payload.get("execution_enabled", False))
        or bool(payload.get("live_capital_authorized", False))
        or payload.get("orders_submitted", 0) != 0
    )
    if unsafe:
        raise PaperValidationError(f"{field} contains forbidden authority")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise PaperValidationError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, payload: object) -> None:
    _write_new(path, canonical_json(payload).encode("utf-8") + b"\n")


def _write_jsonl(path: Path, payloads: Iterable[object]) -> None:
    content = b"".join(canonical_json(item).encode("utf-8") + b"\n" for item in payloads)
    _write_new(path, content)


def _read_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise PaperValidationError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaperValidationError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise PaperValidationError(f"{field} must contain an object")
    return payload


def _read_jsonl(path: Path, *, field: str) -> tuple[dict[str, Any], ...]:
    if path.is_symlink() or not path.is_file():
        raise PaperValidationError(f"{field} must be a regular file")
    records: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise PaperValidationError(f"{field} line {line_number} must be an object")
            records.append(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaperValidationError(f"unable to read {field}") from exc
    return tuple(records)


@dataclass(frozen=True, slots=True)
class PaperValidationPolicy:
    schema_version: str = POLICY_SCHEMA_VERSION
    policy_version: str = "wickhunter-paper-validation-v1"
    minimum_duration_ms: int = 86_400_000
    minimum_snapshot_count: int = 96
    maximum_snapshot_gap_ms: int = 1_800_000
    minimum_fresh_source_ratio: Decimal = Decimal("0.99")
    minimum_decision_count: int = 1
    minimum_allowed_decision_count: int = 1
    minimum_risk_rejection_count: int = 1
    maximum_drawdown_ratio: Decimal = Decimal("0.20")
    required_exercises: tuple[SafetyExerciseKind, ...] = (
        SafetyExerciseKind.CIRCUIT_BREAKER,
        SafetyExerciseKind.MODEL_DRIFT,
        SafetyExerciseKind.RESTART_RECOVERY,
        SafetyExerciseKind.STALE_SOURCE,
    )

    def __post_init__(self) -> None:
        if self.schema_version != POLICY_SCHEMA_VERSION:
            raise PaperValidationError("paper policy schema mismatch")
        _text(self.policy_version, field="policy_version")
        if self.minimum_duration_ms < 86_400_000:
            raise PaperValidationError("minimum_duration_ms cannot weaken the terminal floor")
        if self.minimum_snapshot_count < 96:
            raise PaperValidationError("minimum_snapshot_count cannot weaken the terminal floor")
        if not 1 <= self.maximum_snapshot_gap_ms <= 1_800_000:
            raise PaperValidationError("maximum_snapshot_gap_ms cannot weaken the terminal ceiling")
        decision_count_fields = (
            "minimum_decision_count",
            "minimum_allowed_decision_count",
            "minimum_risk_rejection_count",
        )
        if any(getattr(self, name) < 1 for name in decision_count_fields):
            raise PaperValidationError("paper policy decision counts must be >= 1")
        if not Decimal("0.99") <= self.minimum_fresh_source_ratio <= Decimal(1):
            raise PaperValidationError(
                "minimum_fresh_source_ratio cannot weaken the terminal floor"
            )
        if not Decimal(0) < self.maximum_drawdown_ratio <= Decimal("0.20"):
            raise PaperValidationError("maximum_drawdown_ratio cannot weaken the terminal ceiling")
        expected_exercises = tuple(sorted(SafetyExerciseKind, key=lambda item: item.value))
        if self.required_exercises != expected_exercises:
            raise PaperValidationError("required_exercises must contain the complete canonical set")
        maximum_covered_duration = (self.minimum_snapshot_count - 1) * self.maximum_snapshot_gap_ms
        if maximum_covered_duration < self.minimum_duration_ms:
            raise PaperValidationError("paper policy duration and cadence are infeasible")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class PaperRunRequest:
    schema_version: str
    run_id: str
    created_at_ms: int
    window_start_ms: int
    window_end_ms: int
    bot_instance: str
    mode: BotMode
    model_version: str
    model_hash: str
    parameter_version: str
    parameter_hash: str
    dataset_hash: str
    code_sha: str
    rollback_model_version: str
    rollback_model_hash: str
    rollback_parameter_version: str
    rollback_parameter_hash: str
    wh07_snapshot_schema: str
    wh08_consumer_version: str
    policy_sha256: str
    protected_holdout_accessed: bool = False
    automatic_promotion_enabled: bool = False
    trading_credentials_present: bool = False
    execution_enabled: bool = False
    live_capital_authorized: bool = False
    orders_submitted: int = 0

    def __post_init__(self) -> None:
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise PaperValidationError("paper request schema mismatch")
        _sha256(self.run_id, field="run_id")
        if self.created_at_ms <= 0 or self.window_start_ms < self.created_at_ms:
            raise PaperValidationError("request timestamps are invalid")
        if self.window_end_ms <= self.window_start_ms:
            raise PaperValidationError("paper window must be positive")
        if self.mode not in {BotMode.SHADOW, BotMode.PAPER}:
            raise PaperValidationError("paper request mode must be shadow or paper")
        text_fields = (
            (self.bot_instance, "bot_instance"),
            (self.model_version, "model_version"),
            (self.parameter_version, "parameter_version"),
            (self.rollback_model_version, "rollback_model_version"),
            (self.rollback_parameter_version, "rollback_parameter_version"),
            (self.wh07_snapshot_schema, "wh07_snapshot_schema"),
            (self.wh08_consumer_version, "wh08_consumer_version"),
        )
        for value, field_name in text_fields:
            _text(value, field=field_name)
        hash_fields = (
            (self.model_hash, "model_hash"),
            (self.parameter_hash, "parameter_hash"),
            (self.dataset_hash, "dataset_hash"),
            (self.rollback_model_hash, "rollback_model_hash"),
            (self.rollback_parameter_hash, "rollback_parameter_hash"),
            (self.policy_sha256, "policy_sha256"),
        )
        for value, field_name in hash_fields:
            _sha256(value, field=field_name)
        _git_sha(self.code_sha, field="code_sha")
        _assert_zero_authority(asdict(self), field="paper request")


@dataclass(frozen=True, slots=True)
class PaperObservation:
    schema_version: str
    snapshot_id: str
    snapshot_sha256: str
    observed_at_ms: int
    persistence_generation: int
    bot_instance: str
    mode: BotMode
    health: str
    model_version: str
    model_hash: str
    parameter_version: str
    parameter_hash: str
    dataset_hash: str
    code_sha: str
    source_count: int
    fresh_source_count: int
    decision_count: int
    allowed_decision_count: int
    risk_rejection_count: int
    ignored_decision_count: int
    allowed_decision_ids: tuple[str, ...]
    risk_rejection_decision_ids: tuple[str, ...]
    ignored_decision_ids: tuple[str, ...]
    position_count: int
    position_ids: tuple[str, ...]
    cumulative_realized_pnl_quote: Decimal
    unrealized_pnl_quote: Decimal
    simulated_equity_quote: Decimal
    drawdown_ratio: Decimal
    circuit_breaker_active: bool
    circuit_breaker_reasons: tuple[str, ...]
    model_drift: DriftState
    data_drift: DriftState
    read_only: bool
    trading_credentials_present: bool
    order_adapter_present: bool
    orders_submitted: int
    live_capital_authorized: bool

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != OBSERVATION_SCHEMA_VERSION:
            raise PaperValidationError("observation schema mismatch")
        for value, field_name in (
            (self.snapshot_id, "snapshot_id"),
            (self.snapshot_sha256, "snapshot_sha256"),
            (self.model_hash, "model_hash"),
            (self.parameter_hash, "parameter_hash"),
            (self.dataset_hash, "dataset_hash"),
        ):
            _sha256(value, field=field_name)
        _git_sha(self.code_sha, field="code_sha")
        if self.observed_at_ms <= 0 or self.persistence_generation < 0:
            raise PaperValidationError("observation timestamp or generation is invalid")
        if self.mode not in {BotMode.SHADOW, BotMode.PAPER}:
            raise PaperValidationError("observation mode must be shadow or paper")
        if self.health not in {"healthy", "degraded", "fail_closed"}:
            raise PaperValidationError("observation health is unsupported")
        counts = (
            self.source_count,
            self.fresh_source_count,
            self.decision_count,
            self.allowed_decision_count,
            self.risk_rejection_count,
            self.ignored_decision_count,
            self.position_count,
        )
        if any(value < 0 for value in counts):
            raise PaperValidationError("observation counts must be >= 0")
        if self.fresh_source_count > self.source_count:
            raise PaperValidationError("fresh sources exceed all sources")
        decision_total = (
            self.allowed_decision_count + self.risk_rejection_count + self.ignored_decision_count
        )
        if decision_total != self.decision_count:
            raise PaperValidationError("decision counts are inconsistent")
        decision_id_groups = (
            (
                self.allowed_decision_ids,
                self.allowed_decision_count,
                "allowed_decision_ids",
            ),
            (
                self.risk_rejection_decision_ids,
                self.risk_rejection_count,
                "risk_rejection_decision_ids",
            ),
            (
                self.ignored_decision_ids,
                self.ignored_decision_count,
                "ignored_decision_ids",
            ),
        )
        for decision_ids, expected_count, field_name in decision_id_groups:
            if decision_ids != tuple(sorted(set(decision_ids))):
                raise PaperValidationError(f"{field_name} must be unique and sorted")
            if len(decision_ids) != expected_count:
                raise PaperValidationError(f"{field_name} count mismatch")
            for decision_id in decision_ids:
                _sha256(decision_id, field=field_name)
        if self.position_ids != tuple(sorted(set(self.position_ids))):
            raise PaperValidationError("position_ids must be unique and sorted")
        if len(self.position_ids) != self.position_count:
            raise PaperValidationError("position_ids count mismatch")
        for position_id in self.position_ids:
            _sha256(position_id, field="position_ids")
        for decimal_value, field_name in (
            (self.cumulative_realized_pnl_quote, "cumulative_realized_pnl_quote"),
            (self.unrealized_pnl_quote, "unrealized_pnl_quote"),
            (self.simulated_equity_quote, "simulated_equity_quote"),
            (self.drawdown_ratio, "drawdown_ratio"),
        ):
            _decimal(decimal_value, field=field_name)
        if self.simulated_equity_quote <= 0:
            raise PaperValidationError("simulated equity must be positive")
        if not Decimal(0) <= self.drawdown_ratio <= Decimal(1):
            raise PaperValidationError("drawdown_ratio must be in [0, 1]")
        if self.circuit_breaker_reasons != tuple(sorted(set(self.circuit_breaker_reasons))):
            raise PaperValidationError("breaker reasons must be unique and sorted")
        _assert_zero_authority(asdict(self), field="paper observation")
        if not self.read_only:
            raise PaperValidationError("paper observation must be read-only")

    @property
    def observation_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class SafetyExerciseEvidence:
    schema_version: str
    exercise_id: str
    run_id: str
    kind: SafetyExerciseKind
    observed_at_ms: int
    source_snapshot_id: str
    expected_reason: str
    observed_reasons: tuple[str, ...]
    passed: bool
    state_recovered: bool
    read_only: bool = True
    trading_credentials_present: bool = False
    order_adapter_present: bool = False
    orders_submitted: int = 0
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != EXERCISE_SCHEMA_VERSION:
            raise PaperValidationError("safety exercise schema mismatch")
        for value, field_name in (
            (self.exercise_id, "exercise_id"),
            (self.run_id, "run_id"),
            (self.source_snapshot_id, "source_snapshot_id"),
        ):
            _sha256(value, field=field_name)
        if self.observed_at_ms <= 0:
            raise PaperValidationError("exercise observed_at_ms must be > 0")
        _text(self.expected_reason, field="expected_reason")
        if self.observed_reasons != tuple(sorted(set(self.observed_reasons))):
            raise PaperValidationError("exercise reasons must be unique and sorted")
        if self.expected_reason not in self.observed_reasons:
            raise PaperValidationError("exercise expected reason is absent")
        if not self.passed or not self.state_recovered:
            raise PaperValidationError("safety exercise did not pass and recover")
        _assert_zero_authority(asdict(self), field="safety exercise")
        if not self.read_only:
            raise PaperValidationError("safety exercise must be read-only")


@dataclass(frozen=True, slots=True)
class PaperEvidenceSummary:
    observation_start_ms: int
    observation_end_ms: int
    duration_ms: int
    snapshot_count: int
    maximum_gap_ms: int
    source_sample_count: int
    fresh_source_sample_count: int
    fresh_source_ratio: Decimal
    decision_count: int
    allowed_decision_count: int
    risk_rejection_count: int
    ignored_decision_count: int
    unique_position_count: int
    maximum_drawdown_ratio: Decimal
    minimum_equity_quote: Decimal
    maximum_equity_quote: Decimal
    parity_count: int
    safety_exercise_kinds: tuple[SafetyExerciseKind, ...]


@dataclass(frozen=True, slots=True)
class PaperValidationReport:
    schema_version: str
    report_id: str
    run_id: str
    policy_sha256: str
    outcome: PaperValidationOutcome
    summary: PaperEvidenceSummary
    blocker_codes: tuple[str, ...]
    candidate_review_eligible: bool
    owner_decision_required: bool
    automatic_promotion_enabled: bool
    protected_holdout_accessed: bool
    trading_credentials_present: bool
    execution_enabled: bool
    orders_submitted: int
    live_capital_authorized: bool

    def __post_init__(self) -> None:
        if self.schema_version != REPORT_SCHEMA_VERSION:
            raise PaperValidationError("report schema mismatch")
        for value, field_name in (
            (self.report_id, "report_id"),
            (self.run_id, "run_id"),
            (self.policy_sha256, "policy_sha256"),
        ):
            _sha256(value, field=field_name)
        if self.blocker_codes != tuple(sorted(set(self.blocker_codes))):
            raise PaperValidationError("report blockers must be unique and sorted")
        expected = self.outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW
        if self.candidate_review_eligible != expected:
            raise PaperValidationError("report eligibility does not match outcome")
        if not self.owner_decision_required:
            raise PaperValidationError("owner decision must remain required")
        _assert_zero_authority(asdict(self), field="paper report")


@dataclass(frozen=True, slots=True)
class CandidateReviewPackage:
    schema_version: str
    package_id: str
    report_id: str
    run_id: str
    eligible_for_owner_review: bool
    model_version: str
    model_hash: str
    parameter_version: str
    parameter_hash: str
    rollback_model_version: str
    rollback_model_hash: str
    rollback_parameter_version: str
    rollback_parameter_hash: str
    owner_decision_required: bool
    automatic_promotion_enabled: bool
    trading_credentials_present: bool
    execution_enabled: bool
    orders_submitted: int
    live_capital_authorized: bool

    def __post_init__(self) -> None:
        if self.schema_version != REVIEW_SCHEMA_VERSION:
            raise PaperValidationError("candidate review schema mismatch")
        for value, field_name in (
            (self.package_id, "package_id"),
            (self.report_id, "report_id"),
            (self.run_id, "run_id"),
            (self.model_hash, "model_hash"),
            (self.parameter_hash, "parameter_hash"),
            (self.rollback_model_hash, "rollback_model_hash"),
            (self.rollback_parameter_hash, "rollback_parameter_hash"),
        ):
            _sha256(value, field=field_name)
        if not self.owner_decision_required:
            raise PaperValidationError("candidate package requires an owner decision")
        _assert_zero_authority(asdict(self), field="candidate review")


@dataclass(frozen=True, slots=True)
class PaperValidationResult:
    report: PaperValidationReport
    candidate_review: CandidateReviewPackage
    observations: tuple[PaperObservation, ...]


def _assert_request_matches_policy(
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
    *,
    field: str,
) -> None:
    if request.policy_sha256 != policy.policy_sha256:
        raise PaperValidationError(f"{field} policy identity mismatch")
    if request.window_end_ms - request.window_start_ms < policy.minimum_duration_ms:
        raise PaperValidationError(f"{field} window is shorter than policy")


def _request_identity_payload(
    *,
    created_at_ms: int,
    window_start_ms: int,
    window_end_ms: int,
    bot_instance: str,
    mode: BotMode,
    model_version: str,
    model_hash: str,
    parameter_version: str,
    parameter_hash: str,
    dataset_hash: str,
    code_sha: str,
    rollback_model_version: str,
    rollback_model_hash: str,
    rollback_parameter_version: str,
    rollback_parameter_hash: str,
    wh08_consumer_version: str,
    policy_sha256: str,
) -> dict[str, object]:
    return {
        "created_at_ms": created_at_ms,
        "window_start_ms": window_start_ms,
        "window_end_ms": window_end_ms,
        "bot_instance": bot_instance,
        "mode": mode.value,
        "model_version": model_version,
        "model_hash": model_hash,
        "parameter_version": parameter_version,
        "parameter_hash": parameter_hash,
        "dataset_hash": dataset_hash,
        "code_sha": code_sha,
        "rollback_model_version": rollback_model_version,
        "rollback_model_hash": rollback_model_hash,
        "rollback_parameter_version": rollback_parameter_version,
        "rollback_parameter_hash": rollback_parameter_hash,
        "wh07_snapshot_schema": "wickhunter-portal-observability-snapshot-v1",
        "wh08_consumer_version": wh08_consumer_version,
        "policy_sha256": policy_sha256,
    }


def build_paper_run_request(
    *,
    created_at_ms: int,
    window_start_ms: int,
    window_end_ms: int,
    bot_instance: str,
    mode: BotMode,
    model_version: str,
    model_hash: str,
    parameter_version: str,
    parameter_hash: str,
    dataset_hash: str,
    code_sha: str,
    rollback_model_version: str,
    rollback_model_hash: str,
    rollback_parameter_version: str,
    rollback_parameter_hash: str,
    wh08_consumer_version: str,
    policy: PaperValidationPolicy,
) -> PaperRunRequest:
    if window_end_ms - window_start_ms < policy.minimum_duration_ms:
        raise PaperValidationError("paper request window is shorter than policy")
    payload = _request_identity_payload(
        created_at_ms=created_at_ms,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        bot_instance=bot_instance,
        mode=mode,
        model_version=model_version,
        model_hash=model_hash,
        parameter_version=parameter_version,
        parameter_hash=parameter_hash,
        dataset_hash=dataset_hash,
        code_sha=code_sha,
        rollback_model_version=rollback_model_version,
        rollback_model_hash=rollback_model_hash,
        rollback_parameter_version=rollback_parameter_version,
        rollback_parameter_hash=rollback_parameter_hash,
        wh08_consumer_version=wh08_consumer_version,
        policy_sha256=policy.policy_sha256,
    )
    run_id = canonical_sha256({"schema_version": REQUEST_SCHEMA_VERSION, "payload": payload})
    return PaperRunRequest(
        schema_version=REQUEST_SCHEMA_VERSION,
        run_id=run_id,
        created_at_ms=created_at_ms,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        bot_instance=bot_instance,
        mode=mode,
        model_version=model_version,
        model_hash=model_hash,
        parameter_version=parameter_version,
        parameter_hash=parameter_hash,
        dataset_hash=dataset_hash,
        code_sha=code_sha,
        rollback_model_version=rollback_model_version,
        rollback_model_hash=rollback_model_hash,
        rollback_parameter_version=rollback_parameter_version,
        rollback_parameter_hash=rollback_parameter_hash,
        wh07_snapshot_schema="wickhunter-portal-observability-snapshot-v1",
        wh08_consumer_version=wh08_consumer_version,
        policy_sha256=policy.policy_sha256,
    )


def observation_from_snapshot(snapshot: PortalObservabilitySnapshot) -> PaperObservation:
    if snapshot.model_version is None or snapshot.model_hash is None:
        raise PaperValidationError("paper snapshot requires a model identity")
    if snapshot.parameter_version is None or snapshot.parameter_hash is None:
        raise PaperValidationError("paper snapshot requires a parameter identity")
    if snapshot.dataset_hash is None or snapshot.code_sha is None:
        raise PaperValidationError("paper snapshot requires dataset and code identity")
    decision_ids = {status: [] for status in ShadowStatus}
    for decision in snapshot.decisions:
        decision_ids[decision.status].append(decision.shadow_decision_id)
    return PaperObservation(
        schema_version=OBSERVATION_SCHEMA_VERSION,
        snapshot_id=snapshot.snapshot_id,
        snapshot_sha256=canonical_sha256(snapshot),
        observed_at_ms=snapshot.observed_at_ms,
        persistence_generation=snapshot.persistence_generation,
        bot_instance=snapshot.bot_instance,
        mode=snapshot.mode,
        health=snapshot.health.value,
        model_version=snapshot.model_version,
        model_hash=snapshot.model_hash,
        parameter_version=snapshot.parameter_version,
        parameter_hash=snapshot.parameter_hash,
        dataset_hash=snapshot.dataset_hash,
        code_sha=snapshot.code_sha,
        source_count=len(snapshot.source_freshness),
        fresh_source_count=sum(item.fresh for item in snapshot.source_freshness),
        decision_count=len(snapshot.decisions),
        allowed_decision_count=len(decision_ids[ShadowStatus.SIMULATED_ALLOWED]),
        risk_rejection_count=len(decision_ids[ShadowStatus.SIMULATED_REJECTED]),
        ignored_decision_count=len(decision_ids[ShadowStatus.NO_CANDIDATE]),
        allowed_decision_ids=tuple(sorted(decision_ids[ShadowStatus.SIMULATED_ALLOWED])),
        risk_rejection_decision_ids=tuple(sorted(decision_ids[ShadowStatus.SIMULATED_REJECTED])),
        ignored_decision_ids=tuple(sorted(decision_ids[ShadowStatus.NO_CANDIDATE])),
        position_count=len(snapshot.positions),
        position_ids=tuple(sorted(position.position_id for position in snapshot.positions)),
        cumulative_realized_pnl_quote=snapshot.cumulative_realized_pnl_quote,
        unrealized_pnl_quote=snapshot.unrealized_pnl_quote,
        simulated_equity_quote=snapshot.simulated_equity_quote,
        drawdown_ratio=snapshot.drawdown_ratio,
        circuit_breaker_active=snapshot.circuit_breaker_active,
        circuit_breaker_reasons=snapshot.circuit_breaker_reasons,
        model_drift=snapshot.model_drift,
        data_drift=snapshot.data_drift,
        read_only=snapshot.read_only,
        trading_credentials_present=snapshot.trading_credentials_present,
        order_adapter_present=snapshot.order_adapter_present,
        orders_submitted=snapshot.orders_submitted,
        live_capital_authorized=snapshot.live_capital_authorized,
    )


def _validate_request_observation(request: PaperRunRequest, item: PaperObservation) -> None:
    identities = (
        (item.bot_instance, request.bot_instance, "bot_instance"),
        (item.mode, request.mode, "mode"),
        (item.model_version, request.model_version, "model_version"),
        (item.model_hash, request.model_hash, "model_hash"),
        (item.parameter_version, request.parameter_version, "parameter_version"),
        (item.parameter_hash, request.parameter_hash, "parameter_hash"),
        (item.dataset_hash, request.dataset_hash, "dataset_hash"),
        (item.code_sha, request.code_sha, "code_sha"),
    )
    for actual, expected, field_name in identities:
        if actual != expected:
            raise PaperValidationError(f"observation {field_name} does not match request")
    if not request.window_start_ms <= item.observed_at_ms <= request.window_end_ms:
        raise PaperValidationError("observation falls outside the immutable request window")


def _prepare_observations(
    request: PaperRunRequest,
    snapshots: Sequence[PortalObservabilitySnapshot],
) -> tuple[PaperObservation, ...]:
    observations = tuple(
        sorted(
            (observation_from_snapshot(snapshot) for snapshot in snapshots),
            key=lambda item: item.observed_at_ms,
        )
    )
    if not observations:
        raise PaperValidationError("paper validation requires observations")
    if len({item.snapshot_id for item in observations}) != len(observations):
        raise PaperValidationError("paper observations contain duplicate snapshot ids")
    if any(
        later.observed_at_ms <= earlier.observed_at_ms for earlier, later in pairwise(observations)
    ):
        raise PaperValidationError("paper observations must be strictly increasing")
    for observation in observations:
        _validate_request_observation(request, observation)
    return observations


def _validate_parity(
    request: PaperRunRequest,
    snapshots: Sequence[PortalObservabilitySnapshot],
    parity_evidence: Sequence[ReplayShadowParityEvidence],
) -> tuple[set[str], set[str]]:
    parity_ids = {item.shadow_decision_id for item in parity_evidence}
    if len(parity_ids) != len(parity_evidence):
        raise PaperValidationError("parity evidence contains duplicate decisions")
    allowed_ids = {
        decision.shadow_decision_id
        for snapshot in snapshots
        for decision in snapshot.decisions
        if decision.status is ShadowStatus.SIMULATED_ALLOWED
    }
    for item in parity_evidence:
        if item.shadow_decision_id not in allowed_ids:
            raise PaperValidationError("parity evidence does not bind an allowed decision")
        if item.dataset_hash != request.dataset_hash or item.code_sha != request.code_sha:
            raise PaperValidationError("parity evidence identity mismatch")
        accepted = item.identities_match and item.policy_match and item.execution_authority_absent
        if not accepted:
            raise PaperValidationError("parity evidence is not accepted")
    return allowed_ids, parity_ids


def _validate_exercises(
    request: PaperRunRequest,
    observations: Sequence[PaperObservation],
    exercises: Sequence[SafetyExerciseEvidence],
) -> tuple[SafetyExerciseKind, ...]:
    snapshot_ids = {item.snapshot_id for item in observations}
    for exercise in exercises:
        if exercise.run_id != request.run_id:
            raise PaperValidationError("safety exercise run identity mismatch")
        if exercise.source_snapshot_id not in snapshot_ids:
            raise PaperValidationError("safety exercise snapshot identity mismatch")
    return tuple(sorted({item.kind for item in exercises}, key=lambda item: item.value))


def _summarize(
    observations: tuple[PaperObservation, ...],
    parity_count: int,
    exercise_kinds: tuple[SafetyExerciseKind, ...],
) -> PaperEvidenceSummary:
    gaps = tuple(
        later.observed_at_ms - earlier.observed_at_ms for earlier, later in pairwise(observations)
    )
    source_samples = sum(item.source_count for item in observations)
    fresh_samples = sum(item.fresh_source_count for item in observations)
    fresh_ratio = Decimal(fresh_samples) / Decimal(source_samples) if source_samples else Decimal(0)
    position_ids = {
        position_id for observation in observations for position_id in observation.position_ids
    }
    return PaperEvidenceSummary(
        observation_start_ms=observations[0].observed_at_ms,
        observation_end_ms=observations[-1].observed_at_ms,
        duration_ms=observations[-1].observed_at_ms - observations[0].observed_at_ms,
        snapshot_count=len(observations),
        maximum_gap_ms=max(gaps, default=0),
        source_sample_count=source_samples,
        fresh_source_sample_count=fresh_samples,
        fresh_source_ratio=fresh_ratio,
        decision_count=sum(item.decision_count for item in observations),
        allowed_decision_count=sum(item.allowed_decision_count for item in observations),
        risk_rejection_count=sum(item.risk_rejection_count for item in observations),
        ignored_decision_count=sum(item.ignored_decision_count for item in observations),
        unique_position_count=len(position_ids),
        maximum_drawdown_ratio=max(item.drawdown_ratio for item in observations),
        minimum_equity_quote=min(item.simulated_equity_quote for item in observations),
        maximum_equity_quote=max(item.simulated_equity_quote for item in observations),
        parity_count=parity_count,
        safety_exercise_kinds=exercise_kinds,
    )


def _blocker_codes(
    policy: PaperValidationPolicy,
    summary: PaperEvidenceSummary,
    allowed_ids: set[str],
    parity_ids: set[str],
) -> tuple[str, ...]:
    blockers: list[str] = []
    checks = (
        (summary.duration_ms < policy.minimum_duration_ms, "minimum_duration_not_met"),
        (
            summary.snapshot_count < policy.minimum_snapshot_count,
            "minimum_snapshot_count_not_met",
        ),
        (
            summary.maximum_gap_ms > policy.maximum_snapshot_gap_ms,
            "maximum_snapshot_gap_exceeded",
        ),
        (
            summary.fresh_source_ratio < policy.minimum_fresh_source_ratio,
            "fresh_source_ratio_below_policy",
        ),
        (
            summary.decision_count < policy.minimum_decision_count,
            "minimum_decision_count_not_met",
        ),
        (
            summary.allowed_decision_count < policy.minimum_allowed_decision_count,
            "minimum_allowed_decision_count_not_met",
        ),
        (
            summary.risk_rejection_count < policy.minimum_risk_rejection_count,
            "minimum_risk_rejection_count_not_met",
        ),
        (
            summary.maximum_drawdown_ratio > policy.maximum_drawdown_ratio,
            "maximum_drawdown_exceeded",
        ),
        (not allowed_ids.issubset(parity_ids), "replay_shadow_parity_incomplete"),
        (
            bool(set(policy.required_exercises) - set(summary.safety_exercise_kinds)),
            "required_safety_exercises_incomplete",
        ),
    )
    blockers.extend(code for failed, code in checks if failed)
    return tuple(sorted(set(blockers)))


def _build_report(
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
    summary: PaperEvidenceSummary,
    blockers: tuple[str, ...],
) -> PaperValidationReport:
    outcome = (
        PaperValidationOutcome.INCOMPLETE
        if blockers
        else PaperValidationOutcome.READY_FOR_OWNER_REVIEW
    )
    eligible = outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW
    payload = {
        "run_id": request.run_id,
        "policy_sha256": policy.policy_sha256,
        "outcome": outcome.value,
        "summary": summary,
        "blocker_codes": blockers,
        "candidate_review_eligible": eligible,
        "owner_decision_required": True,
        "automatic_promotion_enabled": False,
        "protected_holdout_accessed": False,
        "trading_credentials_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    report_id = canonical_sha256({"schema_version": REPORT_SCHEMA_VERSION, "payload": payload})
    return PaperValidationReport(
        schema_version=REPORT_SCHEMA_VERSION,
        report_id=report_id,
        run_id=request.run_id,
        policy_sha256=policy.policy_sha256,
        outcome=outcome,
        summary=summary,
        blocker_codes=blockers,
        candidate_review_eligible=eligible,
        owner_decision_required=True,
        automatic_promotion_enabled=False,
        protected_holdout_accessed=False,
        trading_credentials_present=False,
        execution_enabled=False,
        orders_submitted=0,
        live_capital_authorized=False,
    )


def _build_review(
    request: PaperRunRequest,
    report: PaperValidationReport,
) -> CandidateReviewPackage:
    payload = {
        "report_id": report.report_id,
        "run_id": request.run_id,
        "eligible_for_owner_review": report.candidate_review_eligible,
        "model_version": request.model_version,
        "model_hash": request.model_hash,
        "parameter_version": request.parameter_version,
        "parameter_hash": request.parameter_hash,
        "rollback_model_version": request.rollback_model_version,
        "rollback_model_hash": request.rollback_model_hash,
        "rollback_parameter_version": request.rollback_parameter_version,
        "rollback_parameter_hash": request.rollback_parameter_hash,
        "owner_decision_required": True,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    package_id = canonical_sha256({"schema_version": REVIEW_SCHEMA_VERSION, "payload": payload})
    return CandidateReviewPackage(
        schema_version=REVIEW_SCHEMA_VERSION,
        package_id=package_id,
        report_id=report.report_id,
        run_id=request.run_id,
        eligible_for_owner_review=report.candidate_review_eligible,
        model_version=request.model_version,
        model_hash=request.model_hash,
        parameter_version=request.parameter_version,
        parameter_hash=request.parameter_hash,
        rollback_model_version=request.rollback_model_version,
        rollback_model_hash=request.rollback_model_hash,
        rollback_parameter_version=request.rollback_parameter_version,
        rollback_parameter_hash=request.rollback_parameter_hash,
        owner_decision_required=True,
        automatic_promotion_enabled=False,
        trading_credentials_present=False,
        execution_enabled=False,
        orders_submitted=0,
        live_capital_authorized=False,
    )


def evaluate_paper_evidence(
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
    snapshots: Sequence[PortalObservabilitySnapshot],
    parity_evidence: Sequence[ReplayShadowParityEvidence],
    safety_exercises: Sequence[SafetyExerciseEvidence],
) -> PaperValidationResult:
    _assert_request_matches_policy(request, policy, field="request")
    observations = _prepare_observations(request, snapshots)
    allowed_ids, parity_ids = _validate_parity(request, snapshots, parity_evidence)
    exercise_kinds = _validate_exercises(request, observations, safety_exercises)
    summary = _summarize(observations, len(parity_evidence), exercise_kinds)
    blockers = _blocker_codes(policy, summary, allowed_ids, parity_ids)
    report = _build_report(request, policy, summary, blockers)
    return PaperValidationResult(
        report=report,
        candidate_review=_build_review(request, report),
        observations=observations,
    )


def _publish_directory(destination: Path, writer: Callable[[Path], None]) -> None:
    if destination.exists() or destination.is_symlink():
        raise PaperValidationError(f"refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        writer(temporary)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _write_checksum_index(root: Path, names: Sequence[str]) -> None:
    content = "".join(f"{_sha256_file(root / name)}  {name}\n" for name in names)
    _write_new(root / CHECKSUM_INDEX_NAME, content.encode("utf-8"))


def _manifest(schema: str, payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": schema,
        "manifest_sha256": canonical_sha256({"schema_version": schema, "payload": payload}),
        **payload,
    }


def publish_paper_run_request(
    destination: Path,
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
) -> dict[str, Any]:
    _assert_request_matches_policy(request, policy, field="activation")

    def write(root: Path) -> None:
        _write_json(root / POLICY_NAME, policy)
        _write_json(root / REQUEST_NAME, request)
        artifacts = (
            (POLICY_NAME, _sha256_file(root / POLICY_NAME)),
            (REQUEST_NAME, _sha256_file(root / REQUEST_NAME)),
        )
        payload: dict[str, object] = {
            "run_id": request.run_id,
            "policy_sha256": policy.policy_sha256,
            "artifacts": artifacts,
            "protected_holdout_accessed": False,
            "automatic_promotion_enabled": False,
            "trading_credentials_present": False,
            "execution_enabled": False,
            "orders_submitted": 0,
            "live_capital_authorized": False,
        }
        _write_json(root / ACTIVATION_MANIFEST_NAME, _manifest(ACTIVATION_SCHEMA_VERSION, payload))
        _write_checksum_index(root, (POLICY_NAME, REQUEST_NAME, ACTIVATION_MANIFEST_NAME))

    _publish_directory(destination, write)
    return verify_paper_run_request(destination)


def publish_paper_validation_package(
    destination: Path,
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
    snapshots: Sequence[PortalObservabilitySnapshot],
    parity_evidence: Sequence[ReplayShadowParityEvidence],
    safety_exercises: Sequence[SafetyExerciseEvidence],
) -> PaperValidationResult:
    result = evaluate_paper_evidence(
        request=request,
        policy=policy,
        snapshots=snapshots,
        parity_evidence=parity_evidence,
        safety_exercises=safety_exercises,
    )

    def write(root: Path) -> None:
        _write_json(root / POLICY_NAME, policy)
        _write_json(root / REQUEST_NAME, request)
        _write_jsonl(root / OBSERVATIONS_NAME, result.observations)
        _write_jsonl(root / PARITY_NAME, parity_evidence)
        _write_jsonl(root / EXERCISES_NAME, safety_exercises)
        _write_json(root / REPORT_NAME, result.report)
        _write_json(root / REVIEW_NAME, result.candidate_review)
        artifact_names = (
            POLICY_NAME,
            REQUEST_NAME,
            OBSERVATIONS_NAME,
            PARITY_NAME,
            EXERCISES_NAME,
            REPORT_NAME,
            REVIEW_NAME,
        )
        payload: dict[str, object] = {
            "run_id": request.run_id,
            "report_id": result.report.report_id,
            "candidate_review_id": result.candidate_review.package_id,
            "artifacts": tuple((name, _sha256_file(root / name)) for name in artifact_names),
            "protected_holdout_accessed": False,
            "automatic_promotion_enabled": False,
            "trading_credentials_present": False,
            "execution_enabled": False,
            "orders_submitted": 0,
            "live_capital_authorized": False,
        }
        _write_json(root / MANIFEST_NAME, _manifest(MANIFEST_SCHEMA_VERSION, payload))
        _write_checksum_index(root, (*artifact_names, MANIFEST_NAME))

    _publish_directory(destination, write)
    verify_paper_validation_package(destination)
    return result


def _verify_index(root: Path, expected_files: set[str]) -> None:
    index_path = root / CHECKSUM_INDEX_NAME
    if index_path.is_symlink() or not index_path.is_file():
        raise PaperValidationError("checksum index must be a regular file")
    entries: dict[str, str] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or name in entries:
            raise PaperValidationError("checksum index is malformed")
        entries[name] = _sha256(digest, field="checksum digest")
    if set(entries) != expected_files:
        raise PaperValidationError("checksum index file set mismatch")
    for name, digest in entries.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or _sha256_file(path) != digest:
            raise PaperValidationError(f"checksum mismatch for {name}")


def _assert_exact_fields(
    payload: Mapping[str, Any],
    model: type[Any],
    *,
    field: str,
) -> None:
    expected = {item.name for item in fields(model)}
    if set(payload) != expected:
        raise PaperValidationError(f"{field} field set mismatch")


def _string_value(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise PaperValidationError(f"{field} must be a string")
    return _text(value, field=field)


def _integer_value(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PaperValidationError(f"{field} must be an integer")
    return value


def _boolean_value(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise PaperValidationError(f"{field} must be a boolean")
    return value


def _list_value(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise PaperValidationError(f"{field} must be a list")
    return value


def _string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    return tuple(_string_value(item, field=field) for item in _list_value(value, field=field))


def _verify_derived_identity(
    payload: Mapping[str, Any],
    *,
    schema: str,
    identity_field: str,
    field: str,
) -> None:
    if payload.get("schema_version") != schema:
        raise PaperValidationError(f"{field} schema mismatch")
    claimed = _sha256(payload.get(identity_field), field=identity_field)
    body = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", identity_field}
    }
    expected = canonical_sha256({"schema_version": schema, "payload": body})
    if claimed != expected:
        raise PaperValidationError(f"{field} derived identity mismatch")


def _verify_artifact_map(
    root: Path,
    manifest: Mapping[str, Any],
    expected_names: set[str],
    *,
    field: str,
) -> None:
    entries = _list_value(manifest.get("artifacts"), field=f"{field} artifacts")
    actual: dict[str, str] = {}
    for entry in entries:
        values = _list_value(entry, field=f"{field} artifact")
        if len(values) != 2:
            raise PaperValidationError(f"{field} artifact entry is malformed")
        name = _string_value(values[0], field=f"{field} artifact name")
        if name in actual:
            raise PaperValidationError(f"{field} artifacts contain duplicates")
        actual[name] = _sha256(values[1], field=f"{field} artifact digest")
    if set(actual) != expected_names:
        raise PaperValidationError(f"{field} artifact set mismatch")
    for name, digest in actual.items():
        if _sha256_file(root / name) != digest:
            raise PaperValidationError(f"{field} artifact digest mismatch for {name}")


def _policy_from_payload(payload: Mapping[str, Any]) -> PaperValidationPolicy:
    _assert_exact_fields(payload, PaperValidationPolicy, field="policy")
    try:
        return PaperValidationPolicy(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            policy_version=_string_value(payload["policy_version"], field="policy_version"),
            minimum_duration_ms=_integer_value(
                payload["minimum_duration_ms"], field="minimum_duration_ms"
            ),
            minimum_snapshot_count=_integer_value(
                payload["minimum_snapshot_count"], field="minimum_snapshot_count"
            ),
            maximum_snapshot_gap_ms=_integer_value(
                payload["maximum_snapshot_gap_ms"], field="maximum_snapshot_gap_ms"
            ),
            minimum_fresh_source_ratio=_decimal(
                payload["minimum_fresh_source_ratio"],
                field="minimum_fresh_source_ratio",
            ),
            minimum_decision_count=_integer_value(
                payload["minimum_decision_count"], field="minimum_decision_count"
            ),
            minimum_allowed_decision_count=_integer_value(
                payload["minimum_allowed_decision_count"],
                field="minimum_allowed_decision_count",
            ),
            minimum_risk_rejection_count=_integer_value(
                payload["minimum_risk_rejection_count"],
                field="minimum_risk_rejection_count",
            ),
            maximum_drawdown_ratio=_decimal(
                payload["maximum_drawdown_ratio"], field="maximum_drawdown_ratio"
            ),
            required_exercises=tuple(
                SafetyExerciseKind(_string_value(item, field="required_exercises"))
                for item in _list_value(payload["required_exercises"], field="required_exercises")
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("policy payload is invalid") from exc


def _request_from_payload(payload: Mapping[str, Any]) -> PaperRunRequest:
    _assert_exact_fields(payload, PaperRunRequest, field="request")
    try:
        request = PaperRunRequest(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            run_id=_string_value(payload["run_id"], field="run_id"),
            created_at_ms=_integer_value(payload["created_at_ms"], field="created_at_ms"),
            window_start_ms=_integer_value(payload["window_start_ms"], field="window_start_ms"),
            window_end_ms=_integer_value(payload["window_end_ms"], field="window_end_ms"),
            bot_instance=_string_value(payload["bot_instance"], field="bot_instance"),
            mode=BotMode(_string_value(payload["mode"], field="mode")),
            model_version=_string_value(payload["model_version"], field="model_version"),
            model_hash=_string_value(payload["model_hash"], field="model_hash"),
            parameter_version=_string_value(
                payload["parameter_version"], field="parameter_version"
            ),
            parameter_hash=_string_value(payload["parameter_hash"], field="parameter_hash"),
            dataset_hash=_string_value(payload["dataset_hash"], field="dataset_hash"),
            code_sha=_string_value(payload["code_sha"], field="code_sha"),
            rollback_model_version=_string_value(
                payload["rollback_model_version"], field="rollback_model_version"
            ),
            rollback_model_hash=_string_value(
                payload["rollback_model_hash"], field="rollback_model_hash"
            ),
            rollback_parameter_version=_string_value(
                payload["rollback_parameter_version"],
                field="rollback_parameter_version",
            ),
            rollback_parameter_hash=_string_value(
                payload["rollback_parameter_hash"], field="rollback_parameter_hash"
            ),
            wh07_snapshot_schema=_string_value(
                payload["wh07_snapshot_schema"], field="wh07_snapshot_schema"
            ),
            wh08_consumer_version=_string_value(
                payload["wh08_consumer_version"], field="wh08_consumer_version"
            ),
            policy_sha256=_string_value(payload["policy_sha256"], field="policy_sha256"),
            protected_holdout_accessed=_boolean_value(
                payload["protected_holdout_accessed"],
                field="protected_holdout_accessed",
            ),
            automatic_promotion_enabled=_boolean_value(
                payload["automatic_promotion_enabled"],
                field="automatic_promotion_enabled",
            ),
            trading_credentials_present=_boolean_value(
                payload["trading_credentials_present"],
                field="trading_credentials_present",
            ),
            execution_enabled=_boolean_value(
                payload["execution_enabled"], field="execution_enabled"
            ),
            live_capital_authorized=_boolean_value(
                payload["live_capital_authorized"], field="live_capital_authorized"
            ),
            orders_submitted=_integer_value(payload["orders_submitted"], field="orders_submitted"),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("request payload is invalid") from exc
    expected_run_id = canonical_sha256(
        {
            "schema_version": REQUEST_SCHEMA_VERSION,
            "payload": _request_identity_payload(
                created_at_ms=request.created_at_ms,
                window_start_ms=request.window_start_ms,
                window_end_ms=request.window_end_ms,
                bot_instance=request.bot_instance,
                mode=request.mode,
                model_version=request.model_version,
                model_hash=request.model_hash,
                parameter_version=request.parameter_version,
                parameter_hash=request.parameter_hash,
                dataset_hash=request.dataset_hash,
                code_sha=request.code_sha,
                rollback_model_version=request.rollback_model_version,
                rollback_model_hash=request.rollback_model_hash,
                rollback_parameter_version=request.rollback_parameter_version,
                rollback_parameter_hash=request.rollback_parameter_hash,
                wh08_consumer_version=request.wh08_consumer_version,
                policy_sha256=request.policy_sha256,
            ),
        }
    )
    if request.run_id != expected_run_id:
        raise PaperValidationError("request derived identity mismatch")
    return request


def _observation_from_payload(payload: Mapping[str, Any]) -> PaperObservation:
    _assert_exact_fields(payload, PaperObservation, field="observation")
    try:
        return PaperObservation(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            snapshot_id=_string_value(payload["snapshot_id"], field="snapshot_id"),
            snapshot_sha256=_string_value(payload["snapshot_sha256"], field="snapshot_sha256"),
            observed_at_ms=_integer_value(payload["observed_at_ms"], field="observed_at_ms"),
            persistence_generation=_integer_value(
                payload["persistence_generation"], field="persistence_generation"
            ),
            bot_instance=_string_value(payload["bot_instance"], field="bot_instance"),
            mode=BotMode(_string_value(payload["mode"], field="mode")),
            health=_string_value(payload["health"], field="health"),
            model_version=_string_value(payload["model_version"], field="model_version"),
            model_hash=_string_value(payload["model_hash"], field="model_hash"),
            parameter_version=_string_value(
                payload["parameter_version"], field="parameter_version"
            ),
            parameter_hash=_string_value(payload["parameter_hash"], field="parameter_hash"),
            dataset_hash=_string_value(payload["dataset_hash"], field="dataset_hash"),
            code_sha=_string_value(payload["code_sha"], field="code_sha"),
            source_count=_integer_value(payload["source_count"], field="source_count"),
            fresh_source_count=_integer_value(
                payload["fresh_source_count"], field="fresh_source_count"
            ),
            decision_count=_integer_value(payload["decision_count"], field="decision_count"),
            allowed_decision_count=_integer_value(
                payload["allowed_decision_count"], field="allowed_decision_count"
            ),
            risk_rejection_count=_integer_value(
                payload["risk_rejection_count"], field="risk_rejection_count"
            ),
            ignored_decision_count=_integer_value(
                payload["ignored_decision_count"], field="ignored_decision_count"
            ),
            allowed_decision_ids=_string_tuple(
                payload["allowed_decision_ids"], field="allowed_decision_ids"
            ),
            risk_rejection_decision_ids=_string_tuple(
                payload["risk_rejection_decision_ids"],
                field="risk_rejection_decision_ids",
            ),
            ignored_decision_ids=_string_tuple(
                payload["ignored_decision_ids"], field="ignored_decision_ids"
            ),
            position_count=_integer_value(payload["position_count"], field="position_count"),
            position_ids=_string_tuple(payload["position_ids"], field="position_ids"),
            cumulative_realized_pnl_quote=_decimal(
                payload["cumulative_realized_pnl_quote"],
                field="cumulative_realized_pnl_quote",
            ),
            unrealized_pnl_quote=_decimal(
                payload["unrealized_pnl_quote"], field="unrealized_pnl_quote"
            ),
            simulated_equity_quote=_decimal(
                payload["simulated_equity_quote"], field="simulated_equity_quote"
            ),
            drawdown_ratio=_decimal(payload["drawdown_ratio"], field="drawdown_ratio"),
            circuit_breaker_active=_boolean_value(
                payload["circuit_breaker_active"], field="circuit_breaker_active"
            ),
            circuit_breaker_reasons=_string_tuple(
                payload["circuit_breaker_reasons"], field="circuit_breaker_reasons"
            ),
            model_drift=DriftState(_string_value(payload["model_drift"], field="model_drift")),
            data_drift=DriftState(_string_value(payload["data_drift"], field="data_drift")),
            read_only=_boolean_value(payload["read_only"], field="read_only"),
            trading_credentials_present=_boolean_value(
                payload["trading_credentials_present"],
                field="trading_credentials_present",
            ),
            order_adapter_present=_boolean_value(
                payload["order_adapter_present"], field="order_adapter_present"
            ),
            orders_submitted=_integer_value(payload["orders_submitted"], field="orders_submitted"),
            live_capital_authorized=_boolean_value(
                payload["live_capital_authorized"], field="live_capital_authorized"
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("observation payload is invalid") from exc


def _parity_from_payload(payload: Mapping[str, Any]) -> ReplayShadowParityEvidence:
    _assert_exact_fields(payload, ReplayShadowParityEvidence, field="parity")
    try:
        parity = ReplayShadowParityEvidence(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            parity_id=_string_value(payload["parity_id"], field="parity_id"),
            shadow_decision_id=_string_value(
                payload["shadow_decision_id"], field="shadow_decision_id"
            ),
            label_id=_string_value(payload["label_id"], field="label_id"),
            symbol=_string_value(payload["symbol"], field="symbol"),
            side=TradeDirection(_string_value(payload["side"], field="side")),
            decision_timestamp_ms=_integer_value(
                payload["decision_timestamp_ms"], field="decision_timestamp_ms"
            ),
            dataset_hash=_string_value(payload["dataset_hash"], field="dataset_hash"),
            code_sha=_string_value(payload["code_sha"], field="code_sha"),
            take_profit_ratio=_decimal(payload["take_profit_ratio"], field="take_profit_ratio"),
            stop_loss_ratio=_decimal(payload["stop_loss_ratio"], field="stop_loss_ratio"),
            label_outcome=LabelOutcome(
                _string_value(payload["label_outcome"], field="label_outcome")
            ),
            identities_match=_boolean_value(payload["identities_match"], field="identities_match"),
            policy_match=_boolean_value(payload["policy_match"], field="policy_match"),
            execution_authority_absent=_boolean_value(
                payload["execution_authority_absent"],
                field="execution_authority_absent",
            ),
        )
    except (ShadowRuntimeError, TypeError, ValueError) as exc:
        raise PaperValidationError("parity payload is invalid") from exc
    expected_parity_id = canonical_sha256(
        {
            "schema_version": parity.schema_version,
            "payload": {
                "shadow_decision_id": parity.shadow_decision_id,
                "label_id": parity.label_id,
                "symbol": parity.symbol,
                "side": parity.side.value,
                "decision_timestamp_ms": parity.decision_timestamp_ms,
                "dataset_hash": parity.dataset_hash,
                "code_sha": parity.code_sha,
                "take_profit_ratio": parity.take_profit_ratio,
                "stop_loss_ratio": parity.stop_loss_ratio,
                "label_outcome": parity.label_outcome.value,
                "identities_match": parity.identities_match,
                "policy_match": parity.policy_match,
                "execution_authority_absent": parity.execution_authority_absent,
            },
        }
    )
    if parity.parity_id != expected_parity_id:
        raise PaperValidationError("parity derived identity mismatch")
    return parity


def _exercise_from_payload(payload: Mapping[str, Any]) -> SafetyExerciseEvidence:
    _assert_exact_fields(payload, SafetyExerciseEvidence, field="safety exercise")
    try:
        return SafetyExerciseEvidence(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            exercise_id=_string_value(payload["exercise_id"], field="exercise_id"),
            run_id=_string_value(payload["run_id"], field="run_id"),
            kind=SafetyExerciseKind(_string_value(payload["kind"], field="kind")),
            observed_at_ms=_integer_value(payload["observed_at_ms"], field="observed_at_ms"),
            source_snapshot_id=_string_value(
                payload["source_snapshot_id"], field="source_snapshot_id"
            ),
            expected_reason=_string_value(payload["expected_reason"], field="expected_reason"),
            observed_reasons=_string_tuple(payload["observed_reasons"], field="observed_reasons"),
            passed=_boolean_value(payload["passed"], field="passed"),
            state_recovered=_boolean_value(payload["state_recovered"], field="state_recovered"),
            read_only=_boolean_value(payload["read_only"], field="read_only"),
            trading_credentials_present=_boolean_value(
                payload["trading_credentials_present"],
                field="trading_credentials_present",
            ),
            order_adapter_present=_boolean_value(
                payload["order_adapter_present"], field="order_adapter_present"
            ),
            orders_submitted=_integer_value(payload["orders_submitted"], field="orders_submitted"),
            live_capital_authorized=_boolean_value(
                payload["live_capital_authorized"], field="live_capital_authorized"
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("safety exercise payload is invalid") from exc


def _summary_from_payload(payload: Mapping[str, Any]) -> PaperEvidenceSummary:
    _assert_exact_fields(payload, PaperEvidenceSummary, field="evidence summary")
    try:
        return PaperEvidenceSummary(
            observation_start_ms=_integer_value(
                payload["observation_start_ms"], field="observation_start_ms"
            ),
            observation_end_ms=_integer_value(
                payload["observation_end_ms"], field="observation_end_ms"
            ),
            duration_ms=_integer_value(payload["duration_ms"], field="duration_ms"),
            snapshot_count=_integer_value(payload["snapshot_count"], field="snapshot_count"),
            maximum_gap_ms=_integer_value(payload["maximum_gap_ms"], field="maximum_gap_ms"),
            source_sample_count=_integer_value(
                payload["source_sample_count"], field="source_sample_count"
            ),
            fresh_source_sample_count=_integer_value(
                payload["fresh_source_sample_count"],
                field="fresh_source_sample_count",
            ),
            fresh_source_ratio=_decimal(payload["fresh_source_ratio"], field="fresh_source_ratio"),
            decision_count=_integer_value(payload["decision_count"], field="decision_count"),
            allowed_decision_count=_integer_value(
                payload["allowed_decision_count"], field="allowed_decision_count"
            ),
            risk_rejection_count=_integer_value(
                payload["risk_rejection_count"], field="risk_rejection_count"
            ),
            ignored_decision_count=_integer_value(
                payload["ignored_decision_count"], field="ignored_decision_count"
            ),
            unique_position_count=_integer_value(
                payload["unique_position_count"], field="unique_position_count"
            ),
            maximum_drawdown_ratio=_decimal(
                payload["maximum_drawdown_ratio"], field="maximum_drawdown_ratio"
            ),
            minimum_equity_quote=_decimal(
                payload["minimum_equity_quote"], field="minimum_equity_quote"
            ),
            maximum_equity_quote=_decimal(
                payload["maximum_equity_quote"], field="maximum_equity_quote"
            ),
            parity_count=_integer_value(payload["parity_count"], field="parity_count"),
            safety_exercise_kinds=tuple(
                SafetyExerciseKind(_string_value(item, field="safety_exercise_kinds"))
                for item in _list_value(
                    payload["safety_exercise_kinds"], field="safety_exercise_kinds"
                )
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("evidence summary payload is invalid") from exc


def _report_from_payload(payload: Mapping[str, Any]) -> PaperValidationReport:
    _assert_exact_fields(payload, PaperValidationReport, field="report")
    _verify_derived_identity(
        payload,
        schema=REPORT_SCHEMA_VERSION,
        identity_field="report_id",
        field="report",
    )
    try:
        return PaperValidationReport(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            report_id=_string_value(payload["report_id"], field="report_id"),
            run_id=_string_value(payload["run_id"], field="run_id"),
            policy_sha256=_string_value(payload["policy_sha256"], field="policy_sha256"),
            outcome=PaperValidationOutcome(_string_value(payload["outcome"], field="outcome")),
            summary=_summary_from_payload(payload["summary"]),
            blocker_codes=_string_tuple(payload["blocker_codes"], field="blocker_codes"),
            candidate_review_eligible=_boolean_value(
                payload["candidate_review_eligible"],
                field="candidate_review_eligible",
            ),
            owner_decision_required=_boolean_value(
                payload["owner_decision_required"], field="owner_decision_required"
            ),
            automatic_promotion_enabled=_boolean_value(
                payload["automatic_promotion_enabled"],
                field="automatic_promotion_enabled",
            ),
            protected_holdout_accessed=_boolean_value(
                payload["protected_holdout_accessed"],
                field="protected_holdout_accessed",
            ),
            trading_credentials_present=_boolean_value(
                payload["trading_credentials_present"],
                field="trading_credentials_present",
            ),
            execution_enabled=_boolean_value(
                payload["execution_enabled"], field="execution_enabled"
            ),
            orders_submitted=_integer_value(payload["orders_submitted"], field="orders_submitted"),
            live_capital_authorized=_boolean_value(
                payload["live_capital_authorized"], field="live_capital_authorized"
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("report payload is invalid") from exc


def _review_from_payload(payload: Mapping[str, Any]) -> CandidateReviewPackage:
    _assert_exact_fields(payload, CandidateReviewPackage, field="candidate review")
    _verify_derived_identity(
        payload,
        schema=REVIEW_SCHEMA_VERSION,
        identity_field="package_id",
        field="candidate review",
    )
    try:
        return CandidateReviewPackage(
            schema_version=_string_value(payload["schema_version"], field="schema_version"),
            package_id=_string_value(payload["package_id"], field="package_id"),
            report_id=_string_value(payload["report_id"], field="report_id"),
            run_id=_string_value(payload["run_id"], field="run_id"),
            eligible_for_owner_review=_boolean_value(
                payload["eligible_for_owner_review"],
                field="eligible_for_owner_review",
            ),
            model_version=_string_value(payload["model_version"], field="model_version"),
            model_hash=_string_value(payload["model_hash"], field="model_hash"),
            parameter_version=_string_value(
                payload["parameter_version"], field="parameter_version"
            ),
            parameter_hash=_string_value(payload["parameter_hash"], field="parameter_hash"),
            rollback_model_version=_string_value(
                payload["rollback_model_version"], field="rollback_model_version"
            ),
            rollback_model_hash=_string_value(
                payload["rollback_model_hash"], field="rollback_model_hash"
            ),
            rollback_parameter_version=_string_value(
                payload["rollback_parameter_version"],
                field="rollback_parameter_version",
            ),
            rollback_parameter_hash=_string_value(
                payload["rollback_parameter_hash"], field="rollback_parameter_hash"
            ),
            owner_decision_required=_boolean_value(
                payload["owner_decision_required"], field="owner_decision_required"
            ),
            automatic_promotion_enabled=_boolean_value(
                payload["automatic_promotion_enabled"],
                field="automatic_promotion_enabled",
            ),
            trading_credentials_present=_boolean_value(
                payload["trading_credentials_present"],
                field="trading_credentials_present",
            ),
            execution_enabled=_boolean_value(
                payload["execution_enabled"], field="execution_enabled"
            ),
            orders_submitted=_integer_value(payload["orders_submitted"], field="orders_submitted"),
            live_capital_authorized=_boolean_value(
                payload["live_capital_authorized"], field="live_capital_authorized"
            ),
        )
    except (TypeError, ValueError) as exc:
        raise PaperValidationError("candidate review payload is invalid") from exc


def _verify_manifest(payload: Mapping[str, Any], *, schema: str, field: str) -> None:
    if payload.get("schema_version") != schema:
        raise PaperValidationError(f"{field} schema mismatch")
    claimed = _sha256(payload.get("manifest_sha256"), field=f"{field}_sha256")
    body = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", "manifest_sha256"}
    }
    expected = canonical_sha256({"schema_version": schema, "payload": body})
    if claimed != expected:
        raise PaperValidationError(f"{field} self-hash mismatch")
    _assert_zero_authority(payload, field=field)


def _verify_root(root: Path, required: set[str], *, field: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise PaperValidationError(f"{field} root must be a regular directory")
    if {item.name for item in root.iterdir()} != required:
        raise PaperValidationError(f"{field} file set mismatch")
    _verify_index(root, required - {CHECKSUM_INDEX_NAME})


def verify_paper_run_request(root: Path) -> dict[str, Any]:
    required = {POLICY_NAME, REQUEST_NAME, ACTIVATION_MANIFEST_NAME, CHECKSUM_INDEX_NAME}
    _verify_root(root, required, field="activation")
    manifest = _read_json(root / ACTIVATION_MANIFEST_NAME, field="activation manifest")
    request_payload = _read_json(root / REQUEST_NAME, field="request")
    policy_payload = _read_json(root / POLICY_NAME, field="policy")
    expected_manifest_fields = {
        "schema_version",
        "manifest_sha256",
        "run_id",
        "policy_sha256",
        "artifacts",
        "protected_holdout_accessed",
        "automatic_promotion_enabled",
        "trading_credentials_present",
        "execution_enabled",
        "orders_submitted",
        "live_capital_authorized",
    }
    if set(manifest) != expected_manifest_fields:
        raise PaperValidationError("activation manifest field set mismatch")
    _verify_manifest(
        manifest,
        schema=ACTIVATION_SCHEMA_VERSION,
        field="activation manifest",
    )
    _verify_artifact_map(
        root,
        manifest,
        {POLICY_NAME, REQUEST_NAME},
        field="activation manifest",
    )
    policy = _policy_from_payload(policy_payload)
    request = _request_from_payload(request_payload)
    if canonical_sha256(policy_payload) != policy.policy_sha256:
        raise PaperValidationError("activation policy canonical identity mismatch")
    _assert_request_matches_policy(request, policy, field="activation")
    if manifest.get("run_id") != request.run_id:
        raise PaperValidationError("activation run identity mismatch")
    if manifest.get("policy_sha256") != policy.policy_sha256:
        raise PaperValidationError("activation policy identity mismatch")
    return {"run_id": request.run_id, "verified": True}


def verify_paper_validation_package(root: Path) -> dict[str, Any]:  # noqa: C901
    required = {
        POLICY_NAME,
        REQUEST_NAME,
        OBSERVATIONS_NAME,
        PARITY_NAME,
        EXERCISES_NAME,
        REPORT_NAME,
        REVIEW_NAME,
        MANIFEST_NAME,
        CHECKSUM_INDEX_NAME,
    }
    _verify_root(root, required, field="paper validation")
    manifest = _read_json(root / MANIFEST_NAME, field="manifest")
    policy_payload = _read_json(root / POLICY_NAME, field="policy")
    request_payload = _read_json(root / REQUEST_NAME, field="request")
    report_payload = _read_json(root / REPORT_NAME, field="report")
    review_payload = _read_json(root / REVIEW_NAME, field="candidate review")
    observation_payloads = _read_jsonl(root / OBSERVATIONS_NAME, field="observations")
    parity_payloads = _read_jsonl(root / PARITY_NAME, field="parity")
    exercise_payloads = _read_jsonl(root / EXERCISES_NAME, field="exercises")
    expected_manifest_fields = {
        "schema_version",
        "manifest_sha256",
        "run_id",
        "report_id",
        "candidate_review_id",
        "artifacts",
        "protected_holdout_accessed",
        "automatic_promotion_enabled",
        "trading_credentials_present",
        "execution_enabled",
        "orders_submitted",
        "live_capital_authorized",
    }
    if set(manifest) != expected_manifest_fields:
        raise PaperValidationError("manifest field set mismatch")
    _verify_manifest(manifest, schema=MANIFEST_SCHEMA_VERSION, field="manifest")
    artifact_names = {
        POLICY_NAME,
        REQUEST_NAME,
        OBSERVATIONS_NAME,
        PARITY_NAME,
        EXERCISES_NAME,
        REPORT_NAME,
        REVIEW_NAME,
    }
    _verify_artifact_map(root, manifest, artifact_names, field="manifest")
    policy = _policy_from_payload(policy_payload)
    request = _request_from_payload(request_payload)
    if canonical_sha256(policy_payload) != policy.policy_sha256:
        raise PaperValidationError("policy canonical identity mismatch")
    _assert_request_matches_policy(request, policy, field="package")
    observations = tuple(_observation_from_payload(payload) for payload in observation_payloads)
    if not observations:
        raise PaperValidationError("paper validation requires observations")
    if len({item.snapshot_id for item in observations}) != len(observations):
        raise PaperValidationError("paper observations contain duplicate snapshot ids")
    if any(
        later.observed_at_ms <= earlier.observed_at_ms for earlier, later in pairwise(observations)
    ):
        raise PaperValidationError("paper observations must be strictly increasing")
    for observation in observations:
        _validate_request_observation(request, observation)
    parity = tuple(_parity_from_payload(payload) for payload in parity_payloads)
    if len({item.parity_id for item in parity}) != len(parity):
        raise PaperValidationError("parity evidence contains duplicate ids")
    parity_ids = {item.shadow_decision_id for item in parity}
    if len(parity_ids) != len(parity):
        raise PaperValidationError("parity evidence contains duplicate decisions")
    allowed_ids = {
        decision_id
        for observation in observations
        for decision_id in observation.allowed_decision_ids
    }
    for item in parity:
        if item.shadow_decision_id not in allowed_ids:
            raise PaperValidationError("parity evidence does not bind an allowed decision")
        if item.dataset_hash != request.dataset_hash or item.code_sha != request.code_sha:
            raise PaperValidationError("parity evidence identity mismatch")
        if not request.window_start_ms <= item.decision_timestamp_ms <= request.window_end_ms:
            raise PaperValidationError("parity evidence falls outside request window")
    exercises = tuple(_exercise_from_payload(payload) for payload in exercise_payloads)
    if len({item.exercise_id for item in exercises}) != len(exercises):
        raise PaperValidationError("safety exercises contain duplicate ids")
    exercise_kinds = _validate_exercises(request, observations, exercises)
    summary = _summarize(observations, len(parity), exercise_kinds)
    blockers = _blocker_codes(policy, summary, allowed_ids, parity_ids)
    expected_report = _build_report(request, policy, summary, blockers)
    report = _report_from_payload(report_payload)
    if canonical_json(report) != canonical_json(expected_report):
        raise PaperValidationError("report semantics mismatch")
    expected_review = _build_review(request, expected_report)
    review = _review_from_payload(review_payload)
    if canonical_json(review) != canonical_json(expected_review):
        raise PaperValidationError("candidate review semantics mismatch")
    if manifest.get("run_id") != request.run_id:
        raise PaperValidationError("package run identity mismatch")
    if manifest.get("report_id") != report.report_id:
        raise PaperValidationError("package report identity mismatch")
    if manifest.get("candidate_review_id") != review.package_id:
        raise PaperValidationError("package candidate review identity mismatch")
    return {
        "run_id": request.run_id,
        "report_id": report.report_id,
        "candidate_review_id": review.package_id,
        "outcome": report.outcome.value,
        "observation_count": len(observations),
        "parity_count": len(parity),
        "exercise_count": len(exercises),
        "verified": True,
    }
