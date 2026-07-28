from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json
from ai_platform.wickhunter.dataset import AcceptedImportBundle, load_accepted_import
from ai_platform.wickhunter.live_archive import (
    LIVE_RUN_ID_PATTERN,
    LiveArchiveAcceptanceRequest,
    accept_closed_live_run,
)


REQUEST_SCHEMA_VERSION = "wickhunter-production-live-archive-conversion-request-v1"
REPORT_SCHEMA_VERSION = "wickhunter-production-live-archive-conversion-report-v1"
INDEX_SCHEMA_VERSION = "wickhunter-production-live-archive-conversion-index-v1"
SELECTION_POLICY = "latest-completed-nonempty-before-holdout"
_OPERATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_REQUIRED_SOURCES = ("binance-usdm", "bybit-linear")
_ACCEPTED_FILENAMES = (
    "acceptance.json",
    "artifacts.json",
    "events.jsonl",
    "manifest.json",
    "rejections.json",
    "source-run.json",
)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _require_regular_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required artifact must be a regular file: {path}")


def _require_directory(path: Path, *, field: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{field} must be an existing non-symlink directory")
    return path.resolve()


def _require_false(payload: dict[str, Any], field: str) -> None:
    if payload.get(field) is not False:
        raise ValueError(f"request must keep {field}=false")


def _parse_utc_ms(value: object, *, field: str) -> int:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid RFC3339 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{field} must be UTC")
    return int(parsed.timestamp() * 1000)


@dataclass(frozen=True, slots=True)
class ConversionRequest:
    operation_id: str
    created_at_utc: str
    protected_holdout_start_ms: int
    live_data_root: Path
    accepted_state_root: Path
    storage_root: str


def load_conversion_request(path: Path) -> ConversionRequest:
    _require_regular_file(path)
    payload = _load_json_object(path)
    if payload.get("schema_version") != REQUEST_SCHEMA_VERSION:
        raise ValueError("unsupported WickHunter production conversion request schema")
    operation_id = str(payload.get("operation_id", ""))
    if not _OPERATION_ID_PATTERN.fullmatch(operation_id):
        raise ValueError("operation_id must be a bounded lowercase filesystem identifier")
    if payload.get("selection_policy") != SELECTION_POLICY:
        raise ValueError(f"selection_policy must be {SELECTION_POLICY}")
    for field in (
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
        "model_execution_authorized",
        "live_capital_authorized",
    ):
        _require_false(payload, field)
    created_at_utc = str(payload.get("created_at_utc", ""))
    _parse_utc_ms(created_at_utc, field="created_at_utc")
    protected_holdout_start_ms = _parse_utc_ms(
        payload.get("protected_holdout_start_utc"),
        field="protected_holdout_start_utc",
    )
    live_data_root = Path(str(payload.get("live_data_root", "")))
    accepted_state_root = Path(str(payload.get("accepted_state_root", "")))
    if not live_data_root.is_absolute() or not accepted_state_root.is_absolute():
        raise ValueError("live_data_root and accepted_state_root must be absolute")
    storage_root = str(payload.get("storage_root", "")).strip()
    if not storage_root:
        raise ValueError("storage_root must be non-empty")
    return ConversionRequest(
        operation_id=operation_id,
        created_at_utc=created_at_utc,
        protected_holdout_start_ms=protected_holdout_start_ms,
        live_data_root=live_data_root,
        accepted_state_root=accepted_state_root,
        storage_root=storage_root,
    )


@dataclass(frozen=True, slots=True)
class ClosedRunCandidate:
    run_root: Path
    run_id: str
    completed_at_ms: int
    events_written: int


def _candidate_from_run(  # noqa: C901
    run_root: Path,
    *,
    holdout_start_ms: int,
) -> ClosedRunCandidate | None:
    if (
        run_root.is_symlink()
        or not run_root.is_dir()
        or not LIVE_RUN_ID_PATTERN.fullmatch(run_root.name)
    ):
        return None
    state_path = run_root / "run-state-v1.json"
    if state_path.is_symlink() or not state_path.is_file():
        return None
    try:
        state = _load_json_object(state_path)
    except ValueError:
        return None
    if (
        state.get("run_id") != run_root.name
        or state.get("contract") != "liquidation-live-state-v1"
        or state.get("schema_version") != 1
        or state.get("run_state") != "completed"
        or state.get("data_mode") != "historical"
    ):
        return None
    for field in (
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
    ):
        if state.get(field) is not False:
            return None
    completed_at_ms = state.get("completed_at_ms")
    if (
        isinstance(completed_at_ms, bool)
        or not isinstance(completed_at_ms, int)
        or completed_at_ms <= 0
        or completed_at_ms >= holdout_start_ms
    ):
        return None
    sources = state.get("sources")
    if not isinstance(sources, dict):
        return None
    events_written = 0
    for source in _REQUIRED_SOURCES:
        source_state = sources.get(source)
        if not isinstance(source_state, dict):
            return None
        count = source_state.get("events_written")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return None
        events_written += count
        for suffix in (".ndjson", "-summary.json"):
            artifact = run_root / f"{source}{suffix}"
            if artifact.is_symlink() or not artifact.is_file():
                return None
    if events_written <= 0:
        return None
    return ClosedRunCandidate(
        run_root=run_root,
        run_id=run_root.name,
        completed_at_ms=completed_at_ms,
        events_written=events_written,
    )


def select_closed_run(*, data_root: Path, holdout_start_ms: int) -> ClosedRunCandidate:
    data_root = _require_directory(data_root, field="live_data_root")
    runs_root = data_root / "live" / "runs"
    runs_root = _require_directory(runs_root, field="live runs root")
    candidates = tuple(
        candidate
        for run_root in runs_root.iterdir()
        if (candidate := _candidate_from_run(run_root, holdout_start_ms=holdout_start_ms))
        is not None
    )
    if not candidates:
        raise ValueError("no completed non-empty production Liquid20 run is eligible")
    return max(candidates, key=lambda candidate: (candidate.completed_at_ms, candidate.run_id))


def _operation_hashes(operation_root: Path) -> dict[str, str]:
    relative_paths = ["request.json", "report.json"]
    relative_paths.extend(f"accepted/{name}" for name in _ACCEPTED_FILENAMES)
    hashes: dict[str, str] = {}
    for relative_path in relative_paths:
        path = operation_root / relative_path
        _require_regular_file(path)
        hashes[relative_path] = sha256_file(path)
    return hashes


def _verify_bundle(operation_root: Path, report: dict[str, Any]) -> AcceptedImportBundle:
    accepted_root = operation_root / "accepted"
    bundle = load_accepted_import(accepted_root)
    if bundle.selection.provider_id != "first-party":
        raise ValueError("converted import provider must remain first-party")
    if bundle.selection.import_run_id != report.get("import_run_id"):
        raise ValueError("WH-01 import_run_id does not match operation report")
    if bundle.selection.accepted_records != report.get("accepted_records"):
        raise ValueError("WH-01 accepted record count does not match operation report")
    source_run = _load_json_object(accepted_root / "source-run.json")
    if source_run.get("run_id") != report.get("selected_run_id"):
        raise ValueError("source-run identity does not match selected production run")
    for field in (
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
        "model_execution_authorized",
    ):
        if source_run.get(field) is not False:
            raise ValueError(f"source-run must keep {field}=false")
    return bundle


def convert_production_archive(
    *,
    request_path: Path,
    source_commit_sha: str,
    decision_contract_path: Path,
) -> Path:
    request = load_conversion_request(request_path)
    data_root = _require_directory(request.live_data_root, field="live_data_root")
    state_root = _require_directory(request.accepted_state_root, field="accepted_state_root")
    decision_contract_path = decision_contract_path.resolve()
    _require_regular_file(decision_contract_path)
    final_root = state_root / request.operation_id
    if final_root.exists() or final_root.is_symlink():
        raise FileExistsError(final_root)

    candidate = select_closed_run(
        data_root=data_root,
        holdout_start_ms=request.protected_holdout_start_ms,
    )
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{request.operation_id}.", dir=state_root))
    try:
        accepted_root = temporary_root / "accepted"
        bridge_request = LiveArchiveAcceptanceRequest(
            source_commit_sha=source_commit_sha,
            decision_contract_sha256=sha256_file(decision_contract_path),
            protected_holdout_start_ms=request.protected_holdout_start_ms,
            created_at_utc=request.created_at_utc,
            storage_root=request.storage_root,
        )
        artifacts = accept_closed_live_run(
            run_root=candidate.run_root,
            output_root=accepted_root,
            request=bridge_request,
        )
        request_payload = _load_json_object(request_path)
        _write_json(temporary_root / "request.json", request_payload)
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "operation_id": request.operation_id,
            "selection_policy": SELECTION_POLICY,
            "selected_run_id": candidate.run_id,
            "selected_run_completed_at_ms": candidate.completed_at_ms,
            "selected_run_events_written": candidate.events_written,
            "import_run_id": artifacts.import_run_id,
            "input_identity_sha256": artifacts.input_identity_sha256,
            "accepted_records": artifacts.acceptance.accepted_records,
            "rejected_records": artifacts.acceptance.rejected_records,
            "acceptance_status": artifacts.acceptance.status,
            "manifest_sha256": artifacts.manifest_sha256,
            "events_sha256": artifacts.events_sha256,
            "acceptance_sha256": artifacts.acceptance_sha256,
            "source_run_sha256": artifacts.source_run_sha256,
            "artifact_index_sha256": artifacts.index_sha256,
            "source_commit_sha": source_commit_sha,
            "decision_contract_sha256": bridge_request.decision_contract_sha256,
            "protected_holdout_start_ms": request.protected_holdout_start_ms,
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "model_execution_authorized": False,
            "live_capital_authorized": False,
            "strategy_quality_claimed": False,
            "profitability_claimed": False,
            "wh02_authorized_by_conversion_alone": False,
        }
        _write_json(temporary_root / "report.json", report)
        bundle = _verify_bundle(temporary_root, report)
        if bundle.selection.accepted_records != artifacts.acceptance.accepted_records:
            raise ValueError("bridge and WH-01 accepted record counts disagree")
        index = {
            "schema_version": INDEX_SCHEMA_VERSION,
            "operation_id": request.operation_id,
            "artifacts": _operation_hashes(temporary_root),
        }
        _write_json(temporary_root / "operation-artifacts.json", index)
        temporary_root.replace(final_root)
    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    return final_root


def verify_operation(operation_root: Path) -> dict[str, Any]:
    operation_root = _require_directory(operation_root, field="operation_root")
    report_path = operation_root / "report.json"
    request_path = operation_root / "request.json"
    index_path = operation_root / "operation-artifacts.json"
    for path in (report_path, request_path, index_path):
        _require_regular_file(path)
    report = _load_json_object(report_path)
    request = _load_json_object(request_path)
    index = _load_json_object(index_path)
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError("unsupported conversion report schema")
    if request.get("schema_version") != REQUEST_SCHEMA_VERSION:
        raise ValueError("unsupported copied request schema")
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise ValueError("unsupported conversion index schema")
    operation_id = operation_root.name
    if report.get("operation_id") != operation_id or request.get("operation_id") != operation_id:
        raise ValueError("operation identity mismatch")
    if index.get("operation_id") != operation_id:
        raise ValueError("operation index identity mismatch")
    declared_hashes = index.get("artifacts")
    if not isinstance(declared_hashes, dict):
        raise ValueError("operation index must declare artifacts")
    expected_hashes = _operation_hashes(operation_root)
    if declared_hashes != expected_hashes:
        raise ValueError("operation artifact hashes do not match")
    for field in (
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
        "model_execution_authorized",
        "live_capital_authorized",
        "strategy_quality_claimed",
        "profitability_claimed",
        "wh02_authorized_by_conversion_alone",
    ):
        if report.get(field) is not False:
            raise ValueError(f"conversion report must keep {field}=false")
    bundle = _verify_bundle(operation_root, report)
    return {
        "operation_id": operation_id,
        "selected_run_id": report["selected_run_id"],
        "import_run_id": bundle.selection.import_run_id,
        "accepted_records": bundle.selection.accepted_records,
        "selection_sha256": bundle.selection.selection_sha256,
        "verified": True,
        "trading_authorized": False,
        "model_execution_authorized": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert one completed production Liquid20 archive into a WH-01 accepted import."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    convert = subparsers.add_parser("convert")
    convert.add_argument("--request", type=Path, required=True)
    convert.add_argument("--source-commit-sha", required=True)
    convert.add_argument("--decision-contract", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--operation-root", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "convert":
        operation_root = convert_production_archive(
            request_path=args.request,
            source_commit_sha=args.source_commit_sha,
            decision_contract_path=args.decision_contract,
        )
        result = verify_operation(operation_root)
    else:
        result = verify_operation(args.operation_root)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
