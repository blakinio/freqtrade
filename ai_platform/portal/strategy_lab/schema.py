from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, JsonValue, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime


BoundedDecimal = Annotated[Decimal, Field(ge=Decimal("0"))]
RateDecimal = Annotated[Decimal, Field(ge=Decimal("0"), le=Decimal("0.05"))]
PositiveDecimal = Annotated[Decimal, Field(gt=Decimal("0"))]


class StrategySourceType(StrEnum):
    TRADINGVIEW_INSPIRED_CLEAN_ROOM = "tradingview_inspired_clean_room"


class StrategyDirection(StrEnum):
    LONG = "long"
    SHORT = "short"


class ParameterKind(StrEnum):
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"


class ExperimentStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SignalDecision(StrEnum):
    ENTER_LONG = "ENTER_LONG"
    EXIT_LONG = "EXIT_LONG"
    HOLD = "HOLD"


class ParameterSpec(ContractModel):
    name: NonEmptyStr
    kind: ParameterKind
    default: JsonValue
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    choices: tuple[JsonValue, ...] = ()

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.minimum is not None and self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("parameter maximum cannot be below minimum")
        if self.kind is ParameterKind.ENUM and not self.choices:
            raise ValueError("enum parameter requires choices")
        return self


class StrategyLabDefinition(ContractModel):
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    display_name: NonEmptyStr
    source_type: StrategySourceType
    provenance: dict[str, JsonValue]
    features: tuple[NonEmptyStr, ...]
    entry_rules: tuple[NonEmptyStr, ...]
    exit_rules: tuple[NonEmptyStr, ...]
    parameters: tuple[ParameterSpec, ...]
    timeframe_semantics: NonEmptyStr
    warm_up: int = Field(ge=2, le=1000)
    confirmation_policy: Literal["closed_bar", "confirmed_htf"]
    risk_defaults: dict[str, JsonValue]
    supported_directions: tuple[StrategyDirection, ...]
    dsl: dict[str, JsonValue]


class Candle(ContractModel):
    timestamp: UtcDateTime
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    open: PositiveDecimal
    high: PositiveDecimal
    low: PositiveDecimal
    close: PositiveDecimal
    volume: BoundedDecimal = Decimal("0")
    is_closed: bool = True
    is_confirmed: bool = True
    data_version: Sha256Hex
    source: NonEmptyStr = "synthetic_fixture_v1"

    @model_validator(mode="after")
    def validate_ohlc(self) -> Self:
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("candle high/low do not contain open and close")
        if self.high < self.low:
            raise ValueError("candle high cannot be below low")
        return self


class ExperimentTimerange(ContractModel):
    start_at: UtcDateTime
    end_at: UtcDateTime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end_at <= self.start_at:
            raise ValueError("timerange end must be after start")
        return self


class ExperimentCreateRequest(ContractModel):
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    timerange: ExperimentTimerange
    starting_balance: PositiveDecimal = Decimal("10000")
    fee_rate: RateDecimal = Decimal("0.001")
    slippage_rate: RateDecimal = Decimal("0")
    parameter_overrides: dict[str, JsonValue] = Field(default_factory=dict)
    execution_mode: Literal["backtest"] = "backtest"


class SignalExplanation(ContractModel):
    signal_id: NonEmptyStr
    timestamp: UtcDateTime
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    decision: SignalDecision
    matched_conditions: tuple[NonEmptyStr, ...]
    feature_values: dict[str, JsonValue]
    parameter_values: dict[str, JsonValue]
    reason_codes: tuple[NonEmptyStr, ...]
    price: PositiveDecimal


class ExperimentTrade(ContractModel):
    trade_id: NonEmptyStr
    pair: NonEmptyStr
    side: Literal["long"] = "long"
    entry_at: UtcDateTime
    exit_at: UtcDateTime
    entry_price: PositiveDecimal
    exit_price: PositiveDecimal
    quantity: PositiveDecimal
    fee_abs: BoundedDecimal
    profit_abs: Decimal
    profit_pct: Decimal
    entry_signal_id: NonEmptyStr
    exit_signal_id: NonEmptyStr
    entry_reason_codes: tuple[NonEmptyStr, ...]
    exit_reason_codes: tuple[NonEmptyStr, ...]


class EquityPoint(ContractModel):
    timestamp: UtcDateTime
    equity: BoundedDecimal
    drawdown_pct: BoundedDecimal


class ExperimentResult(ContractModel):
    experiment_id: UUID
    tenant_id: NonEmptyStr
    status: ExperimentStatus
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    timerange: ExperimentTimerange
    data_identity: Sha256Hex
    code_identity: Sha256Hex
    parameters: dict[str, JsonValue]
    started_at: UtcDateTime
    finished_at: UtcDateTime
    trade_count: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    win_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    profit_abs: Decimal
    profit_pct: Decimal
    max_drawdown: BoundedDecimal
    average_trade: Decimal
    exposure: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    equity_curve: tuple[EquityPoint, ...]
    trades: tuple[ExperimentTrade, ...]
    signal_explanations: tuple[SignalExplanation, ...]
    result_hash: Sha256Hex
    research_only: Literal[True] = True
    order_submission_performed: Literal[False] = False

    @model_validator(mode="after")
    def verify_result_hash(self) -> Self:
        payload = self.model_dump(mode="json", exclude={"result_hash"})
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        expected = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if self.result_hash != expected:
            raise ValueError("result_hash does not match experiment payload")
        return self


class ExperimentDetail(ContractModel):
    experiment_id: UUID
    tenant_id: NonEmptyStr
    status: ExperimentStatus
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    timerange: ExperimentTimerange
    data_identity: Sha256Hex
    code_identity: Sha256Hex
    parameters: dict[str, JsonValue]
    started_at: UtcDateTime
    finished_at: UtcDateTime
    trade_count: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    win_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    profit_abs: Decimal
    profit_pct: Decimal
    max_drawdown: BoundedDecimal
    average_trade: Decimal
    exposure: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    result_hash: Sha256Hex
    research_only: Literal[True] = True
    order_submission_performed: Literal[False] = False


class ExperimentSummary(ContractModel):
    experiment_id: UUID
    status: ExperimentStatus
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    pair: NonEmptyStr
    timeframe: NonEmptyStr
    started_at: UtcDateTime
    trade_count: int
    profit_abs: Decimal
    profit_pct: Decimal
    max_drawdown: Decimal


class ExperimentComparison(ContractModel):
    baseline_experiment_id: UUID
    variant_experiment_id: UUID
    metric_deltas: dict[str, Decimal]
    parameter_differences: dict[str, tuple[JsonValue | None, JsonValue | None]]


class PaginatedTrades(ContractModel):
    items: tuple[ExperimentTrade, ...]
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    total: int = Field(ge=0)


class PaginatedSignals(ContractModel):
    items: tuple[SignalExplanation, ...]
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=500)
    total: int = Field(ge=0)
