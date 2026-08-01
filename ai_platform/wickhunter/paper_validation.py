from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import BotMode, DriftState, ShadowStatus
from ai_platform.wickhunter.shadow_runtime import (
    PortalObservabilitySnapshot,
    ReplayShadowParityEvidence,
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


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise PaperValidationError(f"{field} must be an integer")
    try:
        parsed = int(str(value))
    except ValueError as exc:
        raise PaperValidationError(f"{field} must be an integer") from exc
    if parsed < minimum:
        raise PaperValidationError(f"{field} must be >= {minimum}")
    return parsed


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise PaperValidationError(f"{field} line {number} must be an object")
            records.append(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaperValidationError(f"unable to read {field}") from exc
    return tuple(records)


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


def _assert_zero_authority(payload: Mapping[str, object], *, field: str) -> None:
    if any(
        (
            bool(payload.get("protected_holdout_accessed", False)),
            bool(payload.get("automatic_promotion_enabled", False)),
            bool(payload.get("trading_credentials_present", False)),
            bool(payload.get("order_adapter_present", False)),
            bool(payload.get("execution_enabled", False)),
            bool(payload.get("live_capital_authorized", False)),
            payload.get("orders_submitted", 0) != 0,
        )
    ):
        raise PaperValidationError(f"{field} contains forbidden authority")


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
        for field_name in (
            "minimum_duration_ms",
            "minimum_snapshot_count",
            "maximum_snapshot_gap_ms",
            "minimum_decision_count",
            "minimum_allowed_decision_count",
            "minimum_risk_rejection_count",
        ):
            if getattr(self, field_name) < 1:
                raise PaperValidationError(f"{field_name} must be >= 1")
        if not Decimal("0") <= self.minimum_fresh_source_ratio <= Decimal("1"):
            raise PaperValidationError("minimum_fresh_source_ratio must be in [0, 1]")
        if not Decimal("0") < self.maximum_drawdown_ratio < Decimal("1"):
            raise PaperValidationError("maximum_drawdown_ratio must be in (0, 1)")
        expected = tuple(sorted(set(self.required_exercises), key=lambda item: item.value))
        if self.required_exercises != expected:
            raise PaperValidationError("required_exercises must be unique and sorted")

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
        _text(self.bot_instance, field="bot_instance")
        if self.mode not in {BotMode.SHADOW, BotMode.PAPER}:
            raise PaperValidationError("paper request mode must be shadow or paper")
        for value, field_name in (
            (self.model_version, "model_version"),
            (self.parameter_version, "parameter_version"),
            (self.rollback_model_version, "rollback_model_version"),
            (self.rollback_parameter_version, "rollback_parameter_version"),
            (self.wh07_snapshot_schema, "wh07_snapshot_schema"),
            (self.wh08_consumer_version, "wh08_consumer_version"),
        ):
            _text(value, field=field_name)
        for value, field_name in (
            (self.model_hash, "model_hash"),
            (self.parameter_hash, "parameter_hash"),
            (self.dataset_hash, "dataset_hash"),
            (self.rollback_model_hash, "rollback_model_hash"),
            (self.rollback_parameter_hash, "rollback_parameter_hash"),
            (self.policy_sha256, "policy_sha256"),
        ):
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
    position_count: int
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
        for field_name in (
            "source_count",
            "fresh_source_count",
            "decision_count",
            "allowed_decision_count",
            "risk_rejection_count",
            "ignored_decision_count",
            "position_count",
        ):
            if getattr(self, field_name) < 0:
                raise PaperValidationError(f"{field_name} must be >= 0")
        if self.fresh_source_count > self.source_count:
            raise PaperValidationError("fresh sources exceed all sources")
        if (
            self.allowed_decision_count
            + self.risk_rejection_count
            + self.ignored_decision_count
            != self.decision_count
        ):
            raise PaperValidationError("decision counts are inconsistent")
        for value, field_name in (
            (self.cumulative_realized_pnl_quote, "cumulative_realized_pnl_quote"),
            (self.unrealized_pnl_quote, "unrealized_pnl_quote"),
            (self.simulated_equity_quote, "simulated_equity_quote"),
            (self.drawdown_ratio, "drawdown_ratio"),
        ):
            _decimal(value, field=field_name)
        if self.simulated_equity_quote <= 0:
            raise PaperValidationError("simulated equity must be positive")
        if not Decimal("0") <= self.drawdown_ratio <= Decimal("1"):
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
    payload = {
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
        "policy_sha256": policy.policy_sha256,
    }
    return PaperRunRequest(
        schema_version=REQUEST_SCHEMA_VERSION,
        run_id=canonical_sha256({"schema_version": REQUEST_SCHEMA_VERSION, "payload": payload}),
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
    counts = {status: 0 for status in ShadowStatus}
    for decision in snapshot.decisions:
        counts[decision.status] += 1
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
        allowed_decision_count=counts[ShadowStatus.SIMULATED_ALLOWED],
        risk_rejection_count=counts[ShadowStatus.REJECTED_BY_RISK],
        ignored_decision_count=counts[ShadowStatus.IGNORED],
        position_count=len(snapshot.positions),
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


def _validate_request_observation(request: PaperRunRequest, observation: PaperObservation) -> None:
    for actual, expected, field_name in (
        (observation.bot_instance, request.bot_instance, "bot_instance"),
        (observation.mode, request.mode, "mode"),
        (observation.model_version, request.model_version, "model_version"),
        (observation.model_hash, request.model_hash, "model_hash"),
        (observation.parameter_version, request.parameter_version, "parameter_version"),
        (observation.parameter_hash, request.parameter_hash, "parameter_hash"),
        (observation.dataset_hash, request.dataset_hash, "dataset_hash"),
        (observation.code_sha, request.code_sha, "code_sha"),
    ):
        if actual != expected:
            raise PaperValidationError(f"observation {field_name} does not match request")
    if not request.window_start_ms <= observation.observed_at_ms <= request.window_end_ms:
        raise PaperValidationError("observation falls outside the immutable request window")


def evaluate_paper_evidence(
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
    snapshots: Sequence[PortalObservabilitySnapshot],
    parity_evidence: Sequence[ReplayShadowParityEvidence],
    safety_exercises: Sequence[SafetyExerciseEvidence],
) -> PaperValidationResult:  # noqa: C901
    if request.policy_sha256 != policy.policy_sha256:
        raise PaperValidationError("request policy identity mismatch")
    observations = tuple(
        sorted(
            (observation_from_snapshot(item) for item in snapshots),
            key=lambda item: item.observed_at_ms,
        )
    )
    if not observations:
        raise PaperValidationError("paper validation requires observations")
    if len({item.snapshot_id for item in observations}) != len(observations):
        raise PaperValidationError("paper observations contain duplicate snapshot ids")
    if any(
        later.observed_at_ms <= earlier.observed_at_ms
        for earlier, later in zip(observations, observations[1:], strict=False)
    ):
        raise PaperValidationError("paper observations must be strictly increasing")
    for observation in observations:
        _validate_request_observation(request, observation)

    gaps = tuple(
        later.observed_at_ms - earlier.observed_at_ms
        for earlier, later in zip(observations, observations[1:], strict=False)
    )
    duration_ms = observations[-1].observed_at_ms - observations[0].observed_at_ms
    maximum_gap_ms = max(gaps, default=0)
    source_samples = sum(item.source_count for item in observations)
    fresh_samples = sum(item.fresh_source_count for item in observations)
    fresh_ratio = Decimal(fresh_samples) / Decimal(source_samples) if source_samples else Decimal("0")
    decision_count = sum(item.decision_count for item in observations)
    allowed_count = sum(item.allowed_decision_count for item in observations)
    rejected_count = sum(item.risk_rejection_count for item in observations)
    ignored_count = sum(item.ignored_decision_count for item in observations)
    position_count = max(item.position_count for item in observations)
    max_drawdown = max(item.drawdown_ratio for item in observations)
    min_equity = min(item.simulated_equity_quote for item in observations)
    max_equity = max(item.simulated_equity_quote for item in observations)

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
        if not (item.identities_match and item.policy_match and item.execution_authority_absent):
            raise PaperValidationError("parity evidence is not accepted")

    exercise_kinds = tuple(
        sorted({item.kind for item in safety_exercises}, key=lambda item: item.value)
    )
    snapshot_ids = {item.snapshot_id for item in observations}
    for exercise in safety_exercises:
        if exercise.run_id != request.run_id:
            raise PaperValidationError("safety exercise run identity mismatch")
        if exercise.source_snapshot_id not in snapshot_ids:
            raise PaperValidationError("safety exercise snapshot identity mismatch")

    blockers: list[str] = []
    if duration_ms < policy.minimum_duration_ms:
        blockers.append("minimum_duration_not_met")
    if len(observations) < policy.minimum_snapshot_count:
        blockers.append("minimum_snapshot_count_not_met")
    if maximum_gap_ms > policy.maximum_snapshot_gap_ms:
        blockers.append("maximum_snapshot_gap_exceeded")
    if fresh_ratio < policy.minimum_fresh_source_ratio:
        blockers.append("fresh_source_ratio_below_policy")
    if decision_count < policy.minimum_decision_count:
        blockers.append("minimum_decision_count_not_met")
    if allowed_count < policy.minimum_allowed_decision_count:
        blockers.append("minimum_allowed_decision_count_not_met")
    if rejected_count < policy.minimum_risk_rejection_count:
        blockers.append("minimum_risk_rejection_count_not_met")
    if max_drawdown > policy.maximum_drawdown_ratio:
        blockers.append("maximum_drawdown_exceeded")
    if not allowed_ids.issubset(parity_ids):
        blockers.append("replay_shadow_parity_incomplete")
    if set(policy.required_exercises) - set(exercise_kinds):
        blockers.append("required_safety_exercises_incomplete")

    summary = PaperEvidenceSummary(
        observation_start_ms=observations[0].observed_at_ms,
        observation_end_ms=observations[-1].observed_at_ms,
        duration_ms=duration_ms,
        snapshot_count=len(observations),
        maximum_gap_ms=maximum_gap_ms,
        source_sample_count=source_samples,
        fresh_source_sample_count=fresh_samples,
        fresh_source_ratio=fresh_ratio,
        decision_count=decision_count,
        allowed_decision_count=allowed_count,
        risk_rejection_count=rejected_count,
        ignored_decision_count=ignored_count,
        unique_position_count=position_count,
        maximum_drawdown_ratio=max_drawdown,
        minimum_equity_quote=min_equity,
        maximum_equity_quote=max_equity,
        parity_count=len(parity_evidence),
        safety_exercise_kinds=exercise_kinds,
    )
    outcome = (
        PaperValidationOutcome.READY_FOR_OWNER_REVIEW
        if not blockers
        else PaperValidationOutcome.INCOMPLETE
    )
    blockers_tuple = tuple(sorted(set(blockers)))
    report_payload = {
        "run_id": request.run_id,
        "policy_sha256": policy.policy_sha256,
        "outcome": outcome.value,
        "summary": summary,
        "blocker_codes": blockers_tuple,
        "candidate_review_eligible": outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW,
        "owner_decision_required": True,
        "automatic_promotion_enabled": False,
        "protected_holdout_accessed": False,
        "trading_credentials_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    report = PaperValidationReport(
        schema_version=REPORT_SCHEMA_VERSION,
        report_id=canonical_sha256(
            {"schema_version": REPORT_SCHEMA_VERSION, "payload": report_payload}
        ),
        run_id=request.run_id,
        policy_sha256=policy.policy_sha256,
        outcome=outcome,
        summary=summary,
        blocker_codes=blockers_tuple,
        candidate_review_eligible=outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW,
        owner_decision_required=True,
        automatic_promotion_enabled=False,
        protected_holdout_accessed=False,
        trading_credentials_present=False,
        execution_enabled=False,
        orders_submitted=0,
        live_capital_authorized=False,
    )
    review_payload = {
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
    review = CandidateReviewPackage(
        schema_version=REVIEW_SCHEMA_VERSION,
        package_id=canonical_sha256(
            {"schema_version": REVIEW_SCHEMA_VERSION, "payload": review_payload}
        ),
        **review_payload,
    )
    return PaperValidationResult(
        report=report,
        candidate_review=review,
        observations=observations,
    )


def _publish_directory(destination: Path, writer: Any) -> None:
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


def publish_paper_run_request(
    destination: Path,
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
) -> dict[str, Any]:
    if request.policy_sha256 != policy.policy_sha256:
        raise PaperValidationError("activation policy identity mismatch")

    def write(root: Path) -> None:
        _write_json(root / POLICY_NAME, policy)
        _write_json(root / REQUEST_NAME, request)
        artifacts = (
            (POLICY_NAME, _sha256_file(root / POLICY_NAME)),
            (REQUEST_NAME, _sha256_file(root / REQUEST_NAME)),
        )
        payload = {
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
        manifest = {
            "schema_version": ACTIVATION_SCHEMA_VERSION,
            "manifest_sha256": canonical_sha256(
                {"schema_version": ACTIVATION_SCHEMA_VERSION, "payload": payload}
            ),
            **payload,
        }
        _write_json(root / ACTIVATION_MANIFEST_NAME, manifest)
        _write_checksum_index(
            root,
            (POLICY_NAME, REQUEST_NAME, ACTIVATION_MANIFEST_NAME),
        )

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
        artifacts = tuple((name, _sha256_file(root / name)) for name in artifact_names)
        payload = {
            "run_id": request.run_id,
            "report_id": result.report.report_id,
            "candidate_review_id": result.candidate_review.package_id,
            "artifacts": artifacts,
            "protected_holdout_accessed": False,
            "automatic_promotion_enabled": False,
            "trading_credentials_present": False,
            "execution_enabled": False,
            "orders_submitted": 0,
            "live_capital_authorized": False,
        }
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "manifest_sha256": canonical_sha256(
                {"schema_version": MANIFEST_SCHEMA_VERSION, "payload": payload}
            ),
            **payload,
        }
        _write_json(root / MANIFEST_NAME, manifest)
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


def verify_paper_run_request(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise PaperValidationError("activation root must be a regular directory")
    required = {POLICY_NAME, REQUEST_NAME, ACTIVATION_MANIFEST_NAME, CHECKSUM_INDEX_NAME}
    if {item.name for item in root.iterdir()} != required:
        raise PaperValidationError("activation file set mismatch")
    _verify_index(root, required - {CHECKSUM_INDEX_NAME})
    manifest = _read_json(root / ACTIVATION_MANIFEST_NAME, field="activation manifest")
    request = _read_json(root / REQUEST_NAME, field="request")
    policy = _read_json(root / POLICY_NAME, field="policy")
    _verify_manifest(
        manifest,
        schema=ACTIVATION_SCHEMA_VERSION,
        field="activation manifest",
    )
    _assert_zero_authority(request, field="request")
    if manifest.get("run_id") != request.get("run_id"):
        raise PaperValidationError("activation run identity mismatch")
    if manifest.get("policy_sha256") != policy.get("policy_sha256", canonical_sha256(policy)):
        if manifest.get("policy_sha256") != canonical_sha256(policy):
            raise PaperValidationError("activation policy identity mismatch")
    return {"run_id": request["run_id"], "verified": True}


def verify_paper_validation_package(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise PaperValidationError("paper validation root must be a regular directory")
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
    if {item.name for item in root.iterdir()} != required:
        raise PaperValidationError("paper validation file set mismatch")
    _verify_index(root, required - {CHECKSUM_INDEX_NAME})
    manifest = _read_json(root / MANIFEST_NAME, field="manifest")
    request = _read_json(root / REQUEST_NAME, field="request")
    report = _read_json(root / REPORT_NAME, field="report")
    review = _read_json(root / REVIEW_NAME, field="candidate review")
    observations = _read_jsonl(root / OBSERVATIONS_NAME, field="observations")
    parity = _read_jsonl(root / PARITY_NAME, field="parity")
    exercises = _read_jsonl(root / EXERCISES_NAME, field="exercises")
    _verify_manifest(manifest, schema=MANIFEST_SCHEMA_VERSION, field="manifest")
    for payload, field in (
        (request, "request"),
        (report, "report"),
        (review, "candidate review"),
    ):
        _assert_zero_authority(payload, field=field)
    if manifest.get("run_id") != request.get("run_id") or report.get("run_id") != request.get("run_id"):
        raise PaperValidationError("package run identity mismatch")
    if manifest.get("report_id") != report.get("report_id"):
        raise PaperValidationError("package report identity mismatch")
    if manifest.get("candidate_review_id") != review.get("package_id"):
        raise PaperValidationError("package candidate review identity mismatch")
    if review.get("report_id") != report.get("report_id"):
        raise PaperValidationError("candidate review report identity mismatch")
    return {
        "run_id": request["run_id"],
        "report_id": report["report_id"],
        "candidate_review_id": review["package_id"],
        "outcome": report["outcome"],
        "observation_count": len(observations),
        "parity_count": len(parity),
        "exercise_count": len(exercises),
        "verified": True,
    }
