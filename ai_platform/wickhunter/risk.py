from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateScore,
    DriftState,
    ModelPromotionState,
    RiskDecision,
    RiskOutcome,
    ScoreKind,
    SourceHealth,
    WickHunterTradeIntent,
)


class RiskReason(StrEnum):
    RISK_APPROVED = "RISK_APPROVED"
    INTENT_EXPIRED = "INTENT_EXPIRED"
    MODE_NOT_AUTHORIZED = "MODE_NOT_AUTHORIZED"
    GLOBAL_KILL_SWITCH_ACTIVE = "GLOBAL_KILL_SWITCH_ACTIVE"
    CIRCUIT_BREAKER_ACTIVE = "CIRCUIT_BREAKER_ACTIVE"
    LIQUIDATION_DATA_STALE = "LIQUIDATION_DATA_STALE"
    CANDLE_DATA_STALE = "CANDLE_DATA_STALE"
    OPEN_INTEREST_DATA_STALE = "OPEN_INTEREST_DATA_STALE"
    FUNDING_DATA_STALE = "FUNDING_DATA_STALE"
    LIQUIDATION_SOURCE_UNHEALTHY = "LIQUIDATION_SOURCE_UNHEALTHY"
    SCORE_EVIDENCE_MISMATCH = "SCORE_EVIDENCE_MISMATCH"
    MODEL_NOT_APPROVED = "MODEL_NOT_APPROVED"
    MODEL_DRIFT_BLOCK = "MODEL_DRIFT_BLOCK"
    DATA_DRIFT_BLOCK = "DATA_DRIFT_BLOCK"
    MODEL_CONFIDENCE_BELOW_MINIMUM = "MODEL_CONFIDENCE_BELOW_MINIMUM"
    BASE_RISK_LIMIT_EXCEEDED = "BASE_RISK_LIMIT_EXCEEDED"
    LEVERAGE_LIMIT_EXCEEDED = "LEVERAGE_LIMIT_EXCEEDED"
    EFFECTIVE_EXPOSURE_NOT_POSITIVE = "EFFECTIVE_EXPOSURE_NOT_POSITIVE"
    EFFECTIVE_EXPOSURE_LIMIT_EXCEEDED = "EFFECTIVE_EXPOSURE_LIMIT_EXCEEDED"
    DCA_COUNT_LIMIT_EXCEEDED = "DCA_COUNT_LIMIT_EXCEEDED"
    DCA_EXPOSURE_LIMIT_EXCEEDED = "DCA_EXPOSURE_LIMIT_EXCEEDED"
    DCA_SETUP_INVALID = "DCA_SETUP_INVALID"
    DCA_TRIGGER_INVALID = "DCA_TRIGGER_INVALID"
    CONCURRENT_POSITION_LIMIT_EXCEEDED = "CONCURRENT_POSITION_LIMIT_EXCEEDED"
    SYMBOL_EXPOSURE_LIMIT_EXCEEDED = "SYMBOL_EXPOSURE_LIMIT_EXCEEDED"
    CORRELATED_EXPOSURE_LIMIT_EXCEEDED = "CORRELATED_EXPOSURE_LIMIT_EXCEEDED"
    DIRECTIONAL_EXPOSURE_LIMIT_EXCEEDED = "DIRECTIONAL_EXPOSURE_LIMIT_EXCEEDED"
    DAILY_LOSS_LIMIT_EXCEEDED = "DAILY_LOSS_LIMIT_EXCEEDED"
    DRAWDOWN_LIMIT_EXCEEDED = "DRAWDOWN_LIMIT_EXCEEDED"
    CONSECUTIVE_LOSS_COOLDOWN_ACTIVE = "CONSECUTIVE_LOSS_COOLDOWN_ACTIVE"
    SYMBOL_COOLDOWN_ACTIVE = "SYMBOL_COOLDOWN_ACTIVE"
    SPREAD_LIMIT_EXCEEDED = "SPREAD_LIMIT_EXCEEDED"
    LIQUIDITY_LIMIT_NOT_MET = "LIQUIDITY_LIMIT_NOT_MET"


@dataclass(frozen=True, slots=True)
class WickHunterRiskLimits:
    risk_policy_version: str
    maximum_base_risk_ratio: Decimal
    maximum_effective_exposure_ratio: Decimal
    maximum_leverage: Decimal
    maximum_dca_count: int
    maximum_total_dca_risk_ratio: Decimal
    maximum_concurrent_positions: int
    maximum_symbol_exposure_ratio: Decimal
    maximum_correlated_exposure_ratio: Decimal
    maximum_directional_exposure_ratio: Decimal
    maximum_daily_loss_ratio: Decimal
    maximum_drawdown_ratio: Decimal
    maximum_consecutive_losses: int
    maximum_liquidation_age_ms: int
    maximum_candle_age_ms: int
    maximum_open_interest_age_ms: int
    maximum_funding_age_ms: int
    maximum_spread_bps: Decimal
    minimum_quote_volume_usd: Decimal
    minimum_confidence: Decimal

    def __post_init__(self) -> None:
        if not self.risk_policy_version.strip():
            raise ValueError("risk_policy_version must be non-empty")
        decimal_fields = (
            "maximum_base_risk_ratio",
            "maximum_effective_exposure_ratio",
            "maximum_leverage",
            "maximum_total_dca_risk_ratio",
            "maximum_symbol_exposure_ratio",
            "maximum_correlated_exposure_ratio",
            "maximum_directional_exposure_ratio",
            "maximum_daily_loss_ratio",
            "maximum_drawdown_ratio",
            "maximum_spread_bps",
            "minimum_quote_volume_usd",
            "minimum_confidence",
        )
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if not value.is_finite() or value < 0:
                raise ValueError(f"{field_name} must be finite and >= 0")
        integer_fields = (
            "maximum_dca_count",
            "maximum_concurrent_positions",
            "maximum_consecutive_losses",
            "maximum_liquidation_age_ms",
            "maximum_candle_age_ms",
            "maximum_open_interest_age_ms",
            "maximum_funding_age_ms",
        )
        for field_name in integer_fields:
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")


@dataclass(frozen=True, slots=True)
class WickHunterRiskContext:
    evaluated_at_ms: int
    global_kill_switch_active: bool
    circuit_breaker_active: bool
    model_drift: DriftState
    data_drift: DriftState
    projected_concurrent_positions: int
    projected_symbol_exposure_ratio: Decimal
    projected_correlated_exposure_ratio: Decimal
    projected_directional_exposure_ratio: Decimal
    daily_loss_ratio: Decimal
    drawdown_ratio: Decimal
    consecutive_losses: int
    consecutive_loss_cooldown_until_ms: int | None
    symbol_cooldown_until_ms: int | None
    setup_still_valid: bool
    dca_adverse_condition_met: bool
    dca_timing_condition_met: bool
    spread_bps: Decimal
    quote_volume_usd: Decimal
    candidate_paper_validation_authorized: bool = False

    def __post_init__(self) -> None:
        if self.evaluated_at_ms <= 0:
            raise ValueError("evaluated_at_ms must be > 0")
        for field_name in (
            "projected_concurrent_positions",
            "consecutive_losses",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")
        for field_name in (
            "projected_symbol_exposure_ratio",
            "projected_correlated_exposure_ratio",
            "projected_directional_exposure_ratio",
            "daily_loss_ratio",
            "drawdown_ratio",
            "spread_bps",
            "quote_volume_usd",
        ):
            value = getattr(self, field_name)
            if not value.is_finite() or value < 0:
                raise ValueError(f"{field_name} must be finite and >= 0")


def evaluate_trade_intent(  # noqa: C901
    *,
    intent: WickHunterTradeIntent,
    score: CandidateScore,
    context: WickHunterRiskContext,
    limits: WickHunterRiskLimits,
) -> RiskDecision:
    reasons: set[RiskReason] = set()
    if intent.mode not in {BotMode.RESEARCH, BotMode.SHADOW, BotMode.PAPER}:
        reasons.add(RiskReason.MODE_NOT_AUTHORIZED)
    if context.evaluated_at_ms >= intent.expiration_timestamp_ms:
        reasons.add(RiskReason.INTENT_EXPIRED)
    if context.global_kill_switch_active:
        reasons.add(RiskReason.GLOBAL_KILL_SWITCH_ACTIVE)
    if context.circuit_breaker_active:
        reasons.add(RiskReason.CIRCUIT_BREAKER_ACTIVE)

    freshness = intent.freshness
    if freshness.liquidation_age_ms > limits.maximum_liquidation_age_ms:
        reasons.add(RiskReason.LIQUIDATION_DATA_STALE)
    if freshness.candle_age_ms > limits.maximum_candle_age_ms:
        reasons.add(RiskReason.CANDLE_DATA_STALE)
    if (
        freshness.open_interest_age_ms is not None
        and freshness.open_interest_age_ms > limits.maximum_open_interest_age_ms
    ):
        reasons.add(RiskReason.OPEN_INTEREST_DATA_STALE)
    if (
        freshness.funding_age_ms is not None
        and freshness.funding_age_ms > limits.maximum_funding_age_ms
    ):
        reasons.add(RiskReason.FUNDING_DATA_STALE)
    if any(health is not SourceHealth.HEALTHY for _, health in freshness.source_health):
        reasons.add(RiskReason.LIQUIDATION_SOURCE_UNHEALTHY)

    if (
        score.score_id != intent.score_id
        or score.candidate_id != intent.candidate_id
        or score.feature_hash != intent.feature_hash
        or score.confidence != intent.confidence
        or score.model_version != intent.model_version
        or score.model_hash != intent.model_hash
    ):
        reasons.add(RiskReason.SCORE_EVIDENCE_MISMATCH)

    if score.kind is ScoreKind.SUPERVISED_MODEL:
        candidate_paper_authorized = (
            score.promotion_state is ModelPromotionState.CANDIDATE
            and intent.mode in {BotMode.SHADOW, BotMode.PAPER}
            and context.candidate_paper_validation_authorized
        )
        if (
            score.promotion_state is not ModelPromotionState.APPROVED
            and not candidate_paper_authorized
        ):
            reasons.add(RiskReason.MODEL_NOT_APPROVED)
        if context.model_drift is not DriftState.HEALTHY:
            reasons.add(RiskReason.MODEL_DRIFT_BLOCK)
    if context.data_drift is not DriftState.HEALTHY:
        reasons.add(RiskReason.DATA_DRIFT_BLOCK)
    if score.confidence < limits.minimum_confidence:
        reasons.add(RiskReason.MODEL_CONFIDENCE_BELOW_MINIMUM)

    if intent.requested_base_risk_ratio > limits.maximum_base_risk_ratio:
        reasons.add(RiskReason.BASE_RISK_LIMIT_EXCEEDED)
    if intent.requested_leverage > limits.maximum_leverage:
        reasons.add(RiskReason.LEVERAGE_LIMIT_EXCEEDED)
    effective_exposure = (
        max(
            intent.requested_base_risk_ratio,
            intent.dca_plan.maximum_total_risk_ratio,
        )
        * intent.requested_leverage
    )
    if effective_exposure <= 0:
        reasons.add(RiskReason.EFFECTIVE_EXPOSURE_NOT_POSITIVE)
    if effective_exposure > limits.maximum_effective_exposure_ratio:
        reasons.add(RiskReason.EFFECTIVE_EXPOSURE_LIMIT_EXCEEDED)

    if intent.dca_plan.maximum_levels > limits.maximum_dca_count:
        reasons.add(RiskReason.DCA_COUNT_LIMIT_EXCEEDED)
    if intent.dca_plan.maximum_total_risk_ratio > limits.maximum_total_dca_risk_ratio:
        reasons.add(RiskReason.DCA_EXPOSURE_LIMIT_EXCEEDED)
    if intent.dca_plan.enabled:
        if not context.setup_still_valid:
            reasons.add(RiskReason.DCA_SETUP_INVALID)
        if not context.dca_adverse_condition_met or not context.dca_timing_condition_met:
            reasons.add(RiskReason.DCA_TRIGGER_INVALID)

    if context.projected_concurrent_positions > limits.maximum_concurrent_positions:
        reasons.add(RiskReason.CONCURRENT_POSITION_LIMIT_EXCEEDED)
    if context.projected_symbol_exposure_ratio > limits.maximum_symbol_exposure_ratio:
        reasons.add(RiskReason.SYMBOL_EXPOSURE_LIMIT_EXCEEDED)
    if context.projected_correlated_exposure_ratio > limits.maximum_correlated_exposure_ratio:
        reasons.add(RiskReason.CORRELATED_EXPOSURE_LIMIT_EXCEEDED)
    if context.projected_directional_exposure_ratio > limits.maximum_directional_exposure_ratio:
        reasons.add(RiskReason.DIRECTIONAL_EXPOSURE_LIMIT_EXCEEDED)
    if context.daily_loss_ratio > limits.maximum_daily_loss_ratio:
        reasons.add(RiskReason.DAILY_LOSS_LIMIT_EXCEEDED)
    if context.drawdown_ratio > limits.maximum_drawdown_ratio:
        reasons.add(RiskReason.DRAWDOWN_LIMIT_EXCEEDED)
    if context.consecutive_losses >= limits.maximum_consecutive_losses:
        if (
            context.consecutive_loss_cooldown_until_ms is None
            or context.consecutive_loss_cooldown_until_ms > context.evaluated_at_ms
        ):
            reasons.add(RiskReason.CONSECUTIVE_LOSS_COOLDOWN_ACTIVE)
    if (
        context.symbol_cooldown_until_ms is not None
        and context.symbol_cooldown_until_ms > context.evaluated_at_ms
    ):
        reasons.add(RiskReason.SYMBOL_COOLDOWN_ACTIVE)
    if context.spread_bps > limits.maximum_spread_bps:
        reasons.add(RiskReason.SPREAD_LIMIT_EXCEEDED)
    if context.quote_volume_usd < limits.minimum_quote_volume_usd:
        reasons.add(RiskReason.LIQUIDITY_LIMIT_NOT_MET)

    outcome = RiskOutcome.REJECT if reasons else RiskOutcome.ALLOW
    reason_codes = (
        tuple(sorted(reason.value for reason in reasons))
        if reasons
        else (RiskReason.RISK_APPROVED.value,)
    )
    decision_id = canonical_sha256(
        {
            "trade_intent_id": intent.trade_intent_id,
            "risk_policy_version": limits.risk_policy_version,
            "evaluated_at_ms": context.evaluated_at_ms,
            "outcome": outcome.value,
            "reason_codes": reason_codes,
        }
    )
    return RiskDecision(
        risk_decision_id=decision_id,
        trade_intent_id=intent.trade_intent_id,
        outcome=outcome,
        reason_codes=reason_codes,
        evaluated_at_ms=context.evaluated_at_ms,
        risk_policy_version=limits.risk_policy_version,
    )
