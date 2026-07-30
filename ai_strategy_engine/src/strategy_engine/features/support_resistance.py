from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from math import fsum, isfinite
from typing import Literal

import pandas as pd

from strategy_engine.features.pivots import PivotEvent

SupportResistanceKind = Literal["support", "resistance"]


@dataclass(frozen=True)
class SupportResistanceEvent:
    kind: SupportResistanceKind
    level: float
    confirmations: int
    source_pivot_indices: tuple[int, ...]
    event_time: pd.Timestamp
    detected_at: pd.Timestamp
    available_at: pd.Timestamp


@dataclass
class _CandidateLevel:
    kind: SupportResistanceKind
    anchor_level: float
    pivots: list[PivotEvent] = field(default_factory=list)
    emitted: bool = False


def support_resistance_events(
    pivots: Iterable[PivotEvent],
    *,
    min_confirmations: int = 2,
    tolerance_bps: float = 25.0,
) -> list[SupportResistanceEvent]:
    """Build append-only support/resistance confirmations from confirmed pivots.

    A low pivot contributes to support and a high pivot contributes to resistance.
    Levels are grouped against the first pivot's immutable anchor, so later input
    cannot move the matching boundary. A level is emitted once, when the configured
    number of confirmed pivots has become available.
    """

    if (
        not isinstance(min_confirmations, int)
        or isinstance(min_confirmations, bool)
        or min_confirmations < 1
    ):
        raise ValueError("min_confirmations must be an integer >= 1")
    if (
        not isinstance(tolerance_bps, (int, float))
        or isinstance(tolerance_bps, bool)
        or not isfinite(tolerance_bps)
        or tolerance_bps < 0
    ):
        raise ValueError("tolerance_bps must be a finite number >= 0")

    ordered = list(pivots)
    for pivot in ordered:
        _validate_pivot(pivot)
    ordered.sort(key=_availability_order)

    candidates: dict[SupportResistanceKind, list[_CandidateLevel]] = {
        "support": [],
        "resistance": [],
    }
    events: list[SupportResistanceEvent] = []

    for pivot in ordered:
        kind: SupportResistanceKind = "support" if pivot.kind == "low" else "resistance"
        candidate = _nearest_candidate(candidates[kind], pivot.level, tolerance_bps)
        if candidate is None:
            candidate = _CandidateLevel(kind=kind, anchor_level=pivot.level)
            candidates[kind].append(candidate)
        candidate.pivots.append(pivot)

        if candidate.emitted or len(candidate.pivots) < min_confirmations:
            continue

        sources = tuple(candidate.pivots[:min_confirmations])
        events.append(
            SupportResistanceEvent(
                kind=kind,
                level=fsum(source.level for source in sources) / len(sources),
                confirmations=len(sources),
                source_pivot_indices=tuple(source.pivot_index for source in sources),
                event_time=max(source.event_time for source in sources),
                detected_at=max(source.detected_at for source in sources),
                available_at=max(source.available_at for source in sources),
            )
        )
        candidate.emitted = True

    return events


def _availability_order(pivot: PivotEvent) -> tuple[pd.Timestamp, pd.Timestamp, int, str]:
    return (pivot.available_at, pivot.event_time, pivot.pivot_index, pivot.kind)


def _nearest_candidate(
    candidates: list[_CandidateLevel],
    level: float,
    tolerance_bps: float,
) -> _CandidateLevel | None:
    matches = [
        (distance_bps(level, candidate.anchor_level), position, candidate)
        for position, candidate in enumerate(candidates)
        if distance_bps(level, candidate.anchor_level) <= tolerance_bps
    ]
    if not matches:
        return None
    return min(matches, key=lambda match: (match[0], match[1]))[2]


def distance_bps(level: float, anchor_level: float) -> float:
    """Return a symmetric relative distance in basis points."""

    if not isfinite(level) or not isfinite(anchor_level):
        raise ValueError("levels must be finite")
    scale = max(abs(level), abs(anchor_level), 1e-12)
    return abs(level - anchor_level) / scale * 10_000.0


def _validate_pivot(pivot: PivotEvent) -> None:
    if pivot.kind not in {"low", "high"}:
        raise ValueError("pivot kind must be 'low' or 'high'")
    if not isfinite(pivot.level):
        raise ValueError("pivot level must be finite")
    if (
        not isinstance(pivot.pivot_index, int)
        or isinstance(pivot.pivot_index, bool)
        or not isinstance(pivot.detected_index, int)
        or isinstance(pivot.detected_index, bool)
        or pivot.pivot_index < 0
        or pivot.detected_index < pivot.pivot_index
    ):
        raise ValueError("pivot indices must preserve confirmation order")
    for name, timestamp in (
        ("event_time", pivot.event_time),
        ("detected_at", pivot.detected_at),
        ("available_at", pivot.available_at),
    ):
        if not isinstance(timestamp, pd.Timestamp) or timestamp.tz is None:
            raise ValueError(f"pivot {name} must be a timezone-aware pandas Timestamp")
    if not pivot.event_time <= pivot.detected_at <= pivot.available_at:
        raise ValueError("pivot timestamps must satisfy event_time <= detected_at <= available_at")
