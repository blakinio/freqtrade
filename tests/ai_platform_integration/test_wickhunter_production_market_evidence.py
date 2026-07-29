from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from ai_platform.wickhunter.production_market_evidence import (
    ACTIVE_POINTER_NAME,
    BINANCE_24H_URL,
    BINANCE_BOOK_URL,
    BYBIT_TICKERS_URL,
    EXPECTED_REQUEST,
    EXPECTED_SYMBOLS,
    MANIFEST_NAME,
    ProductionMarketEvidenceError,
    STATE_NAME,
    TIMEFRAME_MS,
    collect_due_sample,
    initialize_capture,
    load_capture_request,
    normalize_market_snapshot,
    verify_capture_package,
)

CODE_SHA = "1" * 40
REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/ai-platform-wickhunter-production-market-evidence.yml"
CONTRACT_PATH = (
    REPO_ROOT / "ai_platform/wickhunter/production-market-evidence-contract-v1.json"
)
REQUEST_PATH = (
    REPO_ROOT
    / "ai_platform/wickhunter/run-requests/"
    "wickhunter-production-market-evidence-20260730-v1.json"
)


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_request(
    path: Path,
    *,
    durable_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: dict[str, object] | None = None,
) -> Path:
    monkeypatch.setitem(EXPECTED_REQUEST, "durable_storage_uri", durable_root.as_uri())
    request = dict(EXPECTED_REQUEST) if value is None else value
    request["durable_storage_uri"] = durable_root.as_uri()
    path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
    return path


def _bybit_tickers(*, omit_symbol: str | None = None) -> dict[str, object]:
    rows = [
        {
            "symbol": symbol,
            "lastPrice": "100",
            "bid1Price": "99.9",
            "ask1Price": "100.1",
            "turnover24h": "100000000",
        }
        for symbol in EXPECTED_SYMBOLS
        if symbol != omit_symbol
    ]
    return {"retCode": 0, "result": {"category": "linear", "list": rows}}


def _binance_24h() -> list[dict[str, str]]:
    return [
        {"symbol": symbol, "lastPrice": "100", "quoteVolume": "100000000"}
        for symbol in EXPECTED_SYMBOLS
    ]


def _binance_book() -> list[dict[str, str]]:
    return [
        {"symbol": symbol, "bidPrice": "99.9", "askPrice": "100.1"}
        for symbol in EXPECTED_SYMBOLS
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
            for open_ms in range(start_ms, end_ms, TIMEFRAME_MS)
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
    rows = [
        [
            open_ms,
            "100",
            "101",
            "99",
            "100",
            "10",
            open_ms + TIMEFRAME_MS - 1,
            "1000",
        ]
        for open_ms in range(start_ms, end_ms, TIMEFRAME_MS)
    ]
    return _json_bytes(rows)


def _fetch(url: str) -> bytes:
    if url == BYBIT_TICKERS_URL:
        return _json_bytes(_bybit_tickers())
    if url == BINANCE_24H_URL:
        return _json_bytes(_binance_24h())
    if url == BINANCE_BOOK_URL:
        return _json_bytes(_binance_book())
    return _candle_bytes(url)


def test_full_prospective_capture_is_source_separated_and_verifiable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    durable_root = tmp_path / "state"
    request_path = _write_request(
        tmp_path / "request.json", durable_root=durable_root, monkeypatch=monkeypatch
    )
    initialized = initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=CODE_SHA,
        environment={},
    )
    assert initialized["status"] == "initialized"

    decision_start_ms = int(EXPECTED_REQUEST["decision_start_ms"])
    interval_ms = int(EXPECTED_REQUEST["sample_interval_seconds"]) * 1000
    for index in range(144):
        now_ms = decision_start_ms + index * interval_ms
        result = collect_due_sample(
            durable_root=durable_root,
            environment={},
            fetch_bytes=_fetch,
            wall_clock_ms=lambda now_ms=now_ms: now_ms,
        )
        assert result["status"] == "sampled"
        assert result["sample_status"] == "pass"
        assert result["sample_index"] == index

    finalized = collect_due_sample(
        durable_root=durable_root,
        environment={},
        fetch_bytes=_fetch,
        wall_clock_ms=lambda: int(EXPECTED_REQUEST["decision_end_ms"]),
    )
    assert finalized["status"] == "finalized"
    assert finalized["outcome"] == "accepted"
    assert not (durable_root / ACTIVE_POINTER_NAME).exists()

    run_root = Path(str(finalized["run_root"]))
    verification = verify_capture_package(run_root)
    assert verification == {
        "status": "verified",
        "outcome": "accepted",
        "run_id": EXPECTED_REQUEST["run_id"],
        "manifest_sha256": finalized["manifest_sha256"],
        "market_sample_count": 144,
        "candle_artifact_count": 40,
        "orders_submitted": 0,
    }
    manifest = json.loads((run_root / MANIFEST_NAME).read_text())
    assert manifest["source_separated"] is True
    assert manifest["cross_exchange_deduplication"] is False
    assert manifest["expected_candles_per_file"] == 432
    assert manifest["data_use"] == {
        "performance_research_authorized": False,
        "replay_authorized": False,
        "model_training_authorized": False,
        "strategy_research_authorized": False,
    }
    assert manifest["execution_safety"]["orders_submitted"] == 0


def test_not_due_does_not_call_public_fetcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    durable_root = tmp_path / "state"
    request_path = _write_request(
        tmp_path / "request.json", durable_root=durable_root, monkeypatch=monkeypatch
    )
    initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=CODE_SHA,
        environment={},
    )

    def forbidden_fetch(url: str) -> bytes:
        raise AssertionError(f"unexpected fetch: {url}")

    result = collect_due_sample(
        durable_root=durable_root,
        environment={},
        fetch_bytes=forbidden_fetch,
        wall_clock_ms=lambda: int(EXPECTED_REQUEST["decision_start_ms"]) - 1,
    )
    assert result["status"] == "not_due"
    assert result["next_sample_index"] == 0


def test_request_environment_and_state_tampering_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credential_root = tmp_path / "credential-state"
    monkeypatch.setitem(EXPECTED_REQUEST, "durable_storage_uri", credential_root.as_uri())
    request_value = dict(EXPECTED_REQUEST)
    request_value["execution_enabled"] = True
    request_path = _write_request(
        tmp_path / "request.json",
        durable_root=credential_root,
        monkeypatch=monkeypatch,
        value=request_value,
    )
    with pytest.raises(ProductionMarketEvidenceError, match="request contract mismatch"):
        load_capture_request(request_path)

    valid_path = _write_request(
        tmp_path / "valid.json", durable_root=credential_root, monkeypatch=monkeypatch
    )
    with pytest.raises(ProductionMarketEvidenceError, match="credential environment"):
        initialize_capture(
            request_path=valid_path,
            durable_root=credential_root,
            collector_commit=CODE_SHA,
            environment={"BINANCE_API_KEY": "present"},
        )

    durable_root = tmp_path / "tamper-state"
    valid_path = _write_request(
        tmp_path / "valid-tamper.json", durable_root=durable_root, monkeypatch=monkeypatch
    )
    initialized = initialize_capture(
        request_path=valid_path,
        durable_root=durable_root,
        collector_commit=CODE_SHA,
        environment={},
    )
    state_path = Path(str(initialized["run_root"])) / STATE_NAME
    state = json.loads(state_path.read_text())
    state["next_sample_index"] = 4
    state_path.write_text(json.dumps(state))
    with pytest.raises(ProductionMarketEvidenceError, match="self hash mismatch"):
        collect_due_sample(
            durable_root=durable_root,
            environment={},
            fetch_bytes=_fetch,
            wall_clock_ms=lambda: int(EXPECTED_REQUEST["decision_start_ms"]),
        )


def test_missing_source_symbol_is_rejected() -> None:
    with pytest.raises(ProductionMarketEvidenceError, match="missing ATOMUSDT"):
        normalize_market_snapshot(
            scheduled_at_ms=int(EXPECTED_REQUEST["decision_start_ms"]),
            available_at_ms=int(EXPECTED_REQUEST["decision_start_ms"]) + 100,
            bybit_payload=_bybit_tickers(omit_symbol="ATOMUSDT"),
            binance_24h_payload=_binance_24h(),
            binance_book_payload=_binance_book(),
        )


def test_contract_and_workflow_preserve_bounded_trigger_and_zero_authority() -> None:
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract["classification"] == "prospective_public_market_evidence_only"
    assert contract["time_geometry"]["expected_market_samples"] == 144
    assert contract["time_geometry"]["expected_candles_per_source_symbol"] == 432
    assert contract["time_geometry"]["decision_end_ms"] < contract["time_geometry"][
        "protected_holdout_start_ms"
    ]
    assert contract["policies"]["source_separated"] is True
    assert contract["policies"]["execution_enabled"] is False
    assert contract["policies"]["orders_submitted"] == 0

    workflow_text = WORKFLOW_PATH.read_text()
    workflow = yaml.safe_load(workflow_text)
    assert workflow["on"]["pull_request"]["types"] == ["opened"]
    assert workflow["on"]["schedule"] == [{"cron": "*/5 * * * *"}]
    assert workflow["jobs"]["initialize"]["runs-on"] == ["freqtrade-staging"]
    assert workflow["jobs"]["initialize"]["timeout-minutes"] == 10
    assert workflow["jobs"]["sample"]["timeout-minutes"] == 20
    assert "Validate exact-one-file trigger scope" in workflow_text
    assert "HTTP_PROXY HTTPS_PROXY ALL_PROXY" in workflow_text
    assert "orders_submitted" in (
        REPO_ROOT / "ai_platform/wickhunter/production_market_evidence.py"
    ).read_text()
    assert not REQUEST_PATH.exists()


def test_emit_exact_ruff_import_fix() -> None:
    result = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            "I001",
            "--fix",
            "--diff",
            "ai_platform/wickhunter/production_market_evidence.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    pytest.fail(result.stdout + result.stderr)
