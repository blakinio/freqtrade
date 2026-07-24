from __future__ import annotations

from dataclasses import dataclass

from ai_platform.research.liquidations.contracts import LiquidationEvent


@dataclass(frozen=True, slots=True)
class CandleAlignment:
    timeframe_ms: int
    containing_candle_open_ms: int
    containing_candle_close_ms: int
    last_completed_candle_open_ms: int
    decision_available_at_ms: int


def timeframe_to_ms(timeframe: str) -> int:
    if len(timeframe) < 2:
        raise ValueError("timeframe must contain a positive integer and unit")
    try:
        value = int(timeframe[:-1])
    except ValueError as exc:
        raise ValueError("timeframe must contain a positive integer and unit") from exc
    if value <= 0:
        raise ValueError("timeframe value must be > 0")

    unit = timeframe[-1]
    multipliers = {
        "s": 1_000,
        "m": 60_000,
        "h": 3_600_000,
        "d": 86_400_000,
    }
    try:
        return value * multipliers[unit]
    except KeyError as exc:
        raise ValueError(f"unsupported timeframe unit: {unit}") from exc


def align_event_to_closed_candles(
    event: LiquidationEvent,
    *,
    timeframe: str,
) -> CandleAlignment:
    timeframe_ms = timeframe_to_ms(timeframe)
    containing_open = (event.occurred_at_ms // timeframe_ms) * timeframe_ms
    containing_close = containing_open + timeframe_ms
    return CandleAlignment(
        timeframe_ms=timeframe_ms,
        containing_candle_open_ms=containing_open,
        containing_candle_close_ms=containing_close,
        last_completed_candle_open_ms=containing_open - timeframe_ms,
        decision_available_at_ms=event.received_at_ms,
    )
