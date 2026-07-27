from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

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
from ai_platform.wickhunter.contracts import AvailableMetric, MarketContextSnapshot
from ai_platform.wickhunter.dataset import (
    DatasetSplitGeometry,
    DatasetSplitWindow,
    WickHunterDatasetBuildRequest,
    build_wickhunter_dataset,
    load_accepted_import,
    normalize_historical_event,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


HOLDOUT_START_MS = 10_000_000
CODE_SHA = "1" * 40


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _event(
    *,
    source: str,
    occurred_at_ms: int,
    notional: str,
    index: int,
) -> HistoricalLiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(notional) / price
    return HistoricalLiquidationEvent(
        schema_version=1,
        source=source,
        symbol="BTCUSDT",
        liquidated_position_side=(
            LiquidatedPositionSide.LONG if index % 2 else LiquidatedPositionSide.SHORT
        ),
        occurred_at_ms=occurred_at_ms,
        available_at_ms=occurred_at_ms + 1_000,
        available_at_semantics=AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP,
        price=price,
        quantity=quantity,
        notional_usd=Decimal(notional),
        source_event_id=sha256(f"event-{index}".encode()).hexdigest(),
        provider_event_id=f"provider-{index}",
        dataset_origin=DatasetOrigin.HISTORICAL_VENDOR,
        historical_provider="tardis",
        provider_exchange=("bybit" if source == "bybit-linear" else "binance-futures"),
        provider_timestamp_us=occurred_at_ms * 1_000,
        provider_local_timestamp_us=(occurred_at_ms + 1_000) * 1_000,
        native_channel="liquidations",
        semantic_era="fixture-era-v1",
        import_run_id="accepted-import-v1",
        raw_file_sha256="a" * 64,
        raw_row_number=index,
        raw_side="Sell" if index % 2 else "Buy",
    )


def _events() -> tuple[HistoricalLiquidationEvent, ...]:
    timestamps = (
        1_000_000,
        1_100_000,
        1_200_000,
        1_950_000,
        1_970_000,
        3_000_000,
        3_950_000,
        3_970_000,
    )
    return tuple(
        _event(
            source="bybit-linear" if index % 2 else "binance-usdm",
            occurred_at_ms=timestamp,
            notional=str(10_000 + index * 1_000),
            index=index,
        )
        for index, timestamp in enumerate(timestamps, start=1)
    )


def _write_accepted_import(root: Path, *, status: str = "pass") -> Path:
    root.mkdir()
    events = _events()
    manifest = HistoricalImportManifest(
        schema_version=1,
        import_run_id="accepted-import-v1",
        provider_id="tardis",
        requested_start_ms=900_000,
        requested_end_ms=5_000_000,
        symbols=("BTCUSDT",),
        source_commit_sha=CODE_SHA,
        parser_version="tardis-local-v1",
        decision_contract_sha256="b" * 64,
        license_classification="test-fixture",
        license_reference="fixture-only",
        storage_root="fixture://accepted-import-v1",
        raw_files=(
            RawFileDescriptor(
                relative_path="raw.csv",
                sha256="a" * 64,
                size_bytes=1,
                provider_id="tardis",
                provider_exchange="mixed-fixture",
                symbol="BTCUSDT",
                requested_date="fixture",
                content_encoding="identity",
                parser_hint="fixture",
            ),
        ),
        protected_holdout_start_ms=HOLDOUT_START_MS,
        protected_holdout_excluded=True,
        created_at_utc="2026-07-27T00:00:00Z",
    )
    manifest_path = root / "manifest.json"
    events_path = root / "events.jsonl"
    rejections_path = root / "rejections.json"
    acceptance_path = root / "acceptance.json"
    index_path = root / "artifacts.json"
    manifest_path.write_bytes(_json_bytes(manifest.as_json_dict()))
    events_path.write_bytes(b"".join(_json_bytes(event.as_json_dict()) for event in events))
    rejections_path.write_bytes(_json_bytes([]))
    accepted_ids = "\n".join(sorted(event.source_event_id for event in events))
    acceptance = {
        "schema_version": 1,
        "import_run_id": manifest.import_run_id,
        "manifest_identity_sha256": manifest.identity_sha256,
        "status": status,
        "total_records": len(events),
        "accepted_records": len(events),
        "rejected_records": 0,
        "duplicate_records": 0,
        "rejection_reasons": {},
        "accepted_event_ids_sha256": sha256(accepted_ids.encode()).hexdigest(),
        "earliest_occurred_at_ms": min(event.occurred_at_ms for event in events),
        "latest_occurred_at_ms": max(event.occurred_at_ms for event in events),
        "minimum_availability_latency_ms": 1_000,
        "maximum_availability_latency_ms": 1_000,
        "protected_holdout_excluded": True,
    }
    acceptance_path.write_bytes(_json_bytes(acceptance))
    artifacts = {
        "manifest.json": sha256_file(manifest_path),
        "events.jsonl": sha256_file(events_path),
        "rejections.json": sha256_file(rejections_path),
        "acceptance.json": sha256_file(acceptance_path),
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


def _market(decision_timestamp_ms: int) -> MarketContextSnapshot:
    completed_close = decision_timestamp_ms - 60_000
    available_at = decision_timestamp_ms - 30_000
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
        decision_timestamp_ms=decision_timestamp_ms,
        decision_price=Decimal("100"),
        completed_candle_close_ms=completed_close,
        metrics=tuple(
            AvailableMetric(
                name=name,
                value=Decimal(value),
                available_at_ms=available_at,
                source="completed_candle.fixture",
            )
            for name, value in sorted(values.items())
        ),
    )


def _universe(selected_at_ms: int = 1_800_000) -> DynamicUniverseSnapshot:
    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version="fixture-policy-v1",
        selected_at_ms=selected_at_ms,
        decisions=(
            UniverseInstrumentDecision(
                canonical_instrument_id="bybit:perpetual:BTCUSDT",
                canonical_symbol="BTCUSDT",
                included=True,
                reason_codes=("eligible",),
            ),
        ),
    )


def _request() -> WickHunterDatasetBuildRequest:
    return WickHunterDatasetBuildRequest(
        dataset_version="wickhunter-fixture-dataset-v1",
        code_sha=CODE_SHA,
        burst_window_ms=60_000,
        partition_span_ms=1_000_000,
        minimum_history_events=3,
        maximum_source_age_ms=2_000_000,
        split_geometry=DatasetSplitGeometry(
            geometry_version="fixture-splits-v1",
            windows=(
                DatasetSplitWindow("train", 1_900_000, 2_100_000),
                DatasetSplitWindow("development", 3_900_000, 4_100_000),
            ),
            label_horizon_ms=100_000,
            embargo_ms=100_000,
            protected_holdout_start_ms=HOLDOUT_START_MS,
        ),
    )


def test_loads_only_hash_valid_accepted_import(tmp_path: Path) -> None:
    root = _write_accepted_import(tmp_path / "accepted")

    bundle = load_accepted_import(root)

    assert bundle.selection.accepted_records == 8
    assert bundle.selection.provider_id == "tardis"
    assert tuple(event.source for event in bundle.events[:2]) == (
        "bybit-linear",
        "binance-usdm",
    )


def test_rejects_non_accepted_import(tmp_path: Path) -> None:
    root = _write_accepted_import(tmp_path / "rejected", status="fail")

    with pytest.raises(ValueError, match="not accepted"):
        load_accepted_import(root)


def test_rejects_artifact_hash_mismatch(tmp_path: Path) -> None:
    root = _write_accepted_import(tmp_path / "tampered")
    with (root / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")

    with pytest.raises(ValueError, match="artifact hash mismatch"):
        load_accepted_import(root)


def test_normalization_preserves_source_and_availability() -> None:
    historical = _events()[0]

    normalized = normalize_historical_event(historical)

    assert normalized.source == historical.source
    assert normalized.source_event_id == historical.source_event_id
    assert normalized.received_at_ms == historical.available_at_ms
    assert normalized.occurred_at_ms == historical.occurred_at_ms


def test_split_geometry_enforces_purge_embargo_and_holdout() -> None:
    with pytest.raises(ValueError, match="purge/embargo"):
        DatasetSplitGeometry(
            geometry_version="invalid",
            windows=(
                DatasetSplitWindow("train", 1_000, 2_000),
                DatasetSplitWindow("development", 2_050, 3_000),
            ),
            label_horizon_ms=100,
            embargo_ms=100,
            protected_holdout_start_ms=10_000,
        )

    geometry = _request().split_geometry
    with pytest.raises(ValueError, match="protected final holdout"):
        geometry.classify(HOLDOUT_START_MS)


def test_builds_deterministic_atomic_source_aware_dataset(tmp_path: Path) -> None:
    accepted = _write_accepted_import(tmp_path / "accepted")
    output_one = tmp_path / "dataset-one"
    output_two = tmp_path / "dataset-two"
    markets = (_market(2_000_000), _market(4_000_000))

    first = build_wickhunter_dataset(
        output_root=output_one,
        request=_request(),
        accepted_import_roots=(accepted,),
        market_snapshots=markets,
        universe_snapshots=(_universe(),),
    )
    second = build_wickhunter_dataset(
        output_root=output_two,
        request=_request(),
        accepted_import_roots=(accepted,),
        market_snapshots=tuple(reversed(markets)),
        universe_snapshots=(_universe(),),
    )

    assert first.manifest.total_rows == 2
    assert first.manifest.model_execution_authorized is False
    assert first.manifest.manifest_sha256 == second.manifest.manifest_sha256
    assert tuple(part.sha256 for part in first.manifest.partitions) == tuple(
        part.sha256 for part in second.manifest.partitions
    )
    assert (output_one / "manifest.json").is_file()
    assert (output_one / "sources.json").is_file()
    assert (output_one / "universe" / "history.jsonl").is_file()
    rows: list[dict[str, Any]] = []
    for partition in first.manifest.partitions:
        rows.extend(
            json.loads(line)
            for line in (output_one / partition.relative_path)
            .read_text(encoding="utf-8")
            .splitlines()
        )
    assert {row["split_name"] for row in rows} == {"train", "development"}
    aggregate_sources = {
        item["source"] for row in rows for item in row["feature"]["source_aggregates"]
    }
    assert aggregate_sources == {"binance-usdm", "bybit-linear"}
    assert all(row["feature_available_at_ms"] <= row["decision_timestamp_ms"] for row in rows)
    assert all(len(row["row_sha256"]) == 64 for row in rows)


def test_refuses_to_overwrite_dataset_root(tmp_path: Path) -> None:
    accepted = _write_accepted_import(tmp_path / "accepted")
    output = tmp_path / "dataset"
    output.mkdir()

    with pytest.raises(FileExistsError):
        build_wickhunter_dataset(
            output_root=output,
            request=_request(),
            accepted_import_roots=(accepted,),
            market_snapshots=(_market(2_000_000),),
            universe_snapshots=(_universe(),),
        )


def test_rejects_future_market_availability(tmp_path: Path) -> None:
    accepted = _write_accepted_import(tmp_path / "accepted")
    market = _market(2_000_000)
    future_metric = AvailableMetric(
        name="spread_bps",
        value=Decimal("2"),
        available_at_ms=2_000_001,
        source="completed_candle.fixture",
    )
    metrics = tuple(metric for metric in market.metrics if metric.name != "spread_bps") + (
        future_metric,
    )
    invalid_market = MarketContextSnapshot(
        symbol=market.symbol,
        decision_timestamp_ms=market.decision_timestamp_ms,
        decision_price=market.decision_price,
        completed_candle_close_ms=market.completed_candle_close_ms,
        metrics=metrics,
    )

    with pytest.raises(ValueError, match="not available at decision time"):
        build_wickhunter_dataset(
            output_root=tmp_path / "dataset",
            request=_request(),
            accepted_import_roots=(accepted,),
            market_snapshots=(invalid_market,),
            universe_snapshots=(_universe(),),
        )


def test_rejects_future_only_universe_history(tmp_path: Path) -> None:
    accepted = _write_accepted_import(tmp_path / "accepted")

    with pytest.raises(ValueError, match="no dynamic-universe snapshot"):
        build_wickhunter_dataset(
            output_root=tmp_path / "dataset",
            request=_request(),
            accepted_import_roots=(accepted,),
            market_snapshots=(_market(2_000_000),),
            universe_snapshots=(_universe(2_000_001),),
        )
