from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.historical.contracts import (
    AvailableAtSemantics,
    DatasetOrigin,
    HistoricalLiquidationEvent,
)
from ai_platform.research.liquidations.historical.manifests import (
    HistoricalImportManifest,
    RawFileDescriptor,
    sha256_file,
)
from ai_platform.scripts.wickhunter_dataset_materialization import main
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import AvailableMetric, MarketContextSnapshot
from ai_platform.wickhunter.dataset import load_accepted_import
from ai_platform.wickhunter.materialization import (
    MARKET_CONTEXT_ROW_SCHEMA,
    MATERIALIZATION_REQUEST_SCHEMA,
    UNIVERSE_HISTORY_ROW_SCHEMA,
    load_materialization_request,
    materialize_wickhunter_dataset_package,
    preflight_materialization_package,
    verify_materialized_dataset,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


CODE_SHA = "1" * 40
HOLDOUT_START_MS = 10_000_000


def _json_bytes(payload: object) -> bytes:
    return (canonical_json(payload) + "\n").encode("utf-8")


def _event(
    *,
    source: str,
    occurred_at_ms: int,
    index: int,
) -> HistoricalLiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(str(index + 1))
    return HistoricalLiquidationEvent(
        schema_version=1,
        source=source,
        symbol="BTCUSDT",
        liquidated_position_side=(
            LiquidatedPositionSide.LONG if index % 2 else LiquidatedPositionSide.SHORT
        ),
        occurred_at_ms=occurred_at_ms,
        available_at_ms=occurred_at_ms + 100,
        available_at_semantics=AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP,
        price=price,
        quantity=quantity,
        notional_usd=price * quantity,
        source_event_id=sha256(f"event-{index}".encode()).hexdigest(),
        provider_event_id=f"provider-{index}",
        dataset_origin=DatasetOrigin.HISTORICAL_VENDOR,
        historical_provider="first-party",
        provider_exchange="bybit" if source == "bybit-linear" else "binance-futures",
        provider_timestamp_us=occurred_at_ms * 1_000,
        provider_local_timestamp_us=(occurred_at_ms + 100) * 1_000,
        native_channel="liquidations",
        semantic_era="fixture-era-v1",
        import_run_id="accepted-import-v1",
        raw_file_sha256="a" * 64,
        raw_row_number=index,
        raw_side="Sell" if index % 2 else "Buy",
    )


def _write_accepted_import(root: Path) -> Path:
    root.mkdir(parents=True)
    events = tuple(
        sorted(
            (
                _event(source="binance-usdm", occurred_at_ms=1_000_000, index=1),
                _event(source="bybit-linear", occurred_at_ms=1_050_000, index=2),
                _event(source="binance-usdm", occurred_at_ms=1_205_000, index=3),
                _event(source="bybit-linear", occurred_at_ms=1_250_000, index=4),
            ),
            key=lambda event: (
                event.available_at_ms,
                event.occurred_at_ms,
                event.source,
                event.symbol,
                event.source_event_id,
            ),
        )
    )
    manifest = HistoricalImportManifest(
        schema_version=1,
        import_run_id="accepted-import-v1",
        provider_id="first-party",
        requested_start_ms=900_000,
        requested_end_ms=2_000_000,
        symbols=("BTCUSDT",),
        source_commit_sha=CODE_SHA,
        parser_version="fixture-parser-v1",
        decision_contract_sha256="b" * 64,
        license_classification="test-fixture",
        license_reference="fixture-only",
        storage_root="fixture://accepted-import-v1",
        raw_files=(
            RawFileDescriptor(
                relative_path="raw.ndjson",
                sha256="a" * 64,
                size_bytes=1,
                provider_id="first-party",
                provider_exchange="mixed-fixture",
                symbol="BTCUSDT",
                requested_date="fixture",
                content_encoding="identity",
                parser_hint="fixture",
            ),
        ),
        protected_holdout_start_ms=HOLDOUT_START_MS,
        protected_holdout_excluded=True,
        created_at_utc="2026-07-29T00:00:00Z",
    )
    manifest_path = root / "manifest.json"
    events_path = root / "events.jsonl"
    acceptance_path = root / "acceptance.json"
    rejections_path = root / "rejections.json"
    index_path = root / "artifacts.json"
    manifest_path.write_bytes(_json_bytes(manifest.as_json_dict()))
    events_path.write_bytes(b"".join(_json_bytes(event.as_json_dict()) for event in events))
    rejections_path.write_bytes(_json_bytes([]))
    accepted_ids = "\n".join(sorted(event.source_event_id for event in events))
    acceptance = {
        "schema_version": 1,
        "import_run_id": manifest.import_run_id,
        "manifest_identity_sha256": manifest.identity_sha256,
        "status": "pass",
        "total_records": len(events),
        "accepted_records": len(events),
        "rejected_records": 0,
        "duplicate_records": 0,
        "rejection_reasons": {},
        "accepted_event_ids_sha256": sha256(accepted_ids.encode()).hexdigest(),
        "earliest_occurred_at_ms": min(event.occurred_at_ms for event in events),
        "latest_occurred_at_ms": max(event.occurred_at_ms for event in events),
        "minimum_availability_latency_ms": 100,
        "maximum_availability_latency_ms": 100,
        "protected_holdout_excluded": True,
    }
    acceptance_path.write_bytes(_json_bytes(acceptance))
    artifacts = {
        "manifest.json": sha256_file(manifest_path),
        "events.jsonl": sha256_file(events_path),
        "acceptance.json": sha256_file(acceptance_path),
        "rejections.json": sha256_file(rejections_path),
    }
    index_path.write_bytes(
        _json_bytes(
            {
                "schema_version": 1,
                "import_run_id": manifest.import_run_id,
                "manifest_identity_sha256": manifest.identity_sha256,
                "artifacts": artifacts,
            }
        )
    )
    return root


def _market(*, metric_available_at_ms: int = 1_290_000) -> MarketContextSnapshot:
    values = {
        "quote_volume_24h_usd": "1000000000",
        "vwap": "100",
        "vwma": "100",
        "atr_ratio": "0.01",
        "volatility_ratio": "1.2",
        "wick_ratio": "0.8",
        "trend_return_ratio": "0.02",
        "spread_bps": "2",
        "market_wide_liquidation_intensity": "1.1",
    }
    return MarketContextSnapshot(
        symbol="BTCUSDT",
        decision_timestamp_ms=1_300_000,
        decision_price=Decimal("100"),
        completed_candle_close_ms=1_280_000,
        metrics=tuple(
            AvailableMetric(
                name=name,
                value=Decimal(value),
                available_at_ms=metric_available_at_ms,
                source="completed_candle.fixture",
            )
            for name, value in sorted(values.items())
        ),
    )


def _universe() -> DynamicUniverseSnapshot:
    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version="fixture-policy-v1",
        selected_at_ms=1_200_000,
        decisions=(
            UniverseInstrumentDecision(
                canonical_instrument_id="bybit:perpetual:BTCUSDT",
                canonical_symbol="BTCUSDT",
                included=True,
                reason_codes=("eligible",),
            ),
        ),
    )


def _write_snapshot_files(
    package_root: Path,
    *,
    market: MarketContextSnapshot | None = None,
) -> tuple[Path, Path]:
    market = market or _market()
    market_path = package_root / "market-context.jsonl"
    universe_path = package_root / "universe-history.jsonl"
    market_path.write_bytes(
        _json_bytes(
            {
                "schema_version": MARKET_CONTEXT_ROW_SCHEMA,
                "snapshot": json.loads(canonical_json(market)),
                "snapshot_sha256": canonical_sha256(market),
            }
        )
    )
    universe = _universe()
    universe_path.write_bytes(
        _json_bytes(
            {
                "schema_version": UNIVERSE_HISTORY_ROW_SCHEMA,
                "snapshot": json.loads(canonical_json(universe)),
                "snapshot_sha256": universe.snapshot_hash,
            }
        )
    )
    return market_path, universe_path


def _write_request(package_root: Path) -> Path:
    accepted = load_accepted_import(package_root / "accepted")
    market_path = package_root / "market-context.jsonl"
    universe_path = package_root / "universe-history.jsonl"
    payload = {
        "schema_version": MATERIALIZATION_REQUEST_SCHEMA,
        "accepted_imports": [
            {
                "relative_path": "accepted",
                "import_run_id": accepted.selection.import_run_id,
                "selection_sha256": accepted.selection.selection_sha256,
            }
        ],
        "market_context": {
            "relative_path": market_path.name,
            "sha256": sha256_file(market_path),
        },
        "universe_history": {
            "relative_path": universe_path.name,
            "sha256": sha256_file(universe_path),
        },
        "dataset": {
            "dataset_version": "wickhunter-real-fixture-v1",
            "code_sha": CODE_SHA,
            "burst_window_ms": 100_000,
            "partition_span_ms": 1_000_000,
            "minimum_history_events": 2,
            "maximum_source_age_ms": 500_000,
            "split_geometry": {
                "geometry_version": "fixture-splits-v1",
                "windows": [{"name": "train", "start_ms": 1_250_000, "end_ms": 1_350_000}],
                "label_horizon_ms": 0,
                "embargo_ms": 0,
                "protected_holdout_start_ms": HOLDOUT_START_MS,
            },
        },
        "trading_credentials_present": False,
        "trading_authorized": False,
        "execution_enabled": False,
        "model_execution_authorized": False,
        "live_capital_authorized": False,
    }
    request_path = package_root / "request.json"
    request_path.write_bytes(_json_bytes(payload))
    return request_path


def _package(tmp_path: Path) -> tuple[Path, Path]:
    package_root = tmp_path / "package"
    package_root.mkdir()
    _write_accepted_import(package_root / "accepted")
    _write_snapshot_files(package_root)
    return package_root, _write_request(package_root)


def test_materializes_and_independently_verifies_wh01_dataset(tmp_path: Path) -> None:
    package_root, request_path = _package(tmp_path)
    request = load_materialization_request(request_path)

    preflight = preflight_materialization_package(
        package_root=package_root,
        request=request,
    )
    assert preflight.status == "ready"
    assert preflight.market_snapshot_count == 1
    assert preflight.universe_snapshot_count == 1

    output_root = tmp_path / "dataset"
    result = materialize_wickhunter_dataset_package(
        package_root=package_root,
        request=request,
        output_root=output_root,
    )
    verified = verify_materialized_dataset(output_root)

    assert result.total_rows == 1
    assert result.partition_count == 1
    assert verified["manifest_sha256"] == result.manifest_sha256
    assert verified["model_execution_authorized"] is False
    assert result.model_execution_authorized is False
    assert result.trading_authorized is False
    assert result.live_capital_authorized is False


def test_preflight_reports_missing_inputs_without_creating_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    package_root, request_path = _package(tmp_path)
    (package_root / "market-context.jsonl").unlink()

    exit_code = main(
        [
            "preflight",
            "--package-root",
            str(package_root),
            "--request",
            str(request_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["status"] == "blocked"
    assert payload["missing_paths"] == ["market-context.jsonl"]
    assert payload["model_execution_authorized"] is False


def test_rejects_tampered_market_context_file(tmp_path: Path) -> None:
    package_root, request_path = _package(tmp_path)
    with (package_root / "market-context.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    request = load_materialization_request(request_path)

    with pytest.raises(ValueError, match="market-context file hash mismatch"):
        preflight_materialization_package(package_root=package_root, request=request)


def test_rejects_market_metric_from_future(tmp_path: Path) -> None:
    package_root = tmp_path / "package"
    package_root.mkdir()
    _write_accepted_import(package_root / "accepted")
    _write_snapshot_files(package_root, market=_market(metric_available_at_ms=1_300_001))
    request_path = _write_request(package_root)
    request = load_materialization_request(request_path)

    with pytest.raises(ValueError, match="unavailable at decision time"):
        preflight_materialization_package(package_root=package_root, request=request)


def test_rejects_authority_or_path_traversal(tmp_path: Path) -> None:
    _, request_path = _package(tmp_path)
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["trading_authorized"] = True
    request_path.write_bytes(_json_bytes(payload))
    with pytest.raises(ValueError, match="trading_authorized must be false"):
        load_materialization_request(request_path)

    payload["trading_authorized"] = False
    payload["market_context"]["relative_path"] = "../market-context.jsonl"
    request_path.write_bytes(_json_bytes(payload))
    with pytest.raises(ValueError, match="must stay within the package root"):
        load_materialization_request(request_path)


def test_independent_verifier_rejects_partition_tamper(tmp_path: Path) -> None:
    package_root, request_path = _package(tmp_path)
    request = load_materialization_request(request_path)
    output_root = tmp_path / "dataset"
    materialize_wickhunter_dataset_package(
        package_root=package_root,
        request=request,
        output_root=output_root,
    )
    partition = next((output_root / "features").rglob("*.jsonl"))
    with partition.open("a", encoding="utf-8") as handle:
        handle.write("{}\n")

    with pytest.raises(ValueError, match="partition hash mismatch"):
        verify_materialized_dataset(output_root)
