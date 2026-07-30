from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field

from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.contracts.risk import TradeSide


NonNegativeRate = Annotated[Decimal, Field(ge=0, le=1)]
SlippageBps = Annotated[Decimal, Field(ge=0, lt=10_000)]
PositiveAmount = Annotated[Decimal, Field(gt=0)]
PositivePrice = Annotated[Decimal, Field(gt=0)]


class ExecutionCostModel(ContractModel):
    model_version: Literal["sim-cost-v1"] = "sim-cost-v1"
    entry_fee_rate: NonNegativeRate = Decimal("0")
    exit_fee_rate: NonNegativeRate = Decimal("0")
    entry_slippage_bps: SlippageBps = Decimal("0")
    exit_slippage_bps: SlippageBps = Decimal("0")


class ExecutionCostBreakdown(ContractModel):
    model_version: Literal["sim-cost-v1"] = "sim-cost-v1"
    entry_market_price: PositivePrice
    entry_fill_price: PositivePrice
    exit_market_price: PositivePrice
    exit_fill_price: PositivePrice
    entry_fee: Decimal
    exit_fee: Decimal

    @property
    def total_fees(self) -> Decimal:
        return self.entry_fee + self.exit_fee


def opposite_side(side: TradeSide) -> TradeSide:
    return TradeSide.SELL if side is TradeSide.BUY else TradeSide.BUY


def adverse_fill_price(
    market_price: PositivePrice,
    side: TradeSide,
    slippage_bps: SlippageBps,
) -> Decimal:
    adjustment = Decimal(slippage_bps) / Decimal("10000")
    multiplier = Decimal("1") + adjustment if side is TradeSide.BUY else Decimal("1") - adjustment
    fill_price = Decimal(market_price) * multiplier
    if fill_price <= 0:
        raise ValueError("slippage produced a non-positive fill price")
    return fill_price


def execution_fee(
    fill_price: PositivePrice,
    amount: PositiveAmount,
    fee_rate: NonNegativeRate,
) -> Decimal:
    return Decimal(fill_price) * Decimal(amount) * Decimal(fee_rate)


def build_cost_breakdown(
    *,
    entry_market_price: PositivePrice,
    exit_market_price: PositivePrice,
    entry_side: TradeSide,
    amount: PositiveAmount,
    model: ExecutionCostModel,
) -> ExecutionCostBreakdown:
    entry_fill_price = adverse_fill_price(
        entry_market_price,
        entry_side,
        model.entry_slippage_bps,
    )
    exit_fill_price = adverse_fill_price(
        exit_market_price,
        opposite_side(entry_side),
        model.exit_slippage_bps,
    )
    return ExecutionCostBreakdown(
        entry_market_price=entry_market_price,
        entry_fill_price=entry_fill_price,
        exit_market_price=exit_market_price,
        exit_fill_price=exit_fill_price,
        entry_fee=execution_fee(entry_fill_price, amount, model.entry_fee_rate),
        exit_fee=execution_fee(exit_fill_price, amount, model.exit_fee_rate),
    )
