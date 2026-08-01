from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from ai_platform.wickhunter import production_market_evidence_v2 as subject


def _file_identity(path: Path, *, logical_name: str) -> dict[str, object]:
    return {
        "logical_name": logical_name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _write_minimal_supplement(
    root: Path,
    *,
    identity: dict[str, object] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if identity is None:
        artifact = root / "payload.ndjson"
        artifact.write_text("{}\n", encoding="utf-8")
        identity = _file_identity(artifact, logical_name="payload.ndjson")
    manifest: dict[str, object] = {
        "schema_version": 2,
        "artifact_type": "WickHunterProductionMarketEvidenceOkxSupplement",
        "contract_id": subject.CONTRACT_ID,
        "request_id": "wickhunter-production-market-evidence-20260731-v2",
        "run_id": "wickhunter-production-market-evidence-20260731-v2-r1",
        "base_v1_run_id": "wickhunter-production-market-evidence-20260730-v1-r1",
        "collector_commit": "a" * 40,
        "source": subject.OKX_SOURCE,
        "symbols": list(subject.EXPECTED_SYMBOLS),
        "capture": {},
        "record_counts": {
            "market_quality_observations": subject.EXPECTED_SAMPLES * len(subject.EXPECTED_SYMBOLS),
            "instrument_snapshots": subject.EXPECTED_SAMPLES * len(subject.EXPECTED_SYMBOLS),
            "source_health_snapshots": subject.EXPECTED_SAMPLES,
            "completed_candles": subject.EXPECTED_CANDLES * len(subject.EXPECTED_SYMBOLS),
        },
        "gaps": [],
        "artifacts": [identity],
        "base_package_bound": False,
        "merge_blocker": "BASE_V1_PACKAGE_NOT_BOUND",
        **subject.AUTHORITY,
    }
    manifest["manifest_sha256"] = subject._canonical_hash(manifest)
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    manifest_identity = _file_identity(manifest_path, logical_name="manifest.json")
    checksum_lines = sorted(
        [
            f"{identity['sha256']}  {identity['logical_name']}",
            f"{manifest_identity['sha256']}  manifest.json",
        ]
    )
    (root / "artifact-sha256.txt").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    (root / "verification-report.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "outcome": "accepted",
                "run_id": manifest["run_id"],
                "manifest_sha256": manifest["manifest_sha256"],
                "artifact_count": 1,
                "base_package_bound": False,
                "merge_blocker": "BASE_V1_PACKAGE_NOT_BOUND",
                **subject.AUTHORITY,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return root


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")


def _request_payload(durable_root: Path) -> dict[str, object]:
    return {
        "schema_version": 2,
        "contract_id": subject.CONTRACT_ID,
        "request_id": "wickhunter-production-market-evidence-20260731-v2",
        "run_id": "wickhunter-production-market-evidence-20260731-v2-r1",
        "base_v1_run_id": ("wickhunter-production-market-evidence-20260730-v1-r1"),
        "profile": "liquid20-v1",
        "symbols": list(subject.EXPECTED_SYMBOLS),
        "sources": list(subject.EXPECTED_SOURCES),
        "timeframe": "5m",
        "pre_roll_start_ms": 1_785_391_200_000,
        "decision_start_ms": 1_785_477_600_000,
        "decision_end_ms": 1_785_520_800_000,
        "sample_interval_seconds": 300,
        "max_sample_lateness_seconds": 420,
        "maximum_source_age_ms": 900_000,
        "protected_holdout_start_ms": 1_785_542_400_000,
        "source_catalog_sha256": subject.EXPECTED_SOURCE_CATALOG_SHA256,
        "symbol_universe_sha256": subject.EXPECTED_SYMBOL_UNIVERSE_SHA256,
        "durable_storage_uri": durable_root.as_uri(),
        "public_only": True,
        "proxy_routing_present": False,
        "production_source_enabled": False,
        "trading_authorized": False,
        **subject.AUTHORITY,
    }


def _instrument_payload() -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instType": "SWAP",
                "instId": subject.okx_native_symbol(symbol),
                "ctVal": "0.01",
                "ctMult": "1",
                "ctValCcy": symbol.removesuffix("USDT"),
                "settleCcy": "USDT",
                "ctType": "linear",
                "state": "live",
            }
            for symbol in subject.EXPECTED_SYMBOLS
        ],
    }


def _ticker_payload(timestamp_ms: int) -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instType": "SWAP",
                "instId": subject.okx_native_symbol(symbol),
                "last": "100",
                "bidPx": "99.5",
                "askPx": "100.5",
                "volCcy24h": "1000",
                "ts": str(timestamp_ms),
            }
            for symbol in subject.EXPECTED_SYMBOLS
        ],
    }


def _candle_row(open_ms: int, *, confirm: str = "1") -> list[str]:
    return [
        str(open_ms),
        "100",
        "110",
        "90",
        "105",
        "50",
        "0.5",
        "52.5",
        confirm,
    ]


def test_load_request_preserves_v1_identity_and_requires_exact_three_sources(
    tmp_path: Path,
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(_request_payload(tmp_path / "durable")),
        encoding="utf-8",
    )

    request = subject.load_capture_request(request_path)

    assert request.base_v1_run_id == ("wickhunter-production-market-evidence-20260730-v1-r1")
    assert request.sources == subject.EXPECTED_SOURCES
    assert request.expected_sample_count == 144

    payload = _request_payload(tmp_path / "other")
    payload["sources"] = ["bybit-linear", "binance-usdm"]
    request_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="exact three-source",
    ):
        subject.load_capture_request(request_path)


def test_initialize_refuses_credentials_and_proxy_routing(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    durable_root = tmp_path / "durable"
    request_path.write_text(
        json.dumps(_request_payload(durable_root)),
        encoding="utf-8",
    )

    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="credentials",
    ):
        subject.initialize_capture(
            request_path=request_path,
            durable_root=durable_root,
            collector_commit="1" * 40,
            environment={"OKX_API_KEY": "secret"},
        )
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="proxy",
    ):
        subject.initialize_capture(
            request_path=request_path,
            durable_root=durable_root,
            collector_commit="1" * 40,
            environment={"HTTPS_PROXY": "http://proxy.invalid"},
        )


def test_okx_market_and_instrument_normalization_is_source_separated() -> None:
    available_at_ms = 1_785_477_601_000
    contracts, instruments = subject.normalize_okx_instruments(
        _instrument_payload(),
        available_at_ms=available_at_ms,
    )
    snapshot = subject.normalize_okx_market_snapshot(
        scheduled_at_ms=1_785_477_600_000,
        available_at_ms=available_at_ms,
        ticker_payload=_ticker_payload(available_at_ms - 1_000),
        instruments=contracts,
        maximum_source_age_ms=900_000,
    )

    assert len(instruments) == 20
    assert len(snapshot["records"]) == 20
    first = snapshot["records"][0]
    assert first["source"] == "okx-swap"
    assert first["quote_volume_24h_usd"] == "100000"
    assert first["received_at_ms"] == available_at_ms
    assert snapshot["orders_submitted"] == 0


def test_okx_ticker_staleness_and_conflicting_instruments_fail_closed() -> None:
    available_at_ms = 1_785_477_601_000
    contracts, _ = subject.normalize_okx_instruments(
        _instrument_payload(),
        available_at_ms=available_at_ms,
    )
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="stale",
    ):
        subject.normalize_okx_market_snapshot(
            scheduled_at_ms=1_785_477_600_000,
            available_at_ms=available_at_ms,
            ticker_payload=_ticker_payload(available_at_ms - 900_001),
            instruments=contracts,
            maximum_source_age_ms=900_000,
        )

    payload = _instrument_payload()
    rows = payload["data"]
    assert isinstance(rows, list)
    conflicting = dict(rows[0])
    conflicting["ctVal"] = "0.02"
    rows.append(conflicting)
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="conflicting",
    ):
        subject.normalize_okx_instruments(
            payload,
            available_at_ms=available_at_ms,
        )


def test_okx_candles_require_confirmed_rows_and_exact_coverage() -> None:
    start_ms = 1_785_391_200_000
    payload = {"code": "0", "data": [_candle_row(start_ms, confirm="0")]}
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="uncompleted",
    ):
        subject.normalize_okx_candle_page(
            payload,
            canonical_symbol="BTCUSDT",
            fetched_at_ms=start_ms + 1_000_000,
        )

    records = subject.normalize_okx_candle_page(
        {"code": "0", "data": [_candle_row(start_ms)]},
        canonical_symbol="BTCUSDT",
        fetched_at_ms=start_ms + 1_000_000,
    )
    with pytest.raises(
        subject.ProductionMarketEvidenceV2Error,
        match="incomplete",
    ):
        subject.validate_okx_candle_coverage(
            records,
            canonical_symbol="BTCUSDT",
            start_ms=start_ms,
            end_ms=start_ms + 2 * subject.TIMEFRAME_MS,
        )


def test_okx_candle_pagination_produces_exact_432_completed_rows() -> None:
    start_ms = 1_785_391_200_000
    end_ms = start_ms + 432 * subject.TIMEFRAME_MS
    rows = [_candle_row(open_ms) for open_ms in range(start_ms, end_ms, subject.TIMEFRAME_MS)]

    def fetch_json(url: str) -> object:
        cursor = int(parse_qs(urlsplit(url).query)["after"][0])
        eligible = [row for row in rows if int(row[0]) < cursor]
        return {"code": "0", "data": list(reversed(eligible[-100:]))}

    captured = subject.capture_okx_candles(
        canonical_symbol="BTCUSDT",
        start_ms=start_ms,
        end_ms=end_ms,
        fetch_json=fetch_json,
        wall_clock_ms=lambda: end_ms + 1,
    )

    assert len(captured) == 432
    assert captured[0]["open_time_ms"] == start_ms
    assert captured[-1]["close_time_ms_exclusive"] == end_ms
    assert all(row["confirmed"] is True for row in captured)


def test_collect_due_sample_persists_one_verified_okx_sample(
    tmp_path: Path,
) -> None:
    durable_root = tmp_path / "durable"
    request_path = tmp_path / "request.json"
    payload = _request_payload(durable_root)
    request_path.write_text(json.dumps(payload), encoding="utf-8")
    subject.initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit="a" * 40,
        environment={},
    )
    due_ms = int(payload["decision_start_ms"])

    def fetch_json(url: str) -> object:
        if url == subject.OKX_INSTRUMENTS_URL:
            return _instrument_payload()
        if url == subject.OKX_TICKERS_URL:
            return _ticker_payload(due_ms)
        raise AssertionError(url)

    result = subject.collect_due_sample(
        durable_root=durable_root,
        environment={},
        fetch_json=fetch_json,
        wall_clock_ms=lambda: due_ms + 1_000,
    )

    assert result["status"] == "sampled"
    sample_root = durable_root / str(payload["run_id"]) / "market-samples" / "0000"
    assert (sample_root / "market-snapshot.json").is_file()
    assert (sample_root / "instrument-snapshot.json").is_file()
    assert (sample_root / "source-health.json").is_file()


def test_verify_supplement_accepts_regular_member(tmp_path: Path) -> None:
    root = _write_minimal_supplement(tmp_path / "supplement")

    result = subject.verify_supplement(root)

    assert result["outcome"] == "accepted"


@pytest.mark.parametrize("logical_name", ["/absolute.ndjson", "../outside.ndjson"])
def test_verify_supplement_rejects_absolute_and_traversing_members(
    tmp_path: Path,
    logical_name: str,
) -> None:
    outside = tmp_path / "outside.ndjson"
    outside.write_text("{}\n", encoding="utf-8")
    identity = _file_identity(outside, logical_name=logical_name)
    root = _write_minimal_supplement(tmp_path / "supplement", identity=identity)

    with pytest.raises(subject.ProductionMarketEvidenceV2Error, match="artifact path"):
        subject.verify_supplement(root)


def test_verify_supplement_rejects_final_file_symlink(tmp_path: Path) -> None:
    root = tmp_path / "supplement"
    root.mkdir()
    target = root / "target.ndjson"
    target.write_text("{}\n", encoding="utf-8")
    link = root / "payload.ndjson"
    _symlink_or_skip(link, target)
    identity = _file_identity(target, logical_name="payload.ndjson")
    _write_minimal_supplement(root, identity=identity)

    with pytest.raises(subject.ProductionMarketEvidenceV2Error, match="symlink"):
        subject.verify_supplement(root)


@pytest.mark.parametrize("target_outside_root", [False, True])
def test_verify_supplement_rejects_symlinked_intermediate_parent(
    tmp_path: Path,
    target_outside_root: bool,
) -> None:
    root = tmp_path / "supplement"
    root.mkdir()
    target_dir = (tmp_path / "outside") if target_outside_root else (root / "inside")
    target_dir.mkdir()
    target = target_dir / "payload.ndjson"
    target.write_text("{}\n", encoding="utf-8")
    _symlink_or_skip(root / "linked", target_dir, target_is_directory=True)
    identity = _file_identity(target, logical_name="linked/payload.ndjson")
    _write_minimal_supplement(root, identity=identity)

    with pytest.raises(subject.ProductionMarketEvidenceV2Error, match="symlink"):
        subject.verify_supplement(root)


def test_verify_supplement_rejects_missing_member(tmp_path: Path) -> None:
    identity = {
        "logical_name": "missing.ndjson",
        "sha256": hashlib.sha256(b"{}\n").hexdigest(),
        "size_bytes": 3,
    }
    root = _write_minimal_supplement(tmp_path / "supplement", identity=identity)

    with pytest.raises(subject.ProductionMarketEvidenceV2Error, match=r"missing|identity"):
        subject.verify_supplement(root)


def test_verify_supplement_rejects_non_regular_member(tmp_path: Path) -> None:
    root = tmp_path / "supplement"
    (root / "directory").mkdir(parents=True)
    identity = {
        "logical_name": "directory",
        "sha256": hashlib.sha256(b"").hexdigest(),
        "size_bytes": 0,
    }
    _write_minimal_supplement(root, identity=identity)

    with pytest.raises(subject.ProductionMarketEvidenceV2Error, match=r"regular|identity"):
        subject.verify_supplement(root)
