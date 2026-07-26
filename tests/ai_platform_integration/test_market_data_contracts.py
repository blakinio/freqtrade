from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from jsonschema import ValidationError

from ai_platform.market_data.contracts import (
    AvailabilityTimestampKind,
    CaptureManifest,
    CaptureRequest,
    ChannelFamily,
    CompressionPolicy,
    EventType,
    Exchange,
    FrozenJsonObject,
    GapMarker,
    GapReason,
    InstrumentSnapshot,
    MarketType,
    OutputImmutabilityState,
    RawMarketEventEnvelope,
    SegmentManifest,
    assert_order_book_reconstructible,
    canonical_instrument_id,
    canonical_sha256,
    load_and_validate_contract_json,
    raw_payload_sha256,
    refuse_trading_credentials,
    validate_contract_payload,
)

COMMIT = "a" * 40
SOURCE_HASH = "b" * 64
CONTENT_HASH = "c" * 64


def spot_instrument(*, native_id: str = "BTCUSDT") -> InstrumentSnapshot:
    return InstrumentSnapshot(
        schema_version=1,
        exchange=Exchange.BINANCE,
        market_type=MarketType.SPOT,
        native_instrument_id=native_id,
        canonical_instrument_id=canonical_instrument_id(
            Exchange.BINANCE,
            MarketType.SPOT,
            native_id,
        ),
        native_symbol=native_id,
        canonical_symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        settlement_asset=None,
        contract_type=MarketType.SPOT,
        contract_value=None,
        contract_value_unit=None,
        tick_size=Decimal("0.10"),
        quantity_step=Decimal("0.00001"),
        active=True,
        listed_at_ms=1_600_000_000_000,
        expires_at_ms=None,
        source_snapshot_id="binance-spot-instruments-1",
        source_snapshot_sha256=SOURCE_HASH,
    )


def derivative_instrument(
    *,
    market_type: MarketType = MarketType.PERPETUAL,
    expires_at_ms: int | None = None,
) -> InstrumentSnapshot:
    native_id = "BTCUSDT" if market_type is MarketType.PERPETUAL else "BTCUSDT_260925"
    return InstrumentSnapshot(
        schema_version=1,
        exchange=Exchange.BYBIT,
        market_type=market_type,
        native_instrument_id=native_id,
        canonical_instrument_id=canonical_instrument_id(
            Exchange.BYBIT,
            market_type,
            native_id,
        ),
        native_symbol=native_id,
        canonical_symbol="BTC/USDT:USDT",
        base_asset="BTC",
        quote_asset="USDT",
        settlement_asset="USDT",
        contract_type=market_type,
        contract_value=Decimal("1"),
        contract_value_unit="base_asset",
        tick_size=Decimal("0.10"),
        quantity_step=Decimal("0.001"),
        active=True,
        listed_at_ms=1_600_000_000_000,
        expires_at_ms=expires_at_ms,
        source_snapshot_id="bybit-linear-instruments-1",
        source_snapshot_sha256=SOURCE_HASH,
    )


def raw_event(
    *,
    timestamp_kind: AvailabilityTimestampKind = (
        AvailabilityTimestampKind.LIVE_COLLECTOR_RECEIVE
    ),
) -> RawMarketEventEnvelope:
    payload = {"price": "100", "quantity": "2"}
    return RawMarketEventEnvelope(
        schema_version=1,
        event_type=EventType.TRADE,
        exchange=Exchange.BINANCE,
        market_type=MarketType.SPOT,
        instrument_id=canonical_instrument_id(
            Exchange.BINANCE,
            MarketType.SPOT,
            "BTCUSDT",
        ),
        native_instrument_id="BTCUSDT",
        native_symbol="BTCUSDT",
        canonical_symbol="BTC/USDT",
        exchange_timestamp_ms=1_700_000_000_000,
        availability_timestamp_ms=1_700_000_000_005,
        availability_timestamp_kind=timestamp_kind,
        ingestion_timestamp_ms=1_700_000_000_006,
        connection_id="connection-1",
        capture_run_id="capture-1",
        sequence=None,
        previous_sequence=None,
        snapshot=False,
        raw_payload_sha256=raw_payload_sha256(payload),
        raw_payload=payload,
    )


def segment() -> SegmentManifest:
    return SegmentManifest.create(
        capture_run_id="capture-1",
        source_id="binance-spot",
        channel_family=ChannelFamily.TRADES,
        connection_id="connection-1",
        instrument_ids=(
            canonical_instrument_id(Exchange.BINANCE, MarketType.SPOT, "BTCUSDT"),
        ),
        opened_at_ms=1_700_000_000_000,
        closed_at_ms=1_700_000_001_000,
        first_event_id="event-1",
        last_event_id="event-2",
        event_count=2,
        first_sequence=None,
        last_sequence=None,
        byte_count=120,
        compression=CompressionPolicy.ZSTD,
        content_sha256=CONTENT_HASH,
    )


def capture_request() -> CaptureRequest:
    return CaptureRequest(
        schema_version=1,
        source_catalog_version="market-data-source-catalog-v1",
        universe_snapshot_ids=("top20-high-frequency-v1:abc",),
        exchanges=(Exchange.BINANCE, Exchange.BYBIT),
        market_types=(MarketType.SPOT, MarketType.PERPETUAL),
        channel_families=(ChannelFamily.TRADES, ChannelFamily.ORDER_BOOK_DELTA),
        start_condition=FrozenJsonObject.from_mapping({"kind": "manual"}),
        end_condition=FrozenJsonObject.from_mapping({"maximum_duration_seconds": 60}),
        raw_segment_policy=FrozenJsonObject.from_mapping({"maximum_bytes": 1_000_000}),
        compression_policy=CompressionPolicy.ZSTD,
        clock_policy=FrozenJsonObject.from_mapping({"preserve_source_timestamps": True}),
        gap_policy=FrozenJsonObject.from_mapping({"fail_closed": True}),
        credential_policy="public_market_data_only_no_trading_credentials",
        output_root_identity="private-object-store:market-data-v1",
        code_commit=COMMIT,
    )


def test_valid_event_envelope_and_schema() -> None:
    event = raw_event()
    assert event.event_id == raw_event().event_id
    validate_contract_payload("RawMarketEventEnvelope", event.as_json_dict())


def test_event_timestamp_kind_is_explicit_and_identity_bearing() -> None:
    live = raw_event()
    provider = raw_event(timestamp_kind=AvailabilityTimestampKind.PROVIDER_CAPTURE)
    assert live.availability_timestamp_kind.value == "live_collector_receive"
    assert provider.availability_timestamp_kind.value == "provider_capture"
    assert live.event_id != provider.event_id


def test_invalid_event_envelopes_fail_closed() -> None:
    event = raw_event()
    with pytest.raises(ValueError, match="instrument_id"):
        replace(event, instrument_id="bybit:spot:BTCUSDT")
    with pytest.raises(ValueError, match="raw_payload_sha256"):
        replace(event, raw_payload_sha256="0" * 64)
    with pytest.raises(ValueError, match="exactly one"):
        replace(event, raw_payload_ref="immutable://same-payload")
    with pytest.raises(ValueError, match="snapshot=true"):
        replace(event, snapshot=True)


def test_raw_payload_reference_is_valid_without_inlining_payload() -> None:
    event = replace(
        raw_event(),
        raw_payload=None,
        raw_payload_ref="segments/segment-1#record-2",
    )
    assert event.as_json_dict()["raw_payload"] is None
    validate_contract_payload("RawMarketEventEnvelope", event.as_json_dict())


def test_valid_spot_and_derivative_instrument_snapshots() -> None:
    spot = spot_instrument()
    perpetual = derivative_instrument()
    dated = derivative_instrument(
        market_type=MarketType.DATED_FUTURE,
        expires_at_ms=1_800_000_000_000,
    )
    for instrument in (spot, perpetual, dated):
        validate_contract_payload("InstrumentSnapshot", instrument.as_json_dict())
        assert len(instrument.content_sha256) == 64


def test_invalid_derivative_contract_metadata_is_rejected() -> None:
    perpetual = derivative_instrument()
    with pytest.raises(ValueError, match="contract_value"):
        replace(perpetual, contract_value=None)
    with pytest.raises(ValueError, match="expires_at_ms"):
        replace(perpetual, expires_at_ms=1_800_000_000_000)
    with pytest.raises(ValueError, match="dated futures require"):
        derivative_instrument(market_type=MarketType.DATED_FUTURE)


def test_capture_request_is_deterministic_and_credentials_are_refused() -> None:
    request = capture_request()
    assert request.request_sha256 == capture_request().request_sha256
    validate_contract_payload("CaptureRequest", request.as_json_dict())
    refuse_trading_credentials({})
    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        refuse_trading_credentials({"BINANCE_API_KEY": "secret"})
    with pytest.raises(ValueError, match="credential_policy"):
        replace(request, credential_policy="exchange_credentials_allowed")


def test_closed_segment_identity_and_self_hash_are_deterministic() -> None:
    first = segment()
    second = segment()
    assert first.segment_id == second.segment_id
    assert first.manifest_sha256 == second.manifest_sha256
    validate_contract_payload("SegmentManifest", first.as_json_dict())
    with pytest.raises(ValueError, match="manifest_sha256"):
        replace(first, event_count=3)
    with pytest.raises(ValueError, match="immutable"):
        replace(first, immutable=False)


def test_sequence_gap_representation_and_order_book_fail_closed() -> None:
    gap = GapMarker.create(
        capture_run_id="capture-1",
        source_id="bybit-linear",
        channel_family=ChannelFamily.ORDER_BOOK_DELTA,
        connection_id="connection-1",
        instrument_id="bybit:perpetual:BTCUSDT",
        detected_at_ms=1_700_000_000_100,
        reason=GapReason.SEQUENCE_GAP,
        missing_from_sequence=101,
        missing_to_sequence=105,
    )
    assert gap.invalidates_order_book
    validate_contract_payload("GapMarker", gap.as_json_dict())
    with pytest.raises(RuntimeError, match="invalid until successful resynchronization"):
        assert_order_book_reconstructible((gap,))

    resolved = GapMarker.create(
        capture_run_id="capture-1",
        source_id="bybit-linear",
        channel_family=ChannelFamily.ORDER_BOOK_DELTA,
        connection_id="connection-2",
        instrument_id="bybit:perpetual:BTCUSDT",
        detected_at_ms=1_700_000_000_100,
        reason=GapReason.SEQUENCE_GAP,
        missing_from_sequence=101,
        missing_to_sequence=105,
        resolved=True,
        resolved_at_ms=1_700_000_000_200,
        resynchronization_segment_id="segment:snapshot-resync",
    )
    assert not resolved.invalidates_order_book
    assert_order_book_reconstructible((resolved,))


def test_capture_manifest_self_hash_and_safety_invariants() -> None:
    request = capture_request()
    manifest = CaptureManifest.create(
        request_sha256=request.request_sha256,
        collector_commit=COMMIT,
        capture_run_id="capture-1",
        host_id="synthetic-host",
        started_at_ms=1_700_000_000_000,
        ended_at_ms=1_700_000_001_000,
        source_channel_states=FrozenJsonObject.from_mapping(
            {"binance-spot:trades": "closed"}
        ),
        connection_intervals=(
            FrozenJsonObject.from_mapping(
                {"connection_id": "connection-1", "state": "closed"}
            ),
        ),
        raw_segments=(segment(),),
        counts=FrozenJsonObject.from_mapping({"events": 2}),
        gaps=(),
        reconnects=FrozenJsonObject.from_mapping({"count": 0}),
        clock_evidence=FrozenJsonObject.from_mapping({"policy": "preserve"}),
        rejected_records=0,
        output_immutability_state=OutputImmutabilityState.CLOSED_IMMUTABLE,
    )
    assert manifest.manifest_sha256 == CaptureManifest.create(
        request_sha256=request.request_sha256,
        collector_commit=COMMIT,
        capture_run_id="capture-1",
        host_id="synthetic-host",
        started_at_ms=1_700_000_000_000,
        ended_at_ms=1_700_000_001_000,
        source_channel_states=manifest.source_channel_states,
        connection_intervals=manifest.connection_intervals,
        raw_segments=manifest.raw_segments,
        counts=manifest.counts,
        gaps=(),
        reconnects=manifest.reconnects,
        clock_evidence=manifest.clock_evidence,
        rejected_records=0,
        output_immutability_state=OutputImmutabilityState.CLOSED_IMMUTABLE,
    ).manifest_sha256
    validate_contract_payload("CaptureManifest", manifest.as_json_dict())
    with pytest.raises(ValueError, match="execution_disabled"):
        replace(manifest, execution_disabled=False)
    with pytest.raises(ValueError, match="manifest_sha256"):
        replace(manifest, rejected_records=1)


def test_malformed_json_and_schema_failures(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSON"):
        load_and_validate_contract_json(
            malformed,
            contract_name="CaptureRequest",
        )

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_and_validate_contract_json(
            invalid,
            contract_name="CaptureRequest",
        )


def test_changed_contract_payload_changes_hash() -> None:
    request = capture_request()
    changed = replace(
        request,
        output_root_identity="private-object-store:market-data-v2",
    )
    assert request.request_sha256 != changed.request_sha256
    assert canonical_sha256(request.as_json_dict()) != canonical_sha256(changed.as_json_dict())
