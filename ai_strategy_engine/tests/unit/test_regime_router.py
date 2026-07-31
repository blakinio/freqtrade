from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum

from strategy_engine.ai.regime_router import (
    DriftEvidence,
    DriftState,
    FeatureEvidence,
    LiquidationEvidence,
    LiquidationRegime,
    RegimeManifest,
    RegimePolicy,
    TrendRegime,
    VolatilityRegime,
    liquidation_evidence_from_alignment,
    route_regime,
)


class Kind(StrEnum):
    OPEN_INTEREST = "open_interest"
    FUNDING_RATE = "funding_rate"


class Status(StrEnum):
    ALIGNED = "aligned"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class Observation:
    source: str
    kind: Kind
    status: Status
    observation_id: str | None
    data_version: str | None
    available_at_ms: int | None


@dataclass(frozen=True, slots=True)
class Alignment:
    liquidation_id: str
    as_of_ms: int
    observations: tuple[Observation, ...]


def liquidation(status: Status = Status.ALIGNED) -> LiquidationEvidence:
    return liquidation_evidence_from_alignment(
        Alignment(
            liquidation_id="liq-1",
            as_of_ms=1_000,
            observations=(
                Observation("bybit", Kind.OPEN_INTEREST, Status.ALIGNED, "oi-1", "v1", 900),
                Observation("bybit", Kind.FUNDING_RATE, status, "fr-1", "v1", 900),
            ),
        ),
        expected_sources=["bybit"],
        severity_score=Decimal("2.5"),
        data_identity="data-v1",
    )


def feature(feature_id: str, value: str, *, approved: bool = True) -> FeatureEvidence:
    return FeatureEvidence(
        feature_id=feature_id,
        feature_version="1.0.0",
        value=Decimal(value),
        available_at_ms=900,
        feature_registry_identity="registry-v1",
        data_identity="data-v1",
        config_identity="config-v1",
        approved_for_ai=approved,
    )


def manifest() -> RegimeManifest:
    return RegimeManifest(
        model_version_id="model-v1",
        feature_registry_identity="registry-v1",
        config_identity="config-v1",
        data_identity="data-v1",
        as_of_ms=1_000,
        evidence_timerange="20260501-20260630",
        approved_feature_ids=("atr.v1", "roc.v1"),
        features=(feature("roc.v1", "0.02"), feature("atr.v1", "0.03")),
        liquidation=liquidation(),
        drift=DriftEvidence(
            evidence_id="drift-1",
            population_stability_index=Decimal("0.10"),
            available_at_ms=950,
            feature_schema_identity="schema-v1",
            reference_data_identity="reference-v1",
            observed_data_identity="data-v1",
        ),
    )


def test_complete_manifest_routes_known_regimes_without_authority() -> None:
    result = route_regime(manifest(), RegimePolicy(policy_id="policy-v1"))

    assert result.trend is TrendRegime.TREND
    assert result.volatility is VolatilityRegime.HIGH
    assert result.liquidation is LiquidationRegime.STRESSED
    assert result.drift is DriftState.STABLE
    assert result.ranking_allowed is True
    assert result.reason_codes == ()
    assert len(result.evidence_hash) == 64
    assert result.selected_model is None
    assert result.promotion_authorized is False
    assert result.execution_authorized is False
    assert result.risk_core_bypassed is False
    assert result.active_model_mutated is False


def test_missing_unapproved_and_ambiguous_features_fail_closed() -> None:
    base = manifest()
    missing = route_regime(
        replace(base, features=(feature("atr.v1", "0.01"),)),
        RegimePolicy(policy_id="policy-v1"),
    )
    unapproved = route_regime(
        replace(
            base,
            features=(feature("roc.v1", "0.02", approved=False), feature("atr.v1", "0.01")),
        ),
        RegimePolicy(policy_id="policy-v1"),
    )
    ambiguous = route_regime(
        replace(base, features=base.features + (feature("roc.v1", "0.03"),)),
        RegimePolicy(policy_id="policy-v1"),
    )

    assert missing.trend is TrendRegime.UNKNOWN
    assert "FEATURE_MISSING:roc.v1" in missing.reason_codes
    assert unapproved.trend is TrendRegime.UNKNOWN
    assert "FEATURE_NOT_APPROVED:roc.v1" in unapproved.reason_codes
    assert ambiguous.trend is TrendRegime.UNKNOWN
    assert "FEATURE_AMBIGUOUS:roc.v1" in ambiguous.reason_codes
    assert not missing.ranking_allowed and not unapproved.ranking_allowed


def test_incomplete_liquidation_alignment_is_explicit_unknown() -> None:
    result = route_regime(
        replace(manifest(), liquidation=liquidation(Status.MISSING)),
        RegimePolicy(policy_id="policy-v1"),
    )

    assert result.liquidation is LiquidationRegime.UNKNOWN
    assert result.ranking_allowed is False
    assert "LIQUIDATION_MISSING" in result.reason_codes
    assert "LIQUIDATION_CONTEXT_INCOMPLETE" in result.reason_codes


def test_drift_blocks_ranking_but_never_mutates_active_model() -> None:
    base = manifest()
    assert base.drift is not None
    drifted = replace(
        base.drift,
        population_stability_index=Decimal("0.30"),
    )
    result = route_regime(
        replace(base, drift=drifted),
        RegimePolicy(policy_id="policy-v1"),
    )

    assert result.drift is DriftState.DRIFTED
    assert result.ranking_allowed is False
    assert "DRIFT_DETECTED" in result.reason_codes
    assert result.active_model_mutated is False


def test_same_manifest_is_deterministic_independent_of_feature_order() -> None:
    base = manifest()
    first = route_regime(base, RegimePolicy(policy_id="policy-v1"))
    second = route_regime(
        replace(base, features=tuple(reversed(base.features))),
        RegimePolicy(policy_id="policy-v1"),
    )

    assert first == second


def test_policy_identity_is_bound_into_explanation_evidence() -> None:
    first = route_regime(manifest(), RegimePolicy(policy_id="policy-v1"))
    second = route_regime(
        manifest(),
        RegimePolicy(policy_id="policy-v2", trend_absolute_threshold=Decimal("0.03")),
    )

    assert first.manifest_hash == second.manifest_hash
    assert first.policy_hash != second.policy_hash
    assert first.evidence_hash != second.evidence_hash


def test_holdout_and_selected_model_guards_fail_closed() -> None:
    result = route_regime(
        replace(
            manifest(),
            evidence_timerange="20260801-20260930",
            protected_holdout_used=True,
            selected_model="candidate-x",
        ),
        RegimePolicy(policy_id="policy-v1"),
    )

    assert result.ranking_allowed is False
    assert "PROTECTED_HOLDOUT_FORBIDDEN" in result.reason_codes
    assert "PROTECTED_HOLDOUT_TIMERANGE_FORBIDDEN" in result.reason_codes
    assert "SELECTED_MODEL_MUST_REMAIN_NULL" in result.reason_codes
    assert result.selected_model is None
