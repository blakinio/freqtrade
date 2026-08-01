from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai_platform.wickhunter import production_market_evidence as v1_core
from ai_platform.wickhunter import production_market_evidence_service as v1_service
from ai_platform.wickhunter import production_market_evidence_v2 as v2
from ai_platform.wickhunter.market_evidence_paths import (
    MarketEvidencePathError,
    safe_regular_member,
)


PACKAGE_DIR_NAME = "immutable-package"
PACKAGE_PARTIAL_DIR_NAME = ".immutable-package.partial"
PACKAGE_MANIFEST_NAME = "manifest.json"
PACKAGE_CHECKSUM_NAME = "artifact-sha256.txt"
PACKAGE_VERIFICATION_NAME = "verification-report.json"
PACKAGE_REQUEST_NAME = "request.json"
PACKAGE_RUN_STATE_NAME = "run-state.json"
PACKAGE_SOURCE_SNAPSHOTS_NAME = "source-snapshots.ndjson"
PACKAGE_MARKET_QUALITY_NAME = "market-quality-observations.ndjson"
PACKAGE_INSTRUMENT_SNAPSHOTS_NAME = "instrument-snapshots.ndjson"
PACKAGE_CANDLE_INDEX_NAME = "completed-candles-index.json"
PACKAGE_BINDING_NAME = "source-package-binding.json"
EXPECTED_COUNTS = {
    "market_quality_observations": 8_640,
    "instrument_snapshots": 8_640,
    "source_health_snapshots": 432,
    "completed_candles": 25_920,
}


class MarketEvidenceV2PublicationError(RuntimeError):
    """Raised when verified immutable source packages cannot be merged safely."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MarketEvidenceV2PublicationError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise MarketEvidenceV2PublicationError(f"{field} must be a list")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise MarketEvidenceV2PublicationError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise MarketEvidenceV2PublicationError(f"{field} must be an integer") from exc


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidenceV2PublicationError(f"{field} must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarketEvidenceV2PublicationError(f"unable to read {field}: {exc}") from exc
    return _object(value, field=field)


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise MarketEvidenceV2PublicationError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: object) -> None:
    content = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _write_new(path, content)


def _safe_member(root: Path, logical_name: str) -> Path:
    try:
        return safe_regular_member(root, logical_name)
    except MarketEvidencePathError as exc:
        raise MarketEvidenceV2PublicationError(str(exc)) from exc


def _identity(path: Path, *, root: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidenceV2PublicationError("artifact is not a regular file")
    try:
        logical_name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise MarketEvidenceV2PublicationError("artifact path escapes package root") from exc
    return {
        "logical_name": logical_name,
        "sha256": _file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _copy_verified(
    source: Path,
    destination: Path,
    *,
    expected_sha256: str,
) -> None:
    if source.is_symlink() or not source.is_file():
        raise MarketEvidenceV2PublicationError("source artifact is not a regular file")
    if _file_hash(source) != expected_sha256:
        raise MarketEvidenceV2PublicationError("source artifact hash mismatch before copy")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise MarketEvidenceV2PublicationError("destination artifact already exists")
    shutil.copyfile(source, destination)
    if _file_hash(destination) != expected_sha256:
        raise MarketEvidenceV2PublicationError("copied artifact hash mismatch")


def _append_verified_ndjson(paths: Sequence[Path], destination: Path) -> int:
    rows = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise MarketEvidenceV2PublicationError("combined NDJSON destination already exists")
    with destination.open("xb") as target:
        for path in paths:
            if path.is_symlink() or not path.is_file():
                raise MarketEvidenceV2PublicationError("NDJSON source must be a regular file")
            with path.open("rb") as source:
                for line in source:
                    if not line.strip():
                        raise MarketEvidenceV2PublicationError("NDJSON source contains a blank row")
                    try:
                        parsed = json.loads(line)
                    except (
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                    ) as exc:
                        raise MarketEvidenceV2PublicationError(
                            "NDJSON source contains invalid JSON"
                        ) from exc
                    if not isinstance(parsed, dict):
                        raise MarketEvidenceV2PublicationError("NDJSON row must be an object")
                    target.write(_canonical_bytes(parsed) + b"\n")
                    rows += 1
        target.flush()
        os.fsync(target.fileno())
    return rows


def _capture_geometry(manifest: Mapping[str, object]) -> dict[str, int]:
    capture = _object(manifest.get("capture"), field="manifest.capture")
    return {
        "pre_roll_start_ms": _integer(
            capture.get("pre_roll_start_ms"),
            field="pre-roll start",
        ),
        "decision_start_ms": _integer(
            capture.get("decision_start_ms"),
            field="decision start",
        ),
        "decision_end_ms": _integer(
            capture.get("decision_end_ms"),
            field="decision end",
        ),
    }


def _candle_artifacts(index: object) -> list[dict[str, Any]]:
    raw = index.get("artifacts") if isinstance(index, dict) else index
    return [_object(item, field="candle artifact") for item in _sequence(raw, field="candle index")]


def _copy_candles(
    *,
    artifacts: Sequence[Mapping[str, Any]],
    source_root: Path,
    destination_root: Path,
    expected_sources: set[str],
) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for artifact in artifacts:
        source = str(artifact.get("source", ""))
        symbol = str(artifact.get("symbol", "")).upper()
        invalid_identity = source not in expected_sources or symbol not in v1_core.EXPECTED_SYMBOLS
        if invalid_identity:
            raise MarketEvidenceV2PublicationError("candle source or symbol identity mismatch")
        identity = (source, symbol)
        if identity in seen:
            raise MarketEvidenceV2PublicationError("duplicate candle source-symbol identity")
        seen.add(identity)
        normalized = _object(
            artifact.get("normalized_file"),
            field="normalized candle file",
        )
        logical_name = str(normalized.get("logical_name", ""))
        source_path = _safe_member(source_root, logical_name)
        expected_sha256 = str(normalized.get("sha256", ""))
        destination = destination_root / "candles" / source / f"{symbol}-5m.ndjson"
        _copy_verified(
            source_path,
            destination,
            expected_sha256=expected_sha256,
        )
        copied.append(
            {
                **dict(artifact),
                "normalized_file": _identity(
                    destination,
                    root=destination_root,
                ),
            }
        )
    expected = {
        (source, symbol) for source in expected_sources for symbol in v1_core.EXPECTED_SYMBOLS
    }
    if seen != expected:
        raise MarketEvidenceV2PublicationError("candle source-symbol coverage mismatch")
    return copied


def _authority_is_safe(
    manifest: Mapping[str, object],
    *,
    field: str,
) -> None:
    authorities = _object(manifest.get("authorities"), field=field)
    if any(authorities.get(key) != value for key, value in v1_service.EXPECTED_AUTHORITY.items()):
        raise MarketEvidenceV2PublicationError(f"{field} authority boundary mismatch")


def merge_verified_packages(
    *,
    base_package_root: Path,
    supplement_root: Path,
    output_run_root: Path,
) -> dict[str, object]:
    base_package = base_package_root.resolve(strict=True)
    supplement = supplement_root.resolve(strict=True)
    v1_verification = v1_service.verify_immutable_package(base_package)
    v2_verification = v2.verify_supplement(supplement)
    base_manifest = _load_json(
        base_package / PACKAGE_MANIFEST_NAME,
        field="base manifest",
    )
    supplement_manifest = _load_json(
        supplement / "manifest.json",
        field="supplement manifest",
    )
    if base_manifest.get("run_id") != supplement_manifest.get("base_v1_run_id"):
        raise MarketEvidenceV2PublicationError(
            "base run identity does not match supplement binding"
        )
    if base_manifest.get("sources") != list(v1_core.EXPECTED_SOURCES):
        raise MarketEvidenceV2PublicationError("base package source coverage mismatch")
    if _capture_geometry(base_manifest) != _capture_geometry(supplement_manifest):
        raise MarketEvidenceV2PublicationError("base and supplement capture geometry differ")
    _authority_is_safe(
        base_manifest,
        field="base package",
    )
    final_root = output_run_root / PACKAGE_DIR_NAME
    if final_root.exists() and not final_root.is_symlink():
        return verify_combined_package(final_root)
    if final_root.exists() or final_root.is_symlink():
        raise MarketEvidenceV2PublicationError("combined package root is unsafe")
    partial_root = output_run_root / PACKAGE_PARTIAL_DIR_NAME
    if partial_root.exists() or partial_root.is_symlink():
        raise MarketEvidenceV2PublicationError("partial combined package already exists")
    output_run_root.mkdir(parents=True, exist_ok=True)
    partial_root.mkdir()
    try:
        base_request = _load_json(
            base_package / PACKAGE_REQUEST_NAME,
            field="base request",
        )
        supplement_request = _load_json(
            supplement / "request.json",
            field="supplement request",
        )
        _write_json(partial_root / PACKAGE_REQUEST_NAME, supplement_request)
        binding: dict[str, object] = {
            "schema_version": 2,
            "binding_type": ("WickHunterMarketEvidenceSourcePackageBinding"),
            "run_id": supplement_manifest["run_id"],
            "base_v1": {
                "run_id": base_manifest["run_id"],
                "manifest_sha256": base_manifest["manifest_sha256"],
                "request_sha256": _file_hash(base_package / PACKAGE_REQUEST_NAME),
                "verification_manifest_sha256": v1_verification["manifest_sha256"],
            },
            "okx_supplement": {
                "run_id": supplement_manifest["run_id"],
                "manifest_sha256": supplement_manifest["manifest_sha256"],
                "request_sha256": _file_hash(supplement / "request.json"),
                "verification_manifest_sha256": v2_verification["manifest_sha256"],
            },
            "geometry": _capture_geometry(base_manifest),
            "sources": list(v2.EXPECTED_SOURCES),
            "symbols": list(v1_core.EXPECTED_SYMBOLS),
            "source_separated": True,
            "cross_exchange_deduplication": False,
            "immutable_inputs_mutated": False,
            **v2.AUTHORITY,
        }
        binding["binding_sha256"] = _canonical_hash(binding)
        _write_json(partial_root / PACKAGE_BINDING_NAME, binding)
        row_counts = {
            "source_health_snapshots": _append_verified_ndjson(
                (
                    base_package / PACKAGE_SOURCE_SNAPSHOTS_NAME,
                    supplement / "source-snapshots.ndjson",
                ),
                partial_root / PACKAGE_SOURCE_SNAPSHOTS_NAME,
            ),
            "market_quality_observations": _append_verified_ndjson(
                (
                    base_package / PACKAGE_MARKET_QUALITY_NAME,
                    supplement / "market-quality-observations.ndjson",
                ),
                partial_root / PACKAGE_MARKET_QUALITY_NAME,
            ),
            "instrument_snapshots": _append_verified_ndjson(
                (
                    base_package / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
                    supplement / "instrument-snapshots.ndjson",
                ),
                partial_root / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
            ),
        }
        base_index = json.loads(
            (base_package / PACKAGE_CANDLE_INDEX_NAME).read_text(encoding="utf-8")
        )
        supplement_index = json.loads(
            (supplement / "completed-candles-index.json").read_text(encoding="utf-8")
        )
        copied_candles = [
            *_copy_candles(
                artifacts=_candle_artifacts(base_index),
                source_root=base_package.parent,
                destination_root=partial_root,
                expected_sources=set(v1_core.EXPECTED_SOURCES),
            ),
            *_copy_candles(
                artifacts=_candle_artifacts(supplement_index),
                source_root=supplement,
                destination_root=partial_root,
                expected_sources={v2.OKX_SOURCE},
            ),
        ]
        row_counts["completed_candles"] = sum(
            _integer(
                item.get("record_count"),
                field="candle record_count",
            )
            for item in copied_candles
        )
        if row_counts != EXPECTED_COUNTS:
            raise MarketEvidenceV2PublicationError(
                f"combined package record counts mismatch: {row_counts}"
            )
        _write_json(
            partial_root / PACKAGE_CANDLE_INDEX_NAME,
            {"schema_version": 2, "artifacts": copied_candles},
        )
        _write_json(
            partial_root / PACKAGE_RUN_STATE_NAME,
            {
                "schema_version": 2,
                "run_id": supplement_manifest["run_id"],
                "state": "completed",
                "active": False,
                "base_v1_run_id": base_manifest["run_id"],
                "source_count": 3,
                "instrument_count": len(v1_core.EXPECTED_SYMBOLS),
                "sample_count": 144,
                "completeness": 1,
                "gap_count": 0,
                "verification_result": "accepted",
                "wh01_ready": False,
                "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                **v2.AUTHORITY,
            },
        )
        top_level_names = (
            PACKAGE_REQUEST_NAME,
            PACKAGE_BINDING_NAME,
            PACKAGE_RUN_STATE_NAME,
            PACKAGE_SOURCE_SNAPSHOTS_NAME,
            PACKAGE_MARKET_QUALITY_NAME,
            PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
            PACKAGE_CANDLE_INDEX_NAME,
        )
        artifacts = [_identity(partial_root / name, root=partial_root) for name in top_level_names]
        artifacts.extend(
            _identity(path, root=partial_root)
            for path in sorted((partial_root / "candles").rglob("*.ndjson"))
        )
        geometry = _capture_geometry(base_manifest)
        manifest: dict[str, object] = {
            "schema_version": 2,
            "artifact_type": ("WickHunterProductionMarketEvidencePackage"),
            "contract_id": v2.CONTRACT_ID,
            "run_id": supplement_manifest["run_id"],
            "base_v1_run_id": base_manifest["run_id"],
            "state": "completed",
            "verification_result": "accepted",
            "collector_commit": supplement_manifest["collector_commit"],
            "source_package_binding_sha256": binding["binding_sha256"],
            "sources": list(v2.EXPECTED_SOURCES),
            "instruments": list(v1_core.EXPECTED_SYMBOLS),
            "capture": {
                **geometry,
                "pre_roll_ms": (geometry["decision_start_ms"] - geometry["pre_roll_start_ms"]),
                "cadence_seconds": 300,
                "timeframe": "5m",
            },
            "record_counts": EXPECTED_COUNTS,
            "first_timestamp_ms": geometry["pre_roll_start_ms"],
            "last_timestamp_ms": geometry["decision_end_ms"],
            "gaps": [],
            "availability": {
                "decision_safe": True,
                "completed_candles_only": True,
                "minimum_pre_roll_satisfied": True,
            },
            "source_health": {
                source: {
                    "healthy": True,
                    "samples": 144,
                    "market_quality_records": 2_880,
                    "completed_candles": 8_640,
                    "gaps": 0,
                }
                for source in v2.EXPECTED_SOURCES
            },
            "wh01": {
                "market_evidence_ready": True,
                "ready": False,
                "blocker_code": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                "blocker_detail": (
                    "A compatible accepted immutable Liquid20 archive and "
                    "prospective WH-01 split binding are still required."
                ),
            },
            "artifacts": artifacts,
            "authorities": v2.AUTHORITY,
            "host_paths_exposed": False,
            "raw_exchange_payloads_exposed_by_portal": False,
            "base_request_identity_sha256": _canonical_hash(base_request),
        }
        manifest["manifest_sha256"] = _canonical_hash(manifest)
        _write_json(partial_root / PACKAGE_MANIFEST_NAME, manifest)
        checksum_identities = [
            *artifacts,
            _identity(
                partial_root / PACKAGE_MANIFEST_NAME,
                root=partial_root,
            ),
        ]
        checksum_lines = sorted(
            f"{item['sha256']}  {item['logical_name']}" for item in checksum_identities
        )
        _write_new(
            partial_root / PACKAGE_CHECKSUM_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        _write_json(
            partial_root / PACKAGE_VERIFICATION_NAME,
            {
                "schema_version": 2,
                "status": "verified",
                "outcome": "accepted",
                "run_id": supplement_manifest["run_id"],
                "manifest_sha256": manifest["manifest_sha256"],
                "binding_sha256": binding["binding_sha256"],
                "artifact_count": len(artifacts),
                **EXPECTED_COUNTS,
                "wh01_ready": False,
                "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                **v2.AUTHORITY,
            },
        )
        verify_combined_package(partial_root)
        partial_root.replace(final_root)
        return verify_combined_package(final_root)
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise


def verify_combined_package(package_root: Path) -> dict[str, object]:
    if package_root.is_symlink() or not package_root.is_dir():
        raise MarketEvidenceV2PublicationError("combined package root must be a regular directory")
    manifest = _load_json(
        package_root / PACKAGE_MANIFEST_NAME,
        field="combined manifest",
    )
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if not isinstance(claimed, str) or _canonical_hash(seed) != claimed:
        raise MarketEvidenceV2PublicationError("combined manifest self hash mismatch")
    invalid_coverage = (
        manifest.get("sources") != list(v2.EXPECTED_SOURCES)
        or manifest.get("instruments") != list(v1_core.EXPECTED_SYMBOLS)
        or manifest.get("record_counts") != EXPECTED_COUNTS
    )
    if invalid_coverage:
        raise MarketEvidenceV2PublicationError("combined package coverage mismatch")
    if manifest.get("authorities") != v2.AUTHORITY:
        raise MarketEvidenceV2PublicationError("combined authority boundary mismatch")
    binding = _load_json(
        package_root / PACKAGE_BINDING_NAME,
        field="source binding",
    )
    binding_claim = binding.get("binding_sha256")
    binding_seed = dict(binding)
    binding_seed.pop("binding_sha256", None)
    invalid_binding = (
        not isinstance(binding_claim, str)
        or _canonical_hash(binding_seed) != binding_claim
        or manifest.get("source_package_binding_sha256") != binding_claim
    )
    if invalid_binding:
        raise MarketEvidenceV2PublicationError("source binding identity mismatch")
    expected_lines: set[str] = set()
    artifacts = _sequence(manifest.get("artifacts"), field="combined artifacts")
    for raw in artifacts:
        identity = _object(raw, field="artifact identity")
        logical_name = str(identity.get("logical_name", ""))
        path = _safe_member(package_root, logical_name)
        identity_mismatch = _file_hash(path) != identity.get(
            "sha256"
        ) or path.stat().st_size != identity.get("size_bytes")
        if identity_mismatch:
            raise MarketEvidenceV2PublicationError("combined artifact identity mismatch")
        expected_lines.add(f"{identity['sha256']}  {logical_name}")
    manifest_identity = _identity(
        package_root / PACKAGE_MANIFEST_NAME,
        root=package_root,
    )
    expected_lines.add(f"{manifest_identity['sha256']}  {PACKAGE_MANIFEST_NAME}")
    checksum = package_root / PACKAGE_CHECKSUM_NAME
    if checksum.is_symlink() or not checksum.is_file():
        raise MarketEvidenceV2PublicationError("combined checksum is missing")
    if set(checksum.read_text(encoding="utf-8").splitlines()) != expected_lines:
        raise MarketEvidenceV2PublicationError("combined checksum mismatch")
    verification = _load_json(
        package_root / PACKAGE_VERIFICATION_NAME,
        field="verification",
    )
    invalid_verification = (
        verification.get("outcome") != "accepted"
        or verification.get("manifest_sha256") != claimed
        or any(verification.get(key) != value for key, value in v2.AUTHORITY.items())
    )
    if invalid_verification:
        raise MarketEvidenceV2PublicationError("combined verification mismatch")
    return {
        "status": "published",
        "outcome": "accepted",
        "run_id": manifest["run_id"],
        "base_v1_run_id": manifest["base_v1_run_id"],
        "package_root": str(package_root),
        "manifest_sha256": claimed,
        "binding_sha256": binding_claim,
        "wh01_ready": False,
        "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
        **v2.AUTHORITY,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge and verify WickHunter Market Evidence v2 packages."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    merge = subparsers.add_parser("merge")
    merge.add_argument("--base-package-root", type=Path, required=True)
    merge.add_argument("--supplement-root", type=Path, required=True)
    merge.add_argument("--output-run-root", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--package-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "merge":
        result = merge_verified_packages(
            base_package_root=args.base_package_root,
            supplement_root=args.supplement_root,
            output_run_root=args.output_run_root,
        )
    else:
        result = verify_combined_package(args.package_root)
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
