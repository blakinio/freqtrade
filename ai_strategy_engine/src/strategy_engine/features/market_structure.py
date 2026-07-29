"""Clean-room research interface.

Do not copy or port proprietary indicator implementations into this module.
Implement only from an independently authored specification and tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class StructureEventType(StrEnum):
    BOS_BULLISH = "bos_bullish"
    BOS_BEARISH = "bos_bearish"
    CHOCH_BULLISH = "choch_bullish"
    CHOCH_BEARISH = "choch_bearish"


@dataclass(frozen=True)
class StructureEvent:
    event_type: StructureEventType
    level: float
    event_time: datetime
    detected_at: datetime
    available_at: datetime
    pivot_version: str
    reason_code: str


def not_implemented_clean_room() -> None:
    raise NotImplementedError(
        "Prepare an independent specification, legal review, point-in-time tests "
        "and an ADR before implementing market structure features."
    )
