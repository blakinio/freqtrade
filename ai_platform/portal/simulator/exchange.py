from __future__ import annotations

import hashlib
from decimal import Decimal
from uuid import UUID, uuid5

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
from ai_platform.portal.simulator.costs import adverse_fill_price, build_cost_breakdown
from ai_platform.portal.simulator.funding import (
    funding_accruals,
    total_funding_cash_flow,
)
from ai_platform.portal.simulator.gap_stop import (
    adverse_stop_reference_price,
    find_stop_trigger,
)
from ai_platform.portal.simulator.latency import LatencyResolution, resolve_execution_tick
from ai_platform.portal.simulator.schema import (
    ScenarioManifest,
    SimulationEvidence,
)


_SIMULATOR_NAMESPACE = UUID("a7377c8a-0908-5d15-a3e7-dc999099d4c2")


class SimulatorStateError(RuntimeError):
    pass


class DeterministicExchangeSimulator:
    def __init__(self, manifest: ScenarioManifest) -> None:
        self.manifest = manifest
        self._ticks = tuple(
            sorted(
                (manifest.entry_tick, *manifest.market_ticks, manifest.exit_tick),
                key=lambda tick: tick.occurred_at,
            )
        )
        self._scenario_digest = hashlib.sha256(
            manifest.canonical_json().encode("utf-8")
        ).hexdigest()
        self._current_tick = manifest.entry_tick
        self._equity = manifest.initial_equity
        self._peak_equity = manifest.initial_equity
        self._daily_loss = Decimal("0")
        self._open_amount = Decimal("0")
        self._entry_market_price: Decimal | None = None
        self._entry_fill_price: Decimal | None = None
        self._entry_side: TradeSide | None = None
        self._entry_latency: LatencyResolution | None = None
        self._order: OrderRecord | None = None
        self._evidence: SimulationEvidence | None = None

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
        del context
        if bot.tenant_id != self.manifest.tenant_id or bot.bot_id != self.manifest.bot_id:
            raise SimulatorStateError("simulator bot identity mismatch")
        if pair != self.manifest.pair or pair != self._current_tick.pair:
            raise SimulatorStateError("simulator pair mismatch")
        if side is not self.manifest.side or amount != self.manifest.amount:
            raise SimulatorStateError("simulator intent does not match the scenario manifest")
        intent_notional = self._current_tick.price * amount
        current_exposure = (
            Decimal("0")
            if self._entry_fill_price is None
            else self._entry_fill_price * self._open_amount
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
        if trade_intent.environment is not self.manifest.environment:
            raise SimulatorStateError("execution environment mismatch")
        if (
            trade_intent.side is not self.manifest.side
            or trade_intent.amount != self.manifest.amount
        ):
            raise SimulatorStateError("execution intent does not match scenario side and amount")
        if self._open_amount != 0:
            raise SimulatorStateError("simulator supports one deterministic position per scenario")

        entry_tick, entry_latency = resolve_execution_tick(
            ticks=self._ticks,
            pair=self.manifest.pair,
            decision_at=self.manifest.entry_tick.occurred_at,
            delay_ms=self.manifest.latency_model.entry_delay_ms,
        )
        if entry_tick.occurred_at >= self.manifest.exit_tick.occurred_at:
            raise SimulatorStateError(
                "entry latency leaves no market interval before the planned scenario exit"
            )
        self._current_tick = entry_tick
        self._open_amount = trade_intent.amount
        self._entry_market_price = entry_tick.price
        self._entry_fill_price = adverse_fill_price(
            entry_tick.price,
            trade_intent.side,
            self.manifest.cost_model.entry_slippage_bps,
        )
        self._entry_side = trade_intent.side
        self._entry_latency = entry_latency
        self._order = OrderRecord(
            tenant_id=trade_intent.tenant_id,
            bot_id=trade_intent.bot_id,
            order_id=f"sim-order-{self._stable_uuid('order').hex}",
            execution_intent_id=str(intent.execution_intent_id),
            pair=trade_intent.pair,
            side=trade_intent.side,
            state=OrderState.FILLED,
            amount=trade_intent.amount,
            created_at=entry_latency.filled_at,
        )
        return self._order

    def close_position(self) -> TradeOutcome:
        if (
            self._order is None
            or self._entry_market_price is None
            or self._entry_fill_price is None
            or self._entry_side is None
            or self._entry_latency is None
        ):
            raise SimulatorStateError("no open simulated position")

        stop_resolution = find_stop_trigger(
            ticks=self._ticks,
            entry_side=self._entry_side,
            stop_price=self.manifest.gap_stop_model.stop_price,
            opened_at=self._entry_latency.filled_at,
            planned_exit_at=self.manifest.exit_tick.occurred_at,
        )
        if stop_resolution.triggered:
            if (
                stop_resolution.decision_at is None
                or stop_resolution.observed_price is None
                or stop_resolution.reason_code is None
                or self.manifest.gap_stop_model.stop_price is None
            ):
                raise SimulatorStateError("triggered stop resolution lacks deterministic evidence")
            exit_decision_at = stop_resolution.decision_at
            exit_reason = stop_resolution.reason_code
        else:
            exit_decision_at = self.manifest.exit_tick.occurred_at
            exit_reason = "scenario_exit"

        exit_tick, exit_latency = resolve_execution_tick(
            ticks=self._ticks,
            pair=self.manifest.pair,
            decision_at=exit_decision_at,
            delay_ms=self.manifest.latency_model.exit_delay_ms,
        )
        self._current_tick = exit_tick
        exit_market_price = exit_tick.price
        if stop_resolution.triggered:
            stop_price = self.manifest.gap_stop_model.stop_price
            observed_price = stop_resolution.observed_price
            if stop_price is None or observed_price is None:
                raise SimulatorStateError("stop price evidence is missing")
            trigger_reference = adverse_stop_reference_price(
                entry_side=self._entry_side,
                stop_price=stop_price,
                observed_price=observed_price,
            )
            exit_market_price = adverse_stop_reference_price(
                entry_side=self._entry_side,
                stop_price=trigger_reference,
                observed_price=exit_tick.price,
            )

        costs = build_cost_breakdown(
            entry_market_price=self._entry_market_price,
            exit_market_price=exit_market_price,
            entry_side=self._entry_side,
            amount=self._open_amount,
            model=self.manifest.cost_model,
        )
        direction = Decimal("1") if self._entry_side is TradeSide.BUY else Decimal("-1")
        gross_pnl = (
            (costs.exit_fill_price - costs.entry_fill_price)
            * self._open_amount
            * direction
        )
        accruals = funding_accruals(
            events=self.manifest.funding_events,
            opened_at=self._entry_latency.filled_at,
            closed_at=exit_latency.filled_at,
            entry_side=self._entry_side,
            entry_notional=costs.entry_fill_price * self._open_amount,
        )
        funding_cash_flow = total_funding_cash_flow(accruals)
        realized_pnl = gross_pnl + funding_cash_flow - costs.total_fees
        self._equity += realized_pnl
        self._peak_equity = max(self._peak_equity, self._equity)
        if realized_pnl < 0:
            self._daily_loss += -realized_pnl

        trade_id = f"sim-trade-{self._stable_uuid('trade').hex}"
        outcome_id = self._stable_uuid("outcome")
        outcome = TradeOutcome(
            outcome_id=outcome_id,
            tenant_id=self.manifest.tenant_id,
            trade_id=trade_id,
            bot_id=self.manifest.bot_id,
            source_runtime_id=self.runtime_id,
            pair=self.manifest.pair,
            realized_pnl=realized_pnl,
            fees=costs.total_fees,
            exit_reason=exit_reason,
            opened_at=self._entry_latency.filled_at,
            closed_at=exit_latency.filled_at,
            reconciliation_status=ReconciliationStatus.SYNCED,
            loss_exceeded_risk_budget=False,
        )
        self._evidence = SimulationEvidence(
            scenario_id=self.manifest.scenario_id,
            seed=self.manifest.seed,
            order_id=self._order.order_id,
            trade_id=trade_id,
            outcome_id=outcome_id,
            entry_latency=self._entry_latency,
            exit_latency=exit_latency,
            costs=costs,
            funding_accruals=accruals,
            funding_cash_flow=funding_cash_flow,
            gross_pnl=gross_pnl,
            realized_pnl=realized_pnl,
            exit_reason=exit_reason,
            stop_resolution=stop_resolution,
        )
        self._open_amount = Decimal("0")
        self._entry_market_price = None
        self._entry_fill_price = None
        self._entry_side = None
        self._entry_latency = None
        return outcome

    def order(self) -> OrderRecord:
        if self._order is None:
            raise SimulatorStateError("simulated order has not been submitted")
        return self._order

    def evidence(self) -> SimulationEvidence:
        if self._evidence is None:
            raise SimulatorStateError("simulation evidence is not available before position close")
        return self._evidence

    def _stable_uuid(self, kind: str) -> UUID:
        return uuid5(_SIMULATOR_NAMESPACE, f"{self._scenario_digest}:{kind}")

    def _drawdown(self) -> Decimal:
        if self._peak_equity <= 0:
            return Decimal("0")
        return max(Decimal("0"), (self._peak_equity - self._equity) / self._peak_equity)
