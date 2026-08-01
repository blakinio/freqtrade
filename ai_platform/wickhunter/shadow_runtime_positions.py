from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai_platform.wickhunter.contracts import ShadowStatus, TradeDirection
from ai_platform.wickhunter.shadow_runtime_common import (
    PositionCloseReason,
    ShadowRuntimeError,
    _quantize,
    _require_finite,
    _require_positive,
    _require_sha256,
    _require_text,
)


@dataclass(frozen=True, slots=True)
class SimulatedPosition:
    position_id: str
    trade_intent_id: str
    symbol: str
    side: TradeDirection
    opened_at_ms: int
    entry_price: Decimal
    mark_price: Decimal
    quantity: Decimal
    take_profit_price: Decimal
    stop_loss_price: Decimal
    model_version: str | None
    model_hash: str | None
    parameter_version: str
    parameter_hash: str

    def __post_init__(self) -> None:
        _require_sha256(self.position_id, field="position_id")
        _require_sha256(self.trade_intent_id, field="trade_intent_id")
        _require_text(self.symbol, field="symbol")
        if self.opened_at_ms <= 0:
            raise ShadowRuntimeError("opened_at_ms must be > 0")
        for field_name in (
            "entry_price",
            "mark_price",
            "quantity",
            "take_profit_price",
            "stop_loss_price",
        ):
            _require_positive(getattr(self, field_name), field=field_name)
        _require_text(self.parameter_version, field="parameter_version")
        _require_sha256(self.parameter_hash, field="parameter_hash")
        if self.model_version is None:
            if self.model_hash is not None:
                raise ShadowRuntimeError("model hash requires a model version")
        else:
            _require_text(self.model_version, field="model_version")
            if self.model_hash is None:
                raise ShadowRuntimeError("model version requires a model hash")
            _require_sha256(self.model_hash, field="model_hash")

    @property
    def unrealized_pnl_quote(self) -> Decimal:
        signed_move = (
            self.mark_price - self.entry_price
            if self.side is TradeDirection.LONG
            else self.entry_price - self.mark_price
        )
        return _quantize(signed_move * self.quantity)


@dataclass(frozen=True, slots=True)
class ClosedSimulatedPosition:
    closed_position_id: str
    position_id: str
    symbol: str
    side: TradeDirection
    opened_at_ms: int
    closed_at_ms: int
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    realized_pnl_quote: Decimal
    close_reason: PositionCloseReason

    def __post_init__(self) -> None:
        _require_sha256(self.closed_position_id, field="closed_position_id")
        _require_sha256(self.position_id, field="position_id")
        _require_text(self.symbol, field="symbol")
        if self.opened_at_ms <= 0 or self.closed_at_ms < self.opened_at_ms:
            raise ShadowRuntimeError("closed position timestamps are invalid")
        for field_name in ("entry_price", "exit_price", "quantity"):
            _require_positive(getattr(self, field_name), field=field_name)
        _require_finite(self.realized_pnl_quote, field="realized_pnl_quote")


@dataclass(frozen=True, slots=True)
class RuntimeDecisionSummary:
    shadow_decision_id: str
    status: ShadowStatus
    symbol: str
    side: TradeDirection | None
    candidate_id: str | None
    score_id: str | None
    risk_decision_id: str | None
    reason_codes: tuple[str, ...]
    observed_at_ms: int

    def __post_init__(self) -> None:
        _require_sha256(self.shadow_decision_id, field="shadow_decision_id")
        _require_text(self.symbol, field="symbol")
        if self.observed_at_ms <= 0:
            raise ShadowRuntimeError("decision observed_at_ms must be > 0")
        for value, field_name in (
            (self.candidate_id, "candidate_id"),
            (self.score_id, "score_id"),
            (self.risk_decision_id, "risk_decision_id"),
        ):
            if value is not None:
                _require_sha256(value, field=field_name)
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ShadowRuntimeError("decision reason_codes must be unique and sorted")
