from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.contracts import validate_sha256
from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import AvailableMetric, MarketContextSnapshot
from ai_platform.wickhunter.dataset import (
    DatasetSplitGeometry,
    DatasetSplitWindow,
    WickHunterDatasetArtifactSet,
    WickHunterDatasetBuildRequest,
    build_wickhunter_dataset,
    load_accepted_import,
)
from ai_platform.wickhunter.features import REQUIRED_MARKET_METRICS
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


MATERIALIZATION_REQUEST_SCHEMA = "wickhunter-dataset-materialization-request-v1"
MATERIALIZATION_REPORT_SCHEMA = "wickhunter-dataset-materialization-report-v1"
MARKET_CONTEXT_ROW_SCHEMA = "wickhunter-market-context-row-v1"
UNIVERSE_HISTORY_ROW_SCHEMA = "wickhunter-universe-history-row-v1"


def _require_text(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    return normalized


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def _false_flag(payload: dict[str, Any], field: str) -> bool:
    value = payload.get(field)
    if value is not False:
        raise ValueError(f"{field} must be false")
    return False


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} must be a decimal-compatible value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def _relative_path(value: str, *, field: str) -> str:
    normalized = _require_text(value, field=field)
    path = Path(normalized)
    if path.is_absolute() or normalized == "." or ".." in path.parts:
        raise ValueError(f"{field} must stay within the package root")
    return path.as_posix()


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path}")
    return payload


def _assert_root(root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("package_root must be a regular directory")
    return root.resolve()


def _resolve_member(root: Path, relative_path: str) -> Path:
    root = _assert_root(root)
    relative = Path(relative_path)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"package member must not traverse a symlink: {relative_path}")
    resolved = current.resolve()
    if resolved == root or root not in resolved.parents:
        raise ValueError(f"package member escapes package root: {relative_path}")
    return resolved


def _require_regular_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required input must be a regular file: {path}")


@dataclass(frozen=True, slots=True)
class InputFileReference:
    relative_path: str
    sha256: str

    def __post_init__(self) -> None:
        _relative_path(self.relative_path, field="relative_path")
        validate_sha256(self.sha256, field="sha256")


@dataclass(frozen=True, slots=True)
class AcceptedImportReference:
    relative_path: str
    import_run_id: str
    selection_sha256: str

    def __post_init__(self) -> None:
        _relative_path(self.relative_path, field="accepted_import.relative_path")
        _require_text(self.import_run_id, field="accepted_import.import_run_id")
        validate_sha256(self.selection_sha256, field="accepted_import.selection_sha256")


@dataclass(frozen=True, slots=True)
class RealDatasetMaterializationRequest:
    schema_version: str
    accepted_imports: tuple[AcceptedImportReference, ...]
    market_context: InputFileReference
    universe_history: InputFileReference
    build_request: WickHunterDatasetBuildRequest
    trading_credentials_present: bool
    trading_authorized: bool
    execution_enabled: bool
    model_execution_authorized: bool
    live_capital_authorized: bool

    def __post_init__(self) -> None:
        if self.schema_version != MATERIALIZATION_REQUEST_SCHEMA:
            raise ValueError(f"schema_version must be {MATERIALIZATION_REQUEST_SCHEMA}")
        if not self.accepted_imports:
            raise ValueError("at least one accepted import reference is required")
        paths = [reference.relative_path for reference in self.accepted_imports]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("accepted import references must be unique and path-sorted")
        if any(
            (
                self.trading_credentials_present,
                self.trading_authorized,
                self.execution_enabled,
                self.model_execution_authorized,
                self.live_capital_authorized,
            )
        ):
            raise ValueError("WH-01 materialization must not authorize credentials or execution")

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class MaterializationPreflightReport:
    status: str
    request_sha256: str
    missing_paths: tuple[str, ...]
    accepted_import_selection_sha256s: tuple[str, ...]
    market_context_sha256: str
    universe_history_sha256: str
    market_snapshot_count: int
    universe_snapshot_count: int
    model_execution_authorized: bool = False
    trading_authorized: bool = False
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"ready", "blocked"}:
            raise ValueError("preflight status must be ready or blocked")
        validate_sha256(self.request_sha256, field="request_sha256")
        for digest in self.accepted_import_selection_sha256s:
            validate_sha256(digest, field="accepted_import_selection_sha256")
        for digest, field in (
            (self.market_context_sha256, "market_context_sha256"),
            (self.universe_history_sha256, "universe_history_sha256"),
        ):
            if digest:
                validate_sha256(digest, field=field)
        if self.market_snapshot_count < 0 or self.universe_snapshot_count < 0:
            raise ValueError("snapshot counts must be >= 0")
        if self.status == "ready" and self.missing_paths:
            raise ValueError("ready preflight must not contain missing paths")
        if self.status == "blocked" and not self.missing_paths:
            raise ValueError("blocked preflight must identify missing paths")
        if (
            self.model_execution_authorized
            or self.trading_authorized
            or self.live_capital_authorized
        ):
            raise ValueError("preflight report must keep authority false")

    def as_json_dict(self) -> dict[str, Any]:
        payload = json.loads(canonical_json(self))
        payload["schema_version"] = MATERIALIZATION_REPORT_SCHEMA
        payload["report_type"] = "preflight"
        return payload


@dataclass(frozen=True, slots=True)
class MaterializationResult:
    request_sha256: str
    output_root: str
    manifest_sha256: str
    manifest_file_sha256: str
    sources_sha256: str
    universe_history_sha256: str
    total_rows: int
    partition_count: int
    model_execution_authorized: bool = False
    trading_authorized: bool = False
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        for digest, field in (
            (self.request_sha256, "request_sha256"),
            (self.manifest_sha256, "manifest_sha256"),
            (self.manifest_file_sha256, "manifest_file_sha256"),
            (self.sources_sha256, "sources_sha256"),
            (self.universe_history_sha256, "universe_history_sha256"),
        ):
            validate_sha256(digest, field=field)
        if self.total_rows <= 0 or self.partition_count <= 0:
            raise ValueError("materialization result must contain rows and partitions")
        if (
            self.model_execution_authorized
            or self.trading_authorized
            or self.live_capital_authorized
        ):
            raise ValueError("materialization result must keep authority false")

    def as_json_dict(self) -> dict[str, Any]:
        payload = json.loads(canonical_json(self))
        payload["schema_version"] = MATERIALIZATION_REPORT_SCHEMA
        payload["report_type"] = "materialization"
        payload["status"] = "success"
        return payload


@dataclass(frozen=True, slots=True)
class _ValidatedInputs:
    accepted_roots: tuple[Path, ...]
    selection_sha256s: tuple[str, ...]
    market_snapshots: tuple[MarketContextSnapshot, ...]
    universe_snapshots: tuple[DynamicUniverseSnapshot, ...]


def _parse_split_geometry(payload: object) -> DatasetSplitGeometry:
    if not isinstance(payload, dict):
        raise ValueError("dataset.split_geometry must contain an object")
    windows_payload = payload.get("windows")
    if not isinstance(windows_payload, list):
        raise ValueError("dataset.split_geometry.windows must contain a list")
    windows: list[DatasetSplitWindow] = []
    for index, item in enumerate(windows_payload):
        if not isinstance(item, dict):
            raise ValueError(f"split window {index} must contain an object")
        windows.append(
            DatasetSplitWindow(
                name=_require_text(str(item.get("name", "")), field=f"windows[{index}].name"),
                start_ms=_integer(
                    item.get("start_ms"),
                    field=f"windows[{index}].start_ms",
                    minimum=1,
                ),
                end_ms=_integer(item.get("end_ms"), field=f"windows[{index}].end_ms", minimum=1),
            )
        )
    return DatasetSplitGeometry(
        geometry_version=_require_text(
            str(payload.get("geometry_version", "")), field="split_geometry.geometry_version"
        ),
        windows=tuple(windows),
        label_horizon_ms=_integer(
            payload.get("label_horizon_ms"), field="split_geometry.label_horizon_ms"
        ),
        embargo_ms=_integer(payload.get("embargo_ms"), field="split_geometry.embargo_ms"),
        protected_holdout_start_ms=_integer(
            payload.get("protected_holdout_start_ms"),
            field="split_geometry.protected_holdout_start_ms",
            minimum=1,
        ),
    )


def _parse_input_file(payload: object, *, field: str) -> InputFileReference:
    if not isinstance(payload, dict):
        raise ValueError(f"{field} must contain an object")
    return InputFileReference(
        relative_path=_relative_path(
            str(payload.get("relative_path", "")), field=f"{field}.relative_path"
        ),
        sha256=str(payload.get("sha256", "")),
    )


def load_materialization_request(path: Path) -> RealDatasetMaterializationRequest:
    _require_regular_file(path)
    payload = _load_json_object(path)
    accepted_payload = payload.get("accepted_imports")
    if not isinstance(accepted_payload, list):
        raise ValueError("accepted_imports must contain a list")
    accepted: list[AcceptedImportReference] = []
    for index, item in enumerate(accepted_payload):
        if not isinstance(item, dict):
            raise ValueError(f"accepted_imports[{index}] must contain an object")
        accepted.append(
            AcceptedImportReference(
                relative_path=_relative_path(
                    str(item.get("relative_path", "")),
                    field=f"accepted_imports[{index}].relative_path",
                ),
                import_run_id=str(item.get("import_run_id", "")),
                selection_sha256=str(item.get("selection_sha256", "")),
            )
        )
    dataset = payload.get("dataset")
    if not isinstance(dataset, dict):
        raise ValueError("dataset must contain an object")
    build_request = WickHunterDatasetBuildRequest(
        dataset_version=_require_text(
            str(dataset.get("dataset_version", "")), field="dataset.dataset_version"
        ),
        code_sha=str(dataset.get("code_sha", "")),
        burst_window_ms=_integer(
            dataset.get("burst_window_ms"), field="dataset.burst_window_ms", minimum=1
        ),
        partition_span_ms=_integer(
            dataset.get("partition_span_ms"), field="dataset.partition_span_ms", minimum=1
        ),
        minimum_history_events=_integer(
            dataset.get("minimum_history_events"),
            field="dataset.minimum_history_events",
            minimum=1,
        ),
        maximum_source_age_ms=_integer(
            dataset.get("maximum_source_age_ms"),
            field="dataset.maximum_source_age_ms",
            minimum=1,
        ),
        split_geometry=_parse_split_geometry(dataset.get("split_geometry")),
    )
    return RealDatasetMaterializationRequest(
        schema_version=str(payload.get("schema_version", "")),
        accepted_imports=tuple(accepted),
        market_context=_parse_input_file(payload.get("market_context"), field="market_context"),
        universe_history=_parse_input_file(
            payload.get("universe_history"), field="universe_history"
        ),
        build_request=build_request,
        trading_credentials_present=_false_flag(payload, "trading_credentials_present"),
        trading_authorized=_false_flag(payload, "trading_authorized"),
        execution_enabled=_false_flag(payload, "execution_enabled"),
        model_execution_authorized=_false_flag(payload, "model_execution_authorized"),
        live_capital_authorized=_false_flag(payload, "live_capital_authorized"),
    )


def _parse_market_snapshot(payload: object, *, line_number: int) -> MarketContextSnapshot:
    if not isinstance(payload, dict):
        raise ValueError(f"market snapshot line {line_number} must contain an object")
    metrics_payload = payload.get("metrics")
    if not isinstance(metrics_payload, list):
        raise ValueError(f"market snapshot metrics must contain a list at line {line_number}")
    metrics: list[AvailableMetric] = []
    for index, metric_payload in enumerate(metrics_payload):
        if not isinstance(metric_payload, dict):
            raise ValueError(f"market metric {index} at line {line_number} must be an object")
        metrics.append(
            AvailableMetric(
                name=str(metric_payload.get("name", "")),
                value=_decimal(
                    metric_payload.get("value"),
                    field=f"market[{line_number}].metrics[{index}].value",
                ),
                available_at_ms=_integer(
                    metric_payload.get("available_at_ms"),
                    field=f"market[{line_number}].metrics[{index}].available_at_ms",
                    minimum=1,
                ),
                source=str(metric_payload.get("source", "")),
            )
        )
    snapshot = MarketContextSnapshot(
        symbol=str(payload.get("symbol", "")),
        decision_timestamp_ms=_integer(
            payload.get("decision_timestamp_ms"),
            field=f"market[{line_number}].decision_timestamp_ms",
            minimum=1,
        ),
        decision_price=_decimal(
            payload.get("decision_price"), field=f"market[{line_number}].decision_price"
        ),
        completed_candle_close_ms=_integer(
            payload.get("completed_candle_close_ms"),
            field=f"market[{line_number}].completed_candle_close_ms",
            minimum=1,
        ),
        metrics=tuple(metrics),
    )
    metric_names = {metric.name for metric in snapshot.metrics}
    missing_metrics = sorted(set(REQUIRED_MARKET_METRICS) - metric_names)
    if missing_metrics:
        raise ValueError(
            f"market snapshot at line {line_number} is missing metrics: {missing_metrics}"
        )
    for metric in snapshot.metrics:
        if metric.available_at_ms > snapshot.decision_timestamp_ms:
            raise ValueError(f"market metric is unavailable at decision time: {metric.name}")
        if (
            metric.source.startswith("completed_candle")
            and metric.available_at_ms < snapshot.completed_candle_close_ms
        ):
            raise ValueError(f"completed-candle metric is available before close: {metric.name}")
    return snapshot


def _parse_market_context(path: Path) -> tuple[MarketContextSnapshot, ...]:
    snapshots: list[MarketContextSnapshot] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank market-context line: {line_number}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid market-context JSON at line {line_number}") from exc
            if not isinstance(row, dict) or row.get("schema_version") != MARKET_CONTEXT_ROW_SCHEMA:
                raise ValueError(f"unsupported market-context row at line {line_number}")
            snapshot = _parse_market_snapshot(row.get("snapshot"), line_number=line_number)
            if row.get("snapshot_sha256") != canonical_sha256(snapshot):
                raise ValueError(f"market-context snapshot hash mismatch at line {line_number}")
            snapshots.append(snapshot)
    if not snapshots:
        raise ValueError("market-context file must contain at least one snapshot")
    ordered = sorted(
        snapshots,
        key=lambda snapshot: (snapshot.decision_timestamp_ms, snapshot.symbol.upper()),
    )
    if snapshots != ordered:
        raise ValueError("market-context snapshots must be in deterministic decision order")
    keys = [(item.decision_timestamp_ms, item.symbol.upper()) for item in snapshots]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate market-context decision keys are not allowed")
    return tuple(snapshots)


def _parse_universe_snapshot(payload: object, *, line_number: int) -> DynamicUniverseSnapshot:
    if not isinstance(payload, dict):
        raise ValueError(f"universe snapshot line {line_number} must contain an object")
    decisions_payload = payload.get("decisions")
    if not isinstance(decisions_payload, list):
        raise ValueError(f"universe decisions must contain a list at line {line_number}")
    decisions: list[UniverseInstrumentDecision] = []
    for index, decision_payload in enumerate(decisions_payload):
        if not isinstance(decision_payload, dict):
            raise ValueError(f"universe decision {index} at line {line_number} must be an object")
        reasons = decision_payload.get("reason_codes")
        if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
            raise ValueError(f"universe reason_codes at line {line_number} must be strings")
        decisions.append(
            UniverseInstrumentDecision(
                canonical_instrument_id=str(decision_payload.get("canonical_instrument_id", "")),
                canonical_symbol=str(decision_payload.get("canonical_symbol", "")),
                included=decision_payload.get("included") is True,
                reason_codes=tuple(reasons),
            )
        )
    schema_version = str(payload.get("schema_version", ""))
    if schema_version != "wickhunter-dynamic-universe-v1":
        raise ValueError(f"unsupported dynamic-universe schema at line {line_number}")
    return DynamicUniverseSnapshot(
        schema_version=schema_version,
        policy_version=str(payload.get("policy_version", "")),
        selected_at_ms=_integer(
            payload.get("selected_at_ms"),
            field=f"universe[{line_number}].selected_at_ms",
            minimum=1,
        ),
        decisions=tuple(decisions),
    )


def _parse_universe_history(path: Path) -> tuple[DynamicUniverseSnapshot, ...]:
    snapshots: list[DynamicUniverseSnapshot] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank universe-history line: {line_number}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid universe-history JSON at line {line_number}") from exc
            if (
                not isinstance(row, dict)
                or row.get("schema_version") != UNIVERSE_HISTORY_ROW_SCHEMA
            ):
                raise ValueError(f"unsupported universe-history row at line {line_number}")
            snapshot = _parse_universe_snapshot(row.get("snapshot"), line_number=line_number)
            if row.get("snapshot_sha256") != snapshot.snapshot_hash:
                raise ValueError(f"universe snapshot hash mismatch at line {line_number}")
            snapshots.append(snapshot)
    if not snapshots:
        raise ValueError("universe-history file must contain at least one snapshot")
    ordered = sorted(snapshots, key=lambda item: (item.selected_at_ms, item.snapshot_hash))
    if snapshots != ordered:
        raise ValueError("universe snapshots must be in deterministic selection order")
    hashes = [item.snapshot_hash for item in snapshots]
    if len(hashes) != len(set(hashes)):
        raise ValueError("duplicate universe snapshots are not allowed")
    return tuple(snapshots)


def _validate_inputs(
    package_root: Path,
    request: RealDatasetMaterializationRequest,
) -> tuple[MaterializationPreflightReport, _ValidatedInputs | None]:
    package_root = _assert_root(package_root)
    accepted_paths = [
        _resolve_member(package_root, reference.relative_path)
        for reference in request.accepted_imports
    ]
    market_path = _resolve_member(package_root, request.market_context.relative_path)
    universe_path = _resolve_member(package_root, request.universe_history.relative_path)
    missing = [
        reference.relative_path
        for reference, path in zip(request.accepted_imports, accepted_paths, strict=True)
        if not path.exists()
    ]
    if not market_path.exists():
        missing.append(request.market_context.relative_path)
    if not universe_path.exists():
        missing.append(request.universe_history.relative_path)
    if missing:
        report = MaterializationPreflightReport(
            status="blocked",
            request_sha256=request.request_sha256,
            missing_paths=tuple(sorted(missing)),
            accepted_import_selection_sha256s=(),
            market_context_sha256="",
            universe_history_sha256="",
            market_snapshot_count=0,
            universe_snapshot_count=0,
        )
        return report, None

    for path in accepted_paths:
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"accepted import root must be a regular directory: {path}")
    _require_regular_file(market_path)
    _require_regular_file(universe_path)
    if sha256_file(market_path) != request.market_context.sha256:
        raise ValueError("market-context file hash mismatch")
    if sha256_file(universe_path) != request.universe_history.sha256:
        raise ValueError("universe-history file hash mismatch")

    selections: list[str] = []
    for reference, path in zip(request.accepted_imports, accepted_paths, strict=True):
        bundle = load_accepted_import(path)
        if bundle.selection.import_run_id != reference.import_run_id:
            raise ValueError("accepted import_run_id does not match request")
        if bundle.selection.selection_sha256 != reference.selection_sha256:
            raise ValueError("accepted import selection hash does not match request")
        if (
            bundle.selection.protected_holdout_start_ms
            != request.build_request.split_geometry.protected_holdout_start_ms
        ):
            raise ValueError("accepted import and materialization holdout disagree")
        selections.append(bundle.selection.selection_sha256)

    markets = _parse_market_context(market_path)
    universes = _parse_universe_history(universe_path)
    report = MaterializationPreflightReport(
        status="ready",
        request_sha256=request.request_sha256,
        missing_paths=(),
        accepted_import_selection_sha256s=tuple(sorted(selections)),
        market_context_sha256=sha256_file(market_path),
        universe_history_sha256=sha256_file(universe_path),
        market_snapshot_count=len(markets),
        universe_snapshot_count=len(universes),
    )
    return report, _ValidatedInputs(
        accepted_roots=tuple(accepted_paths),
        selection_sha256s=tuple(sorted(selections)),
        market_snapshots=markets,
        universe_snapshots=universes,
    )


def preflight_materialization_package(
    *,
    package_root: Path,
    request: RealDatasetMaterializationRequest,
) -> MaterializationPreflightReport:
    report, _ = _validate_inputs(package_root, request)
    return report


def verify_materialized_dataset(output_root: Path) -> dict[str, object]:  # noqa: C901
    if output_root.is_symlink() or not output_root.is_dir():
        raise ValueError("output_root must be a regular directory")
    output_root = output_root.resolve()
    manifest_path = output_root / "manifest.json"
    sources_path = output_root / "sources.json"
    universe_path = output_root / "universe" / "history.jsonl"
    for path in (manifest_path, sources_path, universe_path):
        _require_regular_file(path)
    manifest = _load_json_object(manifest_path)
    if manifest.get("schema_version") != "wickhunter-dataset-manifest-v1":
        raise ValueError("unsupported dataset manifest schema")
    if manifest.get("model_execution_authorized") is not False:
        raise ValueError("dataset manifest must not authorize model execution")
    claimed_manifest_sha = manifest.get("manifest_sha256")
    manifest_identity = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if claimed_manifest_sha != canonical_sha256(manifest_identity):
        raise ValueError("dataset manifest identity hash mismatch")
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("dataset manifest must contain partitions")
    total_rows = 0
    decision_timestamps: list[int] = []
    for index, partition in enumerate(partitions):
        if not isinstance(partition, dict):
            raise ValueError(f"partition {index} must contain an object")
        relative_path = _relative_path(
            str(partition.get("relative_path", "")), field=f"partitions[{index}].relative_path"
        )
        partition_path = _resolve_member(output_root, relative_path)
        _require_regular_file(partition_path)
        if sha256_file(partition_path) != partition.get("sha256"):
            raise ValueError(f"partition hash mismatch: {relative_path}")
        rows = 0
        with partition_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    raise ValueError(f"blank dataset row: {relative_path}:{line_number}")
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid dataset row JSON: {relative_path}:{line_number}"
                    ) from exc
                if not isinstance(row, dict):
                    raise ValueError(f"dataset row must contain an object: {relative_path}")
                claimed_row_sha = row.get("row_sha256")
                material = {key: value for key, value in row.items() if key != "row_sha256"}
                if claimed_row_sha != canonical_sha256(material):
                    raise ValueError(f"dataset row hash mismatch: {relative_path}:{line_number}")
                decision_timestamps.append(
                    _integer(
                        row.get("decision_timestamp_ms"),
                        field="dataset row decision_timestamp_ms",
                        minimum=1,
                    )
                )
                rows += 1
        expected_rows = _integer(
            partition.get("row_count"), field=f"partitions[{index}].row_count", minimum=1
        )
        if rows != expected_rows:
            raise ValueError(f"partition row count mismatch: {relative_path}")
        total_rows += rows
    if total_rows != manifest.get("total_rows"):
        raise ValueError("dataset total_rows does not match partitions")
    if min(decision_timestamps) != manifest.get("earliest_decision_timestamp_ms"):
        raise ValueError("dataset earliest timestamp mismatch")
    if max(decision_timestamps) != manifest.get("latest_decision_timestamp_ms"):
        raise ValueError("dataset latest timestamp mismatch")
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    if not isinstance(sources, list) or not sources:
        raise ValueError("dataset sources.json must contain accepted selections")
    output_universes: list[DynamicUniverseSnapshot] = []
    with universe_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank output universe row: {line_number}")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid output universe JSON at line {line_number}") from exc
            output_universes.append(_parse_universe_snapshot(payload, line_number=line_number))
    universe_hash_payload = manifest.get("universe_snapshot_sha256s")
    if not isinstance(universe_hash_payload, list) or not all(
        isinstance(item, str) for item in universe_hash_payload
    ):
        raise ValueError("dataset manifest universe hashes must contain strings")
    expected_universe_hashes = tuple(universe_hash_payload)
    actual_universe_hashes = tuple(sorted(item.snapshot_hash for item in output_universes))
    if actual_universe_hashes != expected_universe_hashes:
        raise ValueError("dataset universe history does not match manifest")
    return {
        "manifest_sha256": str(claimed_manifest_sha),
        "manifest_file_sha256": sha256_file(manifest_path),
        "sources_sha256": sha256_file(sources_path),
        "universe_history_sha256": sha256_file(universe_path),
        "total_rows": total_rows,
        "partition_count": len(partitions),
        "model_execution_authorized": False,
    }


def materialize_wickhunter_dataset_package(
    *,
    package_root: Path,
    request: RealDatasetMaterializationRequest,
    output_root: Path,
) -> MaterializationResult:
    package_root = _assert_root(package_root)
    output_root = output_root.resolve()
    if output_root == package_root or package_root in output_root.parents:
        raise ValueError("output_root must stay outside the immutable input package")
    report, validated = _validate_inputs(package_root, request)
    if report.status != "ready" or validated is None:
        raise FileNotFoundError(
            "materialization inputs are missing: " + ", ".join(report.missing_paths)
        )
    artifacts: WickHunterDatasetArtifactSet = build_wickhunter_dataset(
        output_root=output_root,
        request=request.build_request,
        accepted_import_roots=validated.accepted_roots,
        market_snapshots=validated.market_snapshots,
        universe_snapshots=validated.universe_snapshots,
    )
    verified = verify_materialized_dataset(artifacts.output_root)
    if verified["manifest_file_sha256"] != artifacts.manifest_file_sha256:
        raise ValueError("independent manifest file hash does not match build result")
    if verified["sources_sha256"] != artifacts.sources_sha256:
        raise ValueError("independent sources hash does not match build result")
    if verified["universe_history_sha256"] != artifacts.universe_history_sha256:
        raise ValueError("independent universe hash does not match build result")
    return MaterializationResult(
        request_sha256=request.request_sha256,
        output_root=str(artifacts.output_root),
        manifest_sha256=artifacts.manifest.manifest_sha256,
        manifest_file_sha256=artifacts.manifest_file_sha256,
        sources_sha256=artifacts.sources_sha256,
        universe_history_sha256=artifacts.universe_history_sha256,
        total_rows=_integer(verified["total_rows"], field="verified.total_rows", minimum=1),
        partition_count=_integer(
            verified["partition_count"], field="verified.partition_count", minimum=1
        ),
    )
