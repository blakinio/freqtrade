from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from ai_platform.wickhunter.canonical import canonical_sha256


SHA256_LENGTH = 64


def _require_text(value: str, *, field: str) -> None:
    if not value.strip():
        raise ValueError(f"{field} must be non-empty")


def _require_sha256(value: str, *, field: str) -> None:
    invalid_character = any(character not in "0123456789abcdef" for character in value)
    if len(value) != SHA256_LENGTH or invalid_character:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _require_git_sha(value: str, *, field: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase 40-character Git SHA")


def _require_ratio(value: Decimal, *, field: str, maximum: Decimal = Decimal("1")) -> None:
    if not value.is_finite() or value < 0 or value > maximum:
        raise ValueError(f"{field} must be within [0, {maximum}]")


def _require_positive(value: Decimal, *, field: str) -> None:
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{field} must be finite and > 0")


class StrategyHypothesis(StrEnum):
    REVERSAL = "reversal"
    CONTINUATION = "continuation"


class TradeDirection(StrEnum):
    LONG = "long"
    SHORT = "short"


class CandidateAction(StrEnum):
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    IGNORE = "ignore"


class ScoreKind(StrEnum):
    DETERMINISTIC_BASELINE = "deterministic_baseline"
    SUPERVISED_MODEL = "supervised_model"


class ModelPromotionState(StrEnum):
    BASELINE = "baseline"
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class SourceHealth(StrEnum):
    HEALTHY = "healthy"
    STALE = "stale"
    OFFLINE = "offline"


class DriftState(StrEnum):
    HEALTHY = "healthy"
    DRIFTED = "drifted"
    UNKNOWN = "unknown"


class BotMode(StrEnum):
    RESEARCH = "research"
    SHADOW = "shadow"
    PAPER = "paper"
    LIVE_BLOCKED = "live_blocked"


class RiskOutcome(StrEnum):
    ALLOW = "allow"
    REJECT = "reject"


class ShadowStatus(StrEnum):
    NO_CANDIDATE = "no_candidate"
    SIMULATED_ALLOWED = "simulated_allowed"
    SIMULATED_REJECTED = "simulated_rejected"


@dataclass(frozen=True, slots=True)
class AvailableMetric:
    name: str
    value: Decimal
    available_at_ms: int
    source: str

    def __post_init__(self) -> None:
        _require_text(self.name, field="metric name")
        _require_text(self.source, field="metric source")
        if not self.value.is_finite():
            raise ValueError("metric value must be finite")
        if self.available_at_ms <= 0:
            raise ValueError("metric available_at_ms must be > 0")


@dataclass(frozen=True, slots=True)
class MarketContextSnapshot:
    symbol: str
    decision_timestamp_ms: int
    decision_price: Decimal
    completed_candle_close_ms: int
    metrics: tuple[AvailableMetric, ...]

    def __post_init__(self) -> None:
        _require_text(self.symbol, field="symbol")
        if self.decision_timestamp_ms <= 0:
            raise ValueError("decision_timestamp_ms must be > 0")
        _require_positive(self.decision_price, field="decision_price")
        if self.completed_candle_close_ms <= 0:
            raise ValueError("completed_candle_close_ms must be > 0")
        if self.completed_candle_close_ms > self.decision_timestamp_ms:
            raise ValueError("completed candle must close before the decision")
        names = [metric.name for metric in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("market metric names must be unique")

    def metric(self, name: str) -> AvailableMetric:
        try:
            return next(metric for metric in self.metrics if metric.name == name)
        except StopIteration as exc:
            raise KeyError(f"missing market metric: {name}") from exc


@dataclass(frozen=True, slots=True)
class LiquidationSourceState:
    source: str
    health: SourceHealth
    coverage_available: bool
    last_received_at_ms: int | None
    observed_at_ms: int

    def __post_init__(self) -> None:
        _require_text(self.source, field="source")
        if self.observed_at_ms <= 0:
            raise ValueError("source observed_at_ms must be > 0")
        if self.last_received_at_ms is not None and self.last_received_at_ms <= 0:
            raise ValueError("source last_received_at_ms must be > 0 when supplied")
        if self.health is SourceHealth.HEALTHY and not self.coverage_available:
            raise ValueError("healthy source requires coverage")


@dataclass(frozen=True, slots=True)
class LiquidationHistorySnapshot:
    symbol: str
    event_notionals_usd: tuple[Decimal, ...]
    burst_window_notionals_usd: tuple[Decimal, ...]
    previous_burst_received_at_ms: int | None
    available_at_ms: int
    history_id: str
    history_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.symbol, field="history symbol")
        _require_text(self.history_id, field="history_id")
        _require_sha256(self.history_sha256, field="history_sha256")
        if self.available_at_ms <= 0:
            raise ValueError("history available_at_ms must be > 0")
        if not self.event_notionals_usd or not self.burst_window_notionals_usd:
            raise ValueError("liquidation history must contain event and burst samples")
        for value in (*self.event_notionals_usd, *self.burst_window_notionals_usd):
            _require_positive(value, field="historical notional")
        if self.previous_burst_received_at_ms is not None:
            if self.previous_burst_received_at_ms <= 0:
                raise ValueError("previous burst timestamp must be > 0")
            if self.previous_burst_received_at_ms > self.available_at_ms:
                raise ValueError("previous burst timestamp cannot be in the future")


@dataclass(frozen=True, slots=True)
class SourceLiquidationAggregate:
    source: str
    event_count: int
    total_notional_usd: Decimal
    liquidated_long_notional_usd: Decimal
    liquidated_short_notional_usd: Decimal
    maximum_event_notional_usd: Decimal
    maximum_ingest_latency_ms: int
    latest_received_at_ms: int

    def __post_init__(self) -> None:
        _require_text(self.source, field="aggregate source")
        if self.event_count < 1:
            raise ValueError("source aggregate event_count must be >= 1")
        for field_name in (
            "total_notional_usd",
            "maximum_event_notional_usd",
        ):
            _require_positive(getattr(self, field_name), field=field_name)
        for field_name in (
            "liquidated_long_notional_usd",
            "liquidated_short_notional_usd",
        ):
            value = getattr(self, field_name)
            if not value.is_finite() or value < 0:
                raise ValueError(f"{field_name} must be finite and >= 0")
        if self.maximum_ingest_latency_ms < 0:
            raise ValueError("maximum_ingest_latency_ms must be >= 0")
        if self.latest_received_at_ms <= 0:
            raise ValueError("latest_received_at_ms must be > 0")


@dataclass(frozen=True, slots=True)
class LiquidationFeatureVector:
    feature_schema_version: str
    symbol: str
    decision_timestamp_ms: int
    decision_price: Decimal
    event_count: int
    total_notional_usd: Decimal
    liquidated_long_notional_usd: Decimal
    liquidated_short_notional_usd: Decimal
    long_short_imbalance: Decimal
    maximum_event_notional_usd: Decimal
    maximum_event_percentile: Decimal
    maximum_event_zscore: Decimal
    liquidation_burst_intensity: Decimal
    time_since_previous_burst_ms: int | None
    ingest_latency_ms: int
    source_coverage_ratio: Decimal
    source_aggregates: tuple[SourceLiquidationAggregate, ...]
    market_metrics: tuple[AvailableMetric, ...]
    feature_available_at_ms: int
    input_event_ids: tuple[str, ...]
    history_id: str
    history_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.feature_schema_version, field="feature_schema_version")
        _require_text(self.symbol, field="feature symbol")
        _require_positive(self.decision_price, field="decision_price")
        if self.event_count < 1:
            raise ValueError("feature event_count must be >= 1")
        _require_positive(self.total_notional_usd, field="total_notional_usd")
        _require_positive(self.maximum_event_notional_usd, field="maximum_event_notional_usd")
        _require_ratio(self.maximum_event_percentile, field="maximum_event_percentile")
        _require_ratio(self.source_coverage_ratio, field="source_coverage_ratio")
        if self.feature_available_at_ms > self.decision_timestamp_ms:
            raise ValueError("feature availability cannot be after decision")
        if not self.source_aggregates:
            raise ValueError("source-labelled aggregates are required")
        sources = [aggregate.source for aggregate in self.source_aggregates]
        if sources != sorted(sources) or len(sources) != len(set(sources)):
            raise ValueError("source aggregates must be unique and sorted")
        if tuple(sorted(self.input_event_ids)) != self.input_event_ids:
            raise ValueError("input_event_ids must be sorted")
        _require_sha256(self.history_sha256, field="history_sha256")

    @property
    def feature_hash(self) -> str:
        return canonical_sha256(self)

    def metric(self, name: str) -> Decimal:
        try:
            return next(metric.value for metric in self.market_metrics if metric.name == name)
        except StopIteration as exc:
            raise KeyError(f"missing feature metric: {name}") from exc


@dataclass(frozen=True, slots=True)
class WickHunterCandidate:
    candidate_id: str
    action: CandidateAction
    hypothesis: StrategyHypothesis
    symbol: str
    decision_timestamp_ms: int
    decision_price: Decimal
    reason_codes: tuple[str, ...]
    feature_hash: str
    parameter_version: str
    parameter_hash: str

    def __post_init__(self) -> None:
        _require_sha256(self.candidate_id, field="candidate_id")
        _require_text(self.symbol, field="candidate symbol")
        _require_positive(self.decision_price, field="candidate decision_price")
        _require_sha256(self.feature_hash, field="feature_hash")
        _require_text(self.parameter_version, field="parameter_version")
        _require_sha256(self.parameter_hash, field="parameter_hash")
        if not self.reason_codes:
            raise ValueError("candidate requires reason_codes")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("candidate reason_codes must be unique and sorted")

    @property
    def side(self) -> TradeDirection | None:
        if self.action is CandidateAction.ENTER_LONG:
            return TradeDirection.LONG
        if self.action is CandidateAction.ENTER_SHORT:
            return TradeDirection.SHORT
        return None


@dataclass(frozen=True, slots=True)
class CandidateScore:
    score_id: str
    kind: ScoreKind
    candidate_id: str
    feature_hash: str
    confidence: Decimal
    expected_return_after_costs: Decimal | None
    bounded_risk_multiplier: Decimal
    model_version: str | None
    model_hash: str | None
    promotion_state: ModelPromotionState
    scored_at_ms: int

    def __post_init__(self) -> None:
        for field_name in ("score_id", "candidate_id", "feature_hash"):
            _require_sha256(getattr(self, field_name), field=field_name)
        _require_ratio(self.confidence, field="confidence")
        _require_ratio(self.bounded_risk_multiplier, field="bounded_risk_multiplier")
        if self.scored_at_ms <= 0:
            raise ValueError("scored_at_ms must be > 0")
        if self.kind is ScoreKind.DETERMINISTIC_BASELINE:
            if self.model_version is not None or self.model_hash is not None:
                raise ValueError("baseline score must not claim a model identity")
            if self.promotion_state is not ModelPromotionState.BASELINE:
                raise ValueError("baseline score must use baseline promotion state")
        else:
            if self.model_version is None or self.model_hash is None:
                raise ValueError("model score requires model identity")
            _require_text(self.model_version, field="model_version")
            _require_sha256(self.model_hash, field="model_hash")


@dataclass(frozen=True, slots=True)
class DcaPlan:
    enabled: bool
    maximum_levels: int
    spacing_ratio: Decimal
    maximum_total_risk_ratio: Decimal

    def __post_init__(self) -> None:
        if self.maximum_levels < 0:
            raise ValueError("maximum_levels must be >= 0")
        _require_ratio(self.spacing_ratio, field="spacing_ratio")
        _require_ratio(self.maximum_total_risk_ratio, field="maximum_total_risk_ratio")
        if not self.enabled and self.maximum_levels != 0:
            raise ValueError("disabled DCA plan requires zero levels")
        if self.enabled and self.maximum_levels < 1:
            raise ValueError("enabled DCA plan requires at least one level")


@dataclass(frozen=True, slots=True)
class DataFreshnessEvidence:
    liquidation_age_ms: int
    candle_age_ms: int
    open_interest_age_ms: int | None
    funding_age_ms: int | None
    source_health: tuple[tuple[str, SourceHealth], ...]

    def __post_init__(self) -> None:
        for field_name in ("liquidation_age_ms", "candle_age_ms"):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")
        for field_name in ("open_interest_age_ms", "funding_age_ms"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be >= 0 when supplied")
        sources = [source for source, _ in self.source_health]
        if sources != sorted(sources) or len(sources) != len(set(sources)):
            raise ValueError("source health evidence must be unique and sorted")


@dataclass(frozen=True, slots=True)
class WickHunterTradeIntent:
    schema_version: str
    trade_intent_id: str
    candidate_id: str
    score_id: str
    bot_instance: str
    strategy_version: str
    model_version: str | None
    parameter_version: str
    symbol: str
    side: TradeDirection
    decision_timestamp_ms: int
    decision_price: Decimal
    candidate_reason: tuple[str, ...]
    liquidation_evidence_ids: tuple[str, ...]
    feature_hash: str
    confidence: Decimal
    requested_base_risk_ratio: Decimal
    requested_leverage: Decimal
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    dca_plan: DcaPlan
    expiration_timestamp_ms: int
    freshness: DataFreshnessEvidence
    dataset_hash: str
    model_hash: str | None
    code_sha: str
    parameter_hash: str
    mode: BotMode

    def __post_init__(self) -> None:
        for field_name in (
            "schema_version",
            "bot_instance",
            "strategy_version",
            "parameter_version",
            "symbol",
        ):
            _require_text(getattr(self, field_name), field=field_name)
        _require_sha256(self.trade_intent_id, field="trade_intent_id")
        _require_sha256(self.candidate_id, field="candidate_id")
        _require_sha256(self.score_id, field="score_id")
        _require_sha256(self.feature_hash, field="feature_hash")
        _require_sha256(self.dataset_hash, field="dataset_hash")
        _require_git_sha(self.code_sha, field="code_sha")
        _require_sha256(self.parameter_hash, field="parameter_hash")
        if self.model_hash is not None:
            _require_sha256(self.model_hash, field="model_hash")
        _require_positive(self.decision_price, field="decision_price")
        _require_ratio(self.confidence, field="confidence")
        _require_ratio(self.requested_base_risk_ratio, field="requested_base_risk_ratio")
        _require_positive(self.requested_leverage, field="requested_leverage")
        _require_ratio(self.take_profit_ratio, field="take_profit_ratio")
        _require_ratio(self.stop_loss_ratio, field="stop_loss_ratio")
        if self.expiration_timestamp_ms <= self.decision_timestamp_ms:
            raise ValueError("trade intent expiration must be after decision")
        if not self.candidate_reason or not self.liquidation_evidence_ids:
            raise ValueError("trade intent requires candidate and liquidation evidence")
        if self.mode is BotMode.LIVE_BLOCKED:
            raise ValueError("live-blocked mode cannot create an executable trade intent")


@dataclass(frozen=True, slots=True)
class RiskDecision:
    risk_decision_id: str
    trade_intent_id: str
    outcome: RiskOutcome
    reason_codes: tuple[str, ...]
    evaluated_at_ms: int
    risk_policy_version: str

    def __post_init__(self) -> None:
        _require_sha256(self.risk_decision_id, field="risk_decision_id")
        _require_sha256(self.trade_intent_id, field="trade_intent_id")
        _require_text(self.risk_policy_version, field="risk_policy_version")
        if not self.reason_codes:
            raise ValueError("risk decision requires reason_codes")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("risk reason_codes must be unique and sorted")
        if self.evaluated_at_ms <= 0:
            raise ValueError("evaluated_at_ms must be > 0")


@dataclass(frozen=True, slots=True)
class ShadowDecisionEvidence:
    schema_version: str
    shadow_decision_id: str
    status: ShadowStatus
    mode: BotMode
    universe_snapshot_hash: str
    feature_hash: str | None
    candidate: WickHunterCandidate | None
    score: CandidateScore | None
    trade_intent: WickHunterTradeIntent | None
    risk_decision: RiskDecision | None
    created_at_ms: int

    def __post_init__(self) -> None:
        _require_text(self.schema_version, field="shadow schema_version")
        _require_sha256(self.shadow_decision_id, field="shadow_decision_id")
        _require_sha256(self.universe_snapshot_hash, field="universe_snapshot_hash")
        if self.feature_hash is not None:
            _require_sha256(self.feature_hash, field="shadow feature_hash")
        if self.created_at_ms <= 0:
            raise ValueError("shadow created_at_ms must be > 0")
        if self.status is ShadowStatus.NO_CANDIDATE:
            if self.trade_intent is not None or self.risk_decision is not None:
                raise ValueError("no-candidate result cannot contain intent or risk decision")
        else:
            if self.trade_intent is None or self.risk_decision is None:
                raise ValueError("simulated result requires intent and risk decision")
