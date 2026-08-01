from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode, DriftState
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime_common import (
    RUNTIME_STATE_SCHEMA_VERSION,
    ShadowRuntimeError,
    ShadowRuntimePolicy,
    _require_finite,
    _require_git_sha,
    _require_positive,
    _require_sha256,
    _require_text,
)
from ai_platform.wickhunter.shadow_runtime_positions import (
    ClosedSimulatedPosition,
    SimulatedPosition,
)
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot


@dataclass(frozen=True, slots=True)
class ShadowRuntimeState:
    schema_version: str
    bot_instance: str
    mode: BotMode
    policy_version: str
    policy_sha256: str
    generation: int
    last_observed_at_ms: int | None
    universe_snapshot_hash: str | None
    positions: tuple[SimulatedPosition, ...]
    closed_positions: tuple[ClosedSimulatedPosition, ...]
    cumulative_realized_pnl_quote: Decimal
    peak_equity_quote: Decimal
    drawdown_ratio: Decimal
    recent_decision_ids: tuple[str, ...]
    model_version: str | None
    model_hash: str | None
    parameter_version: str | None
    parameter_hash: str | None
    dataset_hash: str | None
    code_sha: str | None

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != RUNTIME_STATE_SCHEMA_VERSION:
            raise ShadowRuntimeError("runtime state schema mismatch")
        _require_text(self.bot_instance, field="bot_instance")
        if self.mode is BotMode.LIVE_BLOCKED:
            raise ShadowRuntimeError("live mode is forbidden")
        _require_text(self.policy_version, field="policy_version")
        _require_sha256(self.policy_sha256, field="policy_sha256")
        if self.generation < 0:
            raise ShadowRuntimeError("generation must be >= 0")
        if self.last_observed_at_ms is not None and self.last_observed_at_ms <= 0:
            raise ShadowRuntimeError("last_observed_at_ms must be > 0")
        if self.universe_snapshot_hash is not None:
            _require_sha256(self.universe_snapshot_hash, field="universe_snapshot_hash")
        position_ids = [item.position_id for item in self.positions]
        if position_ids != sorted(position_ids) or len(position_ids) != len(set(position_ids)):
            raise ShadowRuntimeError("positions must be unique and sorted")
        closed_ids = [item.closed_position_id for item in self.closed_positions]
        if closed_ids != sorted(closed_ids) or len(closed_ids) != len(set(closed_ids)):
            raise ShadowRuntimeError("closed positions must be unique and sorted")
        _require_finite(
            self.cumulative_realized_pnl_quote,
            field="cumulative_realized_pnl_quote",
        )
        _require_positive(self.peak_equity_quote, field="peak_equity_quote")
        if not Decimal("0") <= self.drawdown_ratio <= Decimal("1"):
            raise ShadowRuntimeError("drawdown_ratio must be in [0, 1]")
        if self.recent_decision_ids != tuple(dict.fromkeys(self.recent_decision_ids)):
            raise ShadowRuntimeError("recent decision ids must be unique")
        for decision_id in self.recent_decision_ids:
            _require_sha256(decision_id, field="recent_decision_id")
        if self.model_version is None:
            if self.model_hash is not None:
                raise ShadowRuntimeError("model hash requires a model version")
        else:
            _require_text(self.model_version, field="model_version")
            if self.model_hash is None:
                raise ShadowRuntimeError("model version requires a model hash")
            _require_sha256(self.model_hash, field="model_hash")
        if self.parameter_version is None:
            if self.parameter_hash is not None:
                raise ShadowRuntimeError("parameter hash requires a parameter version")
        else:
            _require_text(self.parameter_version, field="parameter_version")
            if self.parameter_hash is None:
                raise ShadowRuntimeError("parameter version requires a parameter hash")
            _require_sha256(self.parameter_hash, field="parameter_hash")
        if self.dataset_hash is not None:
            _require_sha256(self.dataset_hash, field="dataset_hash")
        if self.code_sha is not None:
            _require_git_sha(self.code_sha, field="code_sha")

    @property
    def state_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ShadowRuntimeTick:
    observed_at_ms: int
    universe: DynamicUniverseSnapshot
    decision_requests: tuple[ShadowDecisionRequest, ...]
    mark_prices: tuple[tuple[str, Decimal], ...]
    source_states: tuple[Any, ...]
    model_drift: DriftState
    data_drift: DriftState
    validation_state: str
    retraining_state: str

    def __post_init__(self) -> None:
        if self.observed_at_ms <= 0:
            raise ShadowRuntimeError("observed_at_ms must be > 0")
        symbols = [symbol for symbol, _ in self.mark_prices]
        if symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
            raise ShadowRuntimeError("mark prices must be unique and sorted")
        for symbol, price in self.mark_prices:
            _require_text(symbol, field="mark symbol")
            _require_positive(price, field="mark price")
        sources = [state.source for state in self.source_states]
        if sources != sorted(sources) or len(sources) != len(set(sources)):
            raise ShadowRuntimeError("source states must be unique and sorted")
        _require_text(self.validation_state, field="validation_state")
        _require_text(self.retraining_state, field="retraining_state")


def initial_runtime_state(
    *,
    bot_instance: str,
    mode: BotMode,
    policy: ShadowRuntimePolicy,
) -> ShadowRuntimeState:
    if mode is BotMode.LIVE_BLOCKED:
        raise ShadowRuntimeError("live mode is forbidden")
    return ShadowRuntimeState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        bot_instance=bot_instance,
        mode=mode,
        policy_version=policy.policy_version,
        policy_sha256=policy.policy_sha256,
        generation=0,
        last_observed_at_ms=None,
        universe_snapshot_hash=None,
        positions=(),
        closed_positions=(),
        cumulative_realized_pnl_quote=Decimal("0"),
        peak_equity_quote=policy.simulated_initial_equity_quote,
        drawdown_ratio=Decimal("0"),
        recent_decision_ids=(),
        model_version=None,
        model_hash=None,
        parameter_version=None,
        parameter_hash=None,
        dataset_hash=None,
        code_sha=None,
    )
