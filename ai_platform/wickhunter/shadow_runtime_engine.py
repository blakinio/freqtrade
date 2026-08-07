from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from ai_platform.wickhunter.contracts import (
    BotMode,
    RiskOutcome,
    ShadowDecisionEvidence,
    ShadowStatus,
    SourceHealth,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest, evaluate_shadow_decision
from ai_platform.wickhunter.shadow_runtime_common import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeHealth,
    ShadowRuntimeError,
    ShadowRuntimePolicy,
    _quantize,
)
from ai_platform.wickhunter.shadow_runtime_logic import (
    _circuit_breaker_reasons,
    _decision_summary,
    _mark_and_close_positions,
    _open_position,
    _runtime_identity,
    _source_statuses,
    _validate_request,
)
from ai_platform.wickhunter.shadow_runtime_positions import RuntimeDecisionSummary
from ai_platform.wickhunter.shadow_runtime_snapshot import ShadowRuntimeStepResult
from ai_platform.wickhunter.shadow_runtime_snapshot_builder import _build_snapshot
from ai_platform.wickhunter.shadow_runtime_state import (
    ShadowRuntimeState,
    ShadowRuntimeTick,
    initial_runtime_state,
)
from ai_platform.wickhunter.shadow_runtime_storage import ShadowRuntimeStore


class ShadowRuntime:
    def __init__(
        self,
        *,
        bot_instance: str,
        mode: BotMode,
        policy: ShadowRuntimePolicy,
        store: ShadowRuntimeStore | None = None,
        decision_evaluator: Callable[[ShadowDecisionRequest], ShadowDecisionEvidence] = (
            evaluate_shadow_decision
        ),
    ) -> None:
        if mode is BotMode.LIVE_BLOCKED:
            raise ShadowRuntimeError("live mode is forbidden")
        self.policy = policy
        self.store = store
        self.decision_evaluator = decision_evaluator
        loaded = store.load() if store is not None else None
        if loaded is None:
            self.state = initial_runtime_state(
                bot_instance=bot_instance,
                mode=mode,
                policy=policy,
            )
        else:
            if loaded.bot_instance != bot_instance or loaded.mode is not mode:
                raise ShadowRuntimeError("persisted runtime identity does not match")
            if loaded.policy_sha256 != policy.policy_sha256:
                raise ShadowRuntimeError("persisted runtime policy does not match")
            self.state = loaded

    def step(self, tick: ShadowRuntimeTick) -> ShadowRuntimeStepResult:
        if (
            self.state.last_observed_at_ms is not None
            and tick.observed_at_ms <= self.state.last_observed_at_ms
        ):
            raise ShadowRuntimeError("runtime ticks must be strictly increasing")

        source_statuses = _source_statuses(
            tick=tick,
            maximum_age_ms=self.policy.maximum_source_age_ms,
        )
        updated_positions, newly_closed = _mark_and_close_positions(
            positions=self.state.positions,
            mark_prices=dict(tick.mark_prices),
            observed_at_ms=tick.observed_at_ms,
        )
        realized = self.state.cumulative_realized_pnl_quote + sum(
            (item.realized_pnl_quote for item in newly_closed),
            Decimal("0"),
        )
        breaker_reasons = _circuit_breaker_reasons(
            tick=tick,
            state=self.state,
            source_statuses=source_statuses,
            policy=self.policy,
        )

        decisions: list[ShadowDecisionEvidence] = []
        summaries: list[RuntimeDecisionSummary] = []
        positions = list(updated_positions)
        if not breaker_reasons:
            ordered_requests = sorted(
                tick.decision_requests,
                key=lambda item: (item.market.symbol, item.hypothesis.value),
            )
            for request in ordered_requests:
                _validate_request(
                    request=request,
                    tick=tick,
                    runtime_mode=self.state.mode,
                    bot_instance=self.state.bot_instance,
                )
                evidence = self.decision_evaluator(request)
                decisions.append(evidence)
                runtime_reasons: list[str] = []
                if evidence.status is ShadowStatus.SIMULATED_ALLOWED:
                    if evidence.trade_intent is None or evidence.risk_decision is None:
                        raise ShadowRuntimeError("allowed decision lacks intent or risk evidence")
                    if evidence.risk_decision.outcome is not RiskOutcome.ALLOW:
                        raise ShadowRuntimeError(
                            "allowed shadow decision has rejected risk evidence"
                        )
                    same_symbol = any(
                        item.symbol.upper() == evidence.trade_intent.symbol.upper()
                        for item in positions
                    )
                    if same_symbol:
                        runtime_reasons.append("runtime_position_already_open")
                    elif len(positions) >= self.policy.maximum_open_positions:
                        runtime_reasons.append("runtime_position_limit")
                    else:
                        position = _open_position(
                            evidence=evidence,
                            initial_equity=self.policy.simulated_initial_equity_quote,
                        )
                        if position is None:
                            runtime_reasons.append("runtime_position_quantity_not_positive")
                        else:
                            positions.append(position)
                summaries.append(
                    _decision_summary(
                        evidence=evidence,
                        observed_at_ms=tick.observed_at_ms,
                        runtime_reasons=runtime_reasons,
                    )
                )

        positions_tuple = tuple(sorted(positions, key=lambda item: item.position_id))
        unrealized = sum(
            (item.unrealized_pnl_quote for item in positions_tuple),
            Decimal("0"),
        )
        equity = self.policy.simulated_initial_equity_quote + realized + unrealized
        if equity <= 0:
            equity = Decimal("0.00000001")
        peak = max(self.state.peak_equity_quote, equity)
        drawdown = _quantize((peak - equity) / peak)
        if drawdown >= self.policy.maximum_drawdown_ratio:
            breaker_reasons = tuple(sorted({*breaker_reasons, "maximum_drawdown_exceeded"}))

        decision_ids = tuple(item.shadow_decision_id for item in decisions)
        combined_decision_ids = (*self.state.recent_decision_ids, *decision_ids)
        recent_ids = tuple(
            reversed(
                tuple(dict.fromkeys(reversed(combined_decision_ids)))[
                    : self.policy.decision_history_limit
                ]
            )
        )
        identity = _runtime_identity(decisions, self.state)
        closed_history = tuple(
            sorted(
                (*self.state.closed_positions, *newly_closed),
                key=lambda item: item.closed_position_id,
            )
        )
        new_state = ShadowRuntimeState(
            schema_version=RUNTIME_STATE_SCHEMA_VERSION,
            bot_instance=self.state.bot_instance,
            mode=self.state.mode,
            policy_version=self.policy.policy_version,
            policy_sha256=self.policy.policy_sha256,
            generation=self.state.generation + 1,
            last_observed_at_ms=tick.observed_at_ms,
            universe_snapshot_hash=tick.universe.snapshot_hash,
            positions=positions_tuple,
            closed_positions=closed_history,
            cumulative_realized_pnl_quote=_quantize(realized),
            peak_equity_quote=_quantize(peak),
            drawdown_ratio=drawdown,
            recent_decision_ids=recent_ids,
            model_version=identity[0],
            model_hash=identity[1],
            parameter_version=identity[2],
            parameter_hash=identity[3],
            dataset_hash=identity[4],
            code_sha=identity[5],
        )
        health = (
            RuntimeHealth.FAIL_CLOSED
            if breaker_reasons
            else RuntimeHealth.DEGRADED
            if any(item.health is not SourceHealth.HEALTHY for item in source_statuses)
            else RuntimeHealth.HEALTHY
        )
        snapshot = _build_snapshot(
            state=new_state,
            tick=tick,
            health=health,
            source_statuses=source_statuses,
            decisions=tuple(summaries),
            breaker_reasons=breaker_reasons,
            initial_equity=self.policy.simulated_initial_equity_quote,
        )
        self.state = new_state
        if self.store is not None:
            self.store.save(new_state, snapshot)
        return ShadowRuntimeStepResult(
            state=new_state,
            snapshot=snapshot,
            decisions=tuple(decisions),
            closed_positions=newly_closed,
        )
