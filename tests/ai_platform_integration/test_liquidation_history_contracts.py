from __future__ import annotations

from dataclasses import replace
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.historical.acceptance import (
    AcceptanceStatus,
    evaluate_historical_import,
)
from ai_platform.research.liquidations.historical.contracts import (
    AvailableAtSemantics,
    DatasetOrigin,
    HistoricalLiquidationEvent,
    decimal_text,
    deterministic_historical_event_id,
    historical_event_fingerprint,
    historical_event_from_json_dict,
)
from ai_platform.research.liquidations.historical.manifests import (
    HistoricalImportManifest,
    RawFileDescriptor,
)
from ai_platform.research.liquidations.historical.semantic_eras import (
    DEFAULT_SEMANTIC_ERAS,
    utc_ms,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "ai_platform/research/liquidations/historical"
RAW_SHA = "a" * 64
COMMIT_SHA = "b" * 40
DECISION_SHA = "c" * 64


def _manifest() -> HistoricalImportManifest:
    return HistoricalImportManifest(
        schema_version=1,
        import_run_id="liquid20-history-test",
        provider_id="tardis",
        requested_start_ms=utc_ms("2025-03-01T00:00:00Z"),
        requested_end_ms=utc_ms("2025-03-02T00:00:00Z"),
        symbols=("BTCUSDT",),
        source_commit_sha=COMMIT_SHA,
        parser_version="tardis-v1",
        decision_contract_sha256=DECISION_SHA,
        license_classification="public-free-sample",
        license_reference="H0 decision contract",
        storage_root="historical/imports/tardis/liquid20-history-test",
        raw_files=(
            RawFileDescriptor(
                relative_path="raw/bybit/BTCUSDT/2025-03-01.csv.gz",
                sha256=RAW_SHA,
                size_bytes=123,
                provider_id="tardis",
                provider_exchange="bybit",
                symbol="BTCUSDT",
                requested_date="2025-03-01",
                content_encoding="gzip",
                parser_hint="liquidations-csv-v1",
            ),
        ),
        protected_holdout_start_ms=utc_ms("2026-08-01T00:00:00Z"),
        protected_holdout_excluded=True,
        created_at_utc="2026-07-26T12:00:00Z",
    )


def _event(*, row_number: int = 2, local_offset_us: int = 123_000) -> HistoricalLiquidationEvent:
    timestamp_us = 1_740_787_200_123_456
    local_timestamp_us = timestamp_us + local_offset_us
    price = Decimal("100000.50")
    quantity = Decimal("0.25")
    fingerprint = historical_event_fingerprint(
        historical_provider="tardis",
        provider_exchange="bybit",
        symbol="BTCUSDT",
        provider_timestamp_us=timestamp_us,
        provider_local_timestamp_us=local_timestamp_us,
        liquidated_position_side=LiquidatedPositionSide.LONG,
        price=price,
        quantity=quantity,
        raw_side="sell",
        provider_event_id=None,
    )
    event_id = deterministic_historical_event_id(
        historical_provider="tardis",
        raw_file_sha256=RAW_SHA,
        raw_row_number=row_number,
        event_fingerprint_sha256=fingerprint,
    )
    return HistoricalLiquidationEvent(
        schema_version=1,
        source="bybit-linear",
        symbol="BTCUSDT",
        liquidated_position_side=LiquidatedPositionSide.LONG,
        occurred_at_ms=timestamp_us // 1000,
        available_at_ms=local_timestamp_us // 1000,
        available_at_semantics=AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP,
        price=price,
        quantity=quantity,
        notional_usd=price * quantity,
        source_event_id=event_id,
        provider_event_id=None,
        dataset_origin=DatasetOrigin.SYNTHETIC_FIXTURE,
        historical_provider="tardis",
        provider_exchange="bybit",
        provider_timestamp_us=timestamp_us,
        provider_local_timestamp_us=local_timestamp_us,
        native_channel="allLiquidation",
        semantic_era="tardis-bybit-all-liquidation-v1",
        import_run_id="liquid20-history-test",
        raw_file_sha256=RAW_SHA,
        raw_row_number=row_number,
        raw_side="sell",
    )


def test_decimal_and_event_identity_are_deterministic() -> None:
    assert decimal_text(Decimal("100.5000")) == "100.5"
    first = _event(row_number=2)
    second = _event(row_number=2)
    third = _event(row_number=3)
    assert first.source_event_id == second.source_event_id
    assert first.event_fingerprint_sha256 == third.event_fingerprint_sha256
    assert first.source_event_id != third.source_event_id


def test_event_round_trip_preserves_timestamp_provenance() -> None:
    event = _event()
    payload = event.as_json_dict()
    assert "received_at_ms" not in payload
    assert payload["available_at_semantics"] == "vendor_capture_timestamp"
    assert historical_event_from_json_dict(payload) == event


def test_manifest_identity_excludes_creation_clock() -> None:
    manifest = _manifest()
    changed = replace(manifest, created_at_utc="2026-07-27T00:00:00Z")
    assert manifest.identity_sha256 == changed.identity_sha256


def test_manifest_rejects_protected_holdout_overlap() -> None:
    manifest = _manifest()
    with pytest.raises(ValueError, match="protected final holdout"):
        replace(
            manifest,
            requested_end_ms=utc_ms("2026-08-02T00:00:00Z"),
        )


def test_semantic_era_boundary_is_explicit() -> None:
    with pytest.raises(LookupError):
        DEFAULT_SEMANTIC_ERAS.resolve(
            provider_id="tardis",
            source="bybit-linear",
            timestamp_ms=utc_ms("2025-02-25T23:59:59Z"),
        )
    era = DEFAULT_SEMANTIC_ERAS.resolve(
        provider_id="tardis",
        source="bybit-linear",
        timestamp_ms=utc_ms("2025-02-26T00:00:00Z"),
    )
    assert era.era_id == "tardis-bybit-all-liquidation-v1"


def test_acceptance_passes_clean_event_and_rejects_duplicate() -> None:
    manifest = _manifest()
    event = _event()
    clean = evaluate_historical_import(
        events=[event], manifest=manifest, semantic_eras=DEFAULT_SEMANTIC_ERAS
    )
    assert clean.status is AcceptanceStatus.PASS
    assert clean.accepted_records == 1

    duplicate = evaluate_historical_import(
        events=[event, replace(event, raw_row_number=3, source_event_id="d" * 64)],
        manifest=manifest,
        semantic_eras=DEFAULT_SEMANTIC_ERAS,
    )
    assert duplicate.status is AcceptanceStatus.FAIL
    assert duplicate.duplicate_records == 1
    assert duplicate.rejection_reasons == {"duplicate_fingerprint": 1}


def test_acceptance_rejects_negative_provider_latency() -> None:
    event = _event(local_offset_us=-1_000)
    report = evaluate_historical_import(
        events=[event], manifest=_manifest(), semantic_eras=DEFAULT_SEMANTIC_ERAS
    )
    assert report.status is AcceptanceStatus.FAIL
    assert report.rejection_reasons == {"negative_availability_latency": 1}


@pytest.mark.parametrize(
    "schema_name,payload",
    (
        ("historical-event-v1.schema.json", lambda: _event().as_json_dict()),
        ("historical-import-manifest-v1.schema.json", lambda: _manifest().as_json_dict()),
        (
            "historical-import-acceptance-v1.schema.json",
            lambda: evaluate_historical_import(
                events=[_event()],
                manifest=_manifest(),
                semantic_eras=DEFAULT_SEMANTIC_ERAS,
            ).as_json_dict(),
        ),
    ),
)
def test_draft_2020_12_schemas_validate(
    schema_name: str, payload: Callable[[], dict[str, object]]
) -> None:
    schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload())
