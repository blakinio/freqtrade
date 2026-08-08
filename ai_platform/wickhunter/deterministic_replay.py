from __future__ import annotations

import json
import os
import shutil
import tempfile
from bisect import bisect_left, bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import TradeDirection
from ai_platform.wickhunter.production_dataset_materialization import (
    DATASET_DIR_NAME,
    verify_production_materialization,
)
from ai_platform.wickhunter.replay_price_path import (
    ReplayAggregateTrade,
    verify_replay_price_path_package,
)


POLICY_SCHEMA_VERSION = "wickhunter-deterministic-replay-policy-v1"
REQUEST_SCHEMA_VERSION = "wickhunter-deterministic-replay-request-v1"
LABEL_SCHEMA_VERSION = "wickhunter-candidate-label-v1"
MANIFEST_SCHEMA_VERSION = "wickhunter-deterministic-replay-manifest-v1"
REPORT_SCHEMA_VERSION = "wickhunter-deterministic-replay-report-v1"
REQUEST_NAME = "request.json"
POLICY_NAME = "policy.json"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "verification-report.json"
CHECKSUM_INDEX_NAME = "artifact-sha256.txt"
LABELS_DIR_NAME = "labels"


class DeterministicReplayError(RuntimeError):
    """Raised when deterministic replay evidence cannot be accepted safely."""


class LabelOutcome(StrEnum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TIMEOUT = "timeout"
    MISSING_ENTRY = "missing_entry"


def _decimal(value: object, *, field: str, minimum: Decimal | None = None) -> Decimal:
    if isinstance(value, bool):
        raise DeterministicReplayError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DeterministicReplayError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite() or (minimum is not None and parsed < minimum):
        raise DeterministicReplayError(f"{field} has an invalid value")
    return parsed


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise DeterministicReplayError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise DeterministicReplayError(f"{field} must be an integer") from exc
    if parsed < minimum:
        raise DeterministicReplayError(f"{field} must be >= {minimum}")
    return parsed


def _text(value: object, *, field: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise DeterministicReplayError(f"{field} must be non-empty")
    return normalized


def _sha256(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise DeterministicReplayError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _git_sha(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 40 or any(char not in "0123456789abcdef" for char in normalized):
        raise DeterministicReplayError(f"{field} must be a lowercase 40-character Git SHA")
    return normalized


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise DeterministicReplayError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, payload: object) -> None:
    _write_new(path, canonical_json(payload).encode("utf-8") + b"\n")


def _write_jsonl(path: Path, payloads: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise DeterministicReplayError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        for payload in payloads:
            handle.write(canonical_json(payload).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DeterministicReplayError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeterministicReplayError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise DeterministicReplayError(f"{field} must contain an object")
    return payload


def _safe_member(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if (
        not logical_name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise DeterministicReplayError("artifact path must remain relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise DeterministicReplayError("artifact path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise DeterministicReplayError("artifact path escapes root or is missing") from exc
    if not current.is_file():
        raise DeterministicReplayError("artifact path is not a regular file")
    return current


@dataclass(frozen=True, slots=True)
class ReplayPolicy:
    schema_version: str
    policy_version: str
    entry_delay_ms: int
    maximum_entry_delay_ms: int
    fee_ratio: Decimal
    slippage_ratio: Decimal
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    label_horizon_ms: int
    protected_holdout_start_ms: int

    def __post_init__(self) -> None:
        if self.schema_version != POLICY_SCHEMA_VERSION:
            raise DeterministicReplayError(f"policy schema must be {POLICY_SCHEMA_VERSION}")
        _text(self.policy_version, field="policy_version")
        if self.entry_delay_ms < 0:
            raise DeterministicReplayError("entry_delay_ms must be >= 0")
        if self.maximum_entry_delay_ms < self.entry_delay_ms:
            raise DeterministicReplayError(
                "maximum_entry_delay_ms must not be below entry_delay_ms"
            )
        if self.label_horizon_ms <= 0:
            raise DeterministicReplayError("label_horizon_ms must be > 0")
        if self.maximum_entry_delay_ms >= self.label_horizon_ms:
            raise DeterministicReplayError("maximum_entry_delay_ms must be below label_horizon_ms")
        for value, field, allow_zero in (
            (self.fee_ratio, "fee_ratio", True),
            (self.slippage_ratio, "slippage_ratio", True),
            (self.take_profit_ratio, "take_profit_ratio", False),
            (self.stop_loss_ratio, "stop_loss_ratio", False),
        ):
            minimum = Decimal("0") if allow_zero else Decimal("0.000000000001")
            parsed = _decimal(value, field=field, minimum=minimum)
            if parsed >= Decimal("1"):
                raise DeterministicReplayError(f"{field} must be below 1")
        if self.protected_holdout_start_ms <= 0:
            raise DeterministicReplayError("protected_holdout_start_ms must be > 0")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ReplaySplitWindow:
    split_name: str
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        _text(self.split_name, field="split_name")
        if self.start_ms <= 0 or self.end_ms <= self.start_ms:
            raise DeterministicReplayError("split window must be positive and non-empty")


@dataclass(frozen=True, slots=True)
class ReplayDecision:
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    split_geometry_sha256: str
    dataset_row_sha256: str
    price_path_manifest_sha256: str
    source_commit_sha: str
    split_name: str
    symbol: str
    decision_timestamp_ms: int
    side: TradeDirection

    def __post_init__(self) -> None:
        for value, field in (
            (self.dataset_id, "dataset_id"),
            (self.split_name, "split_name"),
            (self.symbol, "symbol"),
        ):
            _text(value, field=field)
        for value, field in (
            (self.dataset_manifest_sha256, "dataset_manifest_sha256"),
            (self.market_manifest_sha256, "market_manifest_sha256"),
            (self.split_geometry_sha256, "split_geometry_sha256"),
            (self.dataset_row_sha256, "dataset_row_sha256"),
            (self.price_path_manifest_sha256, "price_path_manifest_sha256"),
        ):
            _sha256(value, field=field)
        _git_sha(self.source_commit_sha, field="source_commit_sha")
        if self.decision_timestamp_ms <= 0:
            raise DeterministicReplayError("decision_timestamp_ms must be > 0")


@dataclass(frozen=True, slots=True)
class CandidateLabel:
    schema_version: str
    label_id: str
    policy_version: str
    policy_sha256: str
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    split_geometry_sha256: str
    dataset_row_sha256: str
    price_path_manifest_sha256: str
    source_commit_sha: str
    split_name: str
    symbol: str
    side: TradeDirection
    decision_timestamp_ms: int
    label_end_ms: int
    outcome: LabelOutcome
    entry_timestamp_ms: int | None
    entry_aggregate_trade_id: int | None
    entry_trade_sha256: str | None
    raw_entry_price: Decimal | None
    executed_entry_price: Decimal | None
    exit_timestamp_ms: int | None
    exit_aggregate_trade_id: int | None
    exit_trade_sha256: str | None
    raw_exit_price: Decimal | None
    executed_exit_price: Decimal | None
    gross_return_ratio: Decimal | None
    net_return_ratio: Decimal | None
    maximum_favorable_excursion_ratio: Decimal | None
    maximum_adverse_excursion_ratio: Decimal | None
    time_to_outcome_ms: int | None
    fee_ratio: Decimal
    slippage_ratio: Decimal
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    entry_delay_ms: int
    maximum_entry_delay_ms: int
    protected_holdout_accessed: bool
    immutable_inputs_mutated: bool
    model_execution_authorized: bool
    performance_research_authorized: bool
    execution_enabled: bool
    live_capital_authorized: bool
    trading_credentials_present: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != LABEL_SCHEMA_VERSION:
            raise DeterministicReplayError(f"label schema must be {LABEL_SCHEMA_VERSION}")
        _sha256(self.label_id, field="label_id")
        _sha256(self.policy_sha256, field="policy_sha256")
        _sha256(self.dataset_manifest_sha256, field="dataset_manifest_sha256")
        _sha256(self.market_manifest_sha256, field="market_manifest_sha256")
        _sha256(self.split_geometry_sha256, field="split_geometry_sha256")
        _sha256(self.dataset_row_sha256, field="dataset_row_sha256")
        _sha256(self.price_path_manifest_sha256, field="price_path_manifest_sha256")
        _git_sha(self.source_commit_sha, field="source_commit_sha")
        if self.label_end_ms <= self.decision_timestamp_ms:
            raise DeterministicReplayError("label_end_ms must be after decision")
        optional_fields = (
            self.entry_timestamp_ms,
            self.entry_aggregate_trade_id,
            self.entry_trade_sha256,
            self.raw_entry_price,
            self.executed_entry_price,
            self.exit_timestamp_ms,
            self.exit_aggregate_trade_id,
            self.exit_trade_sha256,
            self.raw_exit_price,
            self.executed_exit_price,
            self.gross_return_ratio,
            self.net_return_ratio,
            self.maximum_favorable_excursion_ratio,
            self.maximum_adverse_excursion_ratio,
            self.time_to_outcome_ms,
        )
        if self.outcome is LabelOutcome.MISSING_ENTRY:
            if any(value is not None for value in optional_fields):
                raise DeterministicReplayError(
                    "missing-entry label cannot contain execution fields"
                )
        else:
            if any(value is None for value in optional_fields):
                raise DeterministicReplayError("executed label requires complete execution fields")
            if (
                self.entry_timestamp_ms is None
                or self.exit_timestamp_ms is None
                or self.time_to_outcome_ms is None
            ):
                raise DeterministicReplayError("executed label requires complete timestamps")
            if self.exit_timestamp_ms < self.entry_timestamp_ms:
                raise DeterministicReplayError("exit cannot precede entry")
            if self.time_to_outcome_ms != self.exit_timestamp_ms - self.entry_timestamp_ms:
                raise DeterministicReplayError("time_to_outcome_ms is inconsistent")
        if (
            self.protected_holdout_accessed
            or self.immutable_inputs_mutated
            or self.model_execution_authorized
            or self.performance_research_authorized
            or self.execution_enabled
            or self.live_capital_authorized
            or self.trading_credentials_present
            or self.orders_submitted != 0
        ):
            raise DeterministicReplayError("label contains unsafe authority")

    @property
    def label_sha256(self) -> str:
        return canonical_sha256(self)

    def as_json_dict(self) -> dict[str, object]:
        payload = json.loads(canonical_json(self))
        payload["label_sha256"] = self.label_sha256
        return payload


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    schema_version: str
    package_id: str
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    price_path_package_id: str
    price_path_manifest_sha256: str
    source_commit_sha: str
    split_geometry_sha256: str
    split_windows: tuple[ReplaySplitWindow, ...]
    sides: tuple[TradeDirection, ...]
    policy: ReplayPolicy
    protected_holdout_excluded: bool
    immutable_inputs_mutated: bool
    model_execution_authorized: bool
    performance_research_authorized: bool
    execution_enabled: bool
    live_capital_authorized: bool
    trading_credentials_present: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise DeterministicReplayError(f"request schema must be {REQUEST_SCHEMA_VERSION}")
        for value, field in (
            (self.package_id, "package_id"),
            (self.dataset_id, "dataset_id"),
            (self.price_path_package_id, "price_path_package_id"),
        ):
            _text(value, field=field)
        for value, field in (
            (self.dataset_manifest_sha256, "dataset_manifest_sha256"),
            (self.market_manifest_sha256, "market_manifest_sha256"),
            (self.price_path_manifest_sha256, "price_path_manifest_sha256"),
            (self.split_geometry_sha256, "split_geometry_sha256"),
        ):
            _sha256(value, field=field)
        _git_sha(self.source_commit_sha, field="source_commit_sha")
        _validate_split_windows(self.split_windows, self.policy.label_horizon_ms)
        if self.policy.protected_holdout_start_ms <= max(
            window.end_ms for window in self.split_windows
        ):
            raise DeterministicReplayError("split windows overlap protected holdout")
        if self.sides != tuple(sorted(set(self.sides), key=lambda side: side.value)):
            raise DeterministicReplayError("sides must be unique and sorted")
        if not self.sides:
            raise DeterministicReplayError("at least one replay side is required")
        if (
            not self.protected_holdout_excluded
            or self.immutable_inputs_mutated
            or self.model_execution_authorized
            or self.performance_research_authorized
            or self.execution_enabled
            or self.live_capital_authorized
            or self.trading_credentials_present
            or self.orders_submitted != 0
        ):
            raise DeterministicReplayError("request contains unsafe authority")

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self)


def _validate_split_windows(
    windows: Sequence[ReplaySplitWindow],
    label_horizon_ms: int,
) -> None:
    if not windows:
        raise DeterministicReplayError("split windows are required")
    names = [window.split_name for window in windows]
    if len(names) != len(set(names)):
        raise DeterministicReplayError("split window names must be unique")
    ordered = tuple(sorted(windows, key=lambda item: (item.start_ms, item.end_ms, item.split_name)))
    if tuple(windows) != ordered:
        raise DeterministicReplayError("split windows must be chronologically sorted")
    for previous, current in pairwise(windows):
        if current.start_ms - previous.end_ms < label_horizon_ms:
            raise DeterministicReplayError(
                "adjacent split windows require purge/embargo at least label_horizon_ms"
            )


def _executed_price(
    raw_price: Decimal,
    *,
    side: TradeDirection,
    entering: bool,
    slippage_ratio: Decimal,
) -> Decimal:
    adverse = (side is TradeDirection.LONG and entering) or (
        side is TradeDirection.SHORT and not entering
    )
    multiplier = Decimal("1") + slippage_ratio if adverse else Decimal("1") - slippage_ratio
    result = raw_price * multiplier
    if result <= 0:
        raise DeterministicReplayError("slippage produced a non-positive execution price")
    return result


def _returns(
    *,
    side: TradeDirection,
    entry_price: Decimal,
    exit_price: Decimal,
    fee_ratio: Decimal,
) -> tuple[Decimal, Decimal]:
    exit_notional_ratio = exit_price / entry_price
    if side is TradeDirection.LONG:
        gross = exit_notional_ratio - Decimal("1")
    else:
        gross = Decimal("1") - exit_notional_ratio
    net = gross - fee_ratio - (fee_ratio * exit_notional_ratio)
    return gross, net


def _excursions(
    *,
    side: TradeDirection,
    entry_price: Decimal,
    raw_prices: Sequence[Decimal],
) -> tuple[Decimal, Decimal]:
    if not raw_prices:
        raise DeterministicReplayError("excursions require observed prices")
    maximum = max(raw_prices)
    minimum = min(raw_prices)
    if side is TradeDirection.LONG:
        favorable = max(Decimal("0"), (maximum - entry_price) / entry_price)
        adverse = max(Decimal("0"), (entry_price - minimum) / entry_price)
    else:
        favorable = max(Decimal("0"), (entry_price - minimum) / entry_price)
        adverse = max(Decimal("0"), (maximum - entry_price) / entry_price)
    return favorable, adverse


def replay_event_label(  # noqa: C901
    *,
    decision: ReplayDecision,
    trades: Sequence[ReplayAggregateTrade],
    policy: ReplayPolicy,
) -> CandidateLabel:
    if (
        decision.decision_timestamp_ms + policy.label_horizon_ms
        >= policy.protected_holdout_start_ms
    ):
        raise DeterministicReplayError("decision label overlaps protected holdout")
    if not trades:
        raise DeterministicReplayError("trade path is empty")
    orders = [(trade.occurred_at_ms, trade.aggregate_trade_id) for trade in trades]
    if orders != sorted(set(orders)):
        raise DeterministicReplayError("trade path must be unique and strictly ordered")
    if any(trade.symbol != decision.symbol for trade in trades):
        raise DeterministicReplayError("trade path symbol does not match decision")

    timestamps = [trade.occurred_at_ms for trade in trades]
    label_end = decision.decision_timestamp_ms + policy.label_horizon_ms
    coverage_index = bisect_left(timestamps, label_end)
    if coverage_index >= len(trades):
        raise DeterministicReplayError("trade path does not reach the exact label deadline")

    eligible_at = decision.decision_timestamp_ms + policy.entry_delay_ms
    entry_index = bisect_left(timestamps, eligible_at)
    entry_deadline = decision.decision_timestamp_ms + policy.maximum_entry_delay_ms
    if (
        entry_index >= len(trades)
        or trades[entry_index].occurred_at_ms > entry_deadline
        or trades[entry_index].occurred_at_ms > label_end
    ):
        return _label(
            decision=decision,
            policy=policy,
            outcome=LabelOutcome.MISSING_ENTRY,
            label_end=label_end,
        )

    entry = trades[entry_index]
    executed_entry = _executed_price(
        entry.price,
        side=decision.side,
        entering=True,
        slippage_ratio=policy.slippage_ratio,
    )
    if decision.side is TradeDirection.LONG:
        take_profit = executed_entry * (Decimal("1") + policy.take_profit_ratio)
        stop_loss = executed_entry * (Decimal("1") - policy.stop_loss_ratio)
    else:
        take_profit = executed_entry * (Decimal("1") - policy.take_profit_ratio)
        stop_loss = executed_entry * (Decimal("1") + policy.stop_loss_ratio)

    window_end = bisect_right(timestamps, label_end)
    window = list(trades[entry_index:window_end])
    if not window:
        raise DeterministicReplayError("entry path contains no observations")

    outcome = LabelOutcome.TIMEOUT
    exit_trade = window[-1]
    observed: list[ReplayAggregateTrade] = []
    for trade in window:
        observed.append(trade)
        if decision.side is TradeDirection.LONG:
            if trade.price >= take_profit:
                outcome = LabelOutcome.TAKE_PROFIT
                exit_trade = trade
                break
            if trade.price <= stop_loss:
                outcome = LabelOutcome.STOP_LOSS
                exit_trade = trade
                break
        else:
            if trade.price <= take_profit:
                outcome = LabelOutcome.TAKE_PROFIT
                exit_trade = trade
                break
            if trade.price >= stop_loss:
                outcome = LabelOutcome.STOP_LOSS
                exit_trade = trade
                break

    executed_exit = _executed_price(
        exit_trade.price,
        side=decision.side,
        entering=False,
        slippage_ratio=policy.slippage_ratio,
    )
    gross, net = _returns(
        side=decision.side,
        entry_price=executed_entry,
        exit_price=executed_exit,
        fee_ratio=policy.fee_ratio,
    )
    mfe, mae = _excursions(
        side=decision.side,
        entry_price=executed_entry,
        raw_prices=[trade.price for trade in observed],
    )
    return _label(
        decision=decision,
        policy=policy,
        outcome=outcome,
        label_end=label_end,
        entry=entry,
        executed_entry=executed_entry,
        exit_trade=exit_trade,
        executed_exit=executed_exit,
        gross_return=gross,
        net_return=net,
        mfe=mfe,
        mae=mae,
    )


def _label(
    *,
    decision: ReplayDecision,
    policy: ReplayPolicy,
    outcome: LabelOutcome,
    label_end: int,
    entry: ReplayAggregateTrade | None = None,
    executed_entry: Decimal | None = None,
    exit_trade: ReplayAggregateTrade | None = None,
    executed_exit: Decimal | None = None,
    gross_return: Decimal | None = None,
    net_return: Decimal | None = None,
    mfe: Decimal | None = None,
    mae: Decimal | None = None,
) -> CandidateLabel:
    identity = {
        "schema_version": LABEL_SCHEMA_VERSION,
        "policy_sha256": policy.policy_sha256,
        "dataset_row_sha256": decision.dataset_row_sha256,
        "price_path_manifest_sha256": decision.price_path_manifest_sha256,
        "side": decision.side.value,
        "decision_timestamp_ms": decision.decision_timestamp_ms,
    }
    label_id = canonical_sha256(identity)
    return CandidateLabel(
        schema_version=LABEL_SCHEMA_VERSION,
        label_id=label_id,
        policy_version=policy.policy_version,
        policy_sha256=policy.policy_sha256,
        dataset_id=decision.dataset_id,
        dataset_manifest_sha256=decision.dataset_manifest_sha256,
        market_manifest_sha256=decision.market_manifest_sha256,
        split_geometry_sha256=decision.split_geometry_sha256,
        dataset_row_sha256=decision.dataset_row_sha256,
        price_path_manifest_sha256=decision.price_path_manifest_sha256,
        source_commit_sha=decision.source_commit_sha,
        split_name=decision.split_name,
        symbol=decision.symbol,
        side=decision.side,
        decision_timestamp_ms=decision.decision_timestamp_ms,
        label_end_ms=label_end,
        outcome=outcome,
        entry_timestamp_ms=None if entry is None else entry.occurred_at_ms,
        entry_aggregate_trade_id=None if entry is None else entry.aggregate_trade_id,
        entry_trade_sha256=None if entry is None else entry.trade_sha256,
        raw_entry_price=None if entry is None else entry.price,
        executed_entry_price=executed_entry,
        exit_timestamp_ms=None if exit_trade is None else exit_trade.occurred_at_ms,
        exit_aggregate_trade_id=None if exit_trade is None else exit_trade.aggregate_trade_id,
        exit_trade_sha256=None if exit_trade is None else exit_trade.trade_sha256,
        raw_exit_price=None if exit_trade is None else exit_trade.price,
        executed_exit_price=executed_exit,
        gross_return_ratio=gross_return,
        net_return_ratio=net_return,
        maximum_favorable_excursion_ratio=mfe,
        maximum_adverse_excursion_ratio=mae,
        time_to_outcome_ms=(
            None
            if entry is None or exit_trade is None
            else exit_trade.occurred_at_ms - entry.occurred_at_ms
        ),
        fee_ratio=policy.fee_ratio,
        slippage_ratio=policy.slippage_ratio,
        take_profit_ratio=policy.take_profit_ratio,
        stop_loss_ratio=policy.stop_loss_ratio,
        entry_delay_ms=policy.entry_delay_ms,
        maximum_entry_delay_ms=policy.maximum_entry_delay_ms,
        protected_holdout_accessed=False,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )


@dataclass(frozen=True, slots=True)
class _DatasetRow:
    split_name: str
    symbol: str
    decision_timestamp_ms: int
    row_sha256: str


def _load_dataset_rows(  # noqa: C901
    dataset_root: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[list[_DatasetRow], dict[str, Any]]:
    manifest = _load_json(dataset_root / MANIFEST_NAME, field="dataset manifest")
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if claimed != expected_manifest_sha256 or canonical_sha256(seed) != claimed:
        raise DeterministicReplayError("dataset manifest identity mismatch")
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise DeterministicReplayError("dataset partitions are missing")
    rows: list[_DatasetRow] = []
    for raw_partition in partitions:
        if not isinstance(raw_partition, dict):
            raise DeterministicReplayError("dataset partition is invalid")
        path = _safe_member(dataset_root, str(raw_partition.get("relative_path", "")))
        if sha256_file(path) != raw_partition.get("sha256"):
            raise DeterministicReplayError("dataset partition hash mismatch")
        partition_count = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise DeterministicReplayError("dataset partition contains a blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DeterministicReplayError("dataset row is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise DeterministicReplayError("dataset row must be an object")
                row_sha = payload.get("row_sha256")
                row_seed = dict(payload)
                row_seed.pop("row_sha256", None)
                if not isinstance(row_sha, str) or canonical_sha256(row_seed) != row_sha:
                    raise DeterministicReplayError("dataset row hash mismatch")
                rows.append(
                    _DatasetRow(
                        split_name=_text(payload.get("split_name"), field="split_name"),
                        symbol=_text(payload.get("symbol"), field="symbol").upper(),
                        decision_timestamp_ms=_integer(
                            payload.get("decision_timestamp_ms"),
                            field="decision_timestamp_ms",
                            minimum=1,
                        ),
                        row_sha256=_sha256(row_sha, field="row_sha256"),
                    )
                )
                partition_count += 1
        if partition_count != raw_partition.get("row_count"):
            raise DeterministicReplayError("dataset partition row count mismatch")
    if len(rows) != manifest.get("total_rows"):
        raise DeterministicReplayError("dataset total row count mismatch")
    keys = [(row.symbol, row.decision_timestamp_ms, row.row_sha256) for row in rows]
    if len(keys) != len(set(keys)):
        raise DeterministicReplayError("dataset replay keys must be unique")
    rows.sort(key=lambda item: (item.split_name, item.symbol, item.decision_timestamp_ms))
    return rows, manifest


def _trade_from_json(payload: Mapping[str, object]) -> ReplayAggregateTrade:
    try:
        trade = ReplayAggregateTrade(
            schema_version=str(payload["schema_version"]),
            source=str(payload["source"]),
            symbol=str(payload["symbol"]),
            aggregate_trade_id=_integer(payload["aggregate_trade_id"], field="aggregate_trade_id"),
            price=_decimal(
                payload["price"],
                field="price",
                minimum=Decimal("0.000000000001"),
            ),
            quantity=_decimal(
                payload["quantity"],
                field="quantity",
                minimum=Decimal("0.000000000001"),
            ),
            first_trade_id=_integer(payload["first_trade_id"], field="first_trade_id"),
            last_trade_id=_integer(payload["last_trade_id"], field="last_trade_id"),
            occurred_at_ms=_integer(payload["occurred_at_ms"], field="occurred_at_ms", minimum=1),
            buyer_is_maker=payload["buyer_is_maker"] is True,
            archive_sha256=str(payload["archive_sha256"]),
            raw_row_number=_integer(
                payload["raw_row_number"],
                field="raw_row_number",
                minimum=1,
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, DeterministicReplayError):
            raise
        raise DeterministicReplayError("invalid normalized aggregate trade") from exc
    if payload.get("buyer_is_maker") not in {True, False}:
        raise DeterministicReplayError("buyer_is_maker must be boolean")
    if payload.get("trade_sha256") != trade.trade_sha256:
        raise DeterministicReplayError("trade hash mismatch")
    return trade


def _load_price_path(  # noqa: C901
    price_path_root: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[dict[str, list[ReplayAggregateTrade]], dict[str, Any]]:
    manifest = _load_json(price_path_root / MANIFEST_NAME, field="price-path manifest")
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if claimed != expected_manifest_sha256 or canonical_sha256(seed) != claimed:
        raise DeterministicReplayError("price-path manifest identity mismatch")
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise DeterministicReplayError("price-path partitions are missing")
    result: dict[str, list[ReplayAggregateTrade]] = {}
    for raw_partition in partitions:
        if not isinstance(raw_partition, dict):
            raise DeterministicReplayError("price-path partition is invalid")
        symbol = _text(raw_partition.get("symbol"), field="partition symbol").upper()
        if symbol in result:
            raise DeterministicReplayError("duplicate price-path symbol")
        path = _safe_member(price_path_root, str(raw_partition.get("relative_path", "")))
        if sha256_file(path) != raw_partition.get("sha256"):
            raise DeterministicReplayError("price-path partition hash mismatch")
        trades: list[ReplayAggregateTrade] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise DeterministicReplayError("price-path partition contains blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DeterministicReplayError("price-path row is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise DeterministicReplayError("price-path row must be an object")
                trades.append(_trade_from_json(payload))
        if len(trades) != raw_partition.get("row_count"):
            raise DeterministicReplayError("price-path row count mismatch")
        result[symbol] = trades
    if sum(len(items) for items in result.values()) != manifest.get("total_trade_rows"):
        raise DeterministicReplayError("price-path total row count mismatch")
    return result, manifest


def _window_for(
    split_name: str,
    windows: Sequence[ReplaySplitWindow],
) -> ReplaySplitWindow:
    try:
        return next(window for window in windows if window.split_name == split_name)
    except StopIteration as exc:
        raise DeterministicReplayError(f"missing declared split window for {split_name}") from exc


def _validated_trade_timestamps(
    trades_by_symbol: Mapping[str, Sequence[ReplayAggregateTrade]],
) -> dict[str, tuple[int, ...]]:
    result: dict[str, tuple[int, ...]] = {}
    for symbol, trades in trades_by_symbol.items():
        if not trades:
            raise DeterministicReplayError(f"trade path is empty for {symbol}")
        orders = tuple((trade.occurred_at_ms, trade.aggregate_trade_id) for trade in trades)
        if list(orders) != sorted(set(orders)):
            raise DeterministicReplayError(
                f"trade path must be unique and strictly ordered for {symbol}"
            )
        if any(trade.symbol != symbol for trade in trades):
            raise DeterministicReplayError(
                f"trade path symbol does not match partition for {symbol}"
            )
        result[symbol] = tuple(trade.occurred_at_ms for trade in trades)
    return result


def _exact_replay_trade_window(
    *,
    trades: Sequence[ReplayAggregateTrade],
    timestamps: Sequence[int],
    decision_timestamp_ms: int,
    policy: ReplayPolicy,
) -> Sequence[ReplayAggregateTrade]:
    eligible_at = decision_timestamp_ms + policy.entry_delay_ms
    label_end = decision_timestamp_ms + policy.label_horizon_ms
    start_index = bisect_left(timestamps, eligible_at)
    coverage_index = bisect_left(timestamps, label_end)
    if coverage_index >= len(trades):
        raise DeterministicReplayError("trade path does not reach the exact label deadline")
    end_index = bisect_right(timestamps, label_end)
    if end_index <= coverage_index:
        end_index = coverage_index + 1
    return trades[start_index:end_index]


def _build_labels(
    *,
    rows: Sequence[_DatasetRow],
    trades_by_symbol: Mapping[str, Sequence[ReplayAggregateTrade]],
    request: ReplayRequest,
) -> list[CandidateLabel]:
    labels: list[CandidateLabel] = []
    timestamps_by_symbol = _validated_trade_timestamps(trades_by_symbol)
    for row in rows:
        window = _window_for(row.split_name, request.split_windows)
        if not window.start_ms <= row.decision_timestamp_ms < window.end_ms:
            raise DeterministicReplayError("dataset decision lies outside its split window")
        if row.decision_timestamp_ms + request.policy.label_horizon_ms > window.end_ms:
            # Boundary eligibility is determined only by the frozen split geometry and
            # explicit label horizon. Excluding the row avoids target leakage across
            # splits without consulting labels, outcomes, test performance, or holdout.
            continue
        trades = trades_by_symbol.get(row.symbol)
        timestamps = timestamps_by_symbol.get(row.symbol)
        if trades is None or timestamps is None:
            raise DeterministicReplayError(f"missing price path for {row.symbol}")
        replay_trades = _exact_replay_trade_window(
            trades=trades,
            timestamps=timestamps,
            decision_timestamp_ms=row.decision_timestamp_ms,
            policy=request.policy,
        )
        for side in request.sides:
            decision = ReplayDecision(
                dataset_id=request.dataset_id,
                dataset_manifest_sha256=request.dataset_manifest_sha256,
                market_manifest_sha256=request.market_manifest_sha256,
                split_geometry_sha256=request.split_geometry_sha256,
                dataset_row_sha256=row.row_sha256,
                price_path_manifest_sha256=request.price_path_manifest_sha256,
                source_commit_sha=request.source_commit_sha,
                split_name=row.split_name,
                symbol=row.symbol,
                decision_timestamp_ms=row.decision_timestamp_ms,
                side=side,
            )
            labels.append(
                replay_event_label(
                    decision=decision,
                    trades=replay_trades,
                    policy=request.policy,
                )
            )
    labels.sort(
        key=lambda item: (
            item.split_name,
            item.symbol,
            item.decision_timestamp_ms,
            item.side.value,
        )
    )
    return labels


def _request_from_json(payload: Mapping[str, object]) -> ReplayRequest:
    raw_policy = payload.get("policy")
    raw_windows = payload.get("split_windows")
    raw_sides = payload.get("sides")
    if not isinstance(raw_policy, dict):
        raise DeterministicReplayError("request policy must be an object")
    if not isinstance(raw_windows, list) or not isinstance(raw_sides, list):
        raise DeterministicReplayError("request split_windows and sides must be lists")
    policy = ReplayPolicy(
        schema_version=str(raw_policy["schema_version"]),
        policy_version=str(raw_policy["policy_version"]),
        entry_delay_ms=_integer(raw_policy["entry_delay_ms"], field="entry_delay_ms"),
        maximum_entry_delay_ms=_integer(
            raw_policy["maximum_entry_delay_ms"], field="maximum_entry_delay_ms"
        ),
        fee_ratio=_decimal(raw_policy["fee_ratio"], field="fee_ratio"),
        slippage_ratio=_decimal(raw_policy["slippage_ratio"], field="slippage_ratio"),
        take_profit_ratio=_decimal(raw_policy["take_profit_ratio"], field="take_profit_ratio"),
        stop_loss_ratio=_decimal(raw_policy["stop_loss_ratio"], field="stop_loss_ratio"),
        label_horizon_ms=_integer(
            raw_policy["label_horizon_ms"], field="label_horizon_ms", minimum=1
        ),
        protected_holdout_start_ms=_integer(
            raw_policy["protected_holdout_start_ms"],
            field="protected_holdout_start_ms",
            minimum=1,
        ),
    )
    try:
        sides = tuple(TradeDirection(str(item)) for item in raw_sides)
    except ValueError as exc:
        raise DeterministicReplayError("request contains an invalid side") from exc
    return ReplayRequest(
        schema_version=str(payload["schema_version"]),
        package_id=str(payload["package_id"]),
        dataset_id=str(payload["dataset_id"]),
        dataset_manifest_sha256=str(payload["dataset_manifest_sha256"]),
        market_manifest_sha256=str(payload["market_manifest_sha256"]),
        price_path_package_id=str(payload["price_path_package_id"]),
        price_path_manifest_sha256=str(payload["price_path_manifest_sha256"]),
        source_commit_sha=str(payload["source_commit_sha"]),
        split_geometry_sha256=str(payload["split_geometry_sha256"]),
        split_windows=tuple(
            ReplaySplitWindow(
                split_name=str(item["split_name"]),
                start_ms=_integer(item["start_ms"], field="split start", minimum=1),
                end_ms=_integer(item["end_ms"], field="split end", minimum=1),
            )
            for item in raw_windows
            if isinstance(item, dict)
        ),
        sides=sides,
        policy=policy,
        protected_holdout_excluded=payload.get("protected_holdout_excluded") is True,
        immutable_inputs_mutated=payload.get("immutable_inputs_mutated") is True,
        model_execution_authorized=payload.get("model_execution_authorized") is True,
        performance_research_authorized=payload.get("performance_research_authorized") is True,
        execution_enabled=payload.get("execution_enabled") is True,
        live_capital_authorized=payload.get("live_capital_authorized") is True,
        trading_credentials_present=payload.get("trading_credentials_present") is True,
        orders_submitted=_integer(payload.get("orders_submitted", -1), field="orders_submitted"),
    )


def _require_safe_authority(payload: Mapping[str, object]) -> None:
    for field in (
        "protected_holdout_accessed",
        "immutable_inputs_mutated",
        "model_execution_authorized",
        "performance_research_authorized",
        "execution_enabled",
        "live_capital_authorized",
        "trading_credentials_present",
    ):
        if payload.get(field) is not False:
            raise DeterministicReplayError(f"{field} must be false")
    if payload.get("orders_submitted") != 0:
        raise DeterministicReplayError("orders_submitted must be zero")


def _checksum_lines(root: Path, paths: Sequence[Path]) -> list[str]:
    return [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(paths)]


def build_deterministic_replay_package(
    *,
    materialization_root: Path,
    price_path_root: Path,
    output_root: Path,
    request: ReplayRequest,
) -> dict[str, object]:
    if output_root.exists() or output_root.is_symlink():
        return verify_deterministic_replay_package(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            output_root=output_root,
        )
    materialization_root = materialization_root.resolve(strict=True)
    price_path_root = price_path_root.resolve(strict=True)
    verify_production_materialization(materialization_root)
    verify_replay_price_path_package(
        output_root=price_path_root, materialization_root=materialization_root
    )
    if materialization_root.name != request.dataset_id:
        raise DeterministicReplayError("materialization root identity mismatch")
    dataset_root = materialization_root / DATASET_DIR_NAME
    rows, dataset_manifest = _load_dataset_rows(
        dataset_root, expected_manifest_sha256=request.dataset_manifest_sha256
    )
    trades_by_symbol, price_manifest = _load_price_path(
        price_path_root, expected_manifest_sha256=request.price_path_manifest_sha256
    )
    if price_manifest.get("package_id") != request.price_path_package_id:
        raise DeterministicReplayError("price-path package identity mismatch")
    if price_manifest.get("dataset_manifest_sha256") != request.dataset_manifest_sha256:
        raise DeterministicReplayError("price-path dataset binding mismatch")
    if price_manifest.get("market_manifest_sha256") != request.market_manifest_sha256:
        raise DeterministicReplayError("price-path market binding mismatch")
    if price_manifest.get("label_horizon_ms") != request.policy.label_horizon_ms:
        raise DeterministicReplayError("price-path horizon does not match replay policy")
    if dataset_manifest.get("split_geometry_sha256") != request.split_geometry_sha256:
        raise DeterministicReplayError("dataset split geometry binding mismatch")

    labels = _build_labels(rows=rows, trades_by_symbol=trades_by_symbol, request=request)
    eligible_decision_count = len(labels) // len(request.sides)
    excluded_split_boundary_decision_count = len(rows) - eligible_decision_count
    if eligible_decision_count <= 0:
        raise DeterministicReplayError("no split-boundary-eligible decisions remain")
    output_root = output_root.resolve()
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        partition_records: list[dict[str, object]] = []
        partition_paths: list[Path] = []
        grouped: dict[tuple[str, str], list[CandidateLabel]] = {}
        for label in labels:
            grouped.setdefault((label.split_name, label.symbol), []).append(label)
        for (split_name, symbol), partition_labels in sorted(grouped.items()):
            path = staging / LABELS_DIR_NAME / split_name / f"{symbol}.jsonl"
            _write_jsonl(path, (label.as_json_dict() for label in partition_labels))
            partition_paths.append(path)
            partition_records.append(
                {
                    "split_name": split_name,
                    "symbol": symbol,
                    "relative_path": path.relative_to(staging).as_posix(),
                    "row_count": len(partition_labels),
                    "sha256": sha256_file(path),
                }
            )
        outcome_counts = {
            outcome.value: sum(label.outcome is outcome for label in labels)
            for outcome in LabelOutcome
        }
        manifest_seed: dict[str, object] = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "package_id": request.package_id,
            "request_sha256": request.request_sha256,
            "policy_sha256": request.policy.policy_sha256,
            "dataset_id": request.dataset_id,
            "dataset_manifest_sha256": request.dataset_manifest_sha256,
            "market_manifest_sha256": request.market_manifest_sha256,
            "split_geometry_sha256": request.split_geometry_sha256,
            "price_path_package_id": request.price_path_package_id,
            "price_path_manifest_sha256": request.price_path_manifest_sha256,
            "source_commit_sha": request.source_commit_sha,
            "source_decision_count": len(rows),
            "decision_count": eligible_decision_count,
            "excluded_split_boundary_decision_count": excluded_split_boundary_decision_count,
            "label_count": len(labels),
            "sides": [side.value for side in request.sides],
            "split_windows": request.split_windows,
            "partitions": partition_records,
            "outcome_counts": outcome_counts,
            "protected_holdout_accessed": False,
            "immutable_inputs_mutated": False,
            "model_execution_authorized": False,
            "performance_research_authorized": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "trading_credentials_present": False,
            "orders_submitted": 0,
        }
        manifest = {
            **json.loads(canonical_json(manifest_seed)),
            "manifest_sha256": canonical_sha256(manifest_seed),
        }
        _write_json(staging / REQUEST_NAME, request)
        _write_json(staging / POLICY_NAME, request.policy)
        _write_json(staging / MANIFEST_NAME, manifest)
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "verified",
            "outcome": "accepted",
            "package_id": request.package_id,
            "manifest_sha256": manifest["manifest_sha256"],
            "source_decision_count": len(rows),
            "decision_count": eligible_decision_count,
            "excluded_split_boundary_decision_count": excluded_split_boundary_decision_count,
            "label_count": len(labels),
            "outcome_counts": outcome_counts,
            "replay_shadow_parity_contract": True,
            "protected_holdout_accessed": False,
            "immutable_inputs_mutated": False,
            "model_execution_authorized": False,
            "performance_research_authorized": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "trading_credentials_present": False,
            "orders_submitted": 0,
        }
        _write_json(staging / REPORT_NAME, report)
        paths = [
            staging / REQUEST_NAME,
            staging / POLICY_NAME,
            staging / MANIFEST_NAME,
            staging / REPORT_NAME,
            *partition_paths,
        ]
        _write_new(
            staging / CHECKSUM_INDEX_NAME,
            ("\n".join(_checksum_lines(staging, paths)) + "\n").encode("utf-8"),
        )
        verify_deterministic_replay_package(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            output_root=staging,
        )
        staging.replace(output_root)
        return verify_deterministic_replay_package(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            output_root=output_root,
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_deterministic_replay_package(  # noqa: C901
    *,
    materialization_root: Path,
    price_path_root: Path,
    output_root: Path,
) -> dict[str, object]:
    if output_root.is_symlink() or not output_root.is_dir():
        raise DeterministicReplayError("replay root must be a regular directory")
    request = _request_from_json(_load_json(output_root / REQUEST_NAME, field="request"))
    policy_payload = _load_json(output_root / POLICY_NAME, field="policy")
    if canonical_sha256(policy_payload) != request.policy.policy_sha256:
        raise DeterministicReplayError("policy identity mismatch")
    manifest = _load_json(output_root / MANIFEST_NAME, field="manifest")
    claimed_manifest = manifest.get("manifest_sha256")
    manifest_seed = dict(manifest)
    manifest_seed.pop("manifest_sha256", None)
    if canonical_sha256(manifest_seed) != claimed_manifest:
        raise DeterministicReplayError("manifest self hash mismatch")
    if manifest.get("request_sha256") != request.request_sha256:
        raise DeterministicReplayError("manifest request identity mismatch")
    if manifest.get("policy_sha256") != request.policy.policy_sha256:
        raise DeterministicReplayError("manifest policy identity mismatch")
    _require_safe_authority(manifest)

    materialization_root = materialization_root.resolve(strict=True)
    price_path_root = price_path_root.resolve(strict=True)
    verify_production_materialization(materialization_root)
    verify_replay_price_path_package(
        output_root=price_path_root, materialization_root=materialization_root
    )
    rows, dataset_manifest = _load_dataset_rows(
        materialization_root / DATASET_DIR_NAME,
        expected_manifest_sha256=request.dataset_manifest_sha256,
    )
    trades_by_symbol, price_manifest = _load_price_path(
        price_path_root, expected_manifest_sha256=request.price_path_manifest_sha256
    )
    if dataset_manifest.get("split_geometry_sha256") != request.split_geometry_sha256:
        raise DeterministicReplayError("verified split geometry mismatch")
    if price_manifest.get("package_id") != request.price_path_package_id:
        raise DeterministicReplayError("verified price-path identity mismatch")
    expected_labels = _build_labels(rows=rows, trades_by_symbol=trades_by_symbol, request=request)
    eligible_decision_count = len(expected_labels) // len(request.sides)
    excluded_split_boundary_decision_count = len(rows) - eligible_decision_count
    if eligible_decision_count <= 0:
        raise DeterministicReplayError("no split-boundary-eligible decisions remain")
    expected_by_id = {label.label_id: label.as_json_dict() for label in expected_labels}
    if len(expected_by_id) != len(expected_labels):
        raise DeterministicReplayError("recomputed label identities are not unique")

    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise DeterministicReplayError("manifest partitions are missing")
    observed: dict[str, dict[str, object]] = {}
    checksum_paths = [
        output_root / REQUEST_NAME,
        output_root / POLICY_NAME,
        output_root / MANIFEST_NAME,
        output_root / REPORT_NAME,
    ]
    for raw_partition in partitions:
        if not isinstance(raw_partition, dict):
            raise DeterministicReplayError("manifest partition is invalid")
        path = _safe_member(output_root, str(raw_partition.get("relative_path", "")))
        checksum_paths.append(path)
        if sha256_file(path) != raw_partition.get("sha256"):
            raise DeterministicReplayError("label partition hash mismatch")
        count = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise DeterministicReplayError("label partition contains blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DeterministicReplayError("label row is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise DeterministicReplayError("label row must be an object")
                label_id = _sha256(payload.get("label_id"), field="label_id")
                if label_id in observed:
                    raise DeterministicReplayError("duplicate label identity")
                observed[label_id] = payload
                count += 1
        if count != raw_partition.get("row_count"):
            raise DeterministicReplayError("label partition row count mismatch")
    if observed != expected_by_id:
        raise DeterministicReplayError("serialized labels do not match deterministic replay")
    if manifest.get("source_decision_count", len(rows)) != len(rows):
        raise DeterministicReplayError("manifest source decision count mismatch")
    if manifest.get("decision_count") != eligible_decision_count:
        raise DeterministicReplayError("manifest decision count mismatch")
    if (
        manifest.get(
            "excluded_split_boundary_decision_count",
            excluded_split_boundary_decision_count,
        )
        != excluded_split_boundary_decision_count
    ):
        raise DeterministicReplayError("manifest excluded decision count mismatch")
    if manifest.get("label_count") != len(expected_labels):
        raise DeterministicReplayError("manifest label count mismatch")
    expected_outcomes = {
        outcome.value: sum(label.outcome is outcome for label in expected_labels)
        for outcome in LabelOutcome
    }
    if manifest.get("outcome_counts") != expected_outcomes:
        raise DeterministicReplayError("manifest outcome counts mismatch")
    report = _load_json(output_root / REPORT_NAME, field="verification report")
    if (
        report.get("manifest_sha256") != claimed_manifest
        or report.get("source_decision_count", len(rows)) != len(rows)
        or report.get("decision_count") != eligible_decision_count
        or report.get(
            "excluded_split_boundary_decision_count",
            excluded_split_boundary_decision_count,
        )
        != excluded_split_boundary_decision_count
        or report.get("label_count") != len(expected_labels)
        or report.get("outcome") != "accepted"
    ):
        raise DeterministicReplayError("verification report mismatch")
    _require_safe_authority(report)

    checksum_path = output_root / CHECKSUM_INDEX_NAME
    if checksum_path.is_symlink() or not checksum_path.is_file():
        raise DeterministicReplayError("checksum index must be a regular file")
    expected_lines = _checksum_lines(output_root, checksum_paths)
    actual_lines = checksum_path.read_text(encoding="utf-8").splitlines()
    if actual_lines != expected_lines:
        raise DeterministicReplayError("artifact checksum index mismatch")
    expected_names = {path.relative_to(output_root).as_posix() for path in checksum_paths} | {
        CHECKSUM_INDEX_NAME
    }
    actual_names = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    if actual_names != expected_names:
        raise DeterministicReplayError("replay package contains unexpected files")
    return report
