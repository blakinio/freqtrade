from __future__ import annotations

from decimal import Decimal

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.shadow_runtime_common import (
    RUNTIME_SNAPSHOT_SCHEMA_VERSION,
    RuntimeHealth,
    RuntimeSourceStatus,
    _quantize,
)
from ai_platform.wickhunter.shadow_runtime_positions import RuntimeDecisionSummary
from ai_platform.wickhunter.shadow_runtime_snapshot import PortalObservabilitySnapshot
from ai_platform.wickhunter.shadow_runtime_state import (
    ShadowRuntimeState,
    ShadowRuntimeTick,
)


def _build_snapshot(
    *,
    state: ShadowRuntimeState,
    tick: ShadowRuntimeTick,
    health: RuntimeHealth,
    source_statuses: tuple[RuntimeSourceStatus, ...],
    decisions: tuple[RuntimeDecisionSummary, ...],
    breaker_reasons: tuple[str, ...],
    initial_equity: Decimal,
) -> PortalObservabilitySnapshot:
    unrealized = sum(
        (item.unrealized_pnl_quote for item in state.positions),
        Decimal("0"),
    )
    equity = initial_equity + state.cumulative_realized_pnl_quote + unrealized
    payload = {
        "bot_instance": state.bot_instance,
        "mode": state.mode.value,
        "health": health.value,
        "observed_at_ms": tick.observed_at_ms,
        "universe_snapshot_hash": tick.universe.snapshot_hash,
        "dynamic_universe": tick.universe.selected_symbols,
        "source_freshness": source_statuses,
        "model_version": state.model_version,
        "model_hash": state.model_hash,
        "parameter_version": state.parameter_version,
        "parameter_hash": state.parameter_hash,
        "dataset_hash": state.dataset_hash,
        "code_sha": state.code_sha,
        "decisions": decisions,
        "positions": state.positions,
        "cumulative_realized_pnl_quote": state.cumulative_realized_pnl_quote,
        "unrealized_pnl_quote": unrealized,
        "simulated_equity_quote": equity,
        "drawdown_ratio": state.drawdown_ratio,
        "retraining_state": tick.retraining_state,
        "validation_state": tick.validation_state,
        "model_drift": tick.model_drift.value,
        "data_drift": tick.data_drift.value,
        "circuit_breaker_active": bool(breaker_reasons),
        "circuit_breaker_reasons": breaker_reasons,
        "persistence_generation": state.generation,
        "runtime_state_sha256": state.state_sha256,
        "read_only": True,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }
    return PortalObservabilitySnapshot(
        schema_version=RUNTIME_SNAPSHOT_SCHEMA_VERSION,
        snapshot_id=canonical_sha256(
            {"schema_version": RUNTIME_SNAPSHOT_SCHEMA_VERSION, "payload": payload}
        ),
        bot_instance=state.bot_instance,
        mode=state.mode,
        health=health,
        observed_at_ms=tick.observed_at_ms,
        universe_snapshot_hash=tick.universe.snapshot_hash,
        dynamic_universe=tick.universe.selected_symbols,
        source_freshness=source_statuses,
        model_version=state.model_version,
        model_hash=state.model_hash,
        parameter_version=state.parameter_version,
        parameter_hash=state.parameter_hash,
        dataset_hash=state.dataset_hash,
        code_sha=state.code_sha,
        decisions=decisions,
        positions=state.positions,
        cumulative_realized_pnl_quote=state.cumulative_realized_pnl_quote,
        unrealized_pnl_quote=_quantize(unrealized),
        simulated_equity_quote=_quantize(equity),
        drawdown_ratio=state.drawdown_ratio,
        retraining_state=tick.retraining_state,
        validation_state=tick.validation_state,
        model_drift=tick.model_drift,
        data_drift=tick.data_drift,
        circuit_breaker_active=bool(breaker_reasons),
        circuit_breaker_reasons=breaker_reasons,
        persistence_generation=state.generation,
        runtime_state_sha256=state.state_sha256,
    )
