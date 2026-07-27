from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BeforeValidator, Field, NonNegativeInt, PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.templates import (
    MarginMode,
    MarketType,
    TradeDirection,
)
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr
from ai_platform.portal.contracts.environment import ExecutionMode


def _finite_decimal(value: object) -> Decimal:
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("value must be a valid Decimal") from exc
    if not parsed.is_finite():
        raise ValueError("Decimal value must be finite")
    return parsed


FiniteDecimal = Annotated[Decimal, BeforeValidator(_finite_decimal)]
PositiveDecimal = Annotated[Decimal, BeforeValidator(_finite_decimal), Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, BeforeValidator(_finite_decimal), Field(ge=0)]
PercentDecimal = Annotated[
    Decimal,
    BeforeValidator(_finite_decimal),
    Field(gt=0, le=100),
]
PercentOrZeroDecimal = Annotated[
    Decimal,
    BeforeValidator(_finite_decimal),
    Field(ge=0, le=100),
]
FractionDecimal = Annotated[
    Decimal,
    BeforeValidator(_finite_decimal),
    Field(gt=0, le=1),
]


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class DuplicateSignalBehavior(StrEnum):
    REJECT = "reject"
    IGNORE = "ignore"
    REPLACE_PENDING = "replace_pending"


class PositionSizingMode(StrEnum):
    FIXED_BASE_QUANTITY = "fixed_base_quantity"
    FIXED_QUOTE_AMOUNT = "fixed_quote_amount"
    QUOTE_ALLOCATION_PERCENT = "quote_allocation_percent"


class DcaTriggerBasis(StrEnum):
    PRICE_DEVIATION_PERCENT = "price_deviation_percent"
    SIGNAL = "signal"
    MANUAL = "manual"


class DcaSizeMode(StrEnum):
    FIXED_QUOTE_AMOUNT = "fixed_quote_amount"
    SIZE_MULTIPLIER = "size_multiplier"


class SignalAuthority(StrEnum):
    ADVISORY_ONLY = "advisory_only"
    EXECUTION_AUTHORIZED = "execution_authorized"


class SignalCommand(StrEnum):
    OPEN = "OPEN"
    DCA = "DCA"
    CLOSE_POSITION = "CLOSE_POSITION"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    CLOSE_ALL = "CLOSE_ALL"
    TAKE_PROFIT = "TAKE_PROFIT"
    ENABLE_BOT = "ENABLE_BOT"
    PAUSE_BOT = "PAUSE_BOT"
    STOP_BOT = "STOP_BOT"


class GridSpacing(StrEnum):
    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"


class GridAllocationMode(StrEnum):
    TOTAL_QUOTE = "total_quote"
    PER_LEVEL_QUOTE = "per_level_quote"


class RuntimeRestartPolicy(StrEnum):
    NEVER = "never"
    ON_FAILURE = "on_failure"


class MarketPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    pairs: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    market_type: MarketType
    direction: TradeDirection
    timeframe: NonEmptyStr
    margin_mode: MarginMode | None = None
    leverage: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_market_policy(self) -> Self:
        if len(self.pairs) != len(set(self.pairs)):
            raise ValueError("pairs must not contain duplicates")
        if list(self.pairs) != sorted(self.pairs):
            raise ValueError("pairs must use deterministic sorted order")
        if self.market_type == MarketType.SPOT:
            if self.margin_mode is not None or self.leverage is not None:
                raise ValueError("spot market must not declare margin mode or leverage")
            if self.direction != TradeDirection.LONG:
                raise ValueError("spot market supports long direction only")
        elif self.margin_mode is None:
            raise ValueError("margin and futures markets require margin_mode")
        if self.leverage is not None and self.market_type == MarketType.MARGIN:
            if self.leverage > Decimal("10"):
                raise ValueError("margin leverage must not exceed 10")
        if self.leverage is not None and self.market_type == MarketType.FUTURES:
            if self.leverage > Decimal("125"):
                raise ValueError("futures leverage must not exceed 125")
        return self


class EntryPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    order_type: OrderType
    limit_offset_percent: PercentOrZeroDecimal | None = None
    cooldown_seconds: NonNegativeInt = 0
    duplicate_signal_behavior: DuplicateSignalBehavior = DuplicateSignalBehavior.REJECT
    max_concurrent_positions: PositiveInt

    @model_validator(mode="after")
    def validate_entry_policy(self) -> Self:
        if self.order_type == OrderType.MARKET and self.limit_offset_percent is not None:
            raise ValueError("market entry must not declare a limit offset")
        return self


class PositionSizingPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    mode: PositionSizingMode
    fixed_base_quantity: PositiveDecimal | None = None
    fixed_quote_amount: PositiveDecimal | None = None
    quote_allocation_percent: PercentDecimal | None = None
    max_per_pair_allocation_percent: PercentDecimal
    max_total_allocation_percent: PercentDecimal

    @model_validator(mode="after")
    def validate_position_sizing(self) -> Self:
        supplied = {
            PositionSizingMode.FIXED_BASE_QUANTITY: self.fixed_base_quantity,
            PositionSizingMode.FIXED_QUOTE_AMOUNT: self.fixed_quote_amount,
            PositionSizingMode.QUOTE_ALLOCATION_PERCENT: self.quote_allocation_percent,
        }
        if supplied[self.mode] is None:
            raise ValueError(f"{self.mode.value} requires its matching sizing value")
        if sum(value is not None for value in supplied.values()) != 1:
            raise ValueError("position sizing must declare exactly one sizing value")
        if self.max_per_pair_allocation_percent > self.max_total_allocation_percent:
            raise ValueError("per-pair allocation must not exceed total allocation")
        if (
            self.quote_allocation_percent is not None
            and self.quote_allocation_percent > self.max_per_pair_allocation_percent
        ):
            raise ValueError("quote allocation must not exceed per-pair allocation limit")
        return self


class DcaStep(ContractModel):
    step_number: PositiveInt
    trigger_deviation_percent: PercentDecimal | None = None
    size_value: PositiveDecimal


class DcaPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    trigger_basis: DcaTriggerBasis
    size_mode: DcaSizeMode
    max_steps: PositiveInt
    max_cumulative_allocation_percent: PercentDecimal
    cooldown_seconds: NonNegativeInt = 0
    steps: Annotated[tuple[DcaStep, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_dca_policy(self) -> Self:
        if len(self.steps) != self.max_steps:
            raise ValueError("max_steps must equal the number of DCA steps")
        numbers = [step.step_number for step in self.steps]
        if numbers != list(range(1, self.max_steps + 1)):
            raise ValueError("DCA steps must be contiguous and ordered from 1")
        trigger_values = [step.trigger_deviation_percent for step in self.steps]
        if self.trigger_basis == DcaTriggerBasis.PRICE_DEVIATION_PERCENT:
            if any(value is None for value in trigger_values):
                raise ValueError("price-deviation DCA requires every trigger deviation")
            triggers = [value for value in trigger_values if value is not None]
            if triggers != sorted(triggers) or len(triggers) != len(set(triggers)):
                raise ValueError(
                    "DCA trigger deviations must be unique and strictly increasing"
                )
        elif any(value is not None for value in trigger_values):
            raise ValueError("signal or manual DCA must not declare price deviations")
        return self


class TakeProfitLevel(ContractModel):
    level_number: PositiveInt
    profit_percent: PercentDecimal
    close_fraction: FractionDecimal


class TakeProfitPolicy(ContractModel):
    levels: Annotated[tuple[TakeProfitLevel, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_take_profit(self) -> Self:
        numbers = [level.level_number for level in self.levels]
        if numbers != list(range(1, len(self.levels) + 1)):
            raise ValueError("take-profit levels must be contiguous and ordered from 1")
        profits = [level.profit_percent for level in self.levels]
        if profits != sorted(profits) or len(profits) != len(set(profits)):
            raise ValueError("take-profit percentages must be unique and strictly increasing")
        total_fraction = sum((level.close_fraction for level in self.levels), Decimal("0"))
        if total_fraction > Decimal("1"):
            raise ValueError("take-profit close fractions must not exceed 1")
        return self


class StopLossPolicy(ContractModel):
    loss_percent: PercentDecimal
    emergency_close: bool = False


class BreakEvenPolicy(ContractModel):
    trigger_profit_percent: PercentDecimal
    lock_profit_percent: PercentOrZeroDecimal = Decimal("0")

    @model_validator(mode="after")
    def validate_break_even(self) -> Self:
        if self.lock_profit_percent >= self.trigger_profit_percent:
            raise ValueError("break-even lock profit must be below its trigger")
        return self


class TrailingStopPolicy(ContractModel):
    activation_profit_percent: PercentDecimal
    trail_distance_percent: PercentDecimal

    @model_validator(mode="after")
    def validate_trailing_stop(self) -> Self:
        if self.trail_distance_percent >= self.activation_profit_percent:
            raise ValueError("trailing distance must be below activation profit")
        return self


class ExitPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    take_profit: TakeProfitPolicy | None = None
    stop_loss: StopLossPolicy | None = None
    break_even: BreakEvenPolicy | None = None
    trailing_stop: TrailingStopPolicy | None = None
    time_exit_seconds: PositiveInt | None = None
    strategy_exit_enabled: bool = False

    @model_validator(mode="after")
    def validate_exit_policy(self) -> Self:
        if not any(
            (
                self.take_profit,
                self.stop_loss,
                self.break_even,
                self.trailing_stop,
                self.time_exit_seconds,
                self.strategy_exit_enabled,
            )
        ):
            raise ValueError("exit policy must enable at least one exit behavior")
        if self.break_even is not None and self.stop_loss is None:
            raise ValueError("break-even requires an explicit stop-loss policy")
        if self.trailing_stop is not None and self.stop_loss is None:
            raise ValueError("trailing stop requires an explicit stop-loss policy")
        if self.take_profit is not None and self.trailing_stop is not None:
            highest_tp = self.take_profit.levels[-1].profit_percent
            if self.trailing_stop.activation_profit_percent >= highest_tp:
                raise ValueError("trailing activation must be below the highest take-profit level")
        return self


class SignalPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    signal_schema_ref: NonEmptyStr
    allowed_commands: Annotated[tuple[SignalCommand, ...], Field(min_length=1)]
    authority: SignalAuthority
    max_signal_age_seconds: PositiveInt
    replay_window_seconds: PositiveInt
    require_nonce: bool = True
    requires_risk_approval: bool = True

    @model_validator(mode="after")
    def validate_signal_policy(self) -> Self:
        values = [command.value for command in self.allowed_commands]
        if len(values) != len(set(values)):
            raise ValueError("allowed signal commands must not contain duplicates")
        if values != sorted(values):
            raise ValueError("allowed signal commands must use deterministic sorted order")
        if self.replay_window_seconds > self.max_signal_age_seconds:
            raise ValueError("replay window must not exceed maximum signal age")
        if self.authority == SignalAuthority.EXECUTION_AUTHORIZED:
            if not self.requires_risk_approval:
                raise ValueError("execution-authorized signals must require risk approval")
        return self


class GridPolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    lower_price: PositiveDecimal
    upper_price: PositiveDecimal
    level_count: Annotated[int, Field(ge=2, le=200)]
    spacing: GridSpacing
    allocation_mode: GridAllocationMode
    total_quote_allocation: PositiveDecimal | None = None
    per_level_quote_amount: PositiveDecimal | None = None
    direction: TradeDirection
    trailing_range_percent: PercentDecimal | None = None
    take_profit_price: PositiveDecimal | None = None
    stop_loss_price: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_grid_policy(self) -> Self:
        if self.lower_price >= self.upper_price:
            raise ValueError("grid lower price must be below upper price")
        if self.direction == TradeDirection.BOTH:
            raise ValueError("grid policy must declare long or short direction")
        if self.allocation_mode == GridAllocationMode.TOTAL_QUOTE:
            if self.total_quote_allocation is None or self.per_level_quote_amount is not None:
                raise ValueError("total-quote grid requires only total_quote_allocation")
        else:
            if self.per_level_quote_amount is None or self.total_quote_allocation is not None:
                raise ValueError("per-level grid requires only per_level_quote_amount")
        if self.direction == TradeDirection.LONG:
            if self.stop_loss_price is not None and self.stop_loss_price >= self.lower_price:
                raise ValueError("long-grid stop loss must be below the grid range")
            if self.take_profit_price is not None and self.take_profit_price <= self.upper_price:
                raise ValueError("long-grid take profit must be above the grid range")
        if self.direction == TradeDirection.SHORT:
            if self.stop_loss_price is not None and self.stop_loss_price <= self.upper_price:
                raise ValueError("short-grid stop loss must be above the grid range")
            if self.take_profit_price is not None and self.take_profit_price >= self.lower_price:
                raise ValueError("short-grid take profit must be below the grid range")
        return self


class RuntimePolicyVersion(ContractModel):
    policy_id: NonEmptyStr
    revision: PositiveInt
    runtime_version: NonEmptyStr
    execution_mode: ExecutionMode
    heartbeat_timeout_seconds: PositiveInt
    command_timeout_seconds: PositiveInt
    reconciliation_timeout_seconds: PositiveInt
    restart_policy: RuntimeRestartPolicy = RuntimeRestartPolicy.NEVER
    max_restart_attempts: NonNegativeInt = 0

    @model_validator(mode="after")
    def validate_runtime_policy(self) -> Self:
        if self.command_timeout_seconds > self.reconciliation_timeout_seconds:
            raise ValueError("command timeout must not exceed reconciliation timeout")
        if self.restart_policy == RuntimeRestartPolicy.NEVER and self.max_restart_attempts != 0:
            raise ValueError("never-restart policy must use zero restart attempts")
        if (
            self.restart_policy == RuntimeRestartPolicy.ON_FAILURE
            and self.max_restart_attempts == 0
        ):
            raise ValueError("on-failure restart policy requires at least one attempt")
        return self
