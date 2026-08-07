from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    ShadowDecisionEvidence,
    SourceHealth,
    TradeDirection,
)
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime_common import (
    PositionCloseReason,
    RuntimeSourceStatus,
    ShadowRuntimeError,
    ShadowRuntimePolicy,
    _quantize,
)
from ai_platform.wickhunter.shadow_runtime_positions import (
    ClosedSimulatedPosition,
    RuntimeDecisionSummary,
    SimulatedPosition,
)
from ai_platform.wickhunter.shadow_runtime_state import (
    ShadowRuntimeState,
    ShadowRuntimeTick,
)


def _source_statuses(
    *,
    tick: ShadowRuntimeTick,
    maximum_age_ms: int,
) -> tuple[RuntimeSourceStatus, ...]:
    statuses: list[RuntimeSourceStatus] = []
    for state in tick.source_states:
        if state.observed_at_ms > tick.observed_at_ms:
            raise ShadowRuntimeError("source state is observed in the future")
        if state.last_received_at_ms is None:
            age_ms = None
        else:
            if state.last_received_at_ms > tick.observed_at_ms:
                raise ShadowRuntimeError("source data is received in the future")
            age_ms = tick.observed_at_ms - state.last_received_at_ms
        fresh = (
            state.health is SourceHealth.HEALTHY
            and state.coverage_available
            and age_ms is not None
            and age_ms <= maximum_age_ms
        )
        statuses.append(
            RuntimeSourceStatus(
                source=state.source,
                health=state.health,
                observed_at_ms=state.observed_at_ms,
                last_received_at_ms=state.last_received_at_ms,
                age_ms=age_ms,
                fresh=fresh,
            )
        )
    return tuple(sorted(statuses, key=lambda item: item.source))


def _circuit_breaker_reasons(
    *,
    tick: ShadowRuntimeTick,
    state: ShadowRuntimeState,
    source_statuses: tuple[RuntimeSourceStatus, ...],
    policy: ShadowRuntimePolicy,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if tick.universe.selected_at_ms > tick.observed_at_ms:
        reasons.append("universe_snapshot_from_future")
    elif tick.observed_at_ms - tick.universe.selected_at_ms > policy.maximum_universe_age_ms:
        reasons.append("universe_snapshot_stale")
    healthy_sources = sum(item.fresh for item in source_statuses)
    if healthy_sources < policy.minimum_healthy_sources:
        reasons.append("insufficient_fresh_sources")
    for item in source_statuses:
        if not item.fresh:
            reasons.append(f"source_unhealthy_or_stale:{item.source}")
    if policy.require_healthy_model_drift and tick.model_drift is not DriftState.HEALTHY:
        reasons.append("model_drift_not_healthy")
    if policy.require_healthy_data_drift and tick.data_drift is not DriftState.HEALTHY:
        reasons.append("data_drift_not_healthy")
    if state.drawdown_ratio >= policy.maximum_drawdown_ratio:
        reasons.append("maximum_drawdown_exceeded")
    return tuple(sorted(set(reasons)))


def _validate_request(
    *,
    request: ShadowDecisionRequest,
    tick: ShadowRuntimeTick,
    runtime_mode: BotMode,
    bot_instance: str,
) -> None:
    if request.mode is not runtime_mode:
        raise ShadowRuntimeError("decision request mode does not match runtime")
    if request.bot_instance != bot_instance:
        raise ShadowRuntimeError("decision request bot identity does not match runtime")
    if request.universe.snapshot_hash != tick.universe.snapshot_hash:
        raise ShadowRuntimeError("decision request uses another universe snapshot")
    if request.market.decision_timestamp_ms > tick.observed_at_ms:
        raise ShadowRuntimeError("decision request is from the future")


def _open_position(
    *,
    evidence: ShadowDecisionEvidence,
    initial_equity: Decimal,
) -> SimulatedPosition | None:
    intent = evidence.trade_intent
    if intent is None:
        raise ShadowRuntimeError("cannot open a position without a trade intent")
    planned_risk = max(
        intent.requested_base_risk_ratio,
        intent.dca_plan.maximum_total_risk_ratio,
    )
    notional = initial_equity * planned_risk * intent.requested_leverage
    quantity = _quantize(notional / intent.decision_price)
    if quantity <= 0:
        return None
    if intent.side is TradeDirection.LONG:
        take_profit = intent.decision_price * (Decimal("1") + intent.take_profit_ratio)
        stop_loss = intent.decision_price * (Decimal("1") - intent.stop_loss_ratio)
    else:
        take_profit = intent.decision_price * (Decimal("1") - intent.take_profit_ratio)
        stop_loss = intent.decision_price * (Decimal("1") + intent.stop_loss_ratio)
    position_id = canonical_sha256(
        {"kind": "shadow_position", "trade_intent_id": intent.trade_intent_id}
    )
    return SimulatedPosition(
        position_id=position_id,
        trade_intent_id=intent.trade_intent_id,
        symbol=intent.symbol,
        side=intent.side,
        opened_at_ms=intent.decision_timestamp_ms,
        entry_price=intent.decision_price,
        mark_price=intent.decision_price,
        quantity=quantity,
        take_profit_price=_quantize(take_profit),
        stop_loss_price=_quantize(stop_loss),
        model_version=intent.model_version,
        model_hash=intent.model_hash,
        parameter_version=intent.parameter_version,
        parameter_hash=intent.parameter_hash,
    )


def _mark_and_close_positions(
    *,
    positions: tuple[SimulatedPosition, ...],
    mark_prices: Mapping[str, Decimal],
    observed_at_ms: int,
) -> tuple[tuple[SimulatedPosition, ...], tuple[ClosedSimulatedPosition, ...]]:
    open_positions: list[SimulatedPosition] = []
    closed_positions: list[ClosedSimulatedPosition] = []
    for position in positions:
        mark = mark_prices.get(position.symbol, position.mark_price)
        if mark <= 0:
            raise ShadowRuntimeError("mark price must be > 0")
        close_reason: PositionCloseReason | None = None
        exit_price: Decimal | None = None
        if position.side is TradeDirection.LONG:
            if mark >= position.take_profit_price:
                close_reason = PositionCloseReason.TAKE_PROFIT
                exit_price = position.take_profit_price
            elif mark <= position.stop_loss_price:
                close_reason = PositionCloseReason.STOP_LOSS
                exit_price = position.stop_loss_price
        else:
            if mark <= position.take_profit_price:
                close_reason = PositionCloseReason.TAKE_PROFIT
                exit_price = position.take_profit_price
            elif mark >= position.stop_loss_price:
                close_reason = PositionCloseReason.STOP_LOSS
                exit_price = position.stop_loss_price
        if close_reason is None or exit_price is None:
            open_positions.append(replace(position, mark_price=mark))
            continue
        signed_move = (
            exit_price - position.entry_price
            if position.side is TradeDirection.LONG
            else position.entry_price - exit_price
        )
        realized = _quantize(signed_move * position.quantity)
        closed_id = canonical_sha256(
            {
                "position_id": position.position_id,
                "closed_at_ms": observed_at_ms,
                "exit_price": exit_price,
                "close_reason": close_reason.value,
            }
        )
        closed_positions.append(
            ClosedSimulatedPosition(
                closed_position_id=closed_id,
                position_id=position.position_id,
                symbol=position.symbol,
                side=position.side,
                opened_at_ms=position.opened_at_ms,
                closed_at_ms=observed_at_ms,
                entry_price=position.entry_price,
                exit_price=exit_price,
                quantity=position.quantity,
                realized_pnl_quote=realized,
                close_reason=close_reason,
            )
        )
    return (
        tuple(sorted(open_positions, key=lambda item: item.position_id)),
        tuple(sorted(closed_positions, key=lambda item: item.closed_position_id)),
    )


def _decision_summary(
    *,
    evidence: ShadowDecisionEvidence,
    observed_at_ms: int,
    runtime_reasons: Sequence[str],
) -> RuntimeDecisionSummary:
    candidate = evidence.candidate
    score = evidence.score
    risk = evidence.risk_decision
    reasons = list(runtime_reasons)
    if candidate is not None:
        reasons.extend(candidate.reason_codes)
    if risk is not None:
        reasons.extend(risk.reason_codes)
    symbol = (
        candidate.symbol
        if candidate is not None
        else evidence.trade_intent.symbol
        if evidence.trade_intent is not None
        else "unknown"
    )
    side = candidate.side if candidate is not None else None
    return RuntimeDecisionSummary(
        shadow_decision_id=evidence.shadow_decision_id,
        status=evidence.status,
        symbol=symbol,
        side=side,
        candidate_id=candidate.candidate_id if candidate is not None else None,
        score_id=score.score_id if score is not None else None,
        risk_decision_id=risk.risk_decision_id if risk is not None else None,
        reason_codes=tuple(sorted(set(reasons))),
        observed_at_ms=observed_at_ms,
    )


def _runtime_identity(
    decisions: Sequence[ShadowDecisionEvidence],
    previous: ShadowRuntimeState,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    intents = [item.trade_intent for item in decisions if item.trade_intent is not None]
    if not intents:
        return (
            previous.model_version,
            previous.model_hash,
            previous.parameter_version,
            previous.parameter_hash,
            previous.dataset_hash,
            previous.code_sha,
        )
    identities = {
        (
            item.model_version,
            item.model_hash,
            item.parameter_version,
            item.parameter_hash,
            item.dataset_hash,
            item.code_sha,
        )
        for item in intents
    }
    if len(identities) != 1:
        raise ShadowRuntimeError("one tick cannot mix runtime identities")
    return next(iter(identities))
