from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.historical.acceptance import AcceptanceStatus
from ai_platform.research.liquidations.historical.importer import HistoricalLocalImporter
from ai_platform.research.liquidations.historical.manifests import (
    HistoricalImportManifest,
    RawFileDescriptor,
    sha256_file,
)
from ai_platform.research.liquidations.historical.providers.base import ProviderParseContext
from ai_platform.research.liquidations.historical.providers.tardis import (
    TardisLiquidationsAdapter,
)
from ai_platform.research.liquidations.historical.semantic_eras import (
    DEFAULT_SEMANTIC_ERAS,
    utc_ms,
)


HEADER = "exchange,symbol,timestamp,local_timestamp,id,side,price,amount\n"
ROWS = (
    "bybit,BTCUSDT,1740787200000000,1740787200001000,,sell,100000.5,0.25\n"
    "bybit,BTCUSDT,1740787201000000,1740787201002000,event-2,buy,99999,0.1\n"
)


def _write_gzip(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            compressed.write(content.encode("utf-8"))


def _manifest(path: Path, *, provider_exchange: str = "bybit") -> HistoricalImportManifest:
    relative = f"raw/{provider_exchange}/BTCUSDT/2025-03-01.csv.gz"
    return HistoricalImportManifest(
        schema_version=1,
        import_run_id="tardis-sample-test",
        provider_id="tardis",
        requested_start_ms=utc_ms("2025-03-01T00:00:00Z"),
        requested_end_ms=utc_ms("2025-03-02T00:00:00Z"),
        symbols=("BTCUSDT",),
        source_commit_sha="b" * 40,
        parser_version="tardis-liquidations-v1",
        decision_contract_sha256="c" * 64,
        license_classification="public-free-sample",
        license_reference="Tardis first-day-of-month sample",
        storage_root="historical/imports/tardis/tardis-sample-test",
        raw_files=(
            RawFileDescriptor(
                relative_path=relative,
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
                provider_id="tardis",
                provider_exchange=provider_exchange,
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


def test_tardis_adapter_maps_liquidated_position_side(tmp_path: Path) -> None:
    path = tmp_path / "raw/bybit/BTCUSDT/2025-03-01.csv.gz"
    _write_gzip(path, HEADER + ROWS)
    manifest = _manifest(path)
    result = TardisLiquidationsAdapter().parse_file(
        path,
        context=ProviderParseContext(
            import_run_id=manifest.import_run_id,
            raw_file=manifest.raw_files[0],
            semantic_eras=DEFAULT_SEMANTIC_ERAS,
        ),
    )
    assert result.rejections == ()
    assert [event.liquidated_position_side for event in result.events] == [
        LiquidatedPositionSide.LONG,
        LiquidatedPositionSide.SHORT,
    ]
    assert result.events[0].available_at_ms == 1_740_787_200_001
    assert result.events[0].provider_local_timestamp_us == 1_740_787_200_001_000


def test_local_import_is_deterministic_and_never_overwrites(tmp_path: Path) -> None:
    path = tmp_path / "input/raw/bybit/BTCUSDT/2025-03-01.csv.gz"
    _write_gzip(path, HEADER + ROWS)
    manifest = _manifest(path)
    importer = HistoricalLocalImporter(
        adapter=TardisLiquidationsAdapter(), semantic_eras=DEFAULT_SEMANTIC_ERAS
    )
    first = importer.run(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output-one",
        manifest=manifest,
    )
    second = importer.run(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output-two",
        manifest=manifest,
    )
    assert first.acceptance.status.value == "pass"
    assert first.events_sha256 == second.events_sha256
    assert first.acceptance_sha256 == second.acceptance_sha256
    assert (tmp_path / "output-one/events.jsonl").read_bytes() == (
        tmp_path / "output-two/events.jsonl"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        importer.run(
            input_root=tmp_path / "input",
            output_root=tmp_path / "output-one",
            manifest=manifest,
        )


def test_tardis_adapter_fails_closed_on_hash_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "raw/bybit/BTCUSDT/2025-03-01.csv.gz"
    _write_gzip(path, HEADER + ROWS)
    manifest = _manifest(path)
    path.write_bytes(path.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="size does not match"):
        TardisLiquidationsAdapter().parse_file(
            path,
            context=ProviderParseContext(
                import_run_id=manifest.import_run_id,
                raw_file=manifest.raw_files[0],
                semantic_eras=DEFAULT_SEMANTIC_ERAS,
            ),
        )


def test_tardis_adapter_rejects_unknown_side_and_header(tmp_path: Path) -> None:
    invalid_side = tmp_path / "side.csv.gz"
    _write_gzip(
        invalid_side,
        HEADER + "bybit,BTCUSDT,1740787200000000,1740787200001000,,unknown,100,1\n",
    )
    side_manifest = _manifest(invalid_side)
    side_result = TardisLiquidationsAdapter().parse_file(
        invalid_side,
        context=ProviderParseContext(
            import_run_id=side_manifest.import_run_id,
            raw_file=side_manifest.raw_files[0],
            semantic_eras=DEFAULT_SEMANTIC_ERAS,
        ),
    )
    assert side_result.events == ()
    assert side_result.rejections[0].detail == "side must be buy or sell"

    invalid_header = tmp_path / "header.csv.gz"
    _write_gzip(invalid_header, "exchange,symbol,timestamp\nbybit,BTCUSDT,1\n")
    header_manifest = _manifest(invalid_header)
    header_result = TardisLiquidationsAdapter().parse_file(
        invalid_header,
        context=ProviderParseContext(
            import_run_id=header_manifest.import_run_id,
            raw_file=header_manifest.raw_files[0],
            semantic_eras=DEFAULT_SEMANTIC_ERAS,
        ),
    )
    assert header_result.events == ()
    assert header_result.rejections[0].reason == "invalid_header"


def test_local_import_fails_acceptance_when_parser_rejects_row(tmp_path: Path) -> None:
    path = tmp_path / "input/raw/bybit/BTCUSDT/2025-03-01.csv.gz"
    _write_gzip(
        path,
        HEADER
        + "bybit,BTCUSDT,1740787200000000,1740787200001000,,sell,100000.5,0.25\n"
        + "bybit,BTCUSDT,1740787201000000,1740787201002000,,unknown,99999,0.1\n",
    )
    manifest = _manifest(path)
    result = HistoricalLocalImporter(
        adapter=TardisLiquidationsAdapter(), semantic_eras=DEFAULT_SEMANTIC_ERAS
    ).run(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        manifest=manifest,
    )
    assert result.acceptance.status is AcceptanceStatus.REJECTED
    assert result.acceptance.total_records == 2
    assert result.acceptance.accepted_records == 1
    assert result.acceptance.rejected_records == 1
    assert result.acceptance.rejection_reasons == {"parser.invalid_row": 1}


def test_tardis_adapter_maps_binance_semantic_era(tmp_path: Path) -> None:
    path = tmp_path / "raw/binance-futures/BTCUSDT/2025-03-01.csv.gz"
    _write_gzip(
        path,
        HEADER + "binance-futures,BTCUSDT,1740787200000000,1740787200001000,,buy,100000,0.2\n",
    )
    manifest = _manifest(path, provider_exchange="binance-futures")
    result = TardisLiquidationsAdapter().parse_file(
        path,
        context=ProviderParseContext(
            import_run_id=manifest.import_run_id,
            raw_file=manifest.raw_files[0],
            semantic_eras=DEFAULT_SEMANTIC_ERAS,
        ),
    )
    assert result.rejections == ()
    assert result.events[0].source == "binance-usdm"
    assert result.events[0].native_channel == "forceOrder"
    assert result.events[0].semantic_era == "tardis-binance-force-order-snapshot-v1"
    assert result.events[0].liquidated_position_side is LiquidatedPositionSide.SHORT
