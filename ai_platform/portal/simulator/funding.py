from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal, Sequence

from pydantic import Field

from ai_platform.portal.contracts.common import ContractModel, UtcDateTime
from ai_platform.portal.contracts.risk import TradeSide


FundingRate = Annotated[Decimal, Field(ge=-1, le=1)]
PositiveNotional = Annotated[Decimal, Field(gt=0)]


class FundingEvent(ContractModel):
    model_version: Literal["sim-funding-event-v1"] = "sim-funding-event-v1"
    occurred_at: UtcDateTime
    rate: FundingRate


class FundingAccrual(ContractModel):
    model_version: Literal["sim-funding-v1"] = "sim-funding-v1"
    occurred_at: UtcDateTime
    rate: FundingRate
    cash_flow: Decimal


def funding_accruals(
    *,
    events: Sequence[FundingEvent],
    opened_at: UtcDateTime,
    closed_at: UtcDateTime,
    entry_side: TradeSide,
    entry_notional: PositiveNotional,
) -> tuple[FundingAccrual, ...]:
    if closed_at <= opened_at:
        raise ValueError("funding window must close after it opens")
    direction = Decimal("1") if entry_side is TradeSide.BUY else Decimal("-1")
    accruals: list[FundingAccrual] = []
    previous_at = None
    for event in events:
        if previous_at is not None and event.occurred_at <= previous_at:
            raise ValueError("funding events must be strictly ordered")
        previous_at = event.occurred_at
        if opened_at < event.occurred_at <= closed_at:
            accruals.append(
                FundingAccrual(
                    occurred_at=event.occurred_at,
                    rate=event.rate,
                    cash_flow=-direction * Decimal(entry_notional) * Decimal(event.rate),
                )
            )
    return tuple(accruals)


def total_funding_cash_flow(accruals: Sequence[FundingAccrual]) -> Decimal:
    return sum((item.cash_flow for item in accruals), Decimal("0"))
