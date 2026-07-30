from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal, Protocol, TypeVar

from pydantic import Field

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime


NonNegativeMilliseconds = Annotated[int, Field(ge=0)]


class LatencyModel(ContractModel):
    model_version: Literal["sim-latency-v1"] = "sim-latency-v1"
    entry_delay_ms: NonNegativeMilliseconds = 0
    exit_delay_ms: NonNegativeMilliseconds = 0


class LatencyResolution(ContractModel):
    model_version: Literal["sim-latency-v1"] = "sim-latency-v1"
    decision_at: UtcDateTime
    ready_at: UtcDateTime
    filled_at: UtcDateTime
    delay_ms: NonNegativeMilliseconds


class TickLike(Protocol):
    occurred_at: datetime
    pair: str
    price: Decimal


TickT = TypeVar("TickT", bound=TickLike)


class SimulationLatencyError(RuntimeError):
    pass


def resolve_execution_tick(
    *,
    ticks: Sequence[TickT],
    pair: NonEmptyStr,
    decision_at: UtcDateTime,
    delay_ms: NonNegativeMilliseconds,
) -> tuple[TickT, LatencyResolution]:
    ready_at = decision_at + timedelta(milliseconds=delay_ms)
    for tick in ticks:
        if tick.pair == pair and tick.occurred_at >= ready_at:
            return tick, LatencyResolution(
                decision_at=decision_at,
                ready_at=ready_at,
                filled_at=tick.occurred_at,
                delay_ms=delay_ms,
            )
    raise SimulationLatencyError(
        f"no {pair} market tick is available at or after latency-ready time"
    )
