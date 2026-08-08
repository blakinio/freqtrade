from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.baseline_strategy import EvaluationCase
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    LiquidationFeatureVector,
    SourceLiquidationAggregate,
    TradeDirection,
)
from ai_platform.wickhunter.dataset import DatasetRow
from ai_platform.wickhunter.deterministic_replay import (
    LABELS_DIR_NAME,
    MANIFEST_NAME,
    CandidateLabel,
    LabelOutcome,
    verify_deterministic_replay_package,
)
from ai_platform.wickhunter.production_dataset_materialization import (
    DATASET_DIR_NAME,
    verify_production_materialization,
)


EVALUATION_DATASET_SCHEMA_VERSION = "wickhunter-production-evaluation-dataset-v1"


class ProductionEvaluationError(RuntimeError):
    """Raised when production evaluation inputs cannot be joined safely."""


def _load_object(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ProductionEvaluationError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionEvaluationError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise ProductionEvaluationError(f"{field} must contain an object")
    return payload


def _safe_member(root: Path, relative_path: object, *, field: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ProductionEvaluationError(f"{field} path is missing")
    relative = Path(relative_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ProductionEvaluationError(f"{field} path must remain relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ProductionEvaluationError(f"{field} path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise ProductionEvaluationError(f"{field} path escapes its root") from exc
    if not current.is_file():
        raise ProductionEvaluationError(f"{field} path is not a regular file")
    return current


def _text(value: object, *, field: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ProductionEvaluationError(f"{field} must be non-empty")
    return normalized


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ProductionEvaluationError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ProductionEvaluationError(f"{field} must be an integer") from exc
    if parsed < minimum:
        raise ProductionEvaluationError(f"{field} must be >= {minimum}")
    return parsed


def _optional_integer(value: object, *, field: str, minimum: int = 0) -> int | None:
    if value is None:
        return None
    return _integer(value, field=field, minimum=minimum)


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ProductionEvaluationError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProductionEvaluationError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise ProductionEvaluationError(f"{field} must be finite")
    return parsed


def _optional_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, field=field)


def _tuple_of_text(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ProductionEvaluationError(f"{field} must be a list")
    return tuple(_text(item, field=field) for item in value)


def _available_metric(payload: object) -> AvailableMetric:
    if not isinstance(payload, Mapping):
        raise ProductionEvaluationError("market metric must be an object")
    try:
        return AvailableMetric(
            name=_text(payload["name"], field="metric name"),
            value=_decimal(payload["value"], field="metric value"),
            available_at_ms=_integer(
                payload["available_at_ms"], field="metric available_at_ms", minimum=1
            ),
            source=_text(payload["source"], field="metric source"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProductionEvaluationError):
            raise
        raise ProductionEvaluationError("invalid market metric") from exc


def _source_aggregate(payload: object) -> SourceLiquidationAggregate:
    if not isinstance(payload, Mapping):
        raise ProductionEvaluationError("source aggregate must be an object")
    try:
        return SourceLiquidationAggregate(
            source=_text(payload["source"], field="aggregate source"),
            event_count=_integer(payload["event_count"], field="aggregate event_count", minimum=1),
            total_notional_usd=_decimal(
                payload["total_notional_usd"], field="aggregate total_notional_usd"
            ),
            liquidated_long_notional_usd=_decimal(
                payload["liquidated_long_notional_usd"],
                field="aggregate liquidated_long_notional_usd",
            ),
            liquidated_short_notional_usd=_decimal(
                payload["liquidated_short_notional_usd"],
                field="aggregate liquidated_short_notional_usd",
            ),
            maximum_event_notional_usd=_decimal(
                payload["maximum_event_notional_usd"],
                field="aggregate maximum_event_notional_usd",
            ),
            maximum_ingest_latency_ms=_integer(
                payload["maximum_ingest_latency_ms"],
                field="aggregate maximum_ingest_latency_ms",
            ),
            latest_received_at_ms=_integer(
                payload["latest_received_at_ms"],
                field="aggregate latest_received_at_ms",
                minimum=1,
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProductionEvaluationError):
            raise
        raise ProductionEvaluationError("invalid source aggregate") from exc


def _feature(payload: object) -> LiquidationFeatureVector:
    if not isinstance(payload, Mapping):
        raise ProductionEvaluationError("feature must be an object")
    raw_aggregates = payload.get("source_aggregates")
    raw_metrics = payload.get("market_metrics")
    if not isinstance(raw_aggregates, list) or not isinstance(raw_metrics, list):
        raise ProductionEvaluationError("feature aggregate and metric lists are required")
    try:
        return LiquidationFeatureVector(
            feature_schema_version=_text(
                payload["feature_schema_version"], field="feature_schema_version"
            ),
            symbol=_text(payload["symbol"], field="feature symbol"),
            decision_timestamp_ms=_integer(
                payload["decision_timestamp_ms"], field="feature decision timestamp", minimum=1
            ),
            decision_price=_decimal(payload["decision_price"], field="feature decision price"),
            event_count=_integer(payload["event_count"], field="feature event_count", minimum=1),
            total_notional_usd=_decimal(
                payload["total_notional_usd"], field="feature total_notional_usd"
            ),
            liquidated_long_notional_usd=_decimal(
                payload["liquidated_long_notional_usd"],
                field="feature liquidated_long_notional_usd",
            ),
            liquidated_short_notional_usd=_decimal(
                payload["liquidated_short_notional_usd"],
                field="feature liquidated_short_notional_usd",
            ),
            long_short_imbalance=_decimal(
                payload["long_short_imbalance"], field="feature long_short_imbalance"
            ),
            maximum_event_notional_usd=_decimal(
                payload["maximum_event_notional_usd"],
                field="feature maximum_event_notional_usd",
            ),
            maximum_event_percentile=_decimal(
                payload["maximum_event_percentile"],
                field="feature maximum_event_percentile",
            ),
            maximum_event_zscore=_decimal(
                payload["maximum_event_zscore"], field="feature maximum_event_zscore"
            ),
            liquidation_burst_intensity=_decimal(
                payload["liquidation_burst_intensity"],
                field="feature liquidation_burst_intensity",
            ),
            time_since_previous_burst_ms=_optional_integer(
                payload.get("time_since_previous_burst_ms"),
                field="feature time_since_previous_burst_ms",
            ),
            ingest_latency_ms=_integer(
                payload["ingest_latency_ms"], field="feature ingest_latency_ms"
            ),
            source_coverage_ratio=_decimal(
                payload["source_coverage_ratio"], field="feature source_coverage_ratio"
            ),
            source_aggregates=tuple(_source_aggregate(item) for item in raw_aggregates),
            market_metrics=tuple(_available_metric(item) for item in raw_metrics),
            feature_available_at_ms=_integer(
                payload["feature_available_at_ms"],
                field="feature available_at_ms",
                minimum=1,
            ),
            input_event_ids=_tuple_of_text(payload["input_event_ids"], field="input_event_ids"),
            history_id=_text(payload["history_id"], field="history_id"),
            history_sha256=_text(payload["history_sha256"], field="history_sha256"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProductionEvaluationError):
            raise
        raise ProductionEvaluationError("invalid liquidation feature") from exc


def _dataset_row(payload: Mapping[str, object]) -> DatasetRow:
    raw_row_sha256 = _text(payload.get("row_sha256"), field="row_sha256")
    try:
        row = DatasetRow(
            schema_version=_text(payload["schema_version"], field="dataset schema_version"),
            dataset_version=_text(payload["dataset_version"], field="dataset_version"),
            split_name=_text(payload["split_name"], field="split_name"),
            symbol=_text(payload["symbol"], field="symbol"),
            decision_timestamp_ms=_integer(
                payload["decision_timestamp_ms"], field="decision_timestamp_ms", minimum=1
            ),
            feature_available_at_ms=_integer(
                payload["feature_available_at_ms"], field="feature_available_at_ms", minimum=1
            ),
            feature=_feature(payload["feature"]),
            universe_snapshot_sha256=_text(
                payload["universe_snapshot_sha256"], field="universe_snapshot_sha256"
            ),
            market_context_sha256=_text(
                payload["market_context_sha256"], field="market_context_sha256"
            ),
            source_selection_sha256s=_tuple_of_text(
                payload["source_selection_sha256s"], field="source_selection_sha256s"
            ),
            historical_provider_ids=_tuple_of_text(
                payload["historical_provider_ids"], field="historical_provider_ids"
            ),
            import_run_ids=_tuple_of_text(payload["import_run_ids"], field="import_run_ids"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProductionEvaluationError):
            raise
        raise ProductionEvaluationError("invalid dataset row") from exc
    if row.row_sha256 != raw_row_sha256:
        raise ProductionEvaluationError("dataset row identity mismatch")
    return row


def _label(payload: Mapping[str, object]) -> CandidateLabel:
    try:
        label = CandidateLabel(
            schema_version=_text(payload["schema_version"], field="label schema_version"),
            label_id=_text(payload["label_id"], field="label_id"),
            policy_version=_text(payload["policy_version"], field="policy_version"),
            policy_sha256=_text(payload["policy_sha256"], field="policy_sha256"),
            dataset_id=_text(payload["dataset_id"], field="dataset_id"),
            dataset_manifest_sha256=_text(
                payload["dataset_manifest_sha256"], field="dataset_manifest_sha256"
            ),
            market_manifest_sha256=_text(
                payload["market_manifest_sha256"], field="market_manifest_sha256"
            ),
            split_geometry_sha256=_text(
                payload["split_geometry_sha256"], field="split_geometry_sha256"
            ),
            dataset_row_sha256=_text(payload["dataset_row_sha256"], field="dataset_row_sha256"),
            price_path_manifest_sha256=_text(
                payload["price_path_manifest_sha256"], field="price_path_manifest_sha256"
            ),
            source_commit_sha=_text(payload["source_commit_sha"], field="source_commit_sha"),
            split_name=_text(payload["split_name"], field="split_name"),
            symbol=_text(payload["symbol"], field="symbol"),
            side=TradeDirection(_text(payload["side"], field="side")),
            decision_timestamp_ms=_integer(
                payload["decision_timestamp_ms"], field="decision_timestamp_ms", minimum=1
            ),
            label_end_ms=_integer(payload["label_end_ms"], field="label_end_ms", minimum=1),
            outcome=LabelOutcome(_text(payload["outcome"], field="outcome")),
            entry_timestamp_ms=_optional_integer(
                payload.get("entry_timestamp_ms"), field="entry_timestamp_ms", minimum=1
            ),
            entry_aggregate_trade_id=_optional_integer(
                payload.get("entry_aggregate_trade_id"), field="entry_aggregate_trade_id"
            ),
            entry_trade_sha256=(
                None
                if payload.get("entry_trade_sha256") is None
                else _text(payload["entry_trade_sha256"], field="entry_trade_sha256")
            ),
            raw_entry_price=_optional_decimal(
                payload.get("raw_entry_price"), field="raw_entry_price"
            ),
            executed_entry_price=_optional_decimal(
                payload.get("executed_entry_price"), field="executed_entry_price"
            ),
            exit_timestamp_ms=_optional_integer(
                payload.get("exit_timestamp_ms"), field="exit_timestamp_ms", minimum=1
            ),
            exit_aggregate_trade_id=_optional_integer(
                payload.get("exit_aggregate_trade_id"), field="exit_aggregate_trade_id"
            ),
            exit_trade_sha256=(
                None
                if payload.get("exit_trade_sha256") is None
                else _text(payload["exit_trade_sha256"], field="exit_trade_sha256")
            ),
            raw_exit_price=_optional_decimal(payload.get("raw_exit_price"), field="raw_exit_price"),
            executed_exit_price=_optional_decimal(
                payload.get("executed_exit_price"), field="executed_exit_price"
            ),
            gross_return_ratio=_optional_decimal(
                payload.get("gross_return_ratio"), field="gross_return_ratio"
            ),
            net_return_ratio=_optional_decimal(
                payload.get("net_return_ratio"), field="net_return_ratio"
            ),
            maximum_favorable_excursion_ratio=_optional_decimal(
                payload.get("maximum_favorable_excursion_ratio"),
                field="maximum_favorable_excursion_ratio",
            ),
            maximum_adverse_excursion_ratio=_optional_decimal(
                payload.get("maximum_adverse_excursion_ratio"),
                field="maximum_adverse_excursion_ratio",
            ),
            time_to_outcome_ms=_optional_integer(
                payload.get("time_to_outcome_ms"), field="time_to_outcome_ms"
            ),
            fee_ratio=_decimal(payload["fee_ratio"], field="fee_ratio"),
            slippage_ratio=_decimal(payload["slippage_ratio"], field="slippage_ratio"),
            take_profit_ratio=_decimal(payload["take_profit_ratio"], field="take_profit_ratio"),
            stop_loss_ratio=_decimal(payload["stop_loss_ratio"], field="stop_loss_ratio"),
            entry_delay_ms=_integer(payload["entry_delay_ms"], field="entry_delay_ms"),
            maximum_entry_delay_ms=_integer(
                payload["maximum_entry_delay_ms"], field="maximum_entry_delay_ms"
            ),
            protected_holdout_accessed=payload.get("protected_holdout_accessed") is True,
            immutable_inputs_mutated=payload.get("immutable_inputs_mutated") is True,
            model_execution_authorized=payload.get("model_execution_authorized") is True,
            performance_research_authorized=payload.get("performance_research_authorized") is True,
            execution_enabled=payload.get("execution_enabled") is True,
            live_capital_authorized=payload.get("live_capital_authorized") is True,
            trading_credentials_present=payload.get("trading_credentials_present") is True,
            orders_submitted=_integer(
                payload.get("orders_submitted", -1), field="orders_submitted"
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProductionEvaluationError):
            raise
        raise ProductionEvaluationError("invalid replay label") from exc
    if payload.get("label_sha256") != label.label_sha256:
        raise ProductionEvaluationError("replay label identity mismatch")
    return label


def _load_dataset_rows(dataset_root: Path, manifest: Mapping[str, object]) -> dict[str, DatasetRow]:
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ProductionEvaluationError("dataset partitions are missing")
    rows: dict[str, DatasetRow] = {}
    for raw_partition in partitions:
        if not isinstance(raw_partition, Mapping):
            raise ProductionEvaluationError("dataset partition is invalid")
        path = _safe_member(
            dataset_root,
            raw_partition.get("relative_path"),
            field="dataset partition",
        )
        if sha256_file(path) != raw_partition.get("sha256"):
            raise ProductionEvaluationError("dataset partition hash mismatch")
        observed_count = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise ProductionEvaluationError("dataset partition contains a blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProductionEvaluationError("dataset row is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise ProductionEvaluationError("dataset row must be an object")
                row = _dataset_row(payload)
                if row.row_sha256 in rows:
                    raise ProductionEvaluationError("duplicate dataset row identity")
                rows[row.row_sha256] = row
                observed_count += 1
        if observed_count != raw_partition.get("row_count"):
            raise ProductionEvaluationError("dataset partition row count mismatch")
    if len(rows) != manifest.get("total_rows"):
        raise ProductionEvaluationError("dataset total row count mismatch")
    return rows


def _load_labels(  # noqa: C901
    replay_root: Path,
    manifest: Mapping[str, object],
) -> dict[str, tuple[CandidateLabel, ...]]:
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ProductionEvaluationError("replay partitions are missing")
    labels_by_row: defaultdict[str, list[CandidateLabel]] = defaultdict(list)
    label_ids: set[str] = set()
    observed_total = 0
    for raw_partition in partitions:
        if not isinstance(raw_partition, Mapping):
            raise ProductionEvaluationError("replay partition is invalid")
        path = _safe_member(
            replay_root,
            raw_partition.get("relative_path"),
            field="replay partition",
        )
        try:
            path.relative_to(replay_root / LABELS_DIR_NAME)
        except ValueError as exc:
            raise ProductionEvaluationError("replay partition is outside labels root") from exc
        if sha256_file(path) != raw_partition.get("sha256"):
            raise ProductionEvaluationError("replay partition hash mismatch")
        observed_count = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise ProductionEvaluationError("replay partition contains a blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProductionEvaluationError("replay label is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise ProductionEvaluationError("replay label must be an object")
                label = _label(payload)
                if label.label_id in label_ids:
                    raise ProductionEvaluationError("duplicate replay label identity")
                label_ids.add(label.label_id)
                labels_by_row[label.dataset_row_sha256].append(label)
                observed_count += 1
                observed_total += 1
        if observed_count != raw_partition.get("row_count"):
            raise ProductionEvaluationError("replay partition row count mismatch")
    if observed_total != manifest.get("label_count"):
        raise ProductionEvaluationError("replay total label count mismatch")
    return {
        row_sha: tuple(sorted(labels, key=lambda item: item.side.value))
        for row_sha, labels in labels_by_row.items()
    }


@dataclass(frozen=True, slots=True)
class VerifiedEvaluationDataset:
    schema_version: str
    dataset_id: str
    dataset_manifest_sha256: str
    replay_package_id: str
    replay_manifest_sha256: str
    replay_policy_sha256: str
    source_commit_sha: str
    cases: tuple[EvaluationCase, ...]
    protected_holdout_accessed: bool
    immutable_inputs_mutated: bool
    model_execution_authorized: bool
    performance_research_authorized: bool
    execution_enabled: bool
    live_capital_authorized: bool
    trading_credentials_present: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != EVALUATION_DATASET_SCHEMA_VERSION:
            raise ProductionEvaluationError(
                f"schema_version must be {EVALUATION_DATASET_SCHEMA_VERSION}"
            )
        if not self.cases:
            raise ProductionEvaluationError("evaluation dataset requires cases")
        case_ids = tuple(case.case_sha256 for case in self.cases)
        if len(case_ids) != len(set(case_ids)):
            raise ProductionEvaluationError("evaluation cases must be unique")
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
            raise ProductionEvaluationError("evaluation dataset contains unsafe authority")

    @property
    def evaluation_sha256(self) -> str:
        return canonical_sha256(
            {
                "schema_version": self.schema_version,
                "dataset_id": self.dataset_id,
                "dataset_manifest_sha256": self.dataset_manifest_sha256,
                "replay_package_id": self.replay_package_id,
                "replay_manifest_sha256": self.replay_manifest_sha256,
                "replay_policy_sha256": self.replay_policy_sha256,
                "source_commit_sha": self.source_commit_sha,
                "case_sha256s": tuple(case.case_sha256 for case in self.cases),
                "protected_holdout_accessed": False,
                "immutable_inputs_mutated": False,
                "model_execution_authorized": False,
                "performance_research_authorized": False,
                "execution_enabled": False,
                "live_capital_authorized": False,
                "trading_credentials_present": False,
                "orders_submitted": 0,
            }
        )


def load_verified_evaluation_dataset(
    *,
    materialization_root: Path,
    price_path_root: Path,
    replay_root: Path,
) -> VerifiedEvaluationDataset:
    materialization_root = materialization_root.resolve(strict=True)
    price_path_root = price_path_root.resolve(strict=True)
    replay_root = replay_root.resolve(strict=True)

    dataset_verification = verify_production_materialization(materialization_root)
    replay_verification = verify_deterministic_replay_package(
        materialization_root=materialization_root,
        price_path_root=price_path_root,
        output_root=replay_root,
    )
    if dataset_verification.get("outcome") != "accepted":
        raise ProductionEvaluationError("production dataset is not accepted")
    if replay_verification.get("outcome") != "accepted":
        raise ProductionEvaluationError("deterministic replay is not accepted")

    dataset_root = materialization_root / DATASET_DIR_NAME
    dataset_manifest = _load_object(dataset_root / MANIFEST_NAME, field="dataset manifest")
    replay_manifest = _load_object(replay_root / MANIFEST_NAME, field="replay manifest")
    rows = _load_dataset_rows(dataset_root, dataset_manifest)
    labels_by_row = _load_labels(replay_root, replay_manifest)

    if not set(labels_by_row).issubset(rows):
        raise ProductionEvaluationError("replay labels reference unknown dataset rows")
    cases = tuple(
        sorted(
            (
                EvaluationCase(
                    dataset_row_sha256=row_sha,
                    split_name=row.split_name,
                    feature=row.feature,
                    labels=labels_by_row[row_sha],
                )
                for row_sha, row in rows.items()
                if row_sha in labels_by_row
            ),
            key=lambda case: (
                case.split_name,
                case.feature.symbol,
                case.feature.decision_timestamp_ms,
                case.dataset_row_sha256,
            ),
        )
    )
    if replay_manifest.get("source_decision_count", len(rows)) != len(rows):
        raise ProductionEvaluationError("evaluation source decision count does not match dataset")
    if replay_manifest.get("excluded_split_boundary_decision_count", len(rows) - len(cases)) != len(
        rows
    ) - len(cases):
        raise ProductionEvaluationError("evaluation excluded decision count mismatch")
    if len(cases) != replay_manifest.get("decision_count"):
        raise ProductionEvaluationError("evaluation case count does not match replay decisions")
    if replay_manifest.get("label_count") != len(cases) * 2:
        raise ProductionEvaluationError("evaluation dataset requires two labels per case")
    if replay_manifest.get("dataset_id") != materialization_root.name:
        raise ProductionEvaluationError("replay dataset root binding mismatch")
    if replay_manifest.get("dataset_manifest_sha256") != dataset_manifest.get("manifest_sha256"):
        raise ProductionEvaluationError("replay dataset manifest binding mismatch")

    return VerifiedEvaluationDataset(
        schema_version=EVALUATION_DATASET_SCHEMA_VERSION,
        dataset_id=_text(replay_manifest.get("dataset_id"), field="dataset_id"),
        dataset_manifest_sha256=_text(
            replay_manifest.get("dataset_manifest_sha256"), field="dataset_manifest_sha256"
        ),
        replay_package_id=_text(replay_manifest.get("package_id"), field="replay_package_id"),
        replay_manifest_sha256=_text(
            replay_manifest.get("manifest_sha256"), field="replay_manifest_sha256"
        ),
        replay_policy_sha256=_text(
            replay_manifest.get("policy_sha256"), field="replay_policy_sha256"
        ),
        source_commit_sha=_text(
            replay_manifest.get("source_commit_sha"), field="source_commit_sha"
        ),
        cases=cases,
        protected_holdout_accessed=False,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )
