from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.execution import (
    OrderRecord,
    OrderState,
    RuntimeHealthState,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent, TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.intelligence.schema import ReconciliationStatus, TradeOutcome
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot
from ai_platform.portal.simulator.schema import MarketTick, ScenarioManifest


class SimulatorStateError(RuntimeError):
    pass


class DeterministicExchangeSimulator:
    def __init__(self, manifest: ScenarioManifest) -> None:
        self.manifest = manifest
        self._current_tick = manifest.entry_tick
        self._equity = manifest.initial_equity
        self._peak_equity = manifest.initial_equity
        self._daily_loss = Decimal("0")
        self._open_amount = Decimal("0")
        self._entry_price: Decimal | None = None
        self._entry_side: TradeSide | None = None
        self._order: OrderRecord | None = None

    @property
    def runtime_id(self) -> str:
        return f"sim-{self.manifest.bot_id}"

    def build_snapshot(
        self,
        context: RequestContext,
        bot: BotInstance,
        *,
        pair: str,
        side: TradeSide,
        amount: Decimal,
    ) -> RiskEvaluationSnapshot:
        del context, side
        if bot.tenant_id != self.manifest.tenant_id or bot.bot_id != self.manifest.bot_id:
            raise SimulatorStateError("simulator bot identity mismatch")
        if pair != self.manifest.pair or pair != self._current_tick.pair:
            raise SimulatorStateError("simulator pair mismatch")
        intent_notional = self._current_tick.price * amount
        current_exposure = (
            Decimal("0") if self._entry_price is None else self._entry_price * self._open_amount
        )
        projected_positions = 1 if self._open_amount == 0 else 2
        return RiskEvaluationSnapshot(
            intent_notional=intent_notional,
            projected_gross_exposure=current_exposure + intent_notional,
            projected_open_positions=projected_positions,
            daily_loss=self._daily_loss,
            current_drawdown=self._drawdown(),
            runtime_health=RuntimeHealthState.HEALTHY,
        )

    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        del context
        trade_intent = intent.trade_intent
        if trade_intent.tenant_id != self.manifest.tenant_id:
            raise SimulatorStateError("execution tenant mismatch")
        if trade_intent.bot_id != self.manifest.bot_id or trade_intent.pair != self.manifest.pair:
            raise SimulatorStateError("execution manifest identity mismatch")
        if self._open_amount != 0:
            raise SimulatorStateError("simulator supports one deterministic position per scenario")
        self._open_amount = trade_intent.amount
        self._entry_price = self._current_tick.price
        self._entry_side = trade_intent.side
        self._order = OrderRecord(
            tenant_id=trade_intent.tenant_id,
            bot_id=trade_intent.bot_id,
            order_id=f"sim-order-{uuid4()}",
            execution_intent_id=str(intent.execution_intent_id),
            pair=trade_intent.pair,
            side=trade_intent.side,
            state=OrderState.FILLED,
            amount=trade_intent.amount,
            created_at=self._current_tick.occurred_at,
        )
        return self._order

    def close_position(self) -> TradeOutcome:
        if self._order is None or self._entry_price is None or self._entry_side is None:
            raise SimulatorStateError("no open simulated position")
        self._current_tick = self.manifest.exit_tick
        direction = Decimal("1") if self._entry_side is TradeSide.BUY else Decimal("-1")
        pnl = (self._current_tick.price - self._entry_price) * self._open_amount * direction
        self._equity += pnl
        self._peak_equity = max(self._peak_equity, self._equity)
        if pnl < 0:
            self._daily_loss += -pnl
        trade_id = f"sim-trade-{uuid4()}"
        outcome = TradeOutcome(
            outcome_id=uuid4(),
            tenant_id=self.manifest.tenant_id,
            trade_id=trade_id,
            bot_id=self.manifest.bot_id,
            source_runtime_id=self.runtime_id,
            pair=self.manifest.pair,
            realized_pnl=pnl,
            fees=Decimal("0"),
            exit_reason="scenario_exit",
            opened_at=self.manifest.entry_tick.occurred_at,
            closed_at=self.manifest.exit_tick.occurred_at,
            reconciliation_status=ReconciliationStatus.SYNCED,
            loss_exceeded_risk_budget=False,
        )
        self._open_amount = Decimal("0")
        self._entry_price = None
        self._entry_side = None
        return outcome

    def order(self) -> OrderRecord:
        if self._order is None:
            raise SimulatorStateError("simulated order has not been submitted")
        return self._order

    def _drawdown(self) -> Decimal:
        if self._peak_equity <= 0:
            return Decimal("0")
        return max(Decimal("0"), (self._peak_equity - self._equity) / self._peak_equity)
