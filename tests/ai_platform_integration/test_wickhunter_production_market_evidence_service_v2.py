from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_platform.wickhunter import production_market_evidence as v1_core
from ai_platform.wickhunter import production_market_evidence_service as v1_service
from ai_platform.wickhunter import production_market_evidence_service_v2 as subject
from ai_platform.wickhunter import production_market_evidence_v2 as v2


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_rows(path: Path, count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n" * count, encoding="utf-8")


def _identity(path: Path, *, root: Path) -> dict[str, object]:
    return {
        "logical_name": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _geometry() -> dict[str, int]:
    return {
        "pre_roll_start_ms": 1_785_391_200_000,
        "decision_start_ms": 1_785_477_600_000,
        "decision_end_ms": 1_785_520_800_000,
    }


def _base_package(root: Path) -> tuple[Path, dict[str, object]]:
    run_root = root / "base-run"
    package = run_root / subject.PACKAGE_DIR_NAME
    package.mkdir(parents=True)
    run_id = "wickhunter-production-market-evidence-20260730-v1-r1"
    manifest = {
        "run_id": run_id,
        "manifest_sha256": "1" * 64,
        "sources": list(v1_core.EXPECTED_SOURCES),
        "capture": _geometry(),
        "authorities": dict(v1_service.EXPECTED_AUTHORITY),
    }
    _write_json(package / subject.PACKAGE_MANIFEST_NAME, manifest)
    _write_json(package / subject.PACKAGE_REQUEST_NAME, {"run_id": run_id})
    _write_rows(package / subject.PACKAGE_SOURCE_SNAPSHOTS_NAME, 288)
    _write_rows(package / subject.PACKAGE_MARKET_QUALITY_NAME, 5_760)
    _write_rows(package / subject.PACKAGE_INSTRUMENT_SNAPSHOTS_NAME, 5_760)
    candle_artifacts: list[dict[str, object]] = []
    for source in v1_core.EXPECTED_SOURCES:
        for symbol in v1_core.EXPECTED_SYMBOLS:
            path = run_root / "base-candles" / source / f"{symbol}-5m.ndjson"
            _write_rows(path, 1)
            candle_artifacts.append(
                {
                    "source": source,
                    "symbol": symbol,
                    "record_count": 432,
                    "normalized_file": _identity(path, root=run_root),
                }
            )
    _write_json(
        package / subject.PACKAGE_CANDLE_INDEX_NAME,
        {"artifacts": candle_artifacts},
    )
    return package, manifest


def _supplement(root: Path) -> tuple[Path, dict[str, object]]:
    package = root / "okx-supplement"
    package.mkdir(parents=True)
    run_id = "wickhunter-production-market-evidence-20260731-v2-r1"
    manifest = {
        "run_id": run_id,
        "base_v1_run_id": ("wickhunter-production-market-evidence-20260730-v1-r1"),
        "manifest_sha256": "2" * 64,
        "collector_commit": "a" * 40,
        "capture": _geometry(),
    }
    _write_json(package / "manifest.json", manifest)
    _write_json(package / "request.json", {"run_id": run_id})
    _write_rows(package / "source-snapshots.ndjson", 144)
    _write_rows(package / "market-quality-observations.ndjson", 2_880)
    _write_rows(package / "instrument-snapshots.ndjson", 2_880)
    candle_artifacts: list[dict[str, object]] = []
    for symbol in v1_core.EXPECTED_SYMBOLS:
        path = package / "candles" / v2.OKX_SOURCE / f"{symbol}-5m.ndjson"
        _write_rows(path, 1)
        candle_artifacts.append(
            {
                "source": v2.OKX_SOURCE,
                "symbol": symbol,
                "record_count": 432,
                "normalized_file": _identity(path, root=package),
            }
        )
    _write_json(
        package / "completed-candles-index.json",
        {"artifacts": candle_artifacts},
    )
    return package, manifest


def test_merge_binds_verified_source_packages_and_keeps_wh01_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, base_manifest = _base_package(tmp_path)
    supplement, supplement_manifest = _supplement(tmp_path)
    monkeypatch.setattr(
        subject.v1_service,
        "verify_immutable_package",
        lambda _: {"manifest_sha256": base_manifest["manifest_sha256"]},
    )
    monkeypatch.setattr(
        subject.v2,
        "verify_supplement",
        lambda _: {"manifest_sha256": supplement_manifest["manifest_sha256"]},
    )

    result = subject.merge_verified_packages(
        base_package_root=base,
        supplement_root=supplement,
        output_run_root=tmp_path / "combined-run",
    )

    assert result["outcome"] == "accepted"
    assert result["wh01_ready"] is False
    assert result["wh01_blocker"] == "LIQUIDATION_ARCHIVE_NOT_BOUND"
    package = Path(str(result["package_root"]))
    manifest = json.loads((package / subject.PACKAGE_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["sources"] == list(v2.EXPECTED_SOURCES)
    assert manifest["record_counts"] == subject.EXPECTED_COUNTS
    assert manifest["wh01"]["market_evidence_ready"] is True
    assert manifest["wh01"]["ready"] is False
    assert manifest["authorities"] == v2.AUTHORITY


def test_combined_package_verifier_rejects_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, base_manifest = _base_package(tmp_path)
    supplement, supplement_manifest = _supplement(tmp_path)
    monkeypatch.setattr(
        subject.v1_service,
        "verify_immutable_package",
        lambda _: {"manifest_sha256": base_manifest["manifest_sha256"]},
    )
    monkeypatch.setattr(
        subject.v2,
        "verify_supplement",
        lambda _: {"manifest_sha256": supplement_manifest["manifest_sha256"]},
    )
    result = subject.merge_verified_packages(
        base_package_root=base,
        supplement_root=supplement,
        output_run_root=tmp_path / "combined-run",
    )
    package = Path(str(result["package_root"]))
    target = package / subject.PACKAGE_MARKET_QUALITY_NAME
    target.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        subject.MarketEvidenceV2PublicationError,
        match="identity mismatch",
    ):
        subject.verify_combined_package(package)
