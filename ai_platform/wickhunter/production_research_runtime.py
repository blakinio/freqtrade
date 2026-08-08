from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from ai_platform.wickhunter.candidate_activation import (
    VerifiedCandidatePackage,
    load_verified_candidate_package,
)
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateScore,
    LiquidationFeatureVector,
    ShadowDecisionEvidence,
    ShadowStatus,
    WickHunterCandidate,
)
from ai_platform.wickhunter.lightgbm_scorer import (
    LightGBMAdvisoryScorer,
    _feature_values,
)
from ai_platform.wickhunter.parameters import DEFAULT_RESEARCH_BOUNDS, WickHunterParameters
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime_common import ShadowRuntimePolicy
from ai_platform.wickhunter.shadow_runtime_engine import ShadowRuntime
from ai_platform.wickhunter.shadow_runtime_snapshot import ShadowRuntimeStepResult
from ai_platform.wickhunter.shadow_runtime_state import ShadowRuntimeTick
from ai_platform.wickhunter.shadow_runtime_storage import ShadowRuntimeStore


GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RESEARCH_IDENTITY_SCHEMA = "wickhunter-production-research-runtime-identity-v1"
RESEARCH_DECISION_SCHEMA = "wickhunter-production-research-decision-v1"
RESEARCH_OUTCOME_SCHEMA = "wickhunter-production-research-outcome-v1"
RESEARCH_TELEMETRY_SCHEMA = "wickhunter-production-research-telemetry-v1"
FROZEN_NO_TRADE_CONFIDENCE = Decimal("0.60")
FROZEN_OUTCOME_HORIZON_MS = 900_000
ZERO_AUTHORITY: dict[str, object] = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


class ProductionResearchRuntimeError(RuntimeError):
    """Raised when the WH09 production research runtime cannot fail closed."""


def _sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if SHA256_RE.fullmatch(normalized) is None:
        raise ProductionResearchRuntimeError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


def _git_sha(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if GIT_SHA_RE.fullmatch(normalized) is None:
        raise ProductionResearchRuntimeError(f"{field_name} must be an exact lowercase Git SHA")
    return normalized


def _absolute_root(path: Path, *, field_name: str, create: bool = False) -> Path:
    if not path.is_absolute():
        raise ProductionResearchRuntimeError(f"{field_name} must be absolute")
    if path.is_symlink():
        raise ProductionResearchRuntimeError(f"{field_name} cannot be a symlink")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ProductionResearchRuntimeError(f"{field_name} must be a directory")
    return path


def _load_object(path: Path, *, field_name: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ProductionResearchRuntimeError(f"{field_name} must be a regular file")
    if path.stat().st_size <= 0 or path.stat().st_size > 512 * 1024:
        raise ProductionResearchRuntimeError(f"{field_name} size is invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionResearchRuntimeError(f"unable to read {field_name}") from exc
    if not isinstance(payload, dict):
        raise ProductionResearchRuntimeError(f"{field_name} must contain an object")
    return payload


def _write_new_or_verify(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ProductionResearchRuntimeError("research journal path cannot traverse a symlink")
    content = canonical_json(payload) + "\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
    except FileExistsError:
        existing = _load_object(path, field_name=f"existing {path.name}")
        if canonical_json(existing) != canonical_json(payload):
            raise ProductionResearchRuntimeError(f"immutable record collision for {path.name}")
        return
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _verify_self_hash(
    payload: dict[str, Any],
    *,
    hash_field: str,
    field_name: str,
) -> dict[str, Any]:
    claimed = payload.get(hash_field)
    if not isinstance(claimed, str) or SHA256_RE.fullmatch(claimed) is None:
        raise ProductionResearchRuntimeError(f"{field_name} self-hash is invalid")
    seed = dict(payload)
    seed.pop(hash_field, None)
    if canonical_sha256(seed) != claimed:
        raise ProductionResearchRuntimeError(f"{field_name} self-hash mismatch")
    return payload


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ProductionResearchRuntimeError("research state path cannot traverse a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o640)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


@dataclass(frozen=True, slots=True)
class ProductionResearchRunIdentity:
    schema_version: str
    run_id: str
    bot_instance: str
    mode: BotMode
    package_id: str
    package_manifest_sha256: str
    model_artifact_sha256: str
    model_version: str
    model_hash: str
    parameter_version: str
    parameter_hash: str
    dataset_hash: str
    model_source_commit: str
    no_trade_confidence: Decimal
    outcome_horizon_ms: int
    protected_holdout_accessed: bool = False
    automatic_promotion_enabled: bool = False
    trading_credentials_present: bool = False
    order_adapter_present: bool = False
    execution_enabled: bool = False
    orders_submitted: int = 0
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_IDENTITY_SCHEMA:
            raise ProductionResearchRuntimeError("research identity schema mismatch")
        _sha256(self.run_id, field_name="run_id")
        _sha256(self.package_manifest_sha256, field_name="package_manifest_sha256")
        _sha256(self.model_artifact_sha256, field_name="model_artifact_sha256")
        _sha256(self.model_hash, field_name="model_hash")
        _sha256(self.parameter_hash, field_name="parameter_hash")
        _sha256(self.dataset_hash, field_name="dataset_hash")
        _git_sha(self.model_source_commit, field_name="model_source_commit")
        if self.mode is not BotMode.SHADOW:
            raise ProductionResearchRuntimeError("production research runtime mode must be SHADOW")
        if self.no_trade_confidence != FROZEN_NO_TRADE_CONFIDENCE:
            raise ProductionResearchRuntimeError("no-trade confidence must remain frozen at 0.60")
        if self.outcome_horizon_ms != FROZEN_OUTCOME_HORIZON_MS:
            raise ProductionResearchRuntimeError(
                "outcome horizon must remain frozen at 900 seconds"
            )
        if (
            self.protected_holdout_accessed
            or self.automatic_promotion_enabled
            or self.trading_credentials_present
            or self.order_adapter_present
            or self.execution_enabled
            or self.orders_submitted != 0
            or self.live_capital_authorized
        ):
            raise ProductionResearchRuntimeError("research identity contains forbidden authority")

    @property
    def identity_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ResearchRuntimeRequest:
    run_id: str
    bot_instance: str
    mode: BotMode
    dataset_hash: str
    code_sha: str


@dataclass(frozen=True, slots=True)
class ResearchScoreTrace:
    score_id: str
    raw_probability: Decimal
    calibrated_confidence: Decimal


@dataclass(slots=True)
class ResearchTracingScorer:
    inner: LightGBMAdvisoryScorer
    _traces: dict[str, ResearchScoreTrace] = field(default_factory=dict, init=False)

    @property
    def artifact(self) -> Any:
        return self.inner.artifact

    def score(
        self,
        *,
        candidate: WickHunterCandidate,
        features: LiquidationFeatureVector,
        parameters: WickHunterParameters,
    ) -> CandidateScore:
        values = _feature_values(features=features, candidate=candidate)
        matrix = np.asarray([[float(value) for value in values]], dtype=np.float64)
        prediction = self.inner._booster.predict(
            matrix,
            num_iteration=self.inner._booster.current_iteration(),
        )
        raw_probability = Decimal(str(float(prediction[0]))).quantize(Decimal("0.000001"))
        score = self.inner.score(
            candidate=candidate,
            features=features,
            parameters=parameters,
        )
        self._traces[score.score_id] = ResearchScoreTrace(
            score_id=score.score_id,
            raw_probability=raw_probability,
            calibrated_confidence=score.confidence,
        )
        return score

    def trace_for(self, score_id: str | None) -> ResearchScoreTrace | None:
        if score_id is None:
            return None
        return self._traces.get(score_id)


@dataclass(frozen=True, slots=True)
class ProductionResearchRuntimeBinding:
    identity: ProductionResearchRunIdentity
    package: VerifiedCandidatePackage
    request: ResearchRuntimeRequest
    parameters: WickHunterParameters
    scorer: ResearchTracingScorer

    @property
    def binding_id(self) -> str:
        return canonical_sha256(
            {
                "run_id": self.identity.run_id,
                "identity_sha256": self.identity.identity_sha256,
                "mode": self.request.mode.value,
                "dataset_hash": self.request.dataset_hash,
                "code_sha": self.request.code_sha,
            }
        )

    def bind_request(self, request: ShadowDecisionRequest) -> ShadowDecisionRequest:
        if request.mode is not BotMode.SHADOW:
            raise ProductionResearchRuntimeError("research decision request mode must be SHADOW")
        if request.bot_instance != self.request.bot_instance:
            raise ProductionResearchRuntimeError("research bot instance does not match")
        if request.risk_context.candidate_paper_validation_authorized:
            raise ProductionResearchRuntimeError(
                "research runtime cannot inherit candidate PAPER authorization"
            )
        return replace(
            request,
            parameters=self.parameters,
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
            scorer=self.scorer,
            dataset_hash=self.request.dataset_hash,
            code_sha=self.request.code_sha,
            risk_context=replace(
                request.risk_context,
                candidate_paper_validation_authorized=False,
            ),
        )


def build_production_research_runtime_binding(
    *,
    model_root: Path,
    expected_package_id: str,
    expected_manifest_sha256: str,
    expected_model_artifact_sha256: str,
    expected_model_hash: str,
    expected_parameter_hash: str,
    bot_instance: str = "wickhunter-wh09-production-research",
) -> ProductionResearchRuntimeBinding:
    package = load_verified_candidate_package(model_root)
    identity = package.identity
    artifact = package.model_artifact
    expected_values = (
        (identity.package_id, expected_package_id, "package_id"),
        (identity.manifest_sha256, expected_manifest_sha256, "manifest_sha256"),
        (
            identity.model_artifact_sha256,
            expected_model_artifact_sha256,
            "model_artifact_sha256",
        ),
        (identity.model_hash, expected_model_hash, "model_hash"),
        (identity.parameter_hash, expected_parameter_hash, "parameter_hash"),
    )
    for actual, expected, field_name in expected_values:
        if actual != expected:
            raise ProductionResearchRuntimeError(f"verified model package {field_name} mismatch")
    if artifact.training_policy.no_trade_confidence != FROZEN_NO_TRADE_CONFIDENCE:
        raise ProductionResearchRuntimeError("model no-trade confidence is not the frozen 0.60")
    if artifact.parameter_sha256 != identity.parameter_hash:
        raise ProductionResearchRuntimeError("model and package parameter identities differ")
    dataset_hash = artifact.dataset_manifest_sha256
    run_seed = {
        "bot_instance": bot_instance,
        "mode": BotMode.SHADOW.value,
        "package_id": identity.package_id,
        "package_manifest_sha256": identity.manifest_sha256,
        "model_artifact_sha256": identity.model_artifact_sha256,
        "model_hash": identity.model_hash,
        "parameter_hash": identity.parameter_hash,
        "dataset_hash": dataset_hash,
        "model_source_commit": identity.source_commit_sha,
        "no_trade_confidence": str(FROZEN_NO_TRADE_CONFIDENCE),
        "outcome_horizon_ms": FROZEN_OUTCOME_HORIZON_MS,
    }
    research_identity = ProductionResearchRunIdentity(
        schema_version=RESEARCH_IDENTITY_SCHEMA,
        run_id=canonical_sha256(run_seed),
        bot_instance=bot_instance,
        mode=BotMode.SHADOW,
        package_id=identity.package_id,
        package_manifest_sha256=identity.manifest_sha256,
        model_artifact_sha256=identity.model_artifact_sha256,
        model_version=identity.model_version,
        model_hash=identity.model_hash,
        parameter_version=identity.parameter_version,
        parameter_hash=identity.parameter_hash,
        dataset_hash=dataset_hash,
        model_source_commit=identity.source_commit_sha,
        no_trade_confidence=FROZEN_NO_TRADE_CONFIDENCE,
        outcome_horizon_ms=FROZEN_OUTCOME_HORIZON_MS,
    )
    request = ResearchRuntimeRequest(
        run_id=research_identity.run_id,
        bot_instance=research_identity.bot_instance,
        mode=BotMode.SHADOW,
        dataset_hash=research_identity.dataset_hash,
        code_sha=research_identity.model_source_commit,
    )
    return ProductionResearchRuntimeBinding(
        identity=research_identity,
        package=package,
        request=request,
        parameters=package.parameters,
        scorer=ResearchTracingScorer(LightGBMAdvisoryScorer(artifact)),
    )


@dataclass(slots=True)
class ProductionResearchJournal:
    root: Path
    identity: ProductionResearchRunIdentity
    _active_traces: dict[str, ResearchScoreTrace] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _pending_outcomes: dict[str, dict[str, object]] = field(
        default_factory=dict, init=False, repr=False
    )
    _decision_count: int = field(default=0, init=False, repr=False)
    _simulated_signal_count: int = field(default=0, init=False, repr=False)
    _directional_decision_count: int = field(default=0, init=False, repr=False)
    _above_threshold_count: int = field(default=0, init=False, repr=False)
    _confidence_count: int = field(default=0, init=False, repr=False)
    _confidence_sum: Decimal = field(default=Decimal("0"), init=False, repr=False)
    _confidence_min: Decimal | None = field(default=None, init=False, repr=False)
    _confidence_max: Decimal | None = field(default=None, init=False, repr=False)
    _outcome_count: int = field(default=0, init=False, repr=False)
    _positive_outcome_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        _absolute_root(self.root, field_name="research journal root", create=True)
        for name in ("decisions", "outcomes", "runtime"):
            child = self.root / name
            child.mkdir(exist_ok=True)
            if child.is_symlink() or not child.is_dir():
                raise ProductionResearchRuntimeError(f"research journal {name} is invalid")
        identity_payload = json.loads(canonical_json(self.identity))
        identity_payload["identity_sha256"] = self.identity.identity_sha256
        _write_new_or_verify(self.root / "identity.json", identity_payload)
        self._rebuild_index()

    def _load_decision_file(self, path: Path) -> dict[str, object]:
        payload = _verify_self_hash(
            _load_object(path, field_name="research decision"),
            hash_field="record_sha256",
            field_name="research decision",
        )
        decision_id = str(payload.get("decision_id", ""))
        if SHA256_RE.fullmatch(decision_id) is None or path.stem != decision_id:
            raise ProductionResearchRuntimeError("research decision identity is invalid")
        return payload

    def _load_outcome_file(self, path: Path) -> dict[str, object]:
        payload = _verify_self_hash(
            _load_object(path, field_name="research outcome"),
            hash_field="record_sha256",
            field_name="research outcome",
        )
        decision_id = str(payload.get("decision_id", ""))
        if SHA256_RE.fullmatch(decision_id) is None or path.stem != decision_id:
            raise ProductionResearchRuntimeError("research outcome decision identity is invalid")
        return payload

    def _register_decision(self, payload: dict[str, object]) -> None:
        decision_id = str(payload.get("decision_id", ""))
        if SHA256_RE.fullmatch(decision_id) is None:
            raise ProductionResearchRuntimeError("research decision identity is invalid")
        self._decision_count += 1
        if payload.get("final_decision") == "SIMULATED_SIGNAL":
            self._simulated_signal_count += 1
        if payload.get("side") in {"long", "short"}:
            self._directional_decision_count += 1
            self._pending_outcomes[decision_id] = payload
        if payload.get("above_no_trade_confidence") is True:
            self._above_threshold_count += 1
        confidence = payload.get("calibrated_confidence")
        if confidence is not None:
            value = Decimal(str(confidence))
            self._confidence_count += 1
            self._confidence_sum += value
            self._confidence_min = (
                value if self._confidence_min is None else min(self._confidence_min, value)
            )
            self._confidence_max = (
                value if self._confidence_max is None else max(self._confidence_max, value)
            )

    def _register_outcome(self, payload: dict[str, object]) -> None:
        decision_id = str(payload.get("decision_id", ""))
        if SHA256_RE.fullmatch(decision_id) is None:
            raise ProductionResearchRuntimeError("research outcome decision identity is invalid")
        if decision_id not in self._pending_outcomes:
            raise ProductionResearchRuntimeError(
                "research outcome is orphaned from a pending directional decision"
            )
        self._outcome_count += 1
        if payload.get("positive_outcome") is True:
            self._positive_outcome_count += 1
        self._pending_outcomes.pop(decision_id, None)

    def _rebuild_index(self) -> None:
        for path in sorted((self.root / "decisions").glob("*.json")):
            self._register_decision(self._load_decision_file(path))
        for path in sorted((self.root / "outcomes").glob("*.json")):
            self._register_outcome(self._load_outcome_file(path))

    @property
    def runtime_store(self) -> ShadowRuntimeStore:
        return ShadowRuntimeStore(self.root / "runtime")

    @property
    def telemetry_path(self) -> Path:
        return self.root / "telemetry.json"

    def _decision_payload(
        self,
        *,
        request: ShadowDecisionRequest,
        evidence: ShadowDecisionEvidence,
        operator_commit: str,
    ) -> dict[str, object]:
        score = evidence.score
        trace = self.identity_trace(score)
        candidate = evidence.candidate
        threshold = self.identity.no_trade_confidence
        above_threshold = None if score is None else score.confidence >= threshold
        final_decision = (
            "SIMULATED_SIGNAL" if evidence.status is ShadowStatus.SIMULATED_ALLOWED else "NO_TRADE"
        )
        reason_codes = set()
        if candidate is not None:
            reason_codes.update(candidate.reason_codes)
        if evidence.risk_decision is not None:
            reason_codes.update(evidence.risk_decision.reason_codes)
        if not reason_codes:
            reason_codes.add(evidence.status.value)
        metrics = tuple(
            {
                "name": metric.name,
                "value": str(metric.value),
                "available_at_ms": metric.available_at_ms,
                "source": metric.source,
            }
            for metric in sorted(request.market.metrics, key=lambda item: item.name)
        )
        payload: dict[str, object] = {
            "schema_version": RESEARCH_DECISION_SCHEMA,
            "decision_id": evidence.shadow_decision_id,
            "run_id": self.identity.run_id,
            "binding_identity_sha256": self.identity.identity_sha256,
            "operator_commit": _git_sha(operator_commit, field_name="operator_commit"),
            "observed_at_ms": evidence.created_at_ms,
            "decision_timestamp_ms": request.market.decision_timestamp_ms,
            "symbol": request.market.symbol.upper(),
            "hypothesis": request.hypothesis.value,
            "decision_price": str(request.market.decision_price),
            "completed_candle_close_ms": request.market.completed_candle_close_ms,
            "market_metrics": metrics,
            "status": evidence.status.value,
            "final_decision": final_decision,
            "reason_codes": tuple(sorted(reason_codes)),
            "candidate_id": None if candidate is None else candidate.candidate_id,
            "candidate_action": None if candidate is None else candidate.action.value,
            "side": (None if candidate is None or candidate.side is None else candidate.side.value),
            "feature_hash": evidence.feature_hash,
            "score_id": None if score is None else score.score_id,
            "raw_probability": None if trace is None else str(trace.raw_probability),
            "calibrated_confidence": None if score is None else str(score.confidence),
            "no_trade_confidence": str(threshold),
            "above_no_trade_confidence": above_threshold,
            "model_version": self.identity.model_version,
            "model_hash": self.identity.model_hash,
            "model_artifact_sha256": self.identity.model_artifact_sha256,
            "parameter_version": self.identity.parameter_version,
            "parameter_hash": self.identity.parameter_hash,
            "dataset_hash": self.identity.dataset_hash,
            "model_source_commit": self.identity.model_source_commit,
            "outcome_horizon_ms": self.identity.outcome_horizon_ms,
            **ZERO_AUTHORITY,
        }
        payload["record_sha256"] = canonical_sha256(payload)
        return payload

    def identity_trace(self, score: CandidateScore | None) -> ResearchScoreTrace | None:
        return self._trace_lookup(score)

    def _trace_lookup(self, score: CandidateScore | None) -> ResearchScoreTrace | None:
        if score is None:
            return None
        return self._active_traces.get(score.score_id)

    def record_decisions(
        self,
        *,
        requests: tuple[ShadowDecisionRequest, ...],
        decisions: tuple[ShadowDecisionEvidence, ...],
        traces: dict[str, ResearchScoreTrace],
        operator_commit: str,
    ) -> int:
        if len(requests) != len(decisions):
            raise ProductionResearchRuntimeError("research requests and decisions are not aligned")
        self._active_traces = traces
        try:
            for request, evidence in zip(requests, decisions, strict=True):
                payload = self._decision_payload(
                    request=request,
                    evidence=evidence,
                    operator_commit=operator_commit,
                )
                decision_path = self.root / "decisions" / f"{evidence.shadow_decision_id}.json"
                is_new = not decision_path.exists()
                _write_new_or_verify(decision_path, payload)
                if is_new:
                    self._register_decision(payload)
        finally:
            self._active_traces = {}
        return len(decisions)

    def pending_outcome_symbols(self, *, observed_at_ms: int) -> tuple[str, ...]:
        symbols = {
            str(decision["symbol"]).upper()
            for decision in self._pending_outcomes.values()
            if observed_at_ms
            >= int(str(decision["decision_timestamp_ms"])) + self.identity.outcome_horizon_ms
        }
        return tuple(sorted(symbols))

    def materialize_due_outcomes(
        self,
        *,
        observed_at_ms: int,
        mark_prices: dict[str, Decimal],
        operator_commit: str,
    ) -> int:
        created = 0
        outcome_root = self.root / "outcomes"
        for decision_id, cached_decision in sorted(tuple(self._pending_outcomes.items())):
            decision_timestamp_ms = int(str(cached_decision["decision_timestamp_ms"]))
            target_at_ms = decision_timestamp_ms + self.identity.outcome_horizon_ms
            if observed_at_ms < target_at_ms:
                continue
            decision_path = self.root / "decisions" / f"{decision_id}.json"
            decision = self._load_decision_file(decision_path)
            if canonical_json(decision) != canonical_json(cached_decision):
                raise ProductionResearchRuntimeError(
                    "immutable research decision changed after startup"
                )
            outcome_path = outcome_root / f"{decision_id}.json"
            if outcome_path.exists():
                raise ProductionResearchRuntimeError(
                    "research outcome appeared outside the journal writer"
                )
            side = decision.get("side")
            if side not in {"long", "short"}:
                raise ProductionResearchRuntimeError("pending research decision is not directional")
            symbol = str(decision["symbol"]).upper()
            outcome_price = mark_prices.get(symbol)
            if outcome_price is None or outcome_price <= 0:
                continue
            entry_price = Decimal(str(decision["decision_price"]))
            gross_return = (outcome_price / entry_price) - Decimal("1")
            directional_return = gross_return if side == "long" else -gross_return
            payload: dict[str, object] = {
                "schema_version": RESEARCH_OUTCOME_SCHEMA,
                "outcome_id": canonical_sha256(
                    {
                        "decision_id": decision_id,
                        "target_at_ms": target_at_ms,
                        "labeled_at_ms": observed_at_ms,
                        "outcome_price": str(outcome_price),
                    }
                ),
                "decision_id": decision_id,
                "run_id": self.identity.run_id,
                "operator_commit": _git_sha(operator_commit, field_name="operator_commit"),
                "symbol": symbol,
                "side": side,
                "decision_timestamp_ms": decision_timestamp_ms,
                "target_horizon_ms": self.identity.outcome_horizon_ms,
                "target_at_ms": target_at_ms,
                "labeled_at_ms": observed_at_ms,
                "observation_delay_ms": observed_at_ms - target_at_ms,
                "entry_price": str(entry_price),
                "outcome_price": str(outcome_price),
                "gross_return_ratio": str(gross_return.quantize(Decimal("0.00000001"))),
                "directional_return_ratio": str(directional_return.quantize(Decimal("0.00000001"))),
                "positive_outcome": directional_return > 0,
                "semantics": "first_observed_mark_at_or_after_target_horizon_no_costs",
                "deterministic_replay_equivalent": False,
                "model_version": self.identity.model_version,
                "model_hash": self.identity.model_hash,
                "parameter_version": self.identity.parameter_version,
                "parameter_hash": self.identity.parameter_hash,
                "dataset_hash": self.identity.dataset_hash,
                "model_source_commit": self.identity.model_source_commit,
                **ZERO_AUTHORITY,
            }
            payload["record_sha256"] = canonical_sha256(payload)
            _write_new_or_verify(outcome_path, payload)
            self._register_outcome(payload)
            created += 1
        return created

    def publish_telemetry(
        self,
        *,
        checked_at_ms: int,
        operator_commit: str,
        runtime_state: Any,
    ) -> dict[str, object]:
        confidence_summary: dict[str, object] = {
            "count": self._confidence_count,
            "minimum": None if self._confidence_min is None else str(self._confidence_min),
            "maximum": None if self._confidence_max is None else str(self._confidence_max),
            "mean": (
                None
                if self._confidence_count == 0
                else str(
                    (self._confidence_sum / Decimal(self._confidence_count)).quantize(
                        Decimal("0.000001")
                    )
                )
            ),
        }
        payload: dict[str, object] = {
            "schema_version": RESEARCH_TELEMETRY_SCHEMA,
            "checked_at_ms": checked_at_ms,
            "operator_commit": _git_sha(operator_commit, field_name="operator_commit"),
            "run_id": self.identity.run_id,
            "mode": self.identity.mode.value,
            "model_version": self.identity.model_version,
            "model_hash": self.identity.model_hash,
            "model_artifact_sha256": self.identity.model_artifact_sha256,
            "parameter_version": self.identity.parameter_version,
            "parameter_hash": self.identity.parameter_hash,
            "dataset_hash": self.identity.dataset_hash,
            "no_trade_confidence": str(self.identity.no_trade_confidence),
            "outcome_horizon_ms": self.identity.outcome_horizon_ms,
            "decision_count": self._decision_count,
            "no_trade_count": self._decision_count - self._simulated_signal_count,
            "simulated_signal_count": self._simulated_signal_count,
            "directional_decision_count": self._directional_decision_count,
            "above_threshold_count": self._above_threshold_count,
            "confidence": confidence_summary,
            "outcome_count": self._outcome_count,
            "pending_outcome_count": len(self._pending_outcomes),
            "positive_outcome_count": self._positive_outcome_count,
            "positive_outcome_rate": (
                None
                if self._outcome_count == 0
                else str(
                    (Decimal(self._positive_outcome_count) / Decimal(self._outcome_count)).quantize(
                        Decimal("0.000001")
                    )
                )
            ),
            "runtime_generation": runtime_state.generation,
            "last_observed_at_ms": runtime_state.last_observed_at_ms,
            "simulated_open_positions": len(runtime_state.positions),
            "simulated_closed_positions": len(runtime_state.closed_positions),
            "simulated_realized_pnl_quote": str(runtime_state.cumulative_realized_pnl_quote),
            "runtime_drawdown_ratio": str(runtime_state.drawdown_ratio),
            **ZERO_AUTHORITY,
        }
        payload["telemetry_sha256"] = canonical_sha256(payload)
        _atomic_json(self.telemetry_path, payload)
        return payload


@dataclass(slots=True)
class ProductionResearchRuntimeService:
    binding: ProductionResearchRuntimeBinding
    journal: ProductionResearchJournal
    runtime: ShadowRuntime
    operator_commit: str

    @classmethod
    def create(
        cls,
        *,
        binding: ProductionResearchRuntimeBinding,
        journal_root: Path,
        operator_commit: str,
        policy: ShadowRuntimePolicy,
    ) -> ProductionResearchRuntimeService:
        exact_commit = _git_sha(operator_commit, field_name="operator_commit")
        journal = ProductionResearchJournal(journal_root, binding.identity)
        store = journal.runtime_store
        loaded = store.load()
        runtime = ShadowRuntime(
            bot_instance=binding.request.bot_instance,
            mode=BotMode.SHADOW,
            policy=policy,
            store=None,
        )
        if loaded is not None:
            if loaded.bot_instance != binding.request.bot_instance:
                raise ProductionResearchRuntimeError("persisted research bot instance differs")
            if loaded.mode is not BotMode.SHADOW:
                raise ProductionResearchRuntimeError("persisted research runtime mode differs")
            if loaded.policy_sha256 != policy.policy_sha256:
                raise ProductionResearchRuntimeError("persisted research runtime policy differs")
            runtime.state = loaded
        return cls(
            binding=binding,
            journal=journal,
            runtime=runtime,
            operator_commit=exact_commit,
        )

    def step(self, tick: ShadowRuntimeTick) -> ShadowRuntimeStepResult:
        bound_requests = tuple(
            self.binding.bind_request(request) for request in tick.decision_requests
        )
        bound_tick = replace(tick, decision_requests=bound_requests)
        previous_state = self.runtime.state
        try:
            result = self.runtime.step(bound_tick)
            ordered_requests = tuple(
                sorted(
                    bound_requests,
                    key=lambda item: (item.market.symbol, item.hypothesis.value),
                )
            )
            if result.decisions and len(result.decisions) != len(ordered_requests):
                raise ProductionResearchRuntimeError(
                    "research runtime decision count does not match evaluated requests"
                )
            traces = {
                score_id: trace
                for score_id, trace in self.binding.scorer._traces.items()
                if trace is not None
            }
            if result.decisions:
                self.journal.record_decisions(
                    requests=ordered_requests,
                    decisions=result.decisions,
                    traces=traces,
                    operator_commit=self.operator_commit,
                )
                for decision in result.decisions:
                    if decision.score is not None:
                        self.binding.scorer._traces.pop(decision.score.score_id, None)
            self.journal.materialize_due_outcomes(
                observed_at_ms=tick.observed_at_ms,
                mark_prices=dict(tick.mark_prices),
                operator_commit=self.operator_commit,
            )
            self.journal.publish_telemetry(
                checked_at_ms=tick.observed_at_ms,
                operator_commit=self.operator_commit,
                runtime_state=result.state,
            )
            self.journal.runtime_store.save(result.state, result.snapshot)
            return result
        except Exception:
            self.runtime.state = previous_state
            raise
