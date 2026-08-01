from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    CandidateAction,
    LiquidationFeatureVector,
    StrategyHypothesis,
    TradeDirection,
    WickHunterCandidate,
)
from ai_platform.wickhunter.deterministic_replay import CandidateLabel, LabelOutcome
from ai_platform.wickhunter.parameters import (
    WickHunterParameterBounds,
    WickHunterParameters,
    validate_parameters,
)
from ai_platform.wickhunter.strategy import (
    STRATEGY_VERSION,
    CooldownRecord,
    SignalMemory,
    generate_candidate,
)


EVALUATION_INTERFACE_VERSION = "wickhunter-evaluation-interface-v1"
BASELINE_POLICY_SCHEMA_VERSION = "wickhunter-baseline-slice-policy-v1"
BASELINE_DECISION_SCHEMA_VERSION = "wickhunter-baseline-decision-v1"
BASELINE_REPORT_SCHEMA_VERSION = "wickhunter-baseline-report-v1"
DESCRIPTIVE_CONCLUSION = "descriptive_only_no_profitability_or_promotion_claim"


class BaselineEvaluationError(RuntimeError):
    """Raised when baseline evidence is incomplete, inconsistent or unsafe."""


class LiquidityBucket(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketRegime(StrEnum):
    DOWNTREND = "downtrend"
    RANGE = "range"
    UPTREND = "uptrend"


class EvaluationStatus(StrEnum):
    SELECTED = "selected"
    IGNORED = "ignored"


@dataclass(frozen=True, slots=True)
class BaselineSlicePolicy:
    schema_version: str
    policy_version: str
    medium_liquidity_usd: Decimal
    high_liquidity_usd: Decimal
    trend_threshold_ratio: Decimal

    def __post_init__(self) -> None:
        if self.schema_version != BASELINE_POLICY_SCHEMA_VERSION:
            raise BaselineEvaluationError(
                f"slice policy schema must be {BASELINE_POLICY_SCHEMA_VERSION}"
            )
        if not self.policy_version.strip():
            raise BaselineEvaluationError("policy_version must be non-empty")
        for value, field_name in (
            (self.medium_liquidity_usd, "medium_liquidity_usd"),
            (self.high_liquidity_usd, "high_liquidity_usd"),
            (self.trend_threshold_ratio, "trend_threshold_ratio"),
        ):
            if not value.is_finite() or value <= 0:
                raise BaselineEvaluationError(f"{field_name} must be finite and > 0")
        if self.high_liquidity_usd <= self.medium_liquidity_usd:
            raise BaselineEvaluationError("high_liquidity_usd must exceed medium_liquidity_usd")
        if self.trend_threshold_ratio >= Decimal("1"):
            raise BaselineEvaluationError("trend_threshold_ratio must be below 1")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


DEFAULT_SLICE_POLICY = BaselineSlicePolicy(
    schema_version=BASELINE_POLICY_SCHEMA_VERSION,
    policy_version="wickhunter-baseline-slices-v1",
    medium_liquidity_usd=Decimal("50000000"),
    high_liquidity_usd=Decimal("200000000"),
    trend_threshold_ratio=Decimal("0.005"),
)


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    dataset_row_sha256: str
    split_name: str
    feature: LiquidationFeatureVector
    labels: tuple[CandidateLabel, ...]

    def __post_init__(self) -> None:
        _require_sha256(self.dataset_row_sha256, field="dataset_row_sha256")
        if not self.split_name.strip():
            raise BaselineEvaluationError("split_name must be non-empty")
        if not self.labels:
            raise BaselineEvaluationError("evaluation case requires replay labels")
        labels = tuple(sorted(self.labels, key=lambda item: item.side.value))
        if labels != self.labels:
            raise BaselineEvaluationError("evaluation labels must be sorted by side")
        sides = tuple(label.side for label in labels)
        if sides != (TradeDirection.LONG, TradeDirection.SHORT):
            raise BaselineEvaluationError("evaluation case requires one long and one short label")
        for label in labels:
            if label.dataset_row_sha256 != self.dataset_row_sha256:
                raise BaselineEvaluationError("label dataset row binding mismatch")
            if label.split_name != self.split_name:
                raise BaselineEvaluationError("label split binding mismatch")
            if label.symbol != self.feature.symbol:
                raise BaselineEvaluationError("label symbol binding mismatch")
            if label.decision_timestamp_ms != self.feature.decision_timestamp_ms:
                raise BaselineEvaluationError("label decision timestamp binding mismatch")
        identities = {
            (
                label.dataset_id,
                label.dataset_manifest_sha256,
                label.market_manifest_sha256,
                label.split_geometry_sha256,
                label.price_path_manifest_sha256,
                label.policy_sha256,
                label.policy_version,
                label.fee_ratio,
                label.slippage_ratio,
                label.take_profit_ratio,
                label.stop_loss_ratio,
                label.label_end_ms,
            )
            for label in labels
        }
        if len(identities) != 1:
            raise BaselineEvaluationError("case labels do not share one replay identity")

    @property
    def case_sha256(self) -> str:
        return canonical_sha256(
            {
                "dataset_row_sha256": self.dataset_row_sha256,
                "split_name": self.split_name,
                "feature_hash": self.feature.feature_hash,
                "label_ids": tuple(label.label_id for label in self.labels),
            }
        )

    def label_for(self, side: TradeDirection) -> CandidateLabel:
        try:
            return next(label for label in self.labels if label.side is side)
        except StopIteration as exc:
            raise BaselineEvaluationError(
                f"evaluation case has no {side.value} replay label"
            ) from exc


@dataclass(frozen=True, slots=True)
class EvaluationDimensions:
    split_name: str
    symbol: str
    side: str
    liquidity: LiquidityBucket
    source: str
    regime: MarketRegime
    hypothesis: StrategyHypothesis


@dataclass(frozen=True, slots=True)
class EvaluationDecision:
    schema_version: str
    interface_version: str
    decision_id: str
    strategy_id: str
    case_sha256: str
    dataset_row_sha256: str
    feature_hash: str
    candidate_id: str
    action: CandidateAction
    side: TradeDirection | None
    status: EvaluationStatus
    reason_codes: tuple[str, ...]
    score_id: str | None
    model_version: str | None
    label_id: str | None
    label_outcome: LabelOutcome | None
    gross_return_ratio: Decimal | None
    net_return_ratio: Decimal | None
    maximum_favorable_excursion_ratio: Decimal | None
    maximum_adverse_excursion_ratio: Decimal | None
    time_to_outcome_ms: int | None
    dimensions: EvaluationDimensions
    protected_holdout_accessed: bool
    model_promoted: bool
    profitability_claimed: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != BASELINE_DECISION_SCHEMA_VERSION:
            raise BaselineEvaluationError(
                f"decision schema must be {BASELINE_DECISION_SCHEMA_VERSION}"
            )
        if self.interface_version != EVALUATION_INTERFACE_VERSION:
            raise BaselineEvaluationError(
                f"interface version must be {EVALUATION_INTERFACE_VERSION}"
            )
        for value, field_name in (
            (self.decision_id, "decision_id"),
            (self.case_sha256, "case_sha256"),
            (self.dataset_row_sha256, "dataset_row_sha256"),
            (self.feature_hash, "feature_hash"),
            (self.candidate_id, "candidate_id"),
        ):
            _require_sha256(value, field=field_name)
        if not self.strategy_id.strip():
            raise BaselineEvaluationError("strategy_id must be non-empty")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))) or not self.reason_codes:
            raise BaselineEvaluationError("reason_codes must be non-empty, unique and sorted")
        if self.status is EvaluationStatus.IGNORED:
            if self.action is not CandidateAction.IGNORE or self.side is not None:
                raise BaselineEvaluationError(
                    "ignored decision must have ignore action and no side"
                )
            if any(
                value is not None
                for value in (
                    self.label_id,
                    self.label_outcome,
                    self.gross_return_ratio,
                    self.net_return_ratio,
                    self.maximum_favorable_excursion_ratio,
                    self.maximum_adverse_excursion_ratio,
                    self.time_to_outcome_ms,
                )
            ):
                raise BaselineEvaluationError("ignored decision cannot contain label results")
        else:
            if self.action is CandidateAction.IGNORE or self.side is None:
                raise BaselineEvaluationError("selected decision requires a directional action")
            if self.label_id is None or self.label_outcome is None:
                raise BaselineEvaluationError("selected decision requires a replay label")
            _require_sha256(self.label_id, field="label_id")
            result_values = (
                self.gross_return_ratio,
                self.net_return_ratio,
                self.maximum_favorable_excursion_ratio,
                self.maximum_adverse_excursion_ratio,
                self.time_to_outcome_ms,
            )
            if self.label_outcome is LabelOutcome.MISSING_ENTRY:
                if any(value is not None for value in result_values):
                    raise BaselineEvaluationError(
                        "missing-entry decision cannot contain execution results"
                    )
            elif any(value is None for value in result_values):
                raise BaselineEvaluationError(
                    "executed selected decision requires complete replay results"
                )
        if self.score_id is not None:
            _require_sha256(self.score_id, field="score_id")
        if (
            self.protected_holdout_accessed
            or self.model_promoted
            or self.profitability_claimed
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise BaselineEvaluationError("evaluation decision contains unsafe authority")


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    dimension: str
    value: str
    decision_count: int
    selected_count: int
    ignored_count: int
    executed_label_count: int
    missing_entry_count: int
    outcome_counts: tuple[tuple[str, int], ...]
    gross_return_sum: Decimal | None
    net_return_sum: Decimal | None
    net_return_mean: Decimal | None
    maximum_favorable_excursion_mean: Decimal | None
    maximum_adverse_excursion_mean: Decimal | None
    time_to_outcome_mean_ms: Decimal | None

    def __post_init__(self) -> None:
        if not self.dimension or not self.value:
            raise BaselineEvaluationError("summary dimension and value must be non-empty")
        if (
            min(
                self.decision_count,
                self.selected_count,
                self.ignored_count,
                self.executed_label_count,
                self.missing_entry_count,
            )
            < 0
        ):
            raise BaselineEvaluationError("summary counts must be non-negative")
        if self.selected_count + self.ignored_count != self.decision_count:
            raise BaselineEvaluationError("summary selected/ignored counts are inconsistent")
        if self.executed_label_count + self.missing_entry_count != self.selected_count:
            raise BaselineEvaluationError("summary label counts are inconsistent")
        if self.outcome_counts != tuple(sorted(self.outcome_counts)):
            raise BaselineEvaluationError("outcome_counts must be sorted")
        numeric = (
            self.gross_return_sum,
            self.net_return_sum,
            self.net_return_mean,
            self.maximum_favorable_excursion_mean,
            self.maximum_adverse_excursion_mean,
            self.time_to_outcome_mean_ms,
        )
        if self.executed_label_count == 0 and any(value is not None for value in numeric):
            raise BaselineEvaluationError("empty executed summary cannot contain numeric metrics")
        if self.executed_label_count > 0 and any(value is None for value in numeric):
            raise BaselineEvaluationError("executed summary requires complete numeric metrics")


@dataclass(frozen=True, slots=True)
class BaselineEvaluationReport:
    schema_version: str
    interface_version: str
    report_id: str
    strategy_version: str
    parameter_version: str
    parameter_sha256: str
    slice_policy_version: str
    slice_policy_sha256: str
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    split_geometry_sha256: str
    price_path_manifest_sha256: str
    replay_policy_version: str
    replay_policy_sha256: str
    fee_ratio: Decimal
    slippage_ratio: Decimal
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    label_horizon_ms: int
    decisions: tuple[EvaluationDecision, ...]
    overall: EvaluationSummary
    slices: tuple[EvaluationSummary, ...]
    conclusion: str
    protected_holdout_accessed: bool
    model_promoted: bool
    profitability_claimed: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != BASELINE_REPORT_SCHEMA_VERSION:
            raise BaselineEvaluationError(f"report schema must be {BASELINE_REPORT_SCHEMA_VERSION}")
        if self.interface_version != EVALUATION_INTERFACE_VERSION:
            raise BaselineEvaluationError(
                f"interface version must be {EVALUATION_INTERFACE_VERSION}"
            )
        for digest, field_name in (
            (self.report_id, "report_id"),
            (self.parameter_sha256, "parameter_sha256"),
            (self.slice_policy_sha256, "slice_policy_sha256"),
            (self.dataset_manifest_sha256, "dataset_manifest_sha256"),
            (self.market_manifest_sha256, "market_manifest_sha256"),
            (self.split_geometry_sha256, "split_geometry_sha256"),
            (self.price_path_manifest_sha256, "price_path_manifest_sha256"),
            (self.replay_policy_sha256, "replay_policy_sha256"),
        ):
            _require_sha256(digest, field=field_name)
        for decimal_value, field_name, allow_zero in (
            (self.fee_ratio, "fee_ratio", True),
            (self.slippage_ratio, "slippage_ratio", True),
            (self.take_profit_ratio, "take_profit_ratio", False),
            (self.stop_loss_ratio, "stop_loss_ratio", False),
        ):
            if (
                not decimal_value.is_finite()
                or decimal_value < 0
                or (not allow_zero and decimal_value == 0)
            ):
                raise BaselineEvaluationError(f"{field_name} has an invalid value")
        if self.label_horizon_ms <= 0:
            raise BaselineEvaluationError("label_horizon_ms must be > 0")
        if not self.decisions:
            raise BaselineEvaluationError("baseline report requires decisions")
        if self.conclusion != DESCRIPTIVE_CONCLUSION:
            raise BaselineEvaluationError("baseline report conclusion is not descriptive-only")
        if (
            self.protected_holdout_accessed
            or self.model_promoted
            or self.profitability_claimed
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise BaselineEvaluationError("baseline report contains unsafe authority")

    def as_json_dict(self) -> dict[str, object]:
        return json.loads(canonical_json(self))


class EvaluationRecordFactory(Protocol):
    """Frozen WH-03 interface implemented by deterministic and advisory evaluators."""

    @property
    def strategy_id(self) -> str: ...

    def evaluate(
        self,
        *,
        case: EvaluationCase,
        slice_policy: BaselineSlicePolicy,
    ) -> EvaluationDecision: ...


@dataclass(slots=True)
class DeterministicBaselineFactory:
    parameters: WickHunterParameters
    hypothesis: StrategyHypothesis
    memory: SignalMemory = field(default_factory=SignalMemory)

    @property
    def strategy_id(self) -> str:
        return f"{STRATEGY_VERSION}:{self.hypothesis.value}"

    def evaluate(
        self,
        *,
        case: EvaluationCase,
        slice_policy: BaselineSlicePolicy,
    ) -> EvaluationDecision:
        candidate = generate_candidate(
            features=case.feature,
            parameters=self.parameters,
            hypothesis=self.hypothesis,
            memory=self.memory,
        )
        dimensions = _dimensions(
            case=case,
            candidate=candidate,
            hypothesis=self.hypothesis,
            policy=slice_policy,
        )
        decision = build_evaluation_decision(
            strategy_id=self.strategy_id,
            case=case,
            candidate=candidate,
            dimensions=dimensions,
        )
        cooldown = self.memory.cooldown_records
        if candidate.side is not None:
            cooldown = (
                *cooldown,
                CooldownRecord(
                    symbol=candidate.symbol,
                    side=candidate.side,
                    hypothesis=self.hypothesis,
                    candidate_at_ms=candidate.decision_timestamp_ms,
                ),
            )
        self.memory = SignalMemory(
            seen_feature_hashes=self.memory.seen_feature_hashes | {case.feature.feature_hash},
            cooldown_records=cooldown,
        )
        return decision


def _require_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise BaselineEvaluationError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _liquidity(feature: LiquidationFeatureVector, policy: BaselineSlicePolicy) -> LiquidityBucket:
    quote_volume = feature.metric("quote_volume_24h_usd")
    if quote_volume >= policy.high_liquidity_usd:
        return LiquidityBucket.HIGH
    if quote_volume >= policy.medium_liquidity_usd:
        return LiquidityBucket.MEDIUM
    return LiquidityBucket.LOW


def _regime(feature: LiquidationFeatureVector, policy: BaselineSlicePolicy) -> MarketRegime:
    trend = feature.metric("trend_return_ratio")
    if trend > policy.trend_threshold_ratio:
        return MarketRegime.UPTREND
    if trend < -policy.trend_threshold_ratio:
        return MarketRegime.DOWNTREND
    return MarketRegime.RANGE


def _source_signature(feature: LiquidationFeatureVector) -> str:
    return "+".join(aggregate.source for aggregate in feature.source_aggregates)


def _dimensions(
    *,
    case: EvaluationCase,
    candidate: WickHunterCandidate | None,
    hypothesis: StrategyHypothesis,
    policy: BaselineSlicePolicy,
) -> EvaluationDimensions:
    side = "ignored" if candidate is None or candidate.side is None else candidate.side.value
    return EvaluationDimensions(
        split_name=case.split_name,
        symbol=case.feature.symbol,
        side=side,
        liquidity=_liquidity(case.feature, policy),
        source=_source_signature(case.feature),
        regime=_regime(case.feature, policy),
        hypothesis=hypothesis,
    )


def build_evaluation_decision(
    *,
    strategy_id: str,
    case: EvaluationCase,
    candidate: WickHunterCandidate,
    dimensions: EvaluationDimensions,
    score_id: str | None = None,
    model_version: str | None = None,
) -> EvaluationDecision:
    if candidate.feature_hash != case.feature.feature_hash:
        raise BaselineEvaluationError("candidate feature identity mismatch")
    if candidate.symbol != case.feature.symbol:
        raise BaselineEvaluationError("candidate symbol identity mismatch")
    if candidate.decision_timestamp_ms != case.feature.decision_timestamp_ms:
        raise BaselineEvaluationError("candidate decision timestamp identity mismatch")
    label = None if candidate.side is None else case.label_for(candidate.side)
    payload = {
        "interface_version": EVALUATION_INTERFACE_VERSION,
        "strategy_id": strategy_id,
        "case_sha256": case.case_sha256,
        "candidate_id": candidate.candidate_id,
        "score_id": score_id,
        "model_version": model_version,
        "label_id": None if label is None else label.label_id,
    }
    return EvaluationDecision(
        schema_version=BASELINE_DECISION_SCHEMA_VERSION,
        interface_version=EVALUATION_INTERFACE_VERSION,
        decision_id=canonical_sha256(payload),
        strategy_id=strategy_id,
        case_sha256=case.case_sha256,
        dataset_row_sha256=case.dataset_row_sha256,
        feature_hash=case.feature.feature_hash,
        candidate_id=candidate.candidate_id,
        action=candidate.action,
        side=candidate.side,
        status=(
            EvaluationStatus.IGNORED
            if candidate.action is CandidateAction.IGNORE
            else EvaluationStatus.SELECTED
        ),
        reason_codes=candidate.reason_codes,
        score_id=score_id,
        model_version=model_version,
        label_id=None if label is None else label.label_id,
        label_outcome=None if label is None else label.outcome,
        gross_return_ratio=None if label is None else label.gross_return_ratio,
        net_return_ratio=None if label is None else label.net_return_ratio,
        maximum_favorable_excursion_ratio=(
            None if label is None else label.maximum_favorable_excursion_ratio
        ),
        maximum_adverse_excursion_ratio=(
            None if label is None else label.maximum_adverse_excursion_ratio
        ),
        time_to_outcome_ms=None if label is None else label.time_to_outcome_ms,
        dimensions=dimensions,
        protected_holdout_accessed=False,
        model_promoted=False,
        profitability_claimed=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )


def _summary(
    decisions: Sequence[EvaluationDecision],
    *,
    dimension: str,
    value: str,
) -> EvaluationSummary:
    selected = [item for item in decisions if item.status is EvaluationStatus.SELECTED]
    executed = [item for item in selected if item.label_outcome is not LabelOutcome.MISSING_ENTRY]
    missing = [item for item in selected if item.label_outcome is LabelOutcome.MISSING_ENTRY]
    outcomes = tuple(
        sorted(
            (
                outcome.value,
                sum(item.label_outcome is outcome for item in selected),
            )
            for outcome in LabelOutcome
        )
    )
    if executed:
        gross_values = [item.gross_return_ratio for item in executed]
        net_values = [item.net_return_ratio for item in executed]
        mfe_values = [item.maximum_favorable_excursion_ratio for item in executed]
        mae_values = [item.maximum_adverse_excursion_ratio for item in executed]
        duration_values = [item.time_to_outcome_ms for item in executed]
        if any(value is None for value in (*gross_values, *net_values, *mfe_values, *mae_values)):
            raise BaselineEvaluationError("executed decisions contain incomplete decimal results")
        if any(value is None for value in duration_values):
            raise BaselineEvaluationError("executed decisions contain incomplete durations")
        gross = [value for value in gross_values if value is not None]
        net = [value for value in net_values if value is not None]
        mfe = [value for value in mfe_values if value is not None]
        mae = [value for value in mae_values if value is not None]
        duration = [Decimal(value) for value in duration_values if value is not None]
        divisor = Decimal(len(executed))
        gross_sum = sum(gross, Decimal(0))
        net_sum = sum(net, Decimal(0))
        return EvaluationSummary(
            dimension=dimension,
            value=value,
            decision_count=len(decisions),
            selected_count=len(selected),
            ignored_count=len(decisions) - len(selected),
            executed_label_count=len(executed),
            missing_entry_count=len(missing),
            outcome_counts=outcomes,
            gross_return_sum=gross_sum,
            net_return_sum=net_sum,
            net_return_mean=net_sum / divisor,
            maximum_favorable_excursion_mean=sum(mfe, Decimal(0)) / divisor,
            maximum_adverse_excursion_mean=sum(mae, Decimal(0)) / divisor,
            time_to_outcome_mean_ms=sum(duration, Decimal(0)) / divisor,
        )
    return EvaluationSummary(
        dimension=dimension,
        value=value,
        decision_count=len(decisions),
        selected_count=len(selected),
        ignored_count=len(decisions) - len(selected),
        executed_label_count=0,
        missing_entry_count=len(missing),
        outcome_counts=outcomes,
        gross_return_sum=None,
        net_return_sum=None,
        net_return_mean=None,
        maximum_favorable_excursion_mean=None,
        maximum_adverse_excursion_mean=None,
        time_to_outcome_mean_ms=None,
    )


def summarize_evaluation(
    decisions: Sequence[EvaluationDecision],
) -> tuple[EvaluationSummary, tuple[EvaluationSummary, ...]]:
    if not decisions:
        raise BaselineEvaluationError("cannot summarize an empty evaluation")
    overall = _summary(decisions, dimension="overall", value="all")
    grouped: dict[tuple[str, str], list[EvaluationDecision]] = defaultdict(list)
    for decision in decisions:
        values = {
            "split": decision.dimensions.split_name,
            "symbol": decision.dimensions.symbol,
            "side": decision.dimensions.side,
            "liquidity": decision.dimensions.liquidity.value,
            "source": decision.dimensions.source,
            "regime": decision.dimensions.regime.value,
            "hypothesis": decision.dimensions.hypothesis.value,
        }
        for dimension, value in values.items():
            grouped[(dimension, value)].append(decision)
    slices = tuple(
        _summary(items, dimension=dimension, value=value)
        for (dimension, value), items in sorted(grouped.items())
    )
    return overall, slices


def _validate_replay_parameter_parity(
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
) -> None:
    for case in cases:
        for label in case.labels:
            if label.take_profit_ratio != parameters.take_profit_ratio:
                raise BaselineEvaluationError(
                    "baseline take_profit_ratio does not match WH-02 label policy"
                )
            if label.stop_loss_ratio != parameters.stop_loss_ratio:
                raise BaselineEvaluationError(
                    "baseline stop_loss_ratio does not match WH-02 label policy"
                )
            if label.label_end_ms - label.decision_timestamp_ms != parameters.maximum_holding_ms:
                raise BaselineEvaluationError(
                    "baseline maximum_holding_ms does not match WH-02 label horizon"
                )


def _identity(cases: Sequence[EvaluationCase]) -> Mapping[str, object]:
    values = {
        (
            label.dataset_id,
            label.dataset_manifest_sha256,
            label.market_manifest_sha256,
            label.split_geometry_sha256,
            label.price_path_manifest_sha256,
            label.policy_version,
            label.policy_sha256,
            label.fee_ratio,
            label.slippage_ratio,
            label.take_profit_ratio,
            label.stop_loss_ratio,
            label.label_end_ms - label.decision_timestamp_ms,
        )
        for case in cases
        for label in case.labels
    }
    if len(values) != 1:
        raise BaselineEvaluationError("evaluation cases do not share one replay identity")
    (
        dataset_id,
        dataset_manifest_sha256,
        market_manifest_sha256,
        split_geometry_sha256,
        price_path_manifest_sha256,
        policy_version,
        policy_sha256,
        fee_ratio,
        slippage_ratio,
        take_profit_ratio,
        stop_loss_ratio,
        label_horizon_ms,
    ) = next(iter(values))
    return {
        "dataset_id": dataset_id,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "market_manifest_sha256": market_manifest_sha256,
        "split_geometry_sha256": split_geometry_sha256,
        "price_path_manifest_sha256": price_path_manifest_sha256,
        "replay_policy_version": policy_version,
        "replay_policy_sha256": policy_sha256,
        "fee_ratio": fee_ratio,
        "slippage_ratio": slippage_ratio,
        "take_profit_ratio": take_profit_ratio,
        "stop_loss_ratio": stop_loss_ratio,
        "label_horizon_ms": label_horizon_ms,
    }


def evaluate_deterministic_baselines(
    *,
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
    parameter_bounds: WickHunterParameterBounds,
    slice_policy: BaselineSlicePolicy = DEFAULT_SLICE_POLICY,
    hypotheses: tuple[StrategyHypothesis, ...] = (
        StrategyHypothesis.CONTINUATION,
        StrategyHypothesis.REVERSAL,
    ),
) -> BaselineEvaluationReport:
    validate_parameters(parameters, parameter_bounds)
    if not cases:
        raise BaselineEvaluationError("baseline evaluation requires cases")
    if hypotheses != tuple(sorted(set(hypotheses), key=lambda item: item.value)):
        raise BaselineEvaluationError("hypotheses must be unique and sorted")
    if not hypotheses:
        raise BaselineEvaluationError("at least one hypothesis is required")
    ordered_cases = tuple(
        sorted(
            cases,
            key=lambda item: (
                item.split_name,
                item.feature.symbol,
                item.feature.decision_timestamp_ms,
                item.dataset_row_sha256,
            ),
        )
    )
    _validate_replay_parameter_parity(ordered_cases, parameters)
    identity = _identity(ordered_cases)
    factories = {
        hypothesis: DeterministicBaselineFactory(parameters, hypothesis)
        for hypothesis in hypotheses
    }
    decisions: list[EvaluationDecision] = []
    for case in ordered_cases:
        for hypothesis in hypotheses:
            factory = factories[hypothesis]
            decisions.append(
                factory.evaluate(
                    case=case,
                    slice_policy=slice_policy,
                )
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
    overall, slices = summarize_evaluation(ordered_decisions)
    report_seed = {
        "schema_version": BASELINE_REPORT_SCHEMA_VERSION,
        "interface_version": EVALUATION_INTERFACE_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "parameter_version": parameters.parameter_version,
        "parameter_sha256": parameters.parameter_hash,
        "slice_policy_version": slice_policy.policy_version,
        "slice_policy_sha256": slice_policy.policy_sha256,
        **identity,
        "decision_ids": tuple(item.decision_id for item in ordered_decisions),
        "overall": overall,
        "slices": slices,
        "conclusion": DESCRIPTIVE_CONCLUSION,
    }
    return BaselineEvaluationReport(
        schema_version=BASELINE_REPORT_SCHEMA_VERSION,
        interface_version=EVALUATION_INTERFACE_VERSION,
        report_id=canonical_sha256(report_seed),
        strategy_version=STRATEGY_VERSION,
        parameter_version=parameters.parameter_version,
        parameter_sha256=parameters.parameter_hash,
        slice_policy_version=slice_policy.policy_version,
        slice_policy_sha256=slice_policy.policy_sha256,
        dataset_id=str(identity["dataset_id"]),
        dataset_manifest_sha256=str(identity["dataset_manifest_sha256"]),
        market_manifest_sha256=str(identity["market_manifest_sha256"]),
        split_geometry_sha256=str(identity["split_geometry_sha256"]),
        price_path_manifest_sha256=str(identity["price_path_manifest_sha256"]),
        replay_policy_version=str(identity["replay_policy_version"]),
        replay_policy_sha256=str(identity["replay_policy_sha256"]),
        fee_ratio=Decimal(str(identity["fee_ratio"])),
        slippage_ratio=Decimal(str(identity["slippage_ratio"])),
        take_profit_ratio=Decimal(str(identity["take_profit_ratio"])),
        stop_loss_ratio=Decimal(str(identity["stop_loss_ratio"])),
        label_horizon_ms=int(str(identity["label_horizon_ms"])),
        decisions=ordered_decisions,
        overall=overall,
        slices=slices,
        conclusion=DESCRIPTIVE_CONCLUSION,
        protected_holdout_accessed=False,
        model_promoted=False,
        profitability_claimed=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )
