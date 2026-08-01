from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_platform.wickhunter import production_dataset_materialization as subject
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.dataset import AcceptedImportSelection


PRE_ROLL_START = 1_785_398_400_000
DECISION_START = 1_785_484_800_000
DECISION_END = 1_785_520_800_000
HOLDOUT_START = 1_785_542_400_000
SOURCES = ["bybit-linear", "binance-usdm", "okx-swap"]
SYMBOL = "BTCUSDT"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _market_package(root: Path) -> Path:
    package = root / "market-package"
    package.mkdir()
    manifest = {
        "run_id": "wickhunter-production-market-evidence-20260731-v3-r1",
        "manifest_sha256": "a" * 64,
        "sources": SOURCES,
        "instruments": [SYMBOL],
        "capture": {
            "pre_roll_start_ms": PRE_ROLL_START,
            "decision_start_ms": DECISION_START,
            "decision_end_ms": DECISION_END,
        },
        "protected_holdout_start_ms": HOLDOUT_START,
    }
    _write_json(package / subject.MARKET_MANIFEST_NAME, manifest)
    source_rows: list[dict[str, object]] = []
    quality_rows: list[dict[str, object]] = []
    for sample_index, scheduled in enumerate(
        range(DECISION_START, DECISION_END, subject.TIMEFRAME_MS)
    ):
        for source_index, source in enumerate(SOURCES):
            available = scheduled + 1_000 + source_index
            source_rows.append(
                {
                    "sample_index": sample_index,
                    "source": source,
                    "scheduled_at_ms": scheduled,
                    "available_at_ms": available,
                    "connected": True,
                    "healthy": True,
                    "wickhunter_available": True,
                    "gaps": 0,
                }
            )
            quality_rows.append(
                {
                    "source": source,
                    "symbol": SYMBOL,
                    "canonical_symbol": SYMBOL,
                    "scheduled_at_ms": scheduled,
                    "available_at_ms": available,
                    "last_price": "100",
                    "spread_bps": "1",
                    "quote_volume_24h_usd": "1000000",
                    "market_available": True,
                }
            )
    _write_rows(package / subject.SOURCE_ROWS_NAME, source_rows)
    _write_rows(package / subject.QUALITY_ROWS_NAME, quality_rows)

    candle_path = package / "candles" / "binance-usdm" / f"{SYMBOL}-5m.ndjson"
    candles = [
        {
            "source": "binance-usdm",
            "symbol": SYMBOL,
            "open_time_ms": timestamp,
            "close_time_ms_exclusive": timestamp + subject.TIMEFRAME_MS,
            "close": "100",
        }
        for timestamp in range(PRE_ROLL_START, DECISION_END, subject.TIMEFRAME_MS)
    ]
    _write_rows(candle_path, candles)
    _write_json(
        package / subject.CANDLE_INDEX_NAME,
        {
            "artifacts": [
                {
                    "source": "binance-usdm",
                    "symbol": SYMBOL,
                    "normalized_file": {
                        "logical_name": candle_path.relative_to(package).as_posix(),
                        "sha256": _sha(candle_path),
                        "size_bytes": candle_path.stat().st_size,
                    },
                }
            ]
        },
    )
    return package


def _selection() -> AcceptedImportSelection:
    return AcceptedImportSelection(
        import_run_id="first-party-live:liquid20-20260731T000000Z-0:test",
        provider_id="first-party-live",
        requested_start_ms=DECISION_START - 8 * 60 * 60 * 1000,
        requested_end_ms=DECISION_END + 60 * 60 * 1000,
        protected_holdout_start_ms=HOLDOUT_START,
        manifest_identity_sha256="1" * 64,
        manifest_file_sha256="2" * 64,
        events_file_sha256="3" * 64,
        acceptance_file_sha256="4" * 64,
        artifacts_index_sha256="5" * 64,
        accepted_event_ids_sha256="6" * 64,
        accepted_records=10,
        root_identity="accepted",
    )


def _fake_dataset_builder(**kwargs: object) -> SimpleNamespace:
    output_root = Path(str(kwargs["output_root"]))
    request = kwargs["request"]
    output_root.mkdir(parents=True)
    partition = output_root / "features" / "split=train" / "symbol=BTCUSDT" / "part.jsonl"
    _write_rows(partition, [{"row_sha256": "7" * 64}])
    (output_root / "universe").mkdir()
    (output_root / "universe" / "history.jsonl").write_text("{}\n", encoding="utf-8")
    _write_json(output_root / "sources.json", [{"selection": "1" * 64}])
    seed = {
        "schema_version": subject.DATASET_MANIFEST_SCHEMA_VERSION,
        "dataset_version": subject.DEFAULT_DATASET_VERSION,
        "dataset_request_sha256": request.request_sha256,
        "code_sha": request.code_sha,
        "split_geometry_sha256": request.split_geometry.geometry_sha256,
        "source_selections": [],
        "universe_snapshot_sha256s": ["8" * 64],
        "partitions": [
            {
                "relative_path": partition.relative_to(output_root).as_posix(),
                "split_name": "train",
                "symbol": SYMBOL,
                "bucket_start_ms": DECISION_START,
                "row_count": 1,
                "earliest_decision_timestamp_ms": DECISION_START + 1_002,
                "latest_decision_timestamp_ms": DECISION_START + 1_002,
                "sha256": _sha(partition),
            }
        ],
        "total_rows": 1,
        "earliest_decision_timestamp_ms": DECISION_START + 1_002,
        "latest_decision_timestamp_ms": DECISION_START + 1_002,
        "model_execution_authorized": False,
    }
    manifest = {**seed, "manifest_sha256": canonical_sha256(seed)}
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
    return SimpleNamespace(
        manifest_file_sha256=_sha(manifest_path),
        universe_history_sha256=_sha(output_root / "universe" / "history.jsonl"),
        sources_sha256=_sha(output_root / "sources.json"),
    )


def test_production_split_geometry_has_purge_and_embargo() -> None:
    geometry = subject.production_split_geometry(
        decision_start_ms=DECISION_START,
        decision_end_ms=DECISION_END,
        protected_holdout_start_ms=HOLDOUT_START,
    )

    assert [window.name for window in geometry.windows] == [
        "train",
        "validation",
        "test",
    ]
    assert geometry.windows[0].end_ms + subject.DEFAULT_EMBARGO_MS == geometry.windows[1].start_ms
    assert geometry.windows[1].end_ms + subject.DEFAULT_EMBARGO_MS == geometry.windows[2].start_ms
    assert geometry.windows[-1].end_ms == DECISION_END


def test_market_inputs_are_availability_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _market_package(tmp_path)
    monkeypatch.setattr(
        subject,
        "verify_intersection_package",
        lambda _: {
            "manifest_sha256": "a" * 64,
            "binding_sha256": "b" * 64,
            "lineage_sha256": "c" * 64,
        },
    )

    markets, universes, evidence = subject._market_inputs(package)

    assert len(markets) == 120
    assert len(universes) == 120
    assert evidence["market_context_count"] == 120
    first = markets[0]
    assert first.completed_candle_close_ms == DECISION_START
    assert first.decision_timestamp_ms == DECISION_START + 1_002
    assert all(metric.available_at_ms <= first.decision_timestamp_ms for metric in first.metrics)
    assert universes[0].includes_symbol(SYMBOL)
    assert universes[-1].selected_at_ms < HOLDOUT_START


def test_materialization_binds_sources_and_verifies_partitions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_package = tmp_path / "market"
    accepted_root = tmp_path / "accepted"
    market_package.mkdir()
    accepted_root.mkdir()
    manifest = {
        "run_id": "wickhunter-production-market-evidence-20260731-v3-r1",
        "manifest_sha256": "a" * 64,
        "capture": {
            "pre_roll_start_ms": PRE_ROLL_START,
            "decision_start_ms": DECISION_START,
            "decision_end_ms": DECISION_END,
        },
        "protected_holdout_start_ms": HOLDOUT_START,
    }
    selection = _selection()
    assert selection.requested_start_ms > DECISION_START - 86_400_000
    assert selection.requested_start_ms <= DECISION_START - subject.DEFAULT_BURST_WINDOW_MS
    monkeypatch.setattr(
        subject,
        "_market_inputs",
        lambda _: (
            (SimpleNamespace(),),
            (SimpleNamespace(),),
            {
                "market_verification": {
                    "manifest_sha256": "a" * 64,
                    "binding_sha256": "b" * 64,
                    "lineage_sha256": "c" * 64,
                },
                "market_manifest": manifest,
                "market_context_count": 1,
                "universe_snapshot_count": 1,
            },
        ),
    )
    monkeypatch.setattr(
        subject,
        "load_accepted_import",
        lambda _: SimpleNamespace(selection=selection),
    )
    monkeypatch.setattr(subject, "build_wickhunter_dataset", _fake_dataset_builder)

    output = tmp_path / "materialized"
    result = subject.materialize_production_dataset(
        output_root=output,
        market_package_root=market_package,
        accepted_import_root=accepted_root,
        code_sha="d" * 40,
    )

    assert result["outcome"] == "accepted"
    assert result["wh01_ready"] is True
    assert result["total_rows"] == 1
    binding = json.loads((output / subject.BINDING_NAME).read_text(encoding="utf-8"))
    assert binding["market_evidence"]["manifest_sha256"] == "a" * 64
    assert binding["liquid20_selection_sha256"] == selection.selection_sha256
    assert binding["protected_holdout_accessed"] is False


def test_verifier_rejects_partition_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_package = tmp_path / "market"
    accepted_root = tmp_path / "accepted"
    market_package.mkdir()
    accepted_root.mkdir()
    manifest = {
        "run_id": "wickhunter-production-market-evidence-20260731-v3-r1",
        "manifest_sha256": "a" * 64,
        "capture": {
            "pre_roll_start_ms": PRE_ROLL_START,
            "decision_start_ms": DECISION_START,
            "decision_end_ms": DECISION_END,
        },
        "protected_holdout_start_ms": HOLDOUT_START,
    }
    monkeypatch.setattr(
        subject,
        "_market_inputs",
        lambda _: (
            (SimpleNamespace(),),
            (SimpleNamespace(),),
            {
                "market_verification": {
                    "manifest_sha256": "a" * 64,
                    "binding_sha256": "b" * 64,
                    "lineage_sha256": "c" * 64,
                },
                "market_manifest": manifest,
                "market_context_count": 1,
                "universe_snapshot_count": 1,
            },
        ),
    )
    monkeypatch.setattr(
        subject,
        "load_accepted_import",
        lambda _: SimpleNamespace(selection=_selection()),
    )
    monkeypatch.setattr(subject, "build_wickhunter_dataset", _fake_dataset_builder)
    output = tmp_path / "materialized"
    subject.materialize_production_dataset(
        output_root=output,
        market_package_root=market_package,
        accepted_import_root=accepted_root,
        code_sha="d" * 40,
    )
    partition = next((output / subject.DATASET_DIR_NAME / "features").rglob("*.jsonl"))
    partition.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        subject.ProductionDatasetMaterializationError,
        match="partition hash mismatch",
    ):
        subject.verify_production_materialization(output)
