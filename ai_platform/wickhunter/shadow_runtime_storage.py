from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from ai_platform.wickhunter.canonical import canonical_json
from ai_platform.wickhunter.contracts import BotMode, TradeDirection
from ai_platform.wickhunter.shadow_runtime_common import (
    RUNTIME_STORE_SCHEMA_VERSION,
    PositionCloseReason,
    ShadowRuntimeError,
)
from ai_platform.wickhunter.shadow_runtime_positions import (
    ClosedSimulatedPosition,
    SimulatedPosition,
)
from ai_platform.wickhunter.shadow_runtime_snapshot import PortalObservabilitySnapshot
from ai_platform.wickhunter.shadow_runtime_state import ShadowRuntimeState


class ShadowRuntimeStore:
    """Atomic single-state store with deterministic integrity verification."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.snapshot_path = root / "portal-observability-snapshot.json"

    def save(
        self,
        state: ShadowRuntimeState,
        snapshot: PortalObservabilitySnapshot | None = None,
    ) -> None:
        if self.root.is_symlink() or self.state_path.is_symlink():
            raise ShadowRuntimeError("runtime store cannot traverse symlinks")
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": RUNTIME_STORE_SCHEMA_VERSION,
            "state": _state_payload(state),
            "state_sha256": state.state_sha256,
        }
        _atomic_write(self.root, self.state_path, payload, prefix=".state.")
        if snapshot is not None:
            _atomic_write(
                self.root,
                self.snapshot_path,
                snapshot,
                prefix=".snapshot.",
            )

    def load(self) -> ShadowRuntimeState | None:
        if not self.state_path.exists():
            return None
        if self.root.is_symlink() or self.state_path.is_symlink() or not self.state_path.is_file():
            raise ShadowRuntimeError("runtime store state must be a regular file")
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ShadowRuntimeError("runtime state is unreadable") from exc
        if payload.get("schema_version") != RUNTIME_STORE_SCHEMA_VERSION:
            raise ShadowRuntimeError("runtime store schema mismatch")
        state_payload = payload.get("state")
        if not isinstance(state_payload, dict):
            raise ShadowRuntimeError("runtime store state payload is invalid")
        state = _state_from_payload(state_payload)
        if payload.get("state_sha256") != state.state_sha256:
            raise ShadowRuntimeError("runtime state integrity check failed")
        return state


def _atomic_write(root: Path, destination: Path, payload: object, *, prefix: str) -> None:
    if destination.is_symlink():
        raise ShadowRuntimeError("runtime store cannot replace a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=prefix,
        suffix=".tmp",
        dir=root,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _position_payload(position: SimulatedPosition) -> dict[str, object]:
    return {
        "position_id": position.position_id,
        "trade_intent_id": position.trade_intent_id,
        "symbol": position.symbol,
        "side": position.side.value,
        "opened_at_ms": position.opened_at_ms,
        "entry_price": str(position.entry_price),
        "mark_price": str(position.mark_price),
        "quantity": str(position.quantity),
        "take_profit_price": str(position.take_profit_price),
        "stop_loss_price": str(position.stop_loss_price),
        "model_version": position.model_version,
        "model_hash": position.model_hash,
        "parameter_version": position.parameter_version,
        "parameter_hash": position.parameter_hash,
    }


def _closed_payload(position: ClosedSimulatedPosition) -> dict[str, object]:
    return {
        "closed_position_id": position.closed_position_id,
        "position_id": position.position_id,
        "symbol": position.symbol,
        "side": position.side.value,
        "opened_at_ms": position.opened_at_ms,
        "closed_at_ms": position.closed_at_ms,
        "entry_price": str(position.entry_price),
        "exit_price": str(position.exit_price),
        "quantity": str(position.quantity),
        "realized_pnl_quote": str(position.realized_pnl_quote),
        "close_reason": position.close_reason.value,
    }


def _state_payload(state: ShadowRuntimeState) -> dict[str, object]:
    return {
        "schema_version": state.schema_version,
        "bot_instance": state.bot_instance,
        "mode": state.mode.value,
        "policy_version": state.policy_version,
        "policy_sha256": state.policy_sha256,
        "generation": state.generation,
        "last_observed_at_ms": state.last_observed_at_ms,
        "universe_snapshot_hash": state.universe_snapshot_hash,
        "positions": [_position_payload(item) for item in state.positions],
        "closed_positions": [_closed_payload(item) for item in state.closed_positions],
        "cumulative_realized_pnl_quote": str(state.cumulative_realized_pnl_quote),
        "peak_equity_quote": str(state.peak_equity_quote),
        "drawdown_ratio": str(state.drawdown_ratio),
        "recent_decision_ids": list(state.recent_decision_ids),
        "model_version": state.model_version,
        "model_hash": state.model_hash,
        "parameter_version": state.parameter_version,
        "parameter_hash": state.parameter_hash,
        "dataset_hash": state.dataset_hash,
        "code_sha": state.code_sha,
    }


def _state_from_payload(payload: Mapping[str, object]) -> ShadowRuntimeState:
    positions_raw = payload.get("positions")
    closed_raw = payload.get("closed_positions")
    if not isinstance(positions_raw, list) or not isinstance(closed_raw, list):
        raise ShadowRuntimeError("persisted positions are invalid")
    positions = tuple(
        SimulatedPosition(
            position_id=str(item["position_id"]),
            trade_intent_id=str(item["trade_intent_id"]),
            symbol=str(item["symbol"]),
            side=TradeDirection(str(item["side"])),
            opened_at_ms=int(item["opened_at_ms"]),
            entry_price=Decimal(str(item["entry_price"])),
            mark_price=Decimal(str(item["mark_price"])),
            quantity=Decimal(str(item["quantity"])),
            take_profit_price=Decimal(str(item["take_profit_price"])),
            stop_loss_price=Decimal(str(item["stop_loss_price"])),
            model_version=(
                None if item.get("model_version") is None else str(item["model_version"])
            ),
            model_hash=None if item.get("model_hash") is None else str(item["model_hash"]),
            parameter_version=str(item["parameter_version"]),
            parameter_hash=str(item["parameter_hash"]),
        )
        for item in positions_raw
        if isinstance(item, dict)
    )
    closed = tuple(
        ClosedSimulatedPosition(
            closed_position_id=str(item["closed_position_id"]),
            position_id=str(item["position_id"]),
            symbol=str(item["symbol"]),
            side=TradeDirection(str(item["side"])),
            opened_at_ms=int(item["opened_at_ms"]),
            closed_at_ms=int(item["closed_at_ms"]),
            entry_price=Decimal(str(item["entry_price"])),
            exit_price=Decimal(str(item["exit_price"])),
            quantity=Decimal(str(item["quantity"])),
            realized_pnl_quote=Decimal(str(item["realized_pnl_quote"])),
            close_reason=PositionCloseReason(str(item["close_reason"])),
        )
        for item in closed_raw
        if isinstance(item, dict)
    )
    recent_raw = payload.get("recent_decision_ids", [])
    if not isinstance(recent_raw, list):
        raise ShadowRuntimeError("persisted recent decision ids are invalid")
    return ShadowRuntimeState(
        schema_version=str(payload["schema_version"]),
        bot_instance=str(payload["bot_instance"]),
        mode=BotMode(str(payload["mode"])),
        policy_version=str(payload["policy_version"]),
        policy_sha256=str(payload["policy_sha256"]),
        generation=int(payload["generation"]),
        last_observed_at_ms=(
            None
            if payload.get("last_observed_at_ms") is None
            else int(payload["last_observed_at_ms"])
        ),
        universe_snapshot_hash=(
            None
            if payload.get("universe_snapshot_hash") is None
            else str(payload["universe_snapshot_hash"])
        ),
        positions=tuple(sorted(positions, key=lambda item: item.position_id)),
        closed_positions=tuple(sorted(closed, key=lambda item: item.closed_position_id)),
        cumulative_realized_pnl_quote=Decimal(
            str(payload["cumulative_realized_pnl_quote"])
        ),
        peak_equity_quote=Decimal(str(payload["peak_equity_quote"])),
        drawdown_ratio=Decimal(str(payload["drawdown_ratio"])),
        recent_decision_ids=tuple(str(item) for item in recent_raw),
        model_version=(
            None if payload.get("model_version") is None else str(payload["model_version"])
        ),
        model_hash=None if payload.get("model_hash") is None else str(payload["model_hash"]),
        parameter_version=(
            None
            if payload.get("parameter_version") is None
            else str(payload["parameter_version"])
        ),
        parameter_hash=(
            None
            if payload.get("parameter_hash") is None
            else str(payload["parameter_hash"])
        ),
        dataset_hash=(
            None if payload.get("dataset_hash") is None else str(payload["dataset_hash"])
        ),
        code_sha=None if payload.get("code_sha") is None else str(payload["code_sha"]),
    )
