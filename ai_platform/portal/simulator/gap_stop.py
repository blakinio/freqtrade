from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Protocol, TypeVar

from pydantic import Field

from ai_platform.portal.contracts.common import ContractModel, UtcDateTime
from ai_platform.portal.contracts.risk import TradeSide


PositivePrice = Annotated[Decimal, Field(gt=0)]


class GapStopModel(ContractModel):
    model_version: Literal["sim-gap-stop-v1"] = "sim-gap-stop-v1"
    stop_price: PositivePrice | None = None


class GapStopResolution(ContractModel):
    model_version: Literal["sim-gap-stop-v1"] = "sim-gap-stop-v1"
    triggered: bool
    decision_at: UtcDateTime | None = None
    observed_price: Decimal | None = None
    reason_code: Literal["stop_loss", "gap_through_stop"] | None = None


class TickLike(Protocol):
    occurred_at: datetime
    price: Decimal


TickT = TypeVar("TickT", bound=TickLike)


def find_stop_trigger(
    *,
    ticks: Sequence[TickT],
    entry_side: TradeSide,
    stop_price: PositivePrice | None,
    opened_at: UtcDateTime,
    planned_exit_at: UtcDateTime,
) -> GapStopResolution:
    if stop_price is None:
        return GapStopResolution(triggered=False)
    for tick in ticks:
        if tick.occurred_at <= opened_at or tick.occurred_at > planned_exit_at:
            continue
        crossed = (
            tick.price <= stop_price if entry_side is TradeSide.BUY else tick.price >= stop_price
        )
        if crossed:
            reason = "stop_loss" if tick.price == stop_price else "gap_through_stop"
            return GapStopResolution(
                triggered=True,
                decision_at=tick.occurred_at,
                observed_price=tick.price,
                reason_code=reason,
            )
    return GapStopResolution(triggered=False)


def adverse_stop_reference_price(
    *,
    entry_side: TradeSide,
    stop_price: PositivePrice,
    observed_price: PositivePrice,
) -> Decimal:
    if entry_side is TradeSide.BUY:
        return min(Decimal(stop_price), Decimal(observed_price))
    return max(Decimal(stop_price), Decimal(observed_price))
