from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Collection

from ai_platform.research.liquidations.contracts import (
    CounterTradeAction,
    LiquidatedPositionSide,
    LiquidationEvent,
    non_negative_decimal,
    positive_decimal,
)


@dataclass(frozen=True, slots=True)
class LiquidationSignalPolicy:
    allowed_sources: frozenset[str]
    allowed_symbols: frozenset[str]
    minimum_notional_usd: Decimal
    long_distance_ratio: Decimal
    short_distance_ratio: Decimal
    maximum_event_age_ms: int
    allow_long: bool = True
    allow_short: bool = True

    @classmethod
    def create(
        cls,
        *,
        allowed_sources: Collection[str],
        allowed_symbols: Collection[str],
        minimum_notional_usd: object,
        long_distance_ratio: object,
        short_distance_ratio: object,
        maximum_event_age_ms: int,
        allow_long: bool = True,
        allow_short: bool = True,
    ) -> LiquidationSignalPolicy:
        sources = frozenset(item.strip().lower() for item in allowed_sources if item.strip())
        symbols = frozenset(item.strip().upper() for item in allowed_symbols if item.strip())
        if not sources:
            raise ValueError("allowed_sources must not be empty")
        if not symbols:
            raise ValueError("allowed_symbols must not be empty")
        if maximum_event_age_ms < 0:
            raise ValueError("maximum_event_age_ms must be >= 0")
        if not allow_long and not allow_short:
            raise ValueError("at least one trade direction must be enabled")
        return cls(
            allowed_sources=sources,
            allowed_symbols=symbols,
            minimum_notional_usd=positive_decimal(
                minimum_notional_usd,
                field="minimum_notional_usd",
            ),
            long_distance_ratio=non_negative_decimal(
                long_distance_ratio,
                field="long_distance_ratio",
            ),
            short_distance_ratio=non_negative_decimal(
                short_distance_ratio,
                field="short_distance_ratio",
            ),
            maximum_event_age_ms=maximum_event_age_ms,
            allow_long=allow_long,
            allow_short=allow_short,
        )


@dataclass(frozen=True, slots=True)
class SignalDecision:
    action: CounterTradeAction
    reason: str
    event_id: str


def decide_counter_trade(
    event: LiquidationEvent,
    *,
    completed_candle_vwap: object,
    decision_time_ms: int,
    policy: LiquidationSignalPolicy,
) -> SignalDecision:
    vwap = positive_decimal(completed_candle_vwap, field="completed_candle_vwap")
    if decision_time_ms < event.received_at_ms:
        raise ValueError("decision_time_ms must be >= received_at_ms")

    if event.source.lower() not in policy.allowed_sources:
        return SignalDecision(
            CounterTradeAction.IGNORE,
            "source_not_allowed",
            event.source_event_id,
        )
    if event.symbol.upper() not in policy.allowed_symbols:
        return SignalDecision(
            CounterTradeAction.IGNORE,
            "symbol_not_allowed",
            event.source_event_id,
        )
    if event.notional_usd < policy.minimum_notional_usd:
        return SignalDecision(
            CounterTradeAction.IGNORE,
            "below_minimum_notional",
            event.source_event_id,
        )
    if decision_time_ms - event.occurred_at_ms > policy.maximum_event_age_ms:
        return SignalDecision(CounterTradeAction.IGNORE, "stale_event", event.source_event_id)

    if event.liquidated_position_side is LiquidatedPositionSide.LONG:
        lower_band = vwap * (Decimal("1") - policy.long_distance_ratio)
        if event.price <= lower_band and policy.allow_long:
            return SignalDecision(
                CounterTradeAction.ENTER_LONG,
                "liquidated_long_below_lower_band",
                event.source_event_id,
            )
        return SignalDecision(CounterTradeAction.IGNORE, "long_band_not_met", event.source_event_id)

    upper_band = vwap * (Decimal("1") + policy.short_distance_ratio)
    if event.price >= upper_band and policy.allow_short:
        return SignalDecision(
            CounterTradeAction.ENTER_SHORT,
            "liquidated_short_above_upper_band",
            event.source_event_id,
        )
    return SignalDecision(CounterTradeAction.IGNORE, "short_band_not_met", event.source_event_id)
