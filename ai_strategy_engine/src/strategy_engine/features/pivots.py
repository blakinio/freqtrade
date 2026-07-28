from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd


@dataclass(frozen=True)
class PivotEvent:
    kind: str
    level: float
    pivot_index: int
    detected_index: int
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp


def confirmed_pivots(
    frame: pd.DataFrame,
    *,
    left_bars: int,
    right_bars: int,
    processing_latency: timedelta = timedelta(0),
) -> list[PivotEvent]:
    if left_bars < 1 or right_bars < 1:
        raise ValueError("left_bars and right_bars must be >= 1")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("frame must use a DatetimeIndex")
    if frame.index.tz is None:
        raise ValueError("frame index must be timezone-aware")

    events: list[PivotEvent] = []
    for pivot_idx in range(left_bars, len(frame) - right_bars):
        start = pivot_idx - left_bars
        stop = pivot_idx + right_bars + 1

        high_window = frame["high"].iloc[start:stop]
        low_window = frame["low"].iloc[start:stop]

        detected_idx = pivot_idx + right_bars
        detected_at = frame.index[detected_idx]

        if frame["high"].iloc[pivot_idx] == high_window.max():
            events.append(
                PivotEvent(
                    kind="high",
                    level=float(frame["high"].iloc[pivot_idx]),
                    pivot_index=pivot_idx,
                    detected_index=detected_idx,
                    event_time=frame.index[pivot_idx],
                    detected_at=detected_at,
                    available_at=detected_at + processing_latency,
                )
            )

        if frame["low"].iloc[pivot_idx] == low_window.min():
            events.append(
                PivotEvent(
                    kind="low",
                    level=float(frame["low"].iloc[pivot_idx]),
                    pivot_index=pivot_idx,
                    detected_index=detected_idx,
                    event_time=frame.index[pivot_idx],
                    detected_at=detected_at,
                    available_at=detected_at + processing_latency,
                )
            )

    return events
