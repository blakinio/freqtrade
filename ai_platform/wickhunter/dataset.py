from __future__ import annotations

import json
import shutil
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.contracts import LiquidationEvent
from ai_platform.research.liquidations.historical.contracts import (
    HistoricalLiquidationEvent,
    historical_event_from_json_dict,
    validate_sha256,
)
from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    LiquidationFeatureVector,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    SourceHealth,
)
from ai_platform.wickhunter.features import build_liquidation_features
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot


DATASET_SCHEMA_VERSION = "wickhunter-dataset-v1"
DATASET_MANIFEST_SCHEMA_VERSION = "wickhunter-dataset-manifest-v1"


def _require_text(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    return normalized


def _require_git_sha(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 40 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a lowercase 40-character Git SHA")
    return normalized


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, payloads: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for payload in payloads:
            handle.write(canonical_json(payload))
            handle.write("\n")


def _manifest_identity(payload: Mapping[str, object]) -> str:
    identity_material = {
        key: payload[key]
        for key in payload
        if key not in {"created_at_utc", "identity_sha256"}
    }
    canonical = json.dumps(
        identity_material,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AcceptedImportSelection:
    import_run_id: str
    provider_id: str
    requested_start_ms: int
    requested_end_ms: int
    protected_holdout_start_ms: int
    manifest_identity_sha256: str
    manifest_file_sha256: str
    events_file_sha256: str
    acceptance_file_sha256: str
    artifacts_index_sha256: str
    accepted_event_ids_sha256: str
    accepted_records: int
    root_identity: str

    def __post_init__(self) -> None:
        for field_name in ("import_run_id", "provider_id", "root_identity"):
            _require_text(str(getattr(self, field_name)), field=field_name)
        for field_name in (
            "manifest_identity_sha256",
            "manifest_file_sha256",
            "events_file_sha256",
            "acceptance_file_sha256",
            "artifacts_index_sha256",
            "accepted_event_ids_sha256",
        ):
            validate_sha256(str(getattr(self, field_name)), field=field_name)
        if self.requested_start_ms <= 0 or self.requested_end_ms <= self.requested_start_ms:
            raise ValueError("accepted import interval must be positive and non-empty")
        if self.requested_end_ms > self.protected_holdout_start_ms:
            raise ValueError("accepted import overlaps the protected final holdout")
        if self.accepted_records <= 0:
            raise ValueError("accepted import must contain at least one accepted event")

    @property
    def selection_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class AcceptedImportBundle:
    selection: AcceptedImportSelection
    events: tuple[HistoricalLiquidationEvent, ...]

    def __post_init__(self) -> None:
        if len(self.events) != self.selection.accepted_records:
            raise ValueError("accepted event count does not match selection")
        ordered = tuple(
            sorted(
                self.events,
                key=lambda event: (
                    event.available_at_ms,
                    event.occurred_at_ms,
                    event.source,
                    event.symbol,
                    event.source_event_id,
                ),
            )
        )
        if ordered != self.events:
            raise ValueError("accepted events must be in deterministic availability order")


@dataclass(frozen=True, slots=True)
class DatasetSplitWindow:
    name: str
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        _require_text(self.name, field="split name")
        if self.start_ms <= 0 or self.end_ms <= self.start_ms:
            raise ValueError("split interval must be positive and non-empty")


@dataclass(frozen=True, slots=True)
class DatasetSplitGeometry:
    geometry_version: str
    windows: tuple[DatasetSplitWindow, ...]
    label_horizon_ms: int
    embargo_ms: int
    protected_holdout_start_ms: int

    def __post_init__(self) -> None:
        _require_text(self.geometry_version, field="geometry_version")
        if not self.windows:
            raise ValueError("at least one split window is required")
        if self.label_horizon_ms < 0 or self.embargo_ms < 0:
            raise ValueError("label horizon and embargo must be >= 0")
        if self.protected_holdout_start_ms <= 0:
            raise ValueError("protected_holdout_start_ms must be > 0")
        names = [window.name for window in self.windows]
        if len(names) != len(set(names)):
            raise ValueError("split names must be unique")
        ordered = tuple(sorted(self.windows, key=lambda window: (window.start_ms, window.name)))
        if ordered != self.windows:
            raise ValueError("split windows must be sorted by start time")
        required_gap = max(self.label_horizon_ms, self.embargo_ms)
        for index, window in enumerate(self.windows):
            if window.end_ms > self.protected_holdout_start_ms:
                raise ValueError("split window overlaps protected final holdout")
            if index:
                previous = self.windows[index - 1]
                if previous.end_ms + required_gap > window.start_ms:
                    raise ValueError("split windows violate purge/embargo separation")

    def classify(self, timestamp_ms: int) -> str | None:
        if timestamp_ms >= self.protected_holdout_start_ms:
            raise ValueError("protected final holdout access is forbidden")
        for window in self.windows:
            if window.start_ms <= timestamp_ms < window.end_ms:
                return window.name
        return None

    @property
    def geometry_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class WickHunterDatasetBuildRequest:
    dataset_version: str
    code_sha: str
    burst_window_ms: int
    partition_span_ms: int
    minimum_history_events: int
    maximum_source_age_ms: int
    split_geometry: DatasetSplitGeometry

    def __post_init__(self) -> None:
        _require_text(self.dataset_version, field="dataset_version")
        _require_git_sha(self.code_sha, field="code_sha")
        for field_name in (
            "burst_window_ms",
            "partition_span_ms",
            "minimum_history_events",
            "maximum_source_age_ms",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be > 0")

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class DatasetRow:
    schema_version: str
    dataset_version: str
    split_name: str
    symbol: str
    decision_timestamp_ms: int
    feature_available_at_ms: int
    feature: LiquidationFeatureVector
    universe_snapshot_sha256: str
    market_context_sha256: str
    source_selection_sha256s: tuple[str, ...]
    historical_provider_ids: tuple[str, ...]
    import_run_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != DATASET_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {DATASET_SCHEMA_VERSION}")
        for field_name in ("dataset_version", "split_name", "symbol"):
            _require_text(str(getattr(self, field_name)), field=field_name)
        if self.decision_timestamp_ms <= 0:
            raise ValueError("decision_timestamp_ms must be > 0")
        if self.feature_available_at_ms > self.decision_timestamp_ms:
            raise ValueError("dataset row uses information unavailable at decision time")
        validate_sha256(self.universe_snapshot_sha256, field="universe_snapshot_sha256")
        validate_sha256(self.market_context_sha256, field="market_context_sha256")
        for digest in self.source_selection_sha256s:
            validate_sha256(digest, field="source_selection_sha256")
        for values, field_name in (
            (self.source_selection_sha256s, "source_selection_sha256s"),
            (self.historical_provider_ids, "historical_provider_ids"),
            (self.import_run_ids, "import_run_ids"),
        ):
            if not values or values != tuple(sorted(set(values))):
                raise ValueError(f"{field_name} must be non-empty, unique and sorted")
        if self.feature.symbol.upper() != self.symbol.upper():
            raise ValueError("feature symbol does not match dataset row")
        if self.feature.decision_timestamp_ms != self.decision_timestamp_ms:
            raise ValueError("feature decision timestamp does not match dataset row")
        if self.feature.feature_available_at_ms != self.feature_available_at_ms:
            raise ValueError("feature availability does not match dataset row")

    @property
    def row_sha256(self) -> str:
        return canonical_sha256(self)

    def as_json_dict(self) -> dict[str, Any]:
        payload = json.loads(canonical_json(self))
        payload["row_sha256"] = self.row_sha256
        return payload


@dataclass(frozen=True, slots=True)
class DatasetPartition:
    relative_path: str
    split_name: str
    symbol: str
    bucket_start_ms: int
    row_count: int
    earliest_decision_timestamp_ms: int
    latest_decision_timestamp_ms: int
    sha256: str

    def __post_init__(self) -> None:
        if Path(self.relative_path).is_absolute() or ".." in Path(self.relative_path).parts:
            raise ValueError("partition path must stay within the dataset root")
        for field_name in ("split_name", "symbol"):
            _require_text(str(getattr(self, field_name)), field=field_name)
        if self.bucket_start_ms <= 0 or self.row_count <= 0:
            raise ValueError("partition bucket and row_count must be > 0")
        if self.latest_decision_timestamp_ms < self.earliest_decision_timestamp_ms:
            raise ValueError("partition timestamps are invalid")
        validate_sha256(self.sha256, field="partition sha256")


@dataclass(frozen=True, slots=True)
class WickHunterDatasetManifest:
    schema_version: str
    dataset_version: str
    dataset_request_sha256: str
    code_sha: str
    split_geometry_sha256: str
    source_selections: tuple[AcceptedImportSelection, ...]
    universe_snapshot_sha256s: tuple[str, ...]
    partitions: tuple[DatasetPartition, ...]
    total_rows: int
    earliest_decision_timestamp_ms: int
    latest_decision_timestamp_ms: int
    model_execution_authorized: bool

    def __post_init__(self) -> None:
        if self.schema_version != DATASET_MANIFEST_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {DATASET_MANIFEST_SCHEMA_VERSION}")
        _require_text(self.dataset_version, field="dataset_version")
        _require_git_sha(self.code_sha, field="code_sha")
        validate_sha256(self.dataset_request_sha256, field="dataset_request_sha256")
        validate_sha256(self.split_geometry_sha256, field="split_geometry_sha256")
        if not self.source_selections:
            raise ValueError("dataset manifest requires accepted source selections")
        if not self.universe_snapshot_sha256s:
            raise ValueError("dataset manifest requires universe history")
        for digest in self.universe_snapshot_sha256s:
            validate_sha256(digest, field="universe_snapshot_sha256")
        if self.universe_snapshot_sha256s != tuple(
            sorted(set(self.universe_snapshot_sha256s))
        ):
            raise ValueError("universe snapshot hashes must be unique and sorted")
        if not self.partitions or self.total_rows <= 0:
            raise ValueError("dataset manifest requires non-empty partitions")
        if sum(partition.row_count for partition in self.partitions) != self.total_rows:
            raise ValueError("partition row counts do not match total_rows")
        if self.latest_decision_timestamp_ms < self.earliest_decision_timestamp_ms:
            raise ValueError("manifest timestamps are invalid")
        if self.model_execution_authorized:
            raise ValueError("WH-01 must not authorize model execution")

    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(self)

    def as_json_dict(self) -> dict[str, Any]:
        payload = json.loads(canonical_json(self))
        payload["manifest_sha256"] = self.manifest_sha256
        return payload


@dataclass(frozen=True, slots=True)
class WickHunterDatasetArtifactSet:
    output_root: Path
    manifest: WickHunterDatasetManifest
    manifest_file_sha256: str
    universe_history_sha256: str
    sources_sha256: str


def load_accepted_import(root: Path) -> AcceptedImportBundle:  # noqa: C901
    root = root.resolve()
    manifest_path = root / "manifest.json"
    events_path = root / "events.jsonl"
    acceptance_path = root / "acceptance.json"
    index_path = root / "artifacts.json"
    for path in (manifest_path, events_path, acceptance_path, index_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = _load_json_object(manifest_path)
    acceptance = _load_json_object(acceptance_path)
    index = _load_json_object(index_path)
    artifacts = index.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("artifacts.json must declare an artifacts object")
    required_hashes = {
        "manifest.json": sha256_file(manifest_path),
        "events.jsonl": sha256_file(events_path),
        "acceptance.json": sha256_file(acceptance_path),
    }
    for name, actual_hash in required_hashes.items():
        expected_hash = artifacts.get(name)
        if expected_hash != actual_hash:
            raise ValueError(f"artifact hash mismatch: {name}")
    if index.get("import_run_id") != manifest.get("import_run_id"):
        raise ValueError("artifact index import_run_id does not match manifest")

    manifest_identity = _manifest_identity(manifest)
    if manifest.get("identity_sha256") != manifest_identity:
        raise ValueError("manifest identity hash does not match manifest content")
    if index.get("manifest_identity_sha256") != manifest_identity:
        raise ValueError("artifact index manifest identity does not match")
    if acceptance.get("manifest_identity_sha256") != manifest_identity:
        raise ValueError("acceptance manifest identity does not match")
    if acceptance.get("status") != "pass":
        raise ValueError("historical import is not accepted")
    if acceptance.get("protected_holdout_excluded") is not True:
        raise ValueError("historical acceptance does not exclude protected holdout")
    accepted_records = acceptance.get("accepted_records")
    rejected_records = acceptance.get("rejected_records")
    if isinstance(accepted_records, bool) or not isinstance(accepted_records, int):
        raise ValueError("accepted_records must be an integer")
    if isinstance(rejected_records, bool) or not isinstance(rejected_records, int):
        raise ValueError("rejected_records must be an integer")
    if accepted_records <= 0 or rejected_records != 0:
        raise ValueError("WH-01 requires a non-empty zero-rejection accepted import")

    events: list[HistoricalLiquidationEvent] = []
    with events_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank historical event line: {line_number}")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid historical event JSON at line {line_number}"
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError(
                    f"historical event line must contain an object: {line_number}"
                )
            events.append(historical_event_from_json_dict(payload))
    deterministic_events = sorted(
        events,
        key=lambda event: (
            event.available_at_ms,
            event.occurred_at_ms,
            event.source,
            event.symbol,
            event.source_event_id,
        ),
    )
    if events != deterministic_events:
        raise ValueError("events.jsonl is not in deterministic availability order")
    if len(events) != accepted_records:
        raise ValueError("events.jsonl count does not match accepted_records")
    accepted_ids = "\n".join(sorted(event.source_event_id for event in events))
    accepted_event_ids_sha256 = sha256(accepted_ids.encode("utf-8")).hexdigest()
    if acceptance.get("accepted_event_ids_sha256") != accepted_event_ids_sha256:
        raise ValueError("accepted event identity hash does not match events.jsonl")

    import_run_id = str(manifest.get("import_run_id", ""))
    provider_id = str(manifest.get("provider_id", ""))
    requested_start_ms = int(manifest.get("requested_start_ms", 0))
    requested_end_ms = int(manifest.get("requested_end_ms", 0))
    protected_holdout_start_ms = int(manifest.get("protected_holdout_start_ms", 0))
    selection = AcceptedImportSelection(
        import_run_id=import_run_id,
        provider_id=provider_id,
        requested_start_ms=requested_start_ms,
        requested_end_ms=requested_end_ms,
        protected_holdout_start_ms=protected_holdout_start_ms,
        manifest_identity_sha256=manifest_identity,
        manifest_file_sha256=required_hashes["manifest.json"],
        events_file_sha256=required_hashes["events.jsonl"],
        acceptance_file_sha256=required_hashes["acceptance.json"],
        artifacts_index_sha256=sha256_file(index_path),
        accepted_event_ids_sha256=accepted_event_ids_sha256,
        accepted_records=accepted_records,
        root_identity=root.name,
    )
    return AcceptedImportBundle(selection=selection, events=tuple(events))


def normalize_historical_event(event: HistoricalLiquidationEvent) -> LiquidationEvent:
    if event.available_at_ms < event.occurred_at_ms:
        raise ValueError("historical event has negative availability latency")
    return LiquidationEvent(
        schema_version=1,
        source=event.source,
        source_event_id=event.source_event_id,
        symbol=event.symbol.upper(),
        liquidated_position_side=event.liquidated_position_side,
        occurred_at_ms=event.occurred_at_ms,
        received_at_ms=event.available_at_ms,
        price=event.price,
        quantity=event.quantity,
        notional_usd=event.notional_usd,
        raw_side=event.raw_side,
    )


def _latest_universe(
    snapshots: Sequence[DynamicUniverseSnapshot],
    *,
    decision_timestamp_ms: int,
) -> DynamicUniverseSnapshot:
    eligible = [
        snapshot for snapshot in snapshots if snapshot.selected_at_ms <= decision_timestamp_ms
    ]
    if not eligible:
        raise ValueError("no dynamic-universe snapshot is available at decision time")
    return max(
        eligible,
        key=lambda snapshot: (snapshot.selected_at_ms, snapshot.snapshot_hash),
    )


def _history_snapshot(
    *,
    symbol: str,
    decision_timestamp_ms: int,
    burst_window_ms: int,
    minimum_history_events: int,
    events: Sequence[LiquidationEvent],
) -> LiquidationHistorySnapshot | None:
    history_cutoff = decision_timestamp_ms - burst_window_ms
    historical = [
        event
        for event in events
        if event.symbol.upper() == symbol.upper() and event.received_at_ms < history_cutoff
    ]
    if len(historical) < minimum_history_events:
        return None
    buckets: dict[int, Decimal] = defaultdict(Decimal)
    for event in historical:
        bucket = (event.received_at_ms // burst_window_ms) * burst_window_ms
        buckets[bucket] += event.notional_usd
    burst_values = tuple(buckets[bucket] for bucket in sorted(buckets))
    if not burst_values:
        return None
    event_values = tuple(event.notional_usd for event in historical)
    available_at_ms = max(event.received_at_ms for event in historical)
    material = {
        "symbol": symbol.upper(),
        "decision_timestamp_ms": decision_timestamp_ms,
        "event_ids": sorted(
            f"{event.source}:{event.source_event_id}" for event in historical
        ),
        "burst_window_ms": burst_window_ms,
    }
    history_sha256 = canonical_sha256(material)
    return LiquidationHistorySnapshot(
        symbol=symbol.upper(),
        event_notionals_usd=event_values,
        burst_window_notionals_usd=burst_values,
        previous_burst_received_at_ms=max(
            event.received_at_ms for event in historical
        ),
        available_at_ms=available_at_ms,
        history_id=f"wickhunter-history:{history_sha256}",
        history_sha256=history_sha256,
    )


def _source_states(
    *,
    symbol: str,
    decision_timestamp_ms: int,
    maximum_source_age_ms: int,
    all_sources: Sequence[str],
    events: Sequence[LiquidationEvent],
) -> tuple[LiquidationSourceState, ...]:
    states: list[LiquidationSourceState] = []
    for source in sorted(set(all_sources)):
        timestamps = [
            event.received_at_ms
            for event in events
            if event.source == source
            and event.symbol.upper() == symbol.upper()
            and event.received_at_ms <= decision_timestamp_ms
        ]
        last_received_at_ms = max(timestamps) if timestamps else None
        healthy = (
            last_received_at_ms is not None
            and decision_timestamp_ms - last_received_at_ms <= maximum_source_age_ms
        )
        states.append(
            LiquidationSourceState(
                source=source,
                health=SourceHealth.HEALTHY if healthy else SourceHealth.STALE,
                coverage_available=last_received_at_ms is not None,
                last_received_at_ms=last_received_at_ms,
                observed_at_ms=decision_timestamp_ms,
            )
        )
    return tuple(states)


def _row_sources(
    *,
    feature: LiquidationFeatureVector,
    event_evidence: Mapping[tuple[str, str], tuple[str, str, str]],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    selections: set[str] = set()
    providers: set[str] = set()
    import_runs: set[str] = set()
    for identity in feature.input_event_ids:
        source, event_id = identity.split(":", 1)
        try:
            selection_hash, provider_id, import_run_id = event_evidence[(source, event_id)]
        except KeyError as exc:
            raise ValueError(
                "feature event is missing accepted-import evidence"
            ) from exc
        selections.add(selection_hash)
        providers.add(provider_id)
        import_runs.add(import_run_id)
    return tuple(sorted(selections)), tuple(sorted(providers)), tuple(sorted(import_runs))


def build_wickhunter_dataset(  # noqa: C901, PLR0913
    *,
    output_root: Path,
    request: WickHunterDatasetBuildRequest,
    accepted_import_roots: Sequence[Path],
    market_snapshots: Sequence[MarketContextSnapshot],
    universe_snapshots: Sequence[DynamicUniverseSnapshot],
) -> WickHunterDatasetArtifactSet:
    output_root = output_root.resolve()
    if output_root.exists():
        raise FileExistsError(output_root)
    if not accepted_import_roots:
        raise ValueError("at least one accepted historical import root is required")
    if not market_snapshots:
        raise ValueError("at least one market snapshot is required")
    if not universe_snapshots:
        raise ValueError("at least one dynamic-universe snapshot is required")

    bundles = tuple(load_accepted_import(root) for root in accepted_import_roots)
    if len({bundle.selection.selection_sha256 for bundle in bundles}) != len(bundles):
        raise ValueError("duplicate accepted import selection")
    for bundle in bundles:
        if (
            bundle.selection.protected_holdout_start_ms
            != request.split_geometry.protected_holdout_start_ms
        ):
            raise ValueError(
                "accepted import and split geometry disagree on protected holdout"
            )

    normalized_events: list[LiquidationEvent] = []
    event_evidence: dict[tuple[str, str], tuple[str, str, str]] = {}
    for bundle in bundles:
        for historical_event in bundle.events:
            event = normalize_historical_event(historical_event)
            identity = (event.source, event.source_event_id)
            if identity in event_evidence:
                raise ValueError(
                    "duplicate source-labelled event across accepted imports"
                )
            event_evidence[identity] = (
                bundle.selection.selection_sha256,
                bundle.selection.provider_id,
                bundle.selection.import_run_id,
            )
            normalized_events.append(event)
    normalized_events.sort(
        key=lambda event: (
            event.received_at_ms,
            event.occurred_at_ms,
            event.source,
            event.symbol,
            event.source_event_id,
        )
    )
    all_sources = tuple(sorted({event.source for event in normalized_events}))
    ordered_markets = tuple(
        sorted(
            market_snapshots,
            key=lambda market: (
                market.decision_timestamp_ms,
                market.symbol.upper(),
            ),
        )
    )
    market_keys = [
        (market.decision_timestamp_ms, market.symbol.upper())
        for market in ordered_markets
    ]
    if len(market_keys) != len(set(market_keys)):
        raise ValueError("duplicate market snapshot decision keys are not allowed")
    ordered_universes = tuple(
        sorted(
            universe_snapshots,
            key=lambda snapshot: (snapshot.selected_at_ms, snapshot.snapshot_hash),
        )
    )
    if len({snapshot.snapshot_hash for snapshot in ordered_universes}) != len(
        ordered_universes
    ):
        raise ValueError("duplicate dynamic-universe snapshots are not allowed")

    rows: list[DatasetRow] = []
    used_universe_hashes: set[str] = set()
    for market in ordered_markets:
        split_name = request.split_geometry.classify(market.decision_timestamp_ms)
        if split_name is None:
            continue
        universe = _latest_universe(
            ordered_universes,
            decision_timestamp_ms=market.decision_timestamp_ms,
        )
        if not universe.includes_symbol(market.symbol):
            continue
        history = _history_snapshot(
            symbol=market.symbol,
            decision_timestamp_ms=market.decision_timestamp_ms,
            burst_window_ms=request.burst_window_ms,
            minimum_history_events=request.minimum_history_events,
            events=normalized_events,
        )
        if history is None:
            continue
        available_events = tuple(
            event
            for event in normalized_events
            if event.symbol.upper() == market.symbol.upper()
            and event.received_at_ms <= market.decision_timestamp_ms
        )
        if not any(
            event.received_at_ms
            >= market.decision_timestamp_ms - request.burst_window_ms
            for event in available_events
        ):
            continue
        source_states = _source_states(
            symbol=market.symbol,
            decision_timestamp_ms=market.decision_timestamp_ms,
            maximum_source_age_ms=request.maximum_source_age_ms,
            all_sources=all_sources,
            events=normalized_events,
        )
        feature = build_liquidation_features(
            events=available_events,
            market=market,
            history=history,
            source_states=source_states,
            burst_window_ms=request.burst_window_ms,
        )
        selections, providers, import_runs = _row_sources(
            feature=feature,
            event_evidence=event_evidence,
        )
        row = DatasetRow(
            schema_version=DATASET_SCHEMA_VERSION,
            dataset_version=request.dataset_version,
            split_name=split_name,
            symbol=market.symbol.upper(),
            decision_timestamp_ms=market.decision_timestamp_ms,
            feature_available_at_ms=feature.feature_available_at_ms,
            feature=feature,
            universe_snapshot_sha256=universe.snapshot_hash,
            market_context_sha256=canonical_sha256(market),
            source_selection_sha256s=selections,
            historical_provider_ids=providers,
            import_run_ids=import_runs,
        )
        rows.append(row)
        used_universe_hashes.add(universe.snapshot_hash)
    if not rows:
        raise ValueError("dataset build produced no eligible rows")

    rows.sort(
        key=lambda row: (
            row.split_name,
            row.symbol,
            row.decision_timestamp_ms,
            row.row_sha256,
        )
    )
    output_parent = output_root.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_parent)
    )
    try:
        source_payload = [
            json.loads(canonical_json(bundle.selection))
            for bundle in sorted(
                bundles,
                key=lambda item: item.selection.selection_sha256,
            )
        ]
        sources_path = temporary_root / "sources.json"
        _write_json(sources_path, source_payload)

        universe_payload = [
            json.loads(canonical_json(snapshot))
            for snapshot in ordered_universes
            if snapshot.snapshot_hash in used_universe_hashes
        ]
        universe_path = temporary_root / "universe" / "history.jsonl"
        _write_jsonl(universe_path, universe_payload)

        grouped: dict[tuple[str, str, int], list[DatasetRow]] = defaultdict(list)
        for row in rows:
            bucket_start_ms = (
                row.decision_timestamp_ms // request.partition_span_ms
            ) * request.partition_span_ms
            grouped[(row.split_name, row.symbol, bucket_start_ms)].append(row)

        partitions: list[DatasetPartition] = []
        for split_name, symbol, bucket_start_ms in sorted(grouped):
            partition_rows = sorted(
                grouped[(split_name, symbol, bucket_start_ms)],
                key=lambda row: (row.decision_timestamp_ms, row.row_sha256),
            )
            relative_path = (
                Path("features")
                / f"split={split_name}"
                / f"symbol={symbol}"
                / f"part-{bucket_start_ms}.jsonl"
            )
            partition_path = temporary_root / relative_path
            _write_jsonl(
                partition_path,
                (row.as_json_dict() for row in partition_rows),
            )
            partitions.append(
                DatasetPartition(
                    relative_path=relative_path.as_posix(),
                    split_name=split_name,
                    symbol=symbol,
                    bucket_start_ms=bucket_start_ms,
                    row_count=len(partition_rows),
                    earliest_decision_timestamp_ms=(
                        partition_rows[0].decision_timestamp_ms
                    ),
                    latest_decision_timestamp_ms=(
                        partition_rows[-1].decision_timestamp_ms
                    ),
                    sha256=sha256_file(partition_path),
                )
            )

        manifest = WickHunterDatasetManifest(
            schema_version=DATASET_MANIFEST_SCHEMA_VERSION,
            dataset_version=request.dataset_version,
            dataset_request_sha256=request.request_sha256,
            code_sha=request.code_sha,
            split_geometry_sha256=request.split_geometry.geometry_sha256,
            source_selections=tuple(
                bundle.selection
                for bundle in sorted(
                    bundles,
                    key=lambda item: item.selection.selection_sha256,
                )
            ),
            universe_snapshot_sha256s=tuple(sorted(used_universe_hashes)),
            partitions=tuple(partitions),
            total_rows=len(rows),
            earliest_decision_timestamp_ms=min(
                row.decision_timestamp_ms for row in rows
            ),
            latest_decision_timestamp_ms=max(
                row.decision_timestamp_ms for row in rows
            ),
            model_execution_authorized=False,
        )
        manifest_path = temporary_root / "manifest.json"
        _write_json(manifest_path, manifest.as_json_dict())
        temporary_root.replace(output_root)
        return WickHunterDatasetArtifactSet(
            output_root=output_root,
            manifest=manifest,
            manifest_file_sha256=sha256_file(output_root / "manifest.json"),
            universe_history_sha256=sha256_file(
                output_root / "universe" / "history.jsonl"
            ),
            sources_sha256=sha256_file(output_root / "sources.json"),
        )
    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
