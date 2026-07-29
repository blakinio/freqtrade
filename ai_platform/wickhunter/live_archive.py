from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.contracts import LiquidationEvent, event_from_json_dict
from ai_platform.research.liquidations.historical.acceptance import (
    AcceptanceStatus,
    HistoricalAcceptanceReport,
    evaluate_historical_import,
)
from ai_platform.research.liquidations.historical.contracts import (
    AvailableAtSemantics,
    DatasetOrigin,
    HistoricalLiquidationEvent,
    validate_sha256,
)
from ai_platform.research.liquidations.historical.manifests import (
    HistoricalImportManifest,
    RawFileDescriptor,
    sha256_file,
)
from ai_platform.research.liquidations.historical.semantic_eras import DEFAULT_SEMANTIC_ERAS


LIVE_ARCHIVE_SCHEMA_VERSION = "wickhunter-live-archive-acceptance-v1"
LIVE_RUN_CONTRACT = "liquidation-live-state-v1"
LIVE_RUN_ID_PATTERN = re.compile(r"^liquid20-\d{8}T\d{6}Z-\d+$")
MULTI_SYMBOL_DESCRIPTOR = "MULTI_SYMBOL_ARCHIVE"


@dataclass(frozen=True, slots=True)
class _SourceSpec:
    source: str
    provider_exchange: str
    native_channel: str

    @property
    def events_filename(self) -> str:
        return f"{self.source}.ndjson"

    @property
    def summary_filename(self) -> str:
        return f"{self.source}-summary.json"


_SOURCE_SPECS = (
    _SourceSpec("binance-usdm", "binance-futures", "forceOrder"),
    _SourceSpec("bybit-linear", "bybit", "allLiquidation"),
)


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


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path.name}")
    return payload


def _require_regular_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required archive artifact must be a regular file: {path.name}")


@dataclass(frozen=True, slots=True)
class LiveArchiveAcceptanceRequest:
    source_commit_sha: str
    decision_contract_sha256: str
    protected_holdout_start_ms: int
    created_at_utc: str
    storage_root: str
    parser_version: str = LIVE_ARCHIVE_SCHEMA_VERSION
    license_classification: str = "first-party-public-market-data"
    license_reference: str = "Liquid20 public WebSocket first-party collection"

    def __post_init__(self) -> None:
        _require_git_sha(self.source_commit_sha, field="source_commit_sha")
        validate_sha256(self.decision_contract_sha256, field="decision_contract_sha256")
        if self.protected_holdout_start_ms <= 0:
            raise ValueError("protected_holdout_start_ms must be > 0")
        for field_name in (
            "created_at_utc",
            "storage_root",
            "parser_version",
            "license_classification",
            "license_reference",
        ):
            _require_text(str(getattr(self, field_name)), field=field_name)


@dataclass(frozen=True, slots=True)
class LiveArchiveArtifactSet:
    output_root: Path
    import_run_id: str
    input_identity_sha256: str
    manifest_sha256: str
    events_sha256: str
    rejections_sha256: str
    acceptance_sha256: str
    source_run_sha256: str
    index_sha256: str
    acceptance: HistoricalAcceptanceReport


@dataclass(frozen=True, slots=True)
class _SourceArchive:
    spec: _SourceSpec
    events_path: Path
    summary_path: Path
    events_sha256: str
    summary_sha256: str
    events_size_bytes: int
    parsed_events: tuple[tuple[int, LiquidationEvent], ...]
    summary: dict[str, Any]
    summary_run_state: str
    legacy_restart_state_accepted: bool


def _validate_run_state(run_root: Path) -> tuple[dict[str, Any], str, str]:
    state_path = run_root / "run-state-v1.json"
    _require_regular_file(state_path)
    state = _load_json_object(state_path)
    run_id = str(state.get("run_id", ""))
    if not LIVE_RUN_ID_PATTERN.fullmatch(run_id) or run_id != run_root.name:
        raise ValueError("run-state run_id must match the closed run directory")
    if state.get("schema_version") != 1 or state.get("contract") != LIVE_RUN_CONTRACT:
        raise ValueError("unsupported live run contract")
    if state.get("run_state") != "completed" or state.get("data_mode") != "historical":
        raise ValueError("live archive bridge accepts completed historical runs only")
    for field_name in (
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
    ):
        if state.get(field_name) is not False:
            raise ValueError(f"closed live run must keep {field_name}=false")
    _integer(state.get("collector_started_at_ms"), field="collector_started_at_ms", minimum=1)
    _integer(state.get("completed_at_ms"), field="completed_at_ms", minimum=1)
    completion_reason = _require_text(
        str(state.get("completion_reason", "")), field="completion_reason"
    )
    collector_commit = _require_git_sha(
        str(state.get("collector_commit", "")), field="collector_commit"
    )
    sources = state.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("run-state must declare source states")
    return state, collector_commit, completion_reason


def _source_summary_state(
    *,
    summary: dict[str, Any],
    run_id: str,
    completion_reason: str,
    source: str,
) -> tuple[str, bool]:
    if summary.get("run_id") != run_id:
        raise ValueError(f"source summary run state mismatch: {source}")
    summary_run_state = summary.get("run_state")
    if summary_run_state == "completed":
        return summary_run_state, False
    if completion_reason == "collector-restart" and summary_run_state == "active":
        return summary_run_state, True
    raise ValueError(f"source summary run state mismatch: {source}")


def _load_source_archive(  # noqa: C901
    *,
    run_root: Path,
    run_id: str,
    completion_reason: str,
    run_state_sources: dict[str, Any],
    spec: _SourceSpec,
) -> _SourceArchive:
    events_path = run_root / spec.events_filename
    summary_path = run_root / spec.summary_filename
    _require_regular_file(events_path)
    _require_regular_file(summary_path)
    events_size_bytes = events_path.stat().st_size
    events_sha256 = sha256_file(events_path)
    summary_sha256 = sha256_file(summary_path)
    summary = _load_json_object(summary_path)
    source_payload = summary.get("source")
    if not isinstance(source_payload, dict) or source_payload.get("id") != spec.source:
        raise ValueError(f"source summary identity mismatch: {spec.source}")
    if summary.get("schema_version") != 1:
        raise ValueError(f"unsupported source summary schema: {spec.source}")
    summary_run_state, legacy_restart_state_accepted = _source_summary_state(
        summary=summary,
        run_id=run_id,
        completion_reason=completion_reason,
        source=spec.source,
    )
    if summary.get("trading_credentials_present") is not False:
        raise ValueError(f"source summary contains trading credentials: {spec.source}")
    if summary.get("execution_enabled") is not False:
        raise ValueError(f"source summary enables execution: {spec.source}")
    stats = summary.get("stats")
    state_stats = run_state_sources.get(spec.source)
    if not isinstance(stats, dict) or not isinstance(state_stats, dict) or stats != state_stats:
        raise ValueError(f"source summary does not match final run state: {spec.source}")
    if _integer(stats.get("parse_error_count"), field=f"{spec.source}.parse_error_count") != 0:
        raise ValueError(f"source run contains parser errors: {spec.source}")

    parsed_events: list[tuple[int, LiquidationEvent]] = []
    with events_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank live event line: {spec.events_filename}:{line_number}")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid live event JSON: {spec.events_filename}:{line_number}"
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError(
                    f"live event line must contain an object: {spec.events_filename}:{line_number}"
                )
            event = event_from_json_dict(payload)
            if event.source != spec.source:
                raise ValueError(
                    f"live event source mismatch: {spec.events_filename}:{line_number}"
                )
            validate_sha256(event.source_event_id, field="source_event_id")
            if event.notional_usd != event.price * event.quantity:
                raise ValueError(
                    f"live event notional mismatch: {spec.events_filename}:{line_number}"
                )
            parsed_events.append((line_number, event))

    expected_events = _integer(stats.get("events_written"), field=f"{spec.source}.events_written")
    if expected_events != len(parsed_events):
        raise ValueError(f"source event count does not match final run state: {spec.source}")
    if (
        events_path.stat().st_size != events_size_bytes
        or sha256_file(events_path) != events_sha256
        or sha256_file(summary_path) != summary_sha256
    ):
        raise ValueError(f"closed live source changed during acceptance: {spec.source}")
    return _SourceArchive(
        spec=spec,
        events_path=events_path,
        summary_path=summary_path,
        events_sha256=events_sha256,
        summary_sha256=summary_sha256,
        events_size_bytes=events_size_bytes,
        parsed_events=tuple(parsed_events),
        summary=summary,
        summary_run_state=summary_run_state,
        legacy_restart_state_accepted=legacy_restart_state_accepted,
    )


def _input_identity(
    *,
    run_id: str,
    collector_commit: str,
    run_state_sha256: str,
    sources: tuple[_SourceArchive, ...],
) -> str:
    material = {
        "schema_version": LIVE_ARCHIVE_SCHEMA_VERSION,
        "run_id": run_id,
        "collector_commit": collector_commit,
        "run_state_sha256": run_state_sha256,
        "sources": [
            {
                "source": source.spec.source,
                "events_sha256": source.events_sha256,
                "summary_sha256": source.summary_sha256,
            }
            for source in sources
        ],
    }
    return sha256(_json_bytes(material).rstrip(b"\n")).hexdigest()


def _assert_archive_unchanged(
    *,
    run_state_path: Path,
    run_state_sha256: str,
    sources: tuple[_SourceArchive, ...],
) -> None:
    _require_regular_file(run_state_path)
    if sha256_file(run_state_path) != run_state_sha256:
        raise ValueError("closed live run state changed during acceptance")
    for source in sources:
        _require_regular_file(source.events_path)
        _require_regular_file(source.summary_path)
        if (
            source.events_path.stat().st_size != source.events_size_bytes
            or sha256_file(source.events_path) != source.events_sha256
            or sha256_file(source.summary_path) != source.summary_sha256
        ):
            raise ValueError(f"closed live source changed during acceptance: {source.spec.source}")


def accept_closed_live_run(  # noqa: C901
    *,
    run_root: Path,
    output_root: Path,
    request: LiveArchiveAcceptanceRequest,
) -> LiveArchiveArtifactSet:
    if run_root.is_symlink():
        raise ValueError("run_root must not be a symlink")
    run_root = run_root.resolve()
    output_root = output_root.resolve()
    if not run_root.is_dir():
        raise FileNotFoundError(run_root)
    if output_root.exists():
        raise FileExistsError(output_root)
    if (
        run_root == output_root
        or run_root in output_root.parents
        or output_root in run_root.parents
    ):
        raise ValueError("output_root must be separate from the immutable live run")

    run_state, collector_commit, completion_reason = _validate_run_state(run_root)
    run_id = str(run_state["run_id"])
    run_state_path = run_root / "run-state-v1.json"
    run_state_sha256 = sha256_file(run_state_path)
    state_sources = run_state["sources"]
    sources = tuple(
        _load_source_archive(
            run_root=run_root,
            run_id=run_id,
            completion_reason=completion_reason,
            run_state_sources=state_sources,
            spec=spec,
        )
        for spec in _SOURCE_SPECS
    )
    _assert_archive_unchanged(
        run_state_path=run_state_path,
        run_state_sha256=run_state_sha256,
        sources=sources,
    )
    input_identity_sha256 = _input_identity(
        run_id=run_id,
        collector_commit=collector_commit,
        run_state_sha256=run_state_sha256,
        sources=sources,
    )
    import_run_id = f"first-party-live:{run_id}:{input_identity_sha256[:16]}"

    historical_events: list[HistoricalLiquidationEvent] = []
    raw_descriptors: list[RawFileDescriptor] = []
    seen_event_ids: set[str] = set()
    for source in sources:
        if source.events_size_bytes > 0:
            raw_descriptors.append(
                RawFileDescriptor(
                    relative_path=source.spec.events_filename,
                    sha256=source.events_sha256,
                    size_bytes=source.events_size_bytes,
                    provider_id="first-party",
                    provider_exchange=source.spec.provider_exchange,
                    symbol=MULTI_SYMBOL_DESCRIPTOR,
                    requested_date=run_id[9:17],
                    content_encoding="identity",
                    parser_hint=(
                        f"{LIVE_RUN_CONTRACT}:{source.spec.source}:multi-symbol-ndjson:"
                        f"collector={collector_commit}"
                    ),
                )
            )
        for row_number, event in source.parsed_events:
            identity = event.source_event_id
            if identity in seen_event_ids:
                raise ValueError("duplicate live source event identity")
            seen_event_ids.add(identity)
            era = DEFAULT_SEMANTIC_ERAS.resolve(
                provider_id="first-party",
                source=event.source,
                timestamp_ms=event.occurred_at_ms,
            )
            historical_events.append(
                HistoricalLiquidationEvent(
                    schema_version=1,
                    source=event.source,
                    symbol=event.symbol.upper(),
                    liquidated_position_side=event.liquidated_position_side,
                    occurred_at_ms=event.occurred_at_ms,
                    available_at_ms=event.received_at_ms,
                    available_at_semantics=AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP,
                    price=event.price,
                    quantity=event.quantity,
                    notional_usd=event.notional_usd,
                    source_event_id=event.source_event_id,
                    provider_event_id=event.source_event_id,
                    dataset_origin=DatasetOrigin.HISTORICAL_VENDOR,
                    historical_provider="first-party",
                    provider_exchange=source.spec.provider_exchange,
                    provider_timestamp_us=event.occurred_at_ms * 1_000,
                    provider_local_timestamp_us=event.received_at_ms * 1_000,
                    native_channel=source.spec.native_channel,
                    semantic_era=era.era_id,
                    import_run_id=import_run_id,
                    raw_file_sha256=source.events_sha256,
                    raw_row_number=row_number,
                    raw_side=event.raw_side,
                )
            )

    if not historical_events or not raw_descriptors:
        raise ValueError("closed live run contains no liquidation events")
    historical_events.sort(
        key=lambda event: (
            event.available_at_ms,
            event.occurred_at_ms,
            event.source,
            event.symbol,
            event.source_event_id,
        )
    )
    requested_start_ms = min(event.occurred_at_ms for event in historical_events)
    requested_end_ms = max(event.occurred_at_ms for event in historical_events) + 1
    if requested_end_ms > request.protected_holdout_start_ms:
        raise ValueError("closed live run overlaps the protected final holdout")
    manifest_symbols = tuple(
        sorted({MULTI_SYMBOL_DESCRIPTOR, *(event.symbol for event in historical_events)})
    )
    manifest = HistoricalImportManifest(
        schema_version=1,
        import_run_id=import_run_id,
        provider_id="first-party",
        requested_start_ms=requested_start_ms,
        requested_end_ms=requested_end_ms,
        symbols=manifest_symbols,
        source_commit_sha=request.source_commit_sha,
        parser_version=request.parser_version,
        decision_contract_sha256=request.decision_contract_sha256,
        license_classification=request.license_classification,
        license_reference=request.license_reference,
        storage_root=request.storage_root,
        raw_files=tuple(raw_descriptors),
        protected_holdout_start_ms=request.protected_holdout_start_ms,
        protected_holdout_excluded=True,
        created_at_utc=request.created_at_utc,
    )
    acceptance = evaluate_historical_import(
        events=historical_events,
        manifest=manifest,
        semantic_eras=DEFAULT_SEMANTIC_ERAS,
    )
    if acceptance.status is not AcceptanceStatus.ACCEPTED:
        raise ValueError("closed live run failed the unchanged historical acceptance contract")

    output_parent = output_root.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_parent))
    try:
        manifest_path = temporary_root / "manifest.json"
        events_path = temporary_root / "events.jsonl"
        rejections_path = temporary_root / "rejections.json"
        acceptance_path = temporary_root / "acceptance.json"
        source_run_path = temporary_root / "source-run.json"
        index_path = temporary_root / "artifacts.json"

        manifest_path.write_bytes(_json_bytes(manifest.as_json_dict()))
        events_path.write_bytes(
            b"".join(_json_bytes(event.as_json_dict()) for event in historical_events)
        )
        rejections_path.write_bytes(_json_bytes([]))
        acceptance_path.write_bytes(_json_bytes(acceptance.as_json_dict()))
        source_run_path.write_bytes(
            _json_bytes(
                {
                    "schema_version": LIVE_ARCHIVE_SCHEMA_VERSION,
                    "run_id": run_id,
                    "import_run_id": import_run_id,
                    "input_identity_sha256": input_identity_sha256,
                    "collector_commit": collector_commit,
                    "completion_reason": completion_reason,
                    "run_state_sha256": run_state_sha256,
                    "sources": [
                        {
                            "source": source.spec.source,
                            "events_path": source.spec.events_filename,
                            "events_sha256": source.events_sha256,
                            "summary_path": source.spec.summary_filename,
                            "summary_sha256": source.summary_sha256,
                            "summary_run_state": source.summary_run_state,
                            "legacy_restart_state_accepted": (source.legacy_restart_state_accepted),
                            "events_written": len(source.parsed_events),
                        }
                        for source in sources
                    ],
                    "execution_enabled": False,
                    "trading_authorized": False,
                    "trading_credentials_present": False,
                    "model_execution_authorized": False,
                }
            )
        )
        artifact_hashes = {
            "manifest.json": sha256_file(manifest_path),
            "events.jsonl": sha256_file(events_path),
            "rejections.json": sha256_file(rejections_path),
            "acceptance.json": sha256_file(acceptance_path),
            "source-run.json": sha256_file(source_run_path),
        }
        index_path.write_bytes(
            _json_bytes(
                {
                    "schema_version": 1,
                    "import_run_id": import_run_id,
                    "manifest_identity_sha256": manifest.identity_sha256,
                    "input_identity_sha256": input_identity_sha256,
                    "artifacts": artifact_hashes,
                }
            )
        )
        _assert_archive_unchanged(
            run_state_path=run_state_path,
            run_state_sha256=run_state_sha256,
            sources=sources,
        )
        temporary_root.replace(output_root)
    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise

    return LiveArchiveArtifactSet(
        output_root=output_root,
        import_run_id=import_run_id,
        input_identity_sha256=input_identity_sha256,
        manifest_sha256=artifact_hashes["manifest.json"],
        events_sha256=artifact_hashes["events.jsonl"],
        rejections_sha256=artifact_hashes["rejections.json"],
        acceptance_sha256=artifact_hashes["acceptance.json"],
        source_run_sha256=artifact_hashes["source-run.json"],
        index_sha256=sha256_file(output_root / "artifacts.json"),
        acceptance=acceptance,
    )
