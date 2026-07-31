"""Deterministic, fail-closed research-only market regime routing."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal, Protocol

SchemaVersion = Literal["1.0.0"]


class TrendRegime(StrEnum):
    TREND = "trend"
    RANGE = "range"
    UNKNOWN = "unknown"


class VolatilityRegime(StrEnum):
    HIGH = "high"
    LOW = "low"
    UNKNOWN = "unknown"


class LiquidationRegime(StrEnum):
    STRESSED = "stressed"
    NORMAL = "normal"
    UNKNOWN = "unknown"


class DriftState(StrEnum):
    STABLE = "stable"
    DRIFTED = "drifted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FeatureEvidence:
    feature_id: str
    feature_version: str
    value: Decimal
    available_at_ms: int
    feature_registry_identity: str
    data_identity: str
    config_identity: str
    approved_for_ai: bool


@dataclass(frozen=True, slots=True)
class LiquidationEvidence:
    evidence_id: str
    severity_score: Decimal | None
    available_at_ms: int
    data_identity: str
    expected_sources: tuple[str, ...]
    aligned_observation_ids: tuple[str, ...]
    complete: bool
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DriftEvidence:
    evidence_id: str
    population_stability_index: Decimal | None
    available_at_ms: int
    feature_schema_identity: str
    reference_data_identity: str
    observed_data_identity: str


@dataclass(frozen=True, slots=True)
class RegimeManifest:
    model_version_id: str
    feature_registry_identity: str
    config_identity: str
    data_identity: str
    as_of_ms: int
    evidence_timerange: str
    approved_feature_ids: tuple[str, ...]
    features: tuple[FeatureEvidence, ...]
    liquidation: LiquidationEvidence | None
    drift: DriftEvidence | None
    schema_version: SchemaVersion = "1.0.0"
    protected_holdout_used: bool = False
    selected_model: str | None = None


@dataclass(frozen=True, slots=True)
class RegimePolicy:
    policy_id: str
    trend_feature_id: str = "roc.v1"
    volatility_feature_id: str = "atr.v1"
    trend_absolute_threshold: Decimal = Decimal("0.01")
    high_volatility_threshold: Decimal = Decimal("0.02")
    liquidation_stress_threshold: Decimal = Decimal("2.0")
    maximum_drift_psi: Decimal = Decimal("0.25")
    schema_version: SchemaVersion = "1.0.0"


@dataclass(frozen=True, slots=True)
class RegimeDecision:
    manifest_hash: str
    evidence_hash: str
    policy_id: str
    policy_hash: str
    model_version_id: str
    feature_registry_identity: str
    config_identity: str
    data_identity: str
    explanation_version: SchemaVersion
    trend: TrendRegime
    volatility: VolatilityRegime
    liquidation: LiquidationRegime
    drift: DriftState
    ranking_allowed: bool
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    selected_model: None = None
    promotion_authorized: Literal[False] = False
    execution_authorized: Literal[False] = False
    risk_core_bypassed: Literal[False] = False
    active_model_mutated: Literal[False] = False


class AlignedObservationLike(Protocol):
    @property
    def source(self) -> str: ...

    @property
    def kind(self) -> object: ...

    @property
    def status(self) -> object: ...

    @property
    def observation_id(self) -> str | None: ...

    @property
    def data_version(self) -> str | None: ...

    @property
    def available_at_ms(self) -> int | None: ...


class LiquidationAlignmentLike(Protocol):
    @property
    def liquidation_id(self) -> str: ...

    @property
    def as_of_ms(self) -> int: ...

    @property
    def observations(self) -> Sequence[AlignedObservationLike]: ...


def liquidation_evidence_from_alignment(
    alignment: LiquidationAlignmentLike,
    *,
    expected_sources: Iterable[str],
    severity_score: Decimal | None,
    data_identity: str,
) -> LiquidationEvidence:
    """Convert point-in-time source alignment into immutable router evidence."""

    sources = tuple(
        sorted({source.strip().lower() for source in expected_sources if source.strip()})
    )
    reasons: set[str] = set()
    if not sources:
        reasons.add("LIQUIDATION_EXPECTED_SOURCES_MISSING")
    seen: Counter[tuple[str, str]] = Counter()
    aligned_ids: set[str] = set()
    for observation in alignment.observations:
        source = observation.source.strip().lower()
        kind = str(observation.kind)
        status = str(observation.status)
        if source not in sources:
            continue
        seen[(source, kind)] += 1
        if seen[(source, kind)] > 1:
            reasons.add("LIQUIDATION_ALIGNMENT_AMBIGUOUS")
        if status != "aligned":
            reasons.add(f"LIQUIDATION_{status.upper()}")
            continue
        if not observation.observation_id:
            reasons.add("LIQUIDATION_OBSERVATION_ID_MISSING")
        elif not observation.data_version:
            reasons.add("LIQUIDATION_DATA_VERSION_MISSING")
        elif (
            observation.available_at_ms is None or observation.available_at_ms > alignment.as_of_ms
        ):
            reasons.add("LIQUIDATION_OBSERVATION_NOT_AVAILABLE")
        else:
            aligned_ids.add(observation.observation_id)
    for source in sources:
        for kind in ("open_interest", "funding_rate"):
            if seen[(source, kind)] != 1:
                reasons.add("LIQUIDATION_CONTEXT_INCOMPLETE")
    severity = _decimal(severity_score)
    if severity_score is not None and severity is None:
        reasons.add("LIQUIDATION_SEVERITY_INVALID")
    return LiquidationEvidence(
        evidence_id=alignment.liquidation_id,
        severity_score=severity,
        available_at_ms=alignment.as_of_ms,
        data_identity=data_identity,
        expected_sources=sources,
        aligned_observation_ids=tuple(sorted(aligned_ids)),
        complete=bool(sources) and not reasons,
        reason_codes=tuple(sorted(reasons)),
    )


def route_regime(manifest: RegimeManifest, policy: RegimePolicy) -> RegimeDecision:
    """Classify research evidence without selecting, promoting or executing a model."""

    reasons: set[str] = set()
    evidence_ids: set[str] = set()
    for name, value in (
        ("MODEL_VERSION_ID", manifest.model_version_id),
        ("FEATURE_REGISTRY_IDENTITY", manifest.feature_registry_identity),
        ("CONFIG_IDENTITY", manifest.config_identity),
        ("DATA_IDENTITY", manifest.data_identity),
        ("POLICY_ID", policy.policy_id),
    ):
        if not value.strip():
            reasons.add(f"{name}_MISSING")
    if manifest.as_of_ms <= 0:
        reasons.add("MANIFEST_AS_OF_INVALID")
    timerange = _timerange(manifest.evidence_timerange)
    if timerange is None:
        reasons.add("EVIDENCE_TIMERANGE_INVALID")
    elif _protected(timerange):
        reasons.add("PROTECTED_HOLDOUT_TIMERANGE_FORBIDDEN")
    if manifest.protected_holdout_used:
        reasons.add("PROTECTED_HOLDOUT_FORBIDDEN")
    if manifest.selected_model is not None:
        reasons.add("SELECTED_MODEL_MUST_REMAIN_NULL")

    approved_counts = Counter(manifest.approved_feature_ids)
    if any(count != 1 for count in approved_counts.values()):
        reasons.add("APPROVED_FEATURE_SET_AMBIGUOUS")
    approved = set(approved_counts)
    trend_value = _feature_value(manifest, policy.trend_feature_id, approved, reasons, evidence_ids)
    volatility_value = _feature_value(
        manifest, policy.volatility_feature_id, approved, reasons, evidence_ids
    )
    trend_threshold = _non_negative(
        policy.trend_absolute_threshold, "TREND_THRESHOLD_INVALID", reasons
    )
    volatility_threshold = _non_negative(
        policy.high_volatility_threshold, "VOLATILITY_THRESHOLD_INVALID", reasons
    )
    liquidation_threshold = _non_negative(
        policy.liquidation_stress_threshold, "LIQUIDATION_THRESHOLD_INVALID", reasons
    )
    drift_threshold = _non_negative(policy.maximum_drift_psi, "DRIFT_THRESHOLD_INVALID", reasons)

    trend = TrendRegime.UNKNOWN
    if trend_value is not None and trend_threshold is not None:
        trend = TrendRegime.TREND if abs(trend_value) >= trend_threshold else TrendRegime.RANGE
    volatility = VolatilityRegime.UNKNOWN
    if volatility_value is not None and volatility_threshold is not None:
        volatility = (
            VolatilityRegime.HIGH
            if volatility_value >= volatility_threshold
            else VolatilityRegime.LOW
        )

    liquidation = LiquidationRegime.UNKNOWN
    if manifest.liquidation is None:
        reasons.add("LIQUIDATION_EVIDENCE_MISSING")
    else:
        liquidation_item = manifest.liquidation
        evidence_ids.add(liquidation_item.evidence_id)
        reasons.update(liquidation_item.reason_codes)
        severity = _decimal(liquidation_item.severity_score)
        if not liquidation_item.complete:
            reasons.add("LIQUIDATION_CONTEXT_INCOMPLETE")
        elif liquidation_item.available_at_ms > manifest.as_of_ms:
            reasons.add("LIQUIDATION_EVIDENCE_NOT_AVAILABLE")
        elif liquidation_item.data_identity != manifest.data_identity:
            reasons.add("LIQUIDATION_DATA_IDENTITY_MISMATCH")
        elif severity is None:
            reasons.add("LIQUIDATION_SEVERITY_MISSING_OR_INVALID")
        elif liquidation_threshold is not None:
            liquidation = (
                LiquidationRegime.STRESSED
                if severity >= liquidation_threshold
                else LiquidationRegime.NORMAL
            )

    drift = DriftState.UNKNOWN
    if manifest.drift is None:
        reasons.add("DRIFT_EVIDENCE_MISSING")
    else:
        drift_item = manifest.drift
        evidence_ids.add(drift_item.evidence_id)
        psi = _decimal(drift_item.population_stability_index)
        if drift_item.available_at_ms > manifest.as_of_ms:
            reasons.add("DRIFT_EVIDENCE_NOT_AVAILABLE")
        elif drift_item.observed_data_identity != manifest.data_identity:
            reasons.add("DRIFT_DATA_IDENTITY_MISMATCH")
        elif not drift_item.feature_schema_identity.strip():
            reasons.add("DRIFT_FEATURE_SCHEMA_IDENTITY_MISSING")
        elif not drift_item.reference_data_identity.strip():
            reasons.add("DRIFT_REFERENCE_IDENTITY_MISSING")
        elif psi is None:
            reasons.add("DRIFT_METRIC_MISSING_OR_INVALID")
        elif drift_threshold is not None:
            drift = DriftState.DRIFTED if psi > drift_threshold else DriftState.STABLE
            if drift is DriftState.DRIFTED:
                reasons.add("DRIFT_DETECTED")

    ranking_allowed = (
        trend is not TrendRegime.UNKNOWN
        and volatility is not VolatilityRegime.UNKNOWN
        and liquidation is not LiquidationRegime.UNKNOWN
        and drift is DriftState.STABLE
        and not reasons
    )
    manifest_hash = _manifest_hash(manifest)
    policy_hash = _policy_hash(policy)
    reason_codes = tuple(sorted(reasons))
    ordered_ids = tuple(sorted(evidence_ids))
    evidence_hash = _sha(
        {
            "manifest_hash": manifest_hash,
            "policy_id": policy.policy_id,
            "policy_hash": policy_hash,
            "trend": trend.value,
            "volatility": volatility.value,
            "liquidation": liquidation.value,
            "drift": drift.value,
            "ranking_allowed": ranking_allowed,
            "reason_codes": reason_codes,
            "evidence_ids": ordered_ids,
            "selected_model": None,
            "promotion_authorized": False,
            "execution_authorized": False,
            "risk_core_bypassed": False,
            "active_model_mutated": False,
        }
    )
    return RegimeDecision(
        manifest_hash=manifest_hash,
        evidence_hash=evidence_hash,
        policy_id=policy.policy_id,
        policy_hash=policy_hash,
        model_version_id=manifest.model_version_id,
        feature_registry_identity=manifest.feature_registry_identity,
        config_identity=manifest.config_identity,
        data_identity=manifest.data_identity,
        explanation_version="1.0.0",
        trend=trend,
        volatility=volatility,
        liquidation=liquidation,
        drift=drift,
        ranking_allowed=ranking_allowed,
        reason_codes=reason_codes,
        evidence_ids=ordered_ids,
    )


def _feature_value(
    manifest: RegimeManifest,
    feature_id: str,
    approved: set[str],
    reasons: set[str],
    evidence_ids: set[str],
) -> Decimal | None:
    matches = [item for item in manifest.features if item.feature_id == feature_id]
    if not matches:
        reasons.add(f"FEATURE_MISSING:{feature_id}")
        return None
    if len(matches) != 1:
        reasons.add(f"FEATURE_AMBIGUOUS:{feature_id}")
        return None
    item = matches[0]
    evidence_ids.add(f"{item.feature_id}@{item.feature_version}")
    if feature_id not in approved or not item.approved_for_ai:
        reasons.add(f"FEATURE_NOT_APPROVED:{feature_id}")
        return None
    if not item.feature_version.strip():
        reasons.add(f"FEATURE_VERSION_MISSING:{feature_id}")
        return None
    if item.available_at_ms > manifest.as_of_ms:
        reasons.add(f"FEATURE_NOT_AVAILABLE:{feature_id}")
        return None
    if item.feature_registry_identity != manifest.feature_registry_identity:
        reasons.add(f"FEATURE_REGISTRY_IDENTITY_MISMATCH:{feature_id}")
        return None
    if item.data_identity != manifest.data_identity:
        reasons.add(f"FEATURE_DATA_IDENTITY_MISMATCH:{feature_id}")
        return None
    if item.config_identity != manifest.config_identity:
        reasons.add(f"FEATURE_CONFIG_IDENTITY_MISMATCH:{feature_id}")
        return None
    value = _decimal(item.value)
    if value is None:
        reasons.add(f"FEATURE_VALUE_INVALID:{feature_id}")
    return value


def _manifest_hash(manifest: RegimeManifest) -> str:
    features = sorted(
        (
            {
                "feature_id": item.feature_id,
                "feature_version": item.feature_version,
                "value": str(item.value),
                "available_at_ms": item.available_at_ms,
                "feature_registry_identity": item.feature_registry_identity,
                "data_identity": item.data_identity,
                "config_identity": item.config_identity,
                "approved_for_ai": item.approved_for_ai,
            }
            for item in manifest.features
        ),
        key=_canonical,
    )
    liquidation: dict[str, object] | None = None
    if manifest.liquidation is not None:
        liquidation_item = manifest.liquidation
        liquidation = {
            "evidence_id": liquidation_item.evidence_id,
            "severity_score": (
                None
                if liquidation_item.severity_score is None
                else str(liquidation_item.severity_score)
            ),
            "available_at_ms": liquidation_item.available_at_ms,
            "data_identity": liquidation_item.data_identity,
            "expected_sources": sorted(liquidation_item.expected_sources),
            "aligned_observation_ids": sorted(liquidation_item.aligned_observation_ids),
            "complete": liquidation_item.complete,
            "reason_codes": sorted(liquidation_item.reason_codes),
        }
    drift: dict[str, object] | None = None
    if manifest.drift is not None:
        drift_item = manifest.drift
        drift = {
            "evidence_id": drift_item.evidence_id,
            "population_stability_index": (
                None
                if drift_item.population_stability_index is None
                else str(drift_item.population_stability_index)
            ),
            "available_at_ms": drift_item.available_at_ms,
            "feature_schema_identity": drift_item.feature_schema_identity,
            "reference_data_identity": drift_item.reference_data_identity,
            "observed_data_identity": drift_item.observed_data_identity,
        }
    return _sha(
        {
            "schema_version": manifest.schema_version,
            "model_version_id": manifest.model_version_id,
            "feature_registry_identity": manifest.feature_registry_identity,
            "config_identity": manifest.config_identity,
            "data_identity": manifest.data_identity,
            "as_of_ms": manifest.as_of_ms,
            "evidence_timerange": manifest.evidence_timerange,
            "approved_feature_ids": sorted(manifest.approved_feature_ids),
            "features": features,
            "liquidation": liquidation,
            "drift": drift,
            "protected_holdout_used": manifest.protected_holdout_used,
            "selected_model": manifest.selected_model,
        }
    )


def _policy_hash(policy: RegimePolicy) -> str:
    return _sha(
        {
            "schema_version": policy.schema_version,
            "policy_id": policy.policy_id,
            "trend_feature_id": policy.trend_feature_id,
            "volatility_feature_id": policy.volatility_feature_id,
            "trend_absolute_threshold": str(policy.trend_absolute_threshold),
            "high_volatility_threshold": str(policy.high_volatility_threshold),
            "liquidation_stress_threshold": str(policy.liquidation_stress_threshold),
            "maximum_drift_psi": str(policy.maximum_drift_psi),
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


def _non_negative(value: Decimal, reason: str, reasons: set[str]) -> Decimal | None:
    parsed = _decimal(value)
    if parsed is None or parsed < 0:
        reasons.add(reason)
        return None
    return parsed


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


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()
