from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from ai_platform.wickhunter import production_market_evidence as core
from ai_platform.wickhunter.production_market_evidence_service import (
    PACKAGE_DIR_NAME,
    PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
    PACKAGE_MANIFEST_NAME,
    PACKAGE_MARKET_QUALITY_NAME,
    PACKAGE_SOURCE_SNAPSHOTS_NAME,
    MarketEvidencePublicationError,
    collect_due_sample,
    initialize_capture,
    publish_immutable_package,
    verify_immutable_package,
)


CODE_SHA = "2" * 40


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _request(path: Path, durable_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setitem(core.EXPECTED_REQUEST, "durable_storage_uri", durable_root.as_uri())
    value = dict(core.EXPECTED_REQUEST)
    value["durable_storage_uri"] = durable_root.as_uri()
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _bybit_tickers() -> dict[str, object]:
    return {
        "retCode": 0,
        "result": {
            "category": "linear",
            "list": [
                {
                    "symbol": symbol,
                    "lastPrice": "100",
                    "bid1Price": "99.9",
                    "ask1Price": "100.1",
                    "turnover24h": "100000000",
                }
                for symbol in core.EXPECTED_SYMBOLS
            ],
        },
    }


def _binance_24h() -> list[dict[str, str]]:
    return [
        {"symbol": symbol, "lastPrice": "100", "quoteVolume": "100000000"}
        for symbol in core.EXPECTED_SYMBOLS
    ]


def _binance_book() -> list[dict[str, str]]:
    return [
        {"symbol": symbol, "bidPrice": "99.9", "askPrice": "100.1"}
        for symbol in core.EXPECTED_SYMBOLS
    ]


def _candle_bytes(url: str) -> bytes:
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    symbol = query["symbol"][0]
    if parsed.hostname == "api.bybit.com":
        start_ms = int(query["start"][0])
        end_ms = int(query["end"][0]) + 1
        rows = [
            [str(open_ms), "100", "101", "99", "100", "10", "1000"]
            for open_ms in range(start_ms, end_ms, core.TIMEFRAME_MS)
        ]
        rows.reverse()
        return _json_bytes(
            {
                "retCode": 0,
                "result": {"category": "linear", "symbol": symbol, "list": rows},
            }
        )
    start_ms = int(query["startTime"][0])
    end_ms = int(query["endTime"][0]) + 1
    return _json_bytes(
        [
            [
                open_ms,
                "100",
                "101",
                "99",
                "100",
                "10",
                open_ms + core.TIMEFRAME_MS - 1,
                "1000",
            ]
            for open_ms in range(start_ms, end_ms, core.TIMEFRAME_MS)
        ]
    )


def _fetch(url: str) -> bytes:
    if url == core.BYBIT_TICKERS_URL:
        return _json_bytes(_bybit_tickers())
    if url == core.BINANCE_24H_URL:
        return _json_bytes(_binance_24h())
    if url == core.BINANCE_BOOK_URL:
        return _json_bytes(_binance_book())
    return _candle_bytes(url)


def _complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, dict[str, object]]:
    durable_root = tmp_path / "state"
    request_path = _request(tmp_path / "request.json", durable_root, monkeypatch)
    initialized = initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=CODE_SHA,
        environment={},
    )
    start_ms = int(core.EXPECTED_REQUEST["decision_start_ms"])
    interval_ms = int(core.EXPECTED_REQUEST["sample_interval_seconds"]) * 1000
    for index in range(144):
        now_ms = start_ms + index * interval_ms + 100
        monkeypatch.setattr(core.time, "time_ns", lambda now_ms=now_ms: now_ms * 1_000_000)
        result = collect_due_sample(
            durable_root=durable_root,
            environment={},
            fetch_bytes=_fetch,
            wall_clock_ms=lambda now_ms=now_ms: now_ms,
        )
        assert result["status"] == "sampled"
        assert result["sample_status"] == "pass"
    end_ms = int(core.EXPECTED_REQUEST["decision_end_ms"])
    monkeypatch.setattr(core.time, "time_ns", lambda: end_ms * 1_000_000)
    finalized = collect_due_sample(
        durable_root=durable_root,
        environment={},
        fetch_bytes=_fetch,
        wall_clock_ms=lambda: end_ms,
    )
    return Path(str(initialized["run_root"])), finalized


def test_full_service_package_is_source_separated_and_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, finalized = _complete(tmp_path, monkeypatch)
    assert finalized["outcome"] == "accepted"
    assert finalized["status"] == "published"
    assert finalized["wh01_ready"] is False
    assert finalized["wh01_blocker"] == "LIQUIDATION_ARCHIVE_NOT_BOUND"

    package_root = run_root / PACKAGE_DIR_NAME
    verification = verify_immutable_package(package_root)
    assert verification["outcome"] == "accepted"
    manifest = json.loads((package_root / PACKAGE_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["sources"] == ["bybit-linear", "binance-usdm"]
    assert manifest["record_counts"] == {
        "market_quality_observations": 5760,
        "instrument_snapshots": 5760,
        "source_health_snapshots": 288,
        "completed_candles": 17280,
    }
    assert manifest["capture"]["pre_roll_ms"] >= 86_400_000
    assert manifest["gaps"] == []
    assert manifest["wh01"]["market_evidence_ready"] is True
    assert manifest["wh01"]["ready"] is False
    assert manifest["authorities"] == {
        "execution_enabled": False,
        "orders_submitted": 0,
        "trading_credentials_present": False,
        "model_execution_authorized": False,
        "replay_authorized": False,
        "performance_research_authorized": False,
        "live_capital_authorized": False,
    }
    assert len((package_root / PACKAGE_SOURCE_SNAPSHOTS_NAME).read_text().splitlines()) == 288
    assert len((package_root / PACKAGE_MARKET_QUALITY_NAME).read_text().splitlines()) == 5760
    assert len((package_root / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME).read_text().splitlines()) == 5760


def test_publication_is_restart_safe_and_no_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, _ = _complete(tmp_path, monkeypatch)
    repeated = publish_immutable_package(run_root)
    assert repeated["idempotent"] is True
    assert repeated["outcome"] == "accepted"

    partial = run_root / ".immutable-package.partial"
    (run_root / PACKAGE_DIR_NAME).rename(run_root / "saved-package")
    partial.mkdir()
    with pytest.raises(MarketEvidencePublicationError, match="staging directory"):
        publish_immutable_package(run_root)


def test_hash_tamper_and_symlink_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, _ = _complete(tmp_path, monkeypatch)
    package_root = run_root / PACKAGE_DIR_NAME
    quality_path = package_root / PACKAGE_MARKET_QUALITY_NAME
    quality_path.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(MarketEvidencePublicationError, match="identity mismatch"):
        verify_immutable_package(package_root)

    other_root, _ = _complete(tmp_path / "other", monkeypatch)
    other_package = other_root / PACKAGE_DIR_NAME
    instrument_path = other_package / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME
    instrument_path.unlink()
    instrument_path.symlink_to(other_package / PACKAGE_MARKET_QUALITY_NAME)
    with pytest.raises(MarketEvidencePublicationError, match="missing or symlinked"):
        verify_immutable_package(other_package)


def test_future_availability_and_wrong_market_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "state"
    request_path = _request(tmp_path / "request.json", durable_root, monkeypatch)
    initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=CODE_SHA,
        environment={},
    )
    start_ms = int(core.EXPECTED_REQUEST["decision_start_ms"])
    future_ms = start_ms + int(core.EXPECTED_REQUEST["max_sample_lateness_seconds"]) * 1000 + 1
    monkeypatch.setattr(core.time, "time_ns", lambda: future_ms * 1_000_000)
    with pytest.raises(MarketEvidencePublicationError, match="availability timestamp"):
        collect_due_sample(
            durable_root=durable_root,
            environment={},
            fetch_bytes=_fetch,
            wall_clock_ms=lambda: start_ms,
        )

    snapshot = core.normalize_market_snapshot(
        scheduled_at_ms=start_ms,
        available_at_ms=start_ms + 1,
        bybit_payload=_bybit_tickers(),
        binance_24h_payload=_binance_24h(),
        binance_book_payload=_binance_book(),
    )
    snapshot["records"][0]["market"] = "spot"
    run_root = durable_root / str(core.EXPECTED_REQUEST["run_id"])
    sample_root = run_root / "market-samples" / "0000"
    (sample_root / "market-snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
    report = json.loads((sample_root / "sample-report.json").read_text())
    report["status"] = "pass"
    (sample_root / "sample-report.json").write_text(json.dumps(report), encoding="utf-8")
    from ai_platform.wickhunter.production_market_evidence_service import _enrich_sample

    with pytest.raises(MarketEvidencePublicationError, match="source or market mismatch"):
        _enrich_sample(run_root, core.EXPECTED_REQUEST, 0)
