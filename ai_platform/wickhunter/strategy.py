from __future__ import annotations

from dataclasses import dataclass

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    CandidateAction,
    LiquidationFeatureVector,
    StrategyHypothesis,
    TradeDirection,
    WickHunterCandidate,
)
from ai_platform.wickhunter.parameters import WickHunterParameters


STRATEGY_VERSION = "wickhunter-deterministic-baseline-v1"


@dataclass(frozen=True, slots=True)
class CooldownRecord:
    symbol: str
    side: TradeDirection
    hypothesis: StrategyHypothesis
    candidate_at_ms: int


@dataclass(frozen=True, slots=True)
class SignalMemory:
    seen_feature_hashes: frozenset[str] = frozenset()
    cooldown_records: tuple[CooldownRecord, ...] = ()


def _candidate(
    *,
    action: CandidateAction,
    hypothesis: StrategyHypothesis,
    features: LiquidationFeatureVector,
    parameters: WickHunterParameters,
    reasons: tuple[str, ...],
) -> WickHunterCandidate:
    sorted_reasons = tuple(sorted(set(reasons)))
    candidate_id = canonical_sha256(
        {
            "strategy_version": STRATEGY_VERSION,
            "action": action.value,
            "hypothesis": hypothesis.value,
            "feature_hash": features.feature_hash,
            "parameter_hash": parameters.parameter_hash,
            "reasons": sorted_reasons,
        }
    )
    return WickHunterCandidate(
        candidate_id=candidate_id,
        action=action,
        hypothesis=hypothesis,
        symbol=features.symbol,
        decision_timestamp_ms=features.decision_timestamp_ms,
        decision_price=features.decision_price,
        reason_codes=sorted_reasons,
        feature_hash=features.feature_hash,
        parameter_version=parameters.parameter_version,
        parameter_hash=parameters.parameter_hash,
    )


def _ignored(
    *,
    hypothesis: StrategyHypothesis,
    features: LiquidationFeatureVector,
    parameters: WickHunterParameters,
    reasons: tuple[str, ...],
) -> WickHunterCandidate:
    return _candidate(
        action=CandidateAction.IGNORE,
        hypothesis=hypothesis,
        features=features,
        parameters=parameters,
        reasons=reasons,
    )


def _is_in_cooldown(
    *,
    memory: SignalMemory,
    symbol: str,
    side: TradeDirection,
    hypothesis: StrategyHypothesis,
    decision_timestamp_ms: int,
    cooldown_ms: int,
) -> bool:
    return any(
        record.symbol.upper() == symbol.upper()
        and record.side is side
        and record.hypothesis is hypothesis
        and decision_timestamp_ms - record.candidate_at_ms < cooldown_ms
        for record in memory.cooldown_records
        if record.candidate_at_ms <= decision_timestamp_ms
    )


def generate_candidate(  # noqa: C901
    *,
    features: LiquidationFeatureVector,
    parameters: WickHunterParameters,
    hypothesis: StrategyHypothesis,
    memory: SignalMemory | None = None,
) -> WickHunterCandidate:
    memory = memory or SignalMemory()
    if features.feature_hash in memory.seen_feature_hashes:
        return _ignored(
            hypothesis=hypothesis,
            features=features,
            parameters=parameters,
            reasons=("duplicate_feature_evidence",),
        )

    event_age_ms = features.decision_timestamp_ms - max(
        aggregate.latest_received_at_ms for aggregate in features.source_aggregates
    )
    rejection_reasons: list[str] = []
    if event_age_ms > parameters.maximum_event_age_ms:
        rejection_reasons.append("liquidation_event_stale")
    if (
        features.maximum_event_percentile < parameters.liquidation_percentile
        and features.maximum_event_zscore < parameters.liquidation_zscore
    ):
        rejection_reasons.append("liquidation_threshold_not_met")

    quote_volume = features.metric("quote_volume_24h_usd")
    volatility = features.metric("volatility_ratio")
    wick_ratio = features.metric("wick_ratio")
    if quote_volume < parameters.minimum_quote_volume_usd:
        rejection_reasons.append("quote_volume_below_minimum")
    if not parameters.minimum_volatility <= volatility <= parameters.maximum_volatility:
        rejection_reasons.append("volatility_outside_range")
    if wick_ratio < parameters.minimum_wick_ratio:
        rejection_reasons.append("wick_ratio_below_minimum")
    if rejection_reasons:
        return _ignored(
            hypothesis=hypothesis,
            features=features,
            parameters=parameters,
            reasons=tuple(rejection_reasons),
        )

    vwap = features.metric("vwap")
    vwma = features.metric("vwma")
    trend_return = features.metric("trend_return_ratio")
    vwap_distance = (features.decision_price - vwap) / vwap
    vwma_distance = (features.decision_price - vwma) / vwma

    long_liquidations_dominate = (
        features.liquidated_long_notional_usd > features.liquidated_short_notional_usd
    )
    short_liquidations_dominate = (
        features.liquidated_short_notional_usd > features.liquidated_long_notional_usd
    )
    action = CandidateAction.IGNORE
    reasons: tuple[str, ...] = ("liquidation_direction_tied",)

    if hypothesis is StrategyHypothesis.REVERSAL:
        if long_liquidations_dominate:
            if (
                vwap_distance <= -parameters.long_vwap_distance_ratio
                and vwma_distance <= -parameters.long_vwap_distance_ratio
            ):
                action = CandidateAction.ENTER_LONG
                reasons = (
                    "liquidated_longs_dominate",
                    "reversal_hypothesis",
                    "below_vwap_vwma_band",
                )
            else:
                reasons = ("reversal_long_band_not_met",)
        elif short_liquidations_dominate:
            if (
                vwap_distance >= parameters.short_vwap_distance_ratio
                and vwma_distance >= parameters.short_vwap_distance_ratio
            ):
                action = CandidateAction.ENTER_SHORT
                reasons = (
                    "liquidated_shorts_dominate",
                    "reversal_hypothesis",
                    "above_vwap_vwma_band",
                )
            else:
                reasons = ("reversal_short_band_not_met",)
    else:
        if long_liquidations_dominate:
            if (
                vwap_distance <= -parameters.long_vwap_distance_ratio
                and vwma_distance <= -parameters.long_vwap_distance_ratio
                and trend_return < 0
            ):
                action = CandidateAction.ENTER_SHORT
                reasons = (
                    "liquidated_longs_dominate",
                    "continuation_hypothesis",
                    "downtrend_continuation_confirmed",
                )
            else:
                reasons = ("continuation_short_confirmation_not_met",)
        elif short_liquidations_dominate:
            if (
                vwap_distance >= parameters.short_vwap_distance_ratio
                and vwma_distance >= parameters.short_vwap_distance_ratio
                and trend_return > 0
            ):
                action = CandidateAction.ENTER_LONG
                reasons = (
                    "liquidated_shorts_dominate",
                    "continuation_hypothesis",
                    "uptrend_continuation_confirmed",
                )
            else:
                reasons = ("continuation_long_confirmation_not_met",)

    if action is CandidateAction.IGNORE:
        return _ignored(
            hypothesis=hypothesis,
            features=features,
            parameters=parameters,
            reasons=reasons,
        )

    side = TradeDirection.LONG if action is CandidateAction.ENTER_LONG else TradeDirection.SHORT
    if _is_in_cooldown(
        memory=memory,
        symbol=features.symbol,
        side=side,
        hypothesis=hypothesis,
        decision_timestamp_ms=features.decision_timestamp_ms,
        cooldown_ms=parameters.cooldown_ms,
    ):
        return _ignored(
            hypothesis=hypothesis,
            features=features,
            parameters=parameters,
            reasons=("symbol_side_cooldown_active",),
        )

    return _candidate(
        action=action,
        hypothesis=hypothesis,
        features=features,
        parameters=parameters,
        reasons=reasons,
    )
