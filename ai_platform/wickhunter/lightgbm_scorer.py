from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

import lightgbm as lgb
import numpy as np

from ai_platform.wickhunter.baseline_strategy import (
    BASELINE_REPORT_SCHEMA_VERSION,
    DEFAULT_SLICE_POLICY,
    EVALUATION_INTERFACE_VERSION,
    BaselineSlicePolicy,
    EvaluationCase,
    EvaluationDecision,
    EvaluationDimensions,
    EvaluationSummary,
    LiquidityBucket,
    MarketRegime,
    build_evaluation_decision,
    evaluate_deterministic_baselines,
    summarize_evaluation,
)
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    CandidateAction,
    CandidateScore,
    LiquidationFeatureVector,
    ModelPromotionState,
    StrategyHypothesis,
    TradeDirection,
    WickHunterCandidate,
)
from ai_platform.wickhunter.deterministic_replay import LabelOutcome
from ai_platform.wickhunter.parameters import (
    WickHunterParameterBounds,
    WickHunterParameters,
    validate_parameters,
)
from ai_platform.wickhunter.scoring import validated_external_model_score
from ai_platform.wickhunter.strategy import CooldownRecord, SignalMemory, generate_candidate


TRAINING_POLICY_SCHEMA_VERSION = "wickhunter-lightgbm-training-policy-v1"
MODEL_ARTIFACT_SCHEMA_VERSION = "wickhunter-lightgbm-model-artifact-v1"
MODEL_COMPARISON_SCHEMA_VERSION = "wickhunter-lightgbm-comparison-v1"
FEATURE_SCHEMA_VERSION = "wickhunter-lightgbm-candidate-features-v1"
MODEL_KIND = "lightgbm_binary_candidate_scorer"
ADVISORY_CONCLUSION = "advisory_candidate_only_no_automatic_promotion"

FEATURE_NAMES = (
    "decision_price",
    "event_count",
    "total_notional_usd",
    "liquidated_long_notional_usd",
    "liquidated_short_notional_usd",
    "long_short_imbalance",
    "maximum_event_notional_usd",
    "maximum_event_percentile",
    "maximum_event_zscore",
    "liquidation_burst_intensity",
    "time_since_previous_burst_ms",
    "ingest_latency_ms",
    "source_coverage_ratio",
    "source_count",
    "quote_volume_24h_usd",
    "trend_return_ratio",
    "volatility_ratio",
    "vwap_distance_ratio",
    "vwma_distance_ratio",
    "wick_ratio",
    "side_sign",
    "hypothesis_sign",
)

FORBIDDEN_FEATURE_TOKENS = (
    "label",
    "outcome",
    "net_return",
    "gross_return",
    "future_return",
    "profit",
    "future",
    "exit",
    "mfe",
    "mae",
    "fee",
    "slippage",
    "time_to_outcome",
)


class LightGBMScorerError(RuntimeError):
    """Raised when advisory model evidence cannot be accepted safely."""


def _decimal(value: object, *, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise LightGBMScorerError(f"{field_name} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise LightGBMScorerError(f"{field_name} must be finite")
    return parsed


def _require_sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise LightGBMScorerError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


@dataclass(frozen=True, slots=True)
class LightGBMTrainingPolicy:
    schema_version: str = TRAINING_POLICY_SCHEMA_VERSION
    policy_version: str = "wickhunter-lightgbm-training-v1"
    training_splits: tuple[str, ...] = ("train",)
    calibration_splits: tuple[str, ...] = ("calibration",)
    validation_splits: tuple[str, ...] = ("validation",)
    forbidden_splits: tuple[str, ...] = ("holdout", "protected_holdout")
    seed: int = 20260801
    num_boost_round: int = 40
    num_leaves: int = 7
    min_data_in_leaf: int = 2
    learning_rate: Decimal = Decimal("0.05")
    calibration_bins: int = 10
    no_trade_confidence: Decimal = Decimal("0.60")

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != TRAINING_POLICY_SCHEMA_VERSION:
            raise LightGBMScorerError(
                f"training policy schema must be {TRAINING_POLICY_SCHEMA_VERSION}"
            )
        if not self.policy_version.strip():
            raise LightGBMScorerError("policy_version must be non-empty")
        split_groups = (
            self.training_splits,
            self.calibration_splits,
            self.validation_splits,
            self.forbidden_splits,
        )
        for group in split_groups:
            if not group or group != tuple(sorted(set(group))):
                raise LightGBMScorerError("split groups must be non-empty, unique and sorted")
            if any(not item.strip() for item in group):
                raise LightGBMScorerError("split names must be non-empty")
        allowed = (
            set(self.training_splits) | set(self.calibration_splits) | set(self.validation_splits)
        )
        if len(allowed) != sum(
            len(group)
            for group in (
                self.training_splits,
                self.calibration_splits,
                self.validation_splits,
            )
        ):
            raise LightGBMScorerError(
                "training, calibration and validation splits must be disjoint"
            )
        if allowed & set(self.forbidden_splits):
            raise LightGBMScorerError("protected splits cannot be assigned to model work")
        if self.seed < 0:
            raise LightGBMScorerError("seed must be non-negative")
        if self.num_boost_round < 1 or self.num_leaves < 2 or self.min_data_in_leaf < 1:
            raise LightGBMScorerError("LightGBM structural parameters are invalid")
        if not Decimal("0") < self.learning_rate <= Decimal("1"):
            raise LightGBMScorerError("learning_rate must be in (0, 1]")
        if self.calibration_bins < 2:
            raise LightGBMScorerError("calibration_bins must be >= 2")
        if not Decimal("0") < self.no_trade_confidence < Decimal("1"):
            raise LightGBMScorerError("no_trade_confidence must be in (0, 1)")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class CalibrationCurve:
    schema_version: str
    upper_bounds: tuple[Decimal, ...]
    probabilities: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "wickhunter-probability-calibration-v1":
            raise LightGBMScorerError("unsupported calibration schema")
        if not self.upper_bounds or len(self.upper_bounds) != len(self.probabilities):
            raise LightGBMScorerError("calibration bounds and probabilities must align")
        if self.upper_bounds != tuple(sorted(self.upper_bounds)):
            raise LightGBMScorerError("calibration bounds must be sorted")
        if self.probabilities != tuple(sorted(self.probabilities)):
            raise LightGBMScorerError("calibration probabilities must be monotonic")
        if self.upper_bounds[-1] != Decimal("1"):
            raise LightGBMScorerError("calibration must cover probability 1")
        if any(not Decimal("0") <= value <= Decimal("1") for value in self.probabilities):
            raise LightGBMScorerError("calibrated probabilities must be in [0, 1]")

    def apply(self, raw_probability: Decimal) -> Decimal:
        bounded = max(Decimal("0"), min(Decimal("1"), raw_probability))
        for upper_bound, probability in zip(self.upper_bounds, self.probabilities, strict=True):
            if bounded <= upper_bound:
                return probability
        return self.probabilities[-1]


@dataclass(frozen=True, slots=True)
class LightGBMModelArtifact:
    schema_version: str
    model_kind: str
    model_version: str
    model_hash: str
    model_text: str
    feature_schema_version: str
    feature_schema_sha256: str
    feature_names: tuple[str, ...]
    training_policy: LightGBMTrainingPolicy
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    split_geometry_sha256: str
    price_path_manifest_sha256: str
    replay_policy_version: str
    replay_policy_sha256: str
    parameter_version: str
    parameter_sha256: str
    training_case_sha256s: tuple[str, ...]
    calibration_case_sha256s: tuple[str, ...]
    training_example_count: int
    calibration_example_count: int
    positive_example_count: int
    negative_example_count: int
    positive_return_mean: Decimal
    negative_return_mean: Decimal
    calibration: CalibrationCurve
    protected_holdout_accessed: bool
    automatic_promotion_enabled: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != MODEL_ARTIFACT_SCHEMA_VERSION:
            raise LightGBMScorerError(
                f"model artifact schema must be {MODEL_ARTIFACT_SCHEMA_VERSION}"
            )
        if self.model_kind != MODEL_KIND:
            raise LightGBMScorerError("model_kind is not the frozen WH-04 model")
        if not self.model_version.strip() or not self.model_text.strip():
            raise LightGBMScorerError("model identity and text must be non-empty")
        _require_sha256(self.model_hash, field_name="model_hash")
        _require_sha256(self.feature_schema_sha256, field_name="feature_schema_sha256")
        if hashlib.sha256(self.model_text.encode("utf-8")).hexdigest() != self.model_hash:
            raise LightGBMScorerError("model text does not match model_hash")
        if self.feature_schema_version != FEATURE_SCHEMA_VERSION:
            raise LightGBMScorerError("feature schema version mismatch")
        if self.feature_names != FEATURE_NAMES:
            raise LightGBMScorerError("feature names do not match the frozen schema")
        if (
            canonical_sha256({"version": self.feature_schema_version, "names": self.feature_names})
            != self.feature_schema_sha256
        ):
            raise LightGBMScorerError("feature schema hash mismatch")
        for digest, field_name in (
            (self.dataset_manifest_sha256, "dataset_manifest_sha256"),
            (self.market_manifest_sha256, "market_manifest_sha256"),
            (self.split_geometry_sha256, "split_geometry_sha256"),
            (self.price_path_manifest_sha256, "price_path_manifest_sha256"),
            (self.replay_policy_sha256, "replay_policy_sha256"),
            (self.parameter_sha256, "parameter_sha256"),
        ):
            _require_sha256(digest, field_name=field_name)
        for values, field_name in (
            (self.training_case_sha256s, "training_case_sha256s"),
            (self.calibration_case_sha256s, "calibration_case_sha256s"),
        ):
            if values != tuple(sorted(set(values))) or not values:
                raise LightGBMScorerError(f"{field_name} must be non-empty, unique and sorted")
            for digest in values:
                _require_sha256(digest, field_name=field_name)
        if self.training_example_count != self.positive_example_count + self.negative_example_count:
            raise LightGBMScorerError("training class counts are inconsistent")
        if (
            min(
                self.training_example_count,
                self.calibration_example_count,
                self.positive_example_count,
                self.negative_example_count,
            )
            < 1
        ):
            raise LightGBMScorerError("model artifact requires non-empty training classes")
        if (
            self.protected_holdout_accessed
            or self.automatic_promotion_enabled
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise LightGBMScorerError("model artifact contains unsafe authority")

    @property
    def artifact_sha256(self) -> str:
        return canonical_sha256(self)

    def as_registry_record(self) -> dict[str, object]:
        payload = json.loads(canonical_json(self))
        payload["artifact_sha256"] = self.artifact_sha256
        payload["promotion_state"] = ModelPromotionState.CANDIDATE.value
        payload["advisory_only"] = True
        return payload


@dataclass(frozen=True, slots=True)
class LightGBMComparisonReport:
    schema_version: str
    interface_version: str
    report_id: str
    model_artifact_sha256: str
    model_version: str
    baseline_report_id: str
    validation_splits: tuple[str, ...]
    decisions: tuple[EvaluationDecision, ...]
    baseline_overall: EvaluationSummary
    model_overall: EvaluationSummary
    baseline_slices: tuple[EvaluationSummary, ...]
    model_slices: tuple[EvaluationSummary, ...]
    conclusion: str
    protected_holdout_accessed: bool
    model_promoted: bool
    profitability_claimed: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != MODEL_COMPARISON_SCHEMA_VERSION:
            raise LightGBMScorerError("comparison schema mismatch")
        if self.interface_version != EVALUATION_INTERFACE_VERSION:
            raise LightGBMScorerError("comparison interface mismatch")
        _require_sha256(self.report_id, field_name="report_id")
        _require_sha256(self.model_artifact_sha256, field_name="model_artifact_sha256")
        _require_sha256(self.baseline_report_id, field_name="baseline_report_id")
        if not self.decisions:
            raise LightGBMScorerError("comparison report requires model decisions")
        if self.conclusion != ADVISORY_CONCLUSION:
            raise LightGBMScorerError("comparison conclusion must remain advisory")
        if (
            self.protected_holdout_accessed
            or self.model_promoted
            or self.profitability_claimed
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise LightGBMScorerError("comparison report contains unsafe authority")

    def as_json_dict(self) -> dict[str, object]:
        return json.loads(canonical_json(self))


@dataclass(frozen=True, slots=True)
class _TrainingExample:
    case_sha256: str
    feature_values: tuple[Decimal, ...]
    target: int
    net_return_ratio: Decimal


@dataclass(slots=True)
class LightGBMAdvisoryScorer:
    artifact: LightGBMModelArtifact
    _booster: lgb.Booster = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._booster = lgb.Booster(model_str=self.artifact.model_text)

    def score(
        self,
        *,
        candidate: WickHunterCandidate,
        features: LiquidationFeatureVector,
        parameters: WickHunterParameters,
    ) -> CandidateScore:
        if candidate.feature_hash != features.feature_hash:
            raise LightGBMScorerError("candidate and feature identities do not match")
        if parameters.parameter_hash != self.artifact.parameter_sha256:
            raise LightGBMScorerError("scoring parameters do not match model artifact")
        values = _feature_values(features=features, candidate=candidate)
        matrix = np.asarray([[float(value) for value in values]], dtype=np.float64)
        prediction = self._booster.predict(matrix, num_iteration=self._booster.current_iteration())
        raw_probability = _decimal(prediction[0], field_name="raw_probability")
        confidence = self.artifact.calibration.apply(raw_probability).quantize(Decimal("0.000001"))
        expected_return = (
            confidence * self.artifact.positive_return_mean
            + (Decimal("1") - confidence) * self.artifact.negative_return_mean
        ).quantize(Decimal("0.00000001"))
        threshold = self.artifact.training_policy.no_trade_confidence
        if confidence < threshold:
            risk_multiplier = Decimal("0")
        else:
            risk_multiplier = ((confidence - threshold) / (Decimal("1") - threshold)).quantize(
                Decimal("0.000001")
            )
        return validated_external_model_score(
            candidate=candidate,
            feature_hash=features.feature_hash,
            confidence=confidence,
            expected_return_after_costs=expected_return,
            bounded_risk_multiplier=risk_multiplier,
            model_version=self.artifact.model_version,
            model_hash=self.artifact.model_hash,
            promotion_state=ModelPromotionState.CANDIDATE,
            scored_at_ms=features.decision_timestamp_ms,
        )


def _audit_feature_schema() -> None:
    lowered = tuple(name.lower() for name in FEATURE_NAMES)
    for name in lowered:
        if any(token in name for token in FORBIDDEN_FEATURE_TOKENS):
            raise LightGBMScorerError(f"leakage-prone feature name is forbidden: {name}")


def _audit_case(case: EvaluationCase, policy: LightGBMTrainingPolicy) -> None:
    if case.split_name in policy.forbidden_splits:
        raise LightGBMScorerError("protected holdout access is forbidden")
    if case.feature.feature_available_at_ms > case.feature.decision_timestamp_ms:
        raise LightGBMScorerError("feature became available after the decision timestamp")
    if any(
        metric.available_at_ms > case.feature.decision_timestamp_ms
        for metric in case.feature.market_metrics
    ):
        raise LightGBMScorerError("market metric became available after the decision timestamp")


def _feature_values(
    *,
    features: LiquidationFeatureVector,
    candidate: WickHunterCandidate,
) -> tuple[Decimal, ...]:
    if candidate.side is None:
        raise LightGBMScorerError("model feature extraction requires a directional candidate")
    vwap = features.metric("vwap")
    vwma = features.metric("vwma")
    side_sign = Decimal("1") if candidate.side is TradeDirection.LONG else Decimal("-1")
    hypothesis_sign = (
        Decimal("1") if candidate.hypothesis is StrategyHypothesis.CONTINUATION else Decimal("-1")
    )
    previous_burst = (
        Decimal("-1")
        if features.time_since_previous_burst_ms is None
        else Decimal(features.time_since_previous_burst_ms)
    )
    values = (
        features.decision_price,
        Decimal(features.event_count),
        features.total_notional_usd,
        features.liquidated_long_notional_usd,
        features.liquidated_short_notional_usd,
        features.long_short_imbalance,
        features.maximum_event_notional_usd,
        features.maximum_event_percentile,
        features.maximum_event_zscore,
        features.liquidation_burst_intensity,
        previous_burst,
        Decimal(features.ingest_latency_ms),
        features.source_coverage_ratio,
        Decimal(len(features.source_aggregates)),
        features.metric("quote_volume_24h_usd"),
        features.metric("trend_return_ratio"),
        features.metric("volatility_ratio"),
        (features.decision_price / vwap) - Decimal("1"),
        (features.decision_price / vwma) - Decimal("1"),
        features.metric("wick_ratio"),
        side_sign,
        hypothesis_sign,
    )
    if len(values) != len(FEATURE_NAMES) or any(not value.is_finite() for value in values):
        raise LightGBMScorerError("candidate model features are incomplete or non-finite")
    return values


def _candidate_examples(
    cases: Sequence[EvaluationCase],
    *,
    parameters: WickHunterParameters,
    policy: LightGBMTrainingPolicy,
) -> tuple[_TrainingExample, ...]:
    examples: list[_TrainingExample] = []
    for case in sorted(cases, key=lambda item: item.case_sha256):
        _audit_case(case, policy)
        for hypothesis in (
            StrategyHypothesis.CONTINUATION,
            StrategyHypothesis.REVERSAL,
        ):
            candidate = generate_candidate(
                features=case.feature,
                parameters=parameters,
                hypothesis=hypothesis,
                memory=SignalMemory(),
            )
            if candidate.action is CandidateAction.IGNORE or candidate.side is None:
                continue
            label = case.label_for(candidate.side)
            if label.outcome is LabelOutcome.MISSING_ENTRY or label.net_return_ratio is None:
                continue
            examples.append(
                _TrainingExample(
                    case_sha256=case.case_sha256,
                    feature_values=_feature_values(features=case.feature, candidate=candidate),
                    target=int(label.net_return_ratio > 0),
                    net_return_ratio=label.net_return_ratio,
                )
            )
    if not examples:
        raise LightGBMScorerError("no eligible candidate-level training examples")
    return tuple(examples)


def _fit_calibration(
    raw_probabilities: Sequence[float],
    targets: Sequence[int],
    *,
    bins: int,
) -> CalibrationCurve:
    if len(raw_probabilities) != len(targets) or not raw_probabilities:
        raise LightGBMScorerError("calibration inputs must be non-empty and aligned")
    counts = [0] * bins
    positives = [0] * bins
    for raw_probability, target in zip(raw_probabilities, targets, strict=True):
        bounded = max(0.0, min(1.0, float(raw_probability)))
        index = min(bins - 1, int(bounded * bins))
        counts[index] += 1
        positives[index] += int(target)
    upper_bounds = tuple(
        (Decimal(index + 1) / Decimal(bins)).quantize(Decimal("0.000000000001"))
        for index in range(bins)
    )
    probabilities: list[Decimal] = []
    previous = Decimal("0")
    for count, positive in zip(counts, positives, strict=True):
        if count == 0:
            calibrated = previous
        else:
            calibrated = Decimal(positive + 1) / Decimal(count + 2)
            calibrated = max(previous, calibrated).quantize(Decimal("0.000000000001"))
        probabilities.append(calibrated)
        previous = calibrated
    probabilities[-1] = max(probabilities[-1], previous)
    return CalibrationCurve(
        schema_version="wickhunter-probability-calibration-v1",
        upper_bounds=upper_bounds[:-1] + (Decimal("1"),),
        probabilities=tuple(probabilities),
    )


def _replay_identity(cases: Sequence[EvaluationCase]) -> Mapping[str, object]:
    identities = {
        (
            label.dataset_id,
            label.dataset_manifest_sha256,
            label.market_manifest_sha256,
            label.split_geometry_sha256,
            label.price_path_manifest_sha256,
            label.policy_version,
            label.policy_sha256,
        )
        for case in cases
        for label in case.labels
    }
    if len(identities) != 1:
        raise LightGBMScorerError("model cases do not share one immutable replay identity")
    (
        dataset_id,
        dataset_manifest_sha256,
        market_manifest_sha256,
        split_geometry_sha256,
        price_path_manifest_sha256,
        replay_policy_version,
        replay_policy_sha256,
    ) = next(iter(identities))
    return {
        "dataset_id": dataset_id,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "market_manifest_sha256": market_manifest_sha256,
        "split_geometry_sha256": split_geometry_sha256,
        "price_path_manifest_sha256": price_path_manifest_sha256,
        "replay_policy_version": replay_policy_version,
        "replay_policy_sha256": replay_policy_sha256,
    }


def train_lightgbm_scorer(
    *,
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
    parameter_bounds: WickHunterParameterBounds,
    policy: LightGBMTrainingPolicy | None = None,
) -> LightGBMModelArtifact:
    policy = policy or LightGBMTrainingPolicy()
    validate_parameters(parameters, parameter_bounds)
    _audit_feature_schema()
    if not cases:
        raise LightGBMScorerError("model training requires evaluation cases")
    ordered_cases = tuple(sorted(cases, key=lambda item: item.case_sha256))
    for case in ordered_cases:
        _audit_case(case, policy)
    training_cases = tuple(
        case for case in ordered_cases if case.split_name in policy.training_splits
    )
    calibration_cases = tuple(
        case for case in ordered_cases if case.split_name in policy.calibration_splits
    )
    if not training_cases or not calibration_cases:
        raise LightGBMScorerError("training and calibration splits must both be populated")
    training_examples = _candidate_examples(training_cases, parameters=parameters, policy=policy)
    calibration_examples = _candidate_examples(
        calibration_cases, parameters=parameters, policy=policy
    )
    targets = [example.target for example in training_examples]
    if set(targets) != {0, 1}:
        raise LightGBMScorerError("training data must contain positive and negative outcomes")
    matrix = np.asarray(
        [[float(value) for value in example.feature_values] for example in training_examples],
        dtype=np.float64,
    )
    labels = np.asarray(targets, dtype=np.int32)
    dataset = lgb.Dataset(
        matrix,
        label=labels,
        feature_name=list(FEATURE_NAMES),
        free_raw_data=False,
    )
    lightgbm_parameters = {
        "objective": "binary",
        "metric": "binary_logloss",
        "verbosity": -1,
        "deterministic": True,
        "force_col_wise": True,
        "num_threads": 1,
        "seed": policy.seed,
        "feature_fraction_seed": policy.seed,
        "bagging_seed": policy.seed,
        "data_random_seed": policy.seed,
        "num_leaves": policy.num_leaves,
        "min_data_in_leaf": policy.min_data_in_leaf,
        "min_data_in_bin": 1,
        "feature_pre_filter": False,
        "learning_rate": float(policy.learning_rate),
    }
    booster = lgb.train(
        lightgbm_parameters,
        dataset,
        num_boost_round=policy.num_boost_round,
    )
    model_text = booster.model_to_string(num_iteration=booster.current_iteration())
    model_hash = hashlib.sha256(model_text.encode("utf-8")).hexdigest()
    calibration_matrix = np.asarray(
        [[float(value) for value in example.feature_values] for example in calibration_examples],
        dtype=np.float64,
    )
    raw_calibration = booster.predict(calibration_matrix, num_iteration=booster.current_iteration())
    calibration = _fit_calibration(
        tuple(float(item) for item in raw_calibration),
        tuple(example.target for example in calibration_examples),
        bins=policy.calibration_bins,
    )
    positive_returns = [
        example.net_return_ratio for example in training_examples if example.target == 1
    ]
    negative_returns = [
        example.net_return_ratio for example in training_examples if example.target == 0
    ]
    identity = _replay_identity(ordered_cases)
    feature_schema_sha256 = canonical_sha256(
        {"version": FEATURE_SCHEMA_VERSION, "names": FEATURE_NAMES}
    )
    return LightGBMModelArtifact(
        schema_version=MODEL_ARTIFACT_SCHEMA_VERSION,
        model_kind=MODEL_KIND,
        model_version=f"wickhunter-lightgbm-{model_hash[:16]}",
        model_hash=model_hash,
        model_text=model_text,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        feature_schema_sha256=feature_schema_sha256,
        feature_names=FEATURE_NAMES,
        training_policy=policy,
        dataset_id=str(identity["dataset_id"]),
        dataset_manifest_sha256=str(identity["dataset_manifest_sha256"]),
        market_manifest_sha256=str(identity["market_manifest_sha256"]),
        split_geometry_sha256=str(identity["split_geometry_sha256"]),
        price_path_manifest_sha256=str(identity["price_path_manifest_sha256"]),
        replay_policy_version=str(identity["replay_policy_version"]),
        replay_policy_sha256=str(identity["replay_policy_sha256"]),
        parameter_version=parameters.parameter_version,
        parameter_sha256=parameters.parameter_hash,
        training_case_sha256s=tuple(sorted(case.case_sha256 for case in training_cases)),
        calibration_case_sha256s=tuple(sorted(case.case_sha256 for case in calibration_cases)),
        training_example_count=len(training_examples),
        calibration_example_count=len(calibration_examples),
        positive_example_count=len(positive_returns),
        negative_example_count=len(negative_returns),
        positive_return_mean=sum(positive_returns, Decimal(0)) / Decimal(len(positive_returns)),
        negative_return_mean=sum(negative_returns, Decimal(0)) / Decimal(len(negative_returns)),
        calibration=calibration,
        protected_holdout_accessed=False,
        automatic_promotion_enabled=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )


def _dimensions(
    *,
    case: EvaluationCase,
    candidate: WickHunterCandidate,
    slice_policy: BaselineSlicePolicy,
) -> EvaluationDimensions:
    quote_volume = case.feature.metric("quote_volume_24h_usd")
    if quote_volume >= slice_policy.high_liquidity_usd:
        liquidity = LiquidityBucket.HIGH
    elif quote_volume >= slice_policy.medium_liquidity_usd:
        liquidity = LiquidityBucket.MEDIUM
    else:
        liquidity = LiquidityBucket.LOW
    trend = case.feature.metric("trend_return_ratio")
    if trend > slice_policy.trend_threshold_ratio:
        regime = MarketRegime.UPTREND
    elif trend < -slice_policy.trend_threshold_ratio:
        regime = MarketRegime.DOWNTREND
    else:
        regime = MarketRegime.RANGE
    return EvaluationDimensions(
        split_name=case.split_name,
        symbol=case.feature.symbol,
        side="ignored" if candidate.side is None else candidate.side.value,
        liquidity=liquidity,
        source="+".join(item.source for item in case.feature.source_aggregates),
        regime=regime,
        hypothesis=candidate.hypothesis,
    )


def _model_ignore_candidate(
    candidate: WickHunterCandidate,
    *,
    score_id: str,
) -> WickHunterCandidate:
    reasons = tuple(sorted({*candidate.reason_codes, "model_confidence_below_threshold"}))
    return WickHunterCandidate(
        candidate_id=canonical_sha256(
            {
                "candidate_id": candidate.candidate_id,
                "score_id": score_id,
                "action": CandidateAction.IGNORE.value,
                "reason_codes": reasons,
            }
        ),
        action=CandidateAction.IGNORE,
        hypothesis=candidate.hypothesis,
        symbol=candidate.symbol,
        decision_timestamp_ms=candidate.decision_timestamp_ms,
        decision_price=candidate.decision_price,
        reason_codes=reasons,
        feature_hash=candidate.feature_hash,
        parameter_version=candidate.parameter_version,
        parameter_hash=candidate.parameter_hash,
    )


def evaluate_lightgbm_against_baseline(
    *,
    artifact: LightGBMModelArtifact,
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
    parameter_bounds: WickHunterParameterBounds,
    slice_policy: BaselineSlicePolicy = DEFAULT_SLICE_POLICY,
) -> LightGBMComparisonReport:
    validate_parameters(parameters, parameter_bounds)
    if parameters.parameter_hash != artifact.parameter_sha256:
        raise LightGBMScorerError("evaluation parameters do not match model artifact")
    validation_cases = tuple(
        sorted(
            (
                case
                for case in cases
                if case.split_name in artifact.training_policy.validation_splits
            ),
            key=lambda item: item.case_sha256,
        )
    )
    if not validation_cases:
        raise LightGBMScorerError("validation split is empty")
    for case in validation_cases:
        _audit_case(case, artifact.training_policy)
    baseline = evaluate_deterministic_baselines(
        cases=validation_cases,
        parameters=parameters,
        parameter_bounds=parameter_bounds,
        slice_policy=slice_policy,
    )
    if baseline.schema_version != BASELINE_REPORT_SCHEMA_VERSION:
        raise LightGBMScorerError("baseline report schema mismatch")
    if (
        baseline.dataset_id != artifact.dataset_id
        or baseline.dataset_manifest_sha256 != artifact.dataset_manifest_sha256
        or baseline.market_manifest_sha256 != artifact.market_manifest_sha256
        or baseline.split_geometry_sha256 != artifact.split_geometry_sha256
        or baseline.price_path_manifest_sha256 != artifact.price_path_manifest_sha256
        or baseline.replay_policy_sha256 != artifact.replay_policy_sha256
    ):
        raise LightGBMScorerError("baseline and model do not share immutable replay evidence")
    scorer = LightGBMAdvisoryScorer(artifact)
    memories = {
        hypothesis: SignalMemory()
        for hypothesis in (
            StrategyHypothesis.CONTINUATION,
            StrategyHypothesis.REVERSAL,
        )
    }
    decisions: list[EvaluationDecision] = []
    for case in validation_cases:
        for hypothesis in (
            StrategyHypothesis.CONTINUATION,
            StrategyHypothesis.REVERSAL,
        ):
            candidate = generate_candidate(
                features=case.feature,
                parameters=parameters,
                hypothesis=hypothesis,
                memory=memories[hypothesis],
            )
            score = None
            evaluated_candidate = candidate
            if candidate.side is not None:
                score = scorer.score(
                    candidate=candidate,
                    features=case.feature,
                    parameters=parameters,
                )
                if score.confidence < artifact.training_policy.no_trade_confidence:
                    evaluated_candidate = _model_ignore_candidate(
                        candidate, score_id=score.score_id
                    )
            decisions.append(
                build_evaluation_decision(
                    strategy_id=f"{MODEL_KIND}:{hypothesis.value}",
                    case=case,
                    candidate=evaluated_candidate,
                    dimensions=_dimensions(
                        case=case,
                        candidate=evaluated_candidate,
                        slice_policy=slice_policy,
                    ),
                    score_id=None if score is None else score.score_id,
                    model_version=None if score is None else artifact.model_version,
                )
            )
            cooldown = memories[hypothesis].cooldown_records
            if candidate.side is not None:
                cooldown = (
                    *cooldown,
                    CooldownRecord(
                        symbol=candidate.symbol,
                        side=candidate.side,
                        hypothesis=hypothesis,
                        candidate_at_ms=candidate.decision_timestamp_ms,
                    ),
                )
            memories[hypothesis] = SignalMemory(
                seen_feature_hashes=memories[hypothesis].seen_feature_hashes
                | {case.feature.feature_hash},
                cooldown_records=cooldown,
            )
    ordered_decisions = tuple(
        sorted(
            decisions,
            key=lambda item: (
                item.dimensions.split_name,
                item.dimensions.symbol,
                item.dataset_row_sha256,
                item.dimensions.hypothesis.value,
            ),
        )
    )
    model_overall, model_slices = summarize_evaluation(ordered_decisions)
    report_seed = {
        "schema_version": MODEL_COMPARISON_SCHEMA_VERSION,
        "interface_version": EVALUATION_INTERFACE_VERSION,
        "model_artifact_sha256": artifact.artifact_sha256,
        "baseline_report_id": baseline.report_id,
        "validation_splits": artifact.training_policy.validation_splits,
        "decision_ids": tuple(item.decision_id for item in ordered_decisions),
        "baseline_overall": baseline.overall,
        "model_overall": model_overall,
        "baseline_slices": baseline.slices,
        "model_slices": model_slices,
        "conclusion": ADVISORY_CONCLUSION,
    }
    return LightGBMComparisonReport(
        schema_version=MODEL_COMPARISON_SCHEMA_VERSION,
        interface_version=EVALUATION_INTERFACE_VERSION,
        report_id=canonical_sha256(report_seed),
        model_artifact_sha256=artifact.artifact_sha256,
        model_version=artifact.model_version,
        baseline_report_id=baseline.report_id,
        validation_splits=artifact.training_policy.validation_splits,
        decisions=ordered_decisions,
        baseline_overall=baseline.overall,
        model_overall=model_overall,
        baseline_slices=baseline.slices,
        model_slices=model_slices,
        conclusion=ADVISORY_CONCLUSION,
        protected_holdout_accessed=False,
        model_promoted=False,
        profitability_claimed=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )
