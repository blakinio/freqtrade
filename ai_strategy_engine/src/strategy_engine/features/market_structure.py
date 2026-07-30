"""Independent, point-in-time market-structure research primitives.

This clean-room implementation uses only confirmed pivots and closed OHLC bars.
It does not copy or port proprietary indicator code.  Every emitted record is
append-only: a pivot is visible only at ``available_at`` and a three-candle fair
value gap is visible only when its third candle has closed.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from math import isfinite
from typing import Literal, cast

import pandas as pd

from strategy_engine.features.pivots import PivotEvent, confirmed_pivots

PivotKind = Literal["high", "low"]
ZoneDirection = Literal["bullish", "bearish"]


class PivotLabel(StrEnum):
    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"
    EQH = "EQH"
    EQL = "EQL"


class StructureEventType(StrEnum):
    BOS_BULLISH = "bos_bullish"
    BOS_BEARISH = "bos_bearish"
    CHOCH_BULLISH = "choch_bullish"
    CHOCH_BEARISH = "choch_bearish"


class FairValueGapDirection(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass(frozen=True, slots=True)
class LabeledPivot:
    kind: PivotKind
    label: PivotLabel | None
    level: float
    previous_level: float | None
    pivot_index: int
    detected_index: int
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp


@dataclass(frozen=True, slots=True)
class StructureEvent:
    event_type: StructureEventType
    level: float
    source_pivot_index: int
    break_index: int
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp
    pivot_version: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class FairValueGap:
    direction: FairValueGapDirection
    lower_bound: float
    upper_bound: float
    first_index: int
    confirmation_index: int
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp


@dataclass(frozen=True, slots=True)
class StructureZone:
    direction: ZoneDirection
    lower_bound: float
    upper_bound: float
    anchor_index: int
    source_break_index: int
    source_event_type: StructureEventType
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp
    heuristic_version: str


@dataclass(frozen=True, slots=True)
class MarketStructureAnalysis:
    pivots: tuple[LabeledPivot, ...]
    structure_events: tuple[StructureEvent, ...]
    fair_value_gaps: tuple[FairValueGap, ...]
    zones: tuple[StructureZone, ...]


def classify_confirmed_pivots(
    pivots: Iterable[PivotEvent],
    *,
    equality_tolerance_bps: float = 10.0,
) -> list[LabeledPivot]:
    """Classify confirmed highs/lows against the prior same-kind pivot."""

    _validate_non_negative_finite(equality_tolerance_bps, "equality_tolerance_bps")
    ordered = sorted((_validated_pivot(item) for item in pivots), key=_pivot_order)
    previous: dict[PivotKind, float] = {}
    result: list[LabeledPivot] = []
    for pivot in ordered:
        kind: PivotKind = "high" if pivot.kind == "high" else "low"
        prior = previous.get(kind)
        label: PivotLabel | None = None
        if prior is not None:
            if _distance_bps(pivot.level, prior) <= equality_tolerance_bps:
                label = PivotLabel.EQH if kind == "high" else PivotLabel.EQL
            elif kind == "high":
                label = PivotLabel.HH if pivot.level > prior else PivotLabel.LH
            else:
                label = PivotLabel.HL if pivot.level > prior else PivotLabel.LL
        result.append(
            LabeledPivot(
                kind=kind,
                label=label,
                level=pivot.level,
                previous_level=prior,
                pivot_index=pivot.pivot_index,
                detected_index=pivot.detected_index,
                event_time=pivot.event_time,
                detected_at=pivot.detected_at,
                available_at=pivot.available_at,
            )
        )
        previous[kind] = pivot.level
    return result


def detect_structure_events(
    frame: pd.DataFrame,
    pivots: Iterable[PivotEvent],
    *,
    processing_latency: timedelta = timedelta(0),
    pivot_version: str = "confirmed-pivots-v1",
) -> list[StructureEvent]:
    """Emit close-confirmed BOS/CHoCH events from pivots already available in time."""

    _validate_frame(frame)
    _validate_latency(processing_latency)
    if not pivot_version.strip():
        raise ValueError("pivot_version must be non-empty")
    ordered = sorted((_validated_pivot(item) for item in pivots), key=_pivot_order)
    next_pivot = 0
    active_high: PivotEvent | None = None
    active_low: PivotEvent | None = None
    high_broken = False
    low_broken = False
    last_direction: ZoneDirection | None = None
    events: list[StructureEvent] = []

    for break_index, (raw_timestamp, close_value) in enumerate(frame["close"].items()):
        timestamp = cast(pd.Timestamp, raw_timestamp)
        while next_pivot < len(ordered) and ordered[next_pivot].available_at <= timestamp:
            pivot = ordered[next_pivot]
            if pivot.kind == "high":
                active_high = pivot
                high_broken = False
            else:
                active_low = pivot
                low_broken = False
            next_pivot += 1

        close = float(close_value)
        if active_high is not None and not high_broken and close > active_high.level:
            event_type = (
                StructureEventType.CHOCH_BULLISH
                if last_direction == "bearish"
                else StructureEventType.BOS_BULLISH
            )
            events.append(
                StructureEvent(
                    event_type=event_type,
                    level=active_high.level,
                    source_pivot_index=active_high.pivot_index,
                    break_index=break_index,
                    event_time=timestamp,
                    detected_at=timestamp,
                    available_at=timestamp + processing_latency,
                    pivot_version=pivot_version,
                    reason_code="CLOSE_ABOVE_CONFIRMED_HIGH",
                )
            )
            high_broken = True
            last_direction = "bullish"

        if active_low is not None and not low_broken and close < active_low.level:
            event_type = (
                StructureEventType.CHOCH_BEARISH
                if last_direction == "bullish"
                else StructureEventType.BOS_BEARISH
            )
            events.append(
                StructureEvent(
                    event_type=event_type,
                    level=active_low.level,
                    source_pivot_index=active_low.pivot_index,
                    break_index=break_index,
                    event_time=timestamp,
                    detected_at=timestamp,
                    available_at=timestamp + processing_latency,
                    pivot_version=pivot_version,
                    reason_code="CLOSE_BELOW_CONFIRMED_LOW",
                )
            )
            low_broken = True
            last_direction = "bearish"

    return events


def confirmed_fair_value_gaps(
    frame: pd.DataFrame,
    *,
    processing_latency: timedelta = timedelta(0),
) -> list[FairValueGap]:
    """Return non-repainting three-candle gaps confirmed at the third bar close."""

    _validate_frame(frame)
    _validate_latency(processing_latency)
    gaps: list[FairValueGap] = []
    for confirmation_index in range(2, len(frame)):
        first_index = confirmation_index - 2
        first_high = float(frame["high"].iloc[first_index])
        first_low = float(frame["low"].iloc[first_index])
        third_high = float(frame["high"].iloc[confirmation_index])
        third_low = float(frame["low"].iloc[confirmation_index])
        detected_at = frame.index[confirmation_index]
        event_time = frame.index[confirmation_index - 1]
        if third_low > first_high:
            gaps.append(
                FairValueGap(
                    direction=FairValueGapDirection.BULLISH,
                    lower_bound=first_high,
                    upper_bound=third_low,
                    first_index=first_index,
                    confirmation_index=confirmation_index,
                    event_time=event_time,
                    detected_at=detected_at,
                    available_at=detected_at + processing_latency,
                )
            )
        if third_high < first_low:
            gaps.append(
                FairValueGap(
                    direction=FairValueGapDirection.BEARISH,
                    lower_bound=third_high,
                    upper_bound=first_low,
                    first_index=first_index,
                    confirmation_index=confirmation_index,
                    event_time=event_time,
                    detected_at=detected_at,
                    available_at=detected_at + processing_latency,
                )
            )
    return gaps


def structure_zones(
    frame: pd.DataFrame,
    events: Iterable[StructureEvent],
    *,
    lookback_bars: int = 3,
) -> list[StructureZone]:
    """Build an independently specified pre-break candle zone.

    Bullish breaks select the lowest-low candle in the preceding window and use
    ``low .. max(open, close)``.  Bearish breaks select the highest-high candle
    and use ``min(open, close) .. high``.  The break candle and all future bars
    are excluded.
    """

    _validate_frame(frame)
    if not isinstance(lookback_bars, int) or isinstance(lookback_bars, bool) or lookback_bars < 1:
        raise ValueError("lookback_bars must be an integer >= 1")
    result: list[StructureZone] = []
    for event in sorted(events, key=lambda item: (item.available_at, item.break_index)):
        _validate_structure_event(event, len(frame))
        start = max(0, event.break_index - lookback_bars)
        window = frame.iloc[start:event.break_index]
        if window.empty:
            continue
        bullish = event.event_type in {
            StructureEventType.BOS_BULLISH,
            StructureEventType.CHOCH_BULLISH,
        }
        if bullish:
            relative_anchor = int(window["low"].to_numpy().argmin())
            anchor_index = start + relative_anchor
            row = frame.iloc[anchor_index]
            lower = float(row["low"])
            upper = max(float(row["open"]), float(row["close"]))
            direction: ZoneDirection = "bullish"
        else:
            relative_anchor = int(window["high"].to_numpy().argmax())
            anchor_index = start + relative_anchor
            row = frame.iloc[anchor_index]
            lower = min(float(row["open"]), float(row["close"]))
            upper = float(row["high"])
            direction = "bearish"
        result.append(
            StructureZone(
                direction=direction,
                lower_bound=lower,
                upper_bound=upper,
                anchor_index=anchor_index,
                source_break_index=event.break_index,
                source_event_type=event.event_type,
                event_time=frame.index[anchor_index],
                detected_at=event.detected_at,
                available_at=event.available_at,
                heuristic_version="pre-break-extreme-body-v1",
            )
        )
    return result


def analyze_market_structure(
    frame: pd.DataFrame,
    *,
    left_bars: int,
    right_bars: int,
    equality_tolerance_bps: float = 10.0,
    processing_latency: timedelta = timedelta(0),
    zone_lookback_bars: int = 3,
) -> MarketStructureAnalysis:
    """Run the complete clean-room analysis with point-in-time availability."""

    _validate_frame(frame)
    pivots = confirmed_pivots(
        frame,
        left_bars=left_bars,
        right_bars=right_bars,
        processing_latency=processing_latency,
    )
    labeled = classify_confirmed_pivots(
        pivots,
        equality_tolerance_bps=equality_tolerance_bps,
    )
    events = detect_structure_events(
        frame,
        pivots,
        processing_latency=processing_latency,
    )
    gaps = confirmed_fair_value_gaps(frame, processing_latency=processing_latency)
    zones = structure_zones(frame, events, lookback_bars=zone_lookback_bars)
    return MarketStructureAnalysis(tuple(labeled), tuple(events), tuple(gaps), tuple(zones))


def _pivot_order(pivot: PivotEvent) -> tuple[pd.Timestamp, pd.Timestamp, int, str]:
    return (pivot.available_at, pivot.event_time, pivot.pivot_index, pivot.kind)


def _validated_pivot(pivot: PivotEvent) -> PivotEvent:
    if pivot.kind not in {"high", "low"}:
        raise ValueError("pivot kind must be 'high' or 'low'")
    if not isfinite(pivot.level):
        raise ValueError("pivot level must be finite")
    if pivot.pivot_index < 0 or pivot.detected_index < pivot.pivot_index:
        raise ValueError("pivot indices must preserve confirmation order")
    for name, value in (
        ("event_time", pivot.event_time),
        ("detected_at", pivot.detected_at),
        ("available_at", pivot.available_at),
    ):
        if not isinstance(value, pd.Timestamp) or value.tz is None:
            raise ValueError(f"pivot {name} must be a timezone-aware pandas Timestamp")
    if not pivot.event_time <= pivot.detected_at <= pivot.available_at:
        raise ValueError("pivot timestamps must satisfy event_time <= detected_at <= available_at")
    return pivot


def _validate_structure_event(event: StructureEvent, frame_length: int) -> None:
    if event.break_index < 0 or event.break_index >= frame_length:
        raise ValueError("structure event break_index is outside the frame")
    if not event.event_time <= event.detected_at <= event.available_at:
        raise ValueError("structure event timestamps must be monotonic")


def _distance_bps(level: float, previous: float) -> float:
    scale = max(abs(level), abs(previous), 1e-12)
    return abs(level - previous) / scale * 10_000.0


def _validate_non_negative_finite(value: float, name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{name} must be a finite number >= 0")


def _validate_latency(value: timedelta) -> None:
    if value < timedelta(0):
        raise ValueError("processing_latency must be >= 0")


def _validate_frame(frame: pd.DataFrame) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("frame must use a DatetimeIndex")
    if frame.index.tz is None:
        raise ValueError("frame index must be timezone-aware")
    if not frame.index.is_monotonic_increasing or not frame.index.is_unique:
        raise ValueError("frame index must be unique and increasing")
    missing = {"open", "high", "low", "close"} - set(frame.columns)
    if missing:
        raise ValueError(f"frame is missing OHLC columns: {sorted(missing)}")
    values = frame[["open", "high", "low", "close"]].to_numpy(dtype=float)
    if not all(isfinite(float(value)) for value in values.ravel()):
        raise ValueError("OHLC values must be finite")
    high_floor = frame[["open", "close", "low"]].astype(float).max(axis=1)
    low_ceiling = frame[["open", "close", "high"]].astype(float).min(axis=1)
    if (frame["high"].astype(float) < high_floor).any():
        raise ValueError("high must be >= open, close and low")
    if (frame["low"].astype(float) > low_ceiling).any():
        raise ValueError("low must be <= open, close and high")
