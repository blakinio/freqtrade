from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_platform.wickhunter import production_market_evidence as v1_core
from ai_platform.wickhunter import production_market_evidence_intersection as subject
from ai_platform.wickhunter import production_market_evidence_service as v1_service
from ai_platform.wickhunter import production_market_evidence_v2 as v2


SYMBOL = "BTCUSDT"
TIMEFRAME_MS = 300_000
BASE_PRE_ROLL = 1_785_391_200_000
BASE_DECISION_START = 1_785_477_600_000
BASE_DECISION_END = 1_785_520_800_000
SUPPLEMENT_PRE_ROLL = 1_785_398_400_000
SUPPLEMENT_DECISION_START = 1_785_484_800_000
SUPPLEMENT_DECISION_END = 1_785_528_000_000
HOLDOUT_START = 1_785_542_400_000


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _identity(path: Path, *, root: Path) -> dict[str, object]:
    return {
        "logical_name": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _sample_rows(
    *,
    sources: tuple[str, ...],
    start_ms: int,
    samples: int,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    source_rows: list[dict[str, object]] = []
    quality_rows: list[dict[str, object]] = []
    instrument_rows: list[dict[str, object]] = []
    for index in range(samples):
        scheduled = start_ms + index * TIMEFRAME_MS
        for source_index, source in enumerate(sources):
            available = scheduled + 1_000 + source_index
            source_rows.append(
                {
                    "source": source,
                    "scheduled_at_ms": scheduled,
                    "available_at_ms": available,
                    "healthy": True,
                }
            )
            quality_rows.append(
                {
                    "source": source,
                    "symbol": SYMBOL,
                    "canonical_symbol": SYMBOL,
                    "scheduled_at_ms": scheduled,
                    "available_at_ms": available,
                }
            )
            instrument_rows.append(
                {
                    "source": source,
                    "canonical_symbol": SYMBOL,
                    "native_symbol": SYMBOL,
                    "captured_at_ms": available,
                    "available_at_ms": available,
                    "active": True,
                }
            )
    return source_rows, quality_rows, instrument_rows


def _candle_artifact(
    *,
    source_root: Path,
    relative_path: Path,
    source: str,
    start_ms: int,
    end_ms: int,
) -> dict[str, object]:
    path = source_root / relative_path
    rows = [
        {
            "source": source,
            "symbol": SYMBOL,
            "open_time_ms": timestamp,
            "close_time_ms_exclusive": timestamp + TIMEFRAME_MS,
        }
        for timestamp in range(start_ms, end_ms, TIMEFRAME_MS)
    ]
    _write_rows(path, rows)
    return {
        "source": source,
        "symbol": SYMBOL,
        "record_count": len(rows),
        "normalized_file": _identity(path, root=source_root),
    }


def _source_packages(root: Path) -> tuple[Path, Path, str, str]:
    base_run = root / "base-run"
    base_package = base_run / subject.PACKAGE_DIR_NAME
    base_package.mkdir(parents=True)
    base_run_id = "wickhunter-production-market-evidence-20260730-v1-r1"
    base_manifest_sha = "1" * 64
    base_manifest = {
        "run_id": base_run_id,
        "manifest_sha256": base_manifest_sha,
        "sources": list(v1_core.EXPECTED_SOURCES),
        "capture": {
            "pre_roll_start_ms": BASE_PRE_ROLL,
            "decision_start_ms": BASE_DECISION_START,
            "decision_end_ms": BASE_DECISION_END,
        },
        "authorities": dict(v1_service.EXPECTED_AUTHORITY),
    }
    _write_json(base_package / subject.MANIFEST_NAME, base_manifest)
    _write_json(
        base_package / subject.REQUEST_NAME,
        {
            "run_id": base_run_id,
            "protected_holdout_start_ms": HOLDOUT_START,
        },
    )
    base_source, base_quality, base_instruments = _sample_rows(
        sources=tuple(v1_core.EXPECTED_SOURCES),
        start_ms=BASE_DECISION_START,
        samples=144,
    )
    _write_rows(base_package / subject.SOURCE_ROWS_NAME, base_source)
    _write_rows(base_package / subject.QUALITY_ROWS_NAME, base_quality)
    _write_rows(base_package / subject.INSTRUMENT_ROWS_NAME, base_instruments)
    base_candles = [
        _candle_artifact(
            source_root=base_run,
            relative_path=Path("base-candles") / source / f"{SYMBOL}-5m.ndjson",
            source=source,
            start_ms=BASE_PRE_ROLL,
            end_ms=BASE_DECISION_END,
        )
        for source in v1_core.EXPECTED_SOURCES
    ]
    _write_json(
        base_package / subject.CANDLE_INDEX_NAME,
        {"artifacts": base_candles},
    )

    supplement = root / "supplement"
    supplement.mkdir()
    supplement_run_id = "wickhunter-production-market-evidence-20260801-v2-r1"
    supplement_manifest_sha = "2" * 64
    _write_json(
        supplement / subject.MANIFEST_NAME,
        {
            "run_id": supplement_run_id,
            "base_v1_run_id": base_run_id,
            "manifest_sha256": supplement_manifest_sha,
            "capture": {
                "pre_roll_start_ms": SUPPLEMENT_PRE_ROLL,
                "decision_start_ms": SUPPLEMENT_DECISION_START,
                "decision_end_ms": SUPPLEMENT_DECISION_END,
            },
            "authorities": dict(v2.AUTHORITY),
        },
    )
    _write_json(
        supplement / subject.REQUEST_NAME,
        {
            "run_id": supplement_run_id,
            "protected_holdout_start_ms": HOLDOUT_START,
        },
    )
    supplement_source, supplement_quality, supplement_instruments = _sample_rows(
        sources=(v2.OKX_SOURCE,),
        start_ms=SUPPLEMENT_DECISION_START,
        samples=144,
    )
    _write_rows(supplement / subject.SOURCE_ROWS_NAME, supplement_source)
    _write_rows(supplement / subject.QUALITY_ROWS_NAME, supplement_quality)
    _write_rows(supplement / subject.INSTRUMENT_ROWS_NAME, supplement_instruments)
    supplement_candle = _candle_artifact(
        source_root=supplement,
        relative_path=Path("candles") / v2.OKX_SOURCE / f"{SYMBOL}-5m.ndjson",
        source=v2.OKX_SOURCE,
        start_ms=SUPPLEMENT_PRE_ROLL,
        end_ms=SUPPLEMENT_DECISION_END,
    )
    _write_json(
        supplement / subject.CANDLE_INDEX_NAME,
        {"artifacts": [supplement_candle]},
    )
    return base_package, supplement, base_manifest_sha, supplement_manifest_sha


def test_builds_verified_intersection_without_touching_holdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, supplement, base_sha, supplement_sha = _source_packages(tmp_path)
    monkeypatch.setattr(subject, "EXPECTED_SYMBOLS", (SYMBOL,))
    monkeypatch.setattr(
        subject.v1_service,
        "verify_immutable_package",
        lambda _: {"manifest_sha256": base_sha},
    )
    monkeypatch.setattr(
        subject.v2,
        "verify_supplement",
        lambda _: {"manifest_sha256": supplement_sha},
    )

    result = subject.build_intersection_package(
        base_package_root=base,
        supplement_root=supplement,
        output_run_root=tmp_path / "aligned-run",
        run_id="wickhunter-production-market-evidence-20260731-v3-r1",
    )

    assert result["outcome"] == "accepted"
    assert result["protected_holdout_accessed"] is False
    assert result["record_counts"] == {
        "source_health_snapshots": 360,
        "market_quality_observations": 360,
        "instrument_snapshots": 360,
        "completed_candles": 1_224,
    }
    package = Path(str(result["package_root"]))
    manifest = json.loads((package / subject.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["capture"] == {
        "pre_roll_start_ms": SUPPLEMENT_PRE_ROLL,
        "decision_start_ms": SUPPLEMENT_DECISION_START,
        "decision_end_ms": BASE_DECISION_END,
        "pre_roll_ms": 86_400_000,
        "cadence_seconds": 300,
        "timeframe": "5m",
    }
    assert manifest["immutable_inputs_mutated"] is False
    assert manifest["backfill_performed"] is False
    assert manifest["synthetic_observations_added"] is False
    assert manifest["wh01"]["blocker_code"] == "LIQUIDATION_ARCHIVE_NOT_BOUND"


def test_rejects_common_geometry_shorter_than_minimum_decision_window() -> None:
    base_manifest = {
        "capture": {
            "pre_roll_start_ms": SUPPLEMENT_PRE_ROLL,
            "decision_start_ms": SUPPLEMENT_DECISION_START,
            "decision_end_ms": SUPPLEMENT_DECISION_START + 10 * 60 * 60 * 1_000,
        }
    }
    supplement_manifest = {
        "capture": {
            "pre_roll_start_ms": SUPPLEMENT_PRE_ROLL,
            "decision_start_ms": SUPPLEMENT_DECISION_START,
            "decision_end_ms": SUPPLEMENT_DECISION_START + 5 * 60 * 60 * 1_000,
        }
    }
    request = {"protected_holdout_start_ms": HOLDOUT_START}

    with pytest.raises(
        subject.MarketEvidenceIntersectionError,
        match="decision interval is too short",
    ):
        subject.derive_common_geometry(
            base_manifest=base_manifest,
            supplement_manifest=supplement_manifest,
            base_request=request,
            supplement_request=request,
        )


def test_intersection_verifier_rejects_tampered_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, supplement, base_sha, supplement_sha = _source_packages(tmp_path)
    monkeypatch.setattr(subject, "EXPECTED_SYMBOLS", (SYMBOL,))
    monkeypatch.setattr(
        subject.v1_service,
        "verify_immutable_package",
        lambda _: {"manifest_sha256": base_sha},
    )
    monkeypatch.setattr(
        subject.v2,
        "verify_supplement",
        lambda _: {"manifest_sha256": supplement_sha},
    )
    result = subject.build_intersection_package(
        base_package_root=base,
        supplement_root=supplement,
        output_run_root=tmp_path / "aligned-run",
        run_id="wickhunter-production-market-evidence-20260731-v3-r1",
    )
    package = Path(str(result["package_root"]))
    with (package / subject.QUALITY_ROWS_NAME).open("a", encoding="utf-8") as handle:
        handle.write("{}\n")

    with pytest.raises(
        subject.MarketEvidenceIntersectionError,
        match="market_quality_observations count mismatch",
    ):
        subject.verify_intersection_package(package)
