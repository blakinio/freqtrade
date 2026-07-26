from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from ai_platform.research.liquidations.datasets.candle_artifact import (
    CandleArtifactError,
    TIMEFRAME_MS,
    build_artifact,
    canonical_json_bytes,
    load_request,
    normalize_binance_payload,
    normalize_bybit_payload,
    sha256_bytes,
    validate_complete_coverage,
)

SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "SUIUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TRXUSDT",
    "DOTUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "ETCUSDT",
    "APTUSDT",
    "NEARUSDT",
    "UNIUSDT",
    "FILUSDT",
    "ATOMUSDT",
)
START_MS = 3_000_000
HOLDOUT_START_MS = 9_900_000
HOLDOUT_END_MS = 20_100_000


def _iso(ms: int) -> str:
    from datetime import UTC, datetime

    return datetime.fromtimestamp(ms / 1000, tz=UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _fixture_repo(tmp_path: Path, *, rows: int = 2) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    catalog_path = repo / "ai_platform/research/liquidations/source-catalog-v1.json"
    universe_path = repo / "ai_platform/research/liquidations/symbol-universes-v1.json"
    catalog = {
        "schema_version": 1,
        "sources": [
            {"source": "bybit-linear"},
            {"source": "binance-usdm"},
        ],
        "cross_source_policy": {
            "deduplicate_between_exchanges": False,
            "sum_events_without_source_labels": False,
        },
    }
    universe = {
        "schema_version": 1,
        "profiles": [
            {
                "name": "liquid20-v1",
                "symbol_count": len(SYMBOLS),
                "symbols": list(SYMBOLS),
            }
        ],
    }
    _write_json(catalog_path, catalog)
    _write_json(universe_path, universe)
    contract = {
        "schema_version": 1,
        "contract_id": "liquid20-source-separated-candle-artifact-v1",
        "classification": "diagnostic_public_market_data_only",
        "source_catalog": {
            "logical_path": catalog_path.relative_to(repo).as_posix(),
            "sha256": sha256_bytes(catalog_path.read_bytes()),
        },
        "symbol_universe": {
            "logical_path": universe_path.relative_to(repo).as_posix(),
            "sha256": sha256_bytes(universe_path.read_bytes()),
            "profile": "liquid20-v1",
        },
        "sources": [
            {
                "source": "bybit-linear",
                "endpoint": "https://api.bybit.com/v5/market/kline",
                "market": "linear perpetual trade-price candles",
                "interval_parameter": "5",
                "response_order": "reverse_start_time",
                "public_market_data": True,
            },
            {
                "source": "binance-usdm",
                "endpoint": "https://fapi.binance.com/fapi/v1/klines",
                "market": "USD-M perpetual trade-price candles",
                "interval_parameter": "5m",
                "response_order": "ascending_start_time",
                "public_market_data": True,
            },
        ],
        "protected_holdout": {
            "start_ms": HOLDOUT_START_MS,
            "end_ms": HOLDOUT_END_MS,
            "start": _iso(HOLDOUT_START_MS),
            "end": _iso(HOLDOUT_END_MS),
        },
        "policies": {
            "credentials_allowed": False,
            "orders_allowed": False,
            "cross_exchange_deduplication": False,
            "missing_candle_is_zero": False,
            "containing_incomplete_candle_allowed": False,
            "performance_research_authorized": False,
        },
    }
    contract_path = (
        repo
        / "ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json"
    )
    _write_json(contract_path, contract)
    request = {
        "schema_version": 1,
        "request_id": "fixture-candle-artifact-v1",
        "contract_id": contract["contract_id"],
        "purpose_classification": "diagnostic_only",
        "target_run_ids": ["liquid20-20260724T170830Z-1"],
        "sources": ["bybit-linear", "binance-usdm"],
        "window": {
            "start_ms": START_MS,
            "end_ms": START_MS + rows * TIMEFRAME_MS,
            "start": _iso(START_MS),
            "end": _iso(START_MS + rows * TIMEFRAME_MS),
            "timeframe": "5m",
            "expected_rows_per_file": rows,
        },
        "pair_mapping": [
            {"symbol": symbol, "pair": f"{symbol[:-4]}/USDT:USDT"} for symbol in SYMBOLS
        ],
        "performance_research_authorized": False,
    }
    request_path = (
        repo
        / "ai_platform/research/liquidations/datasets/run-requests/fixture-candle-artifact-v1.json"
    )
    _write_json(request_path, request)
    return repo, contract_path, request_path


def _bybit_payload(symbol: str, opens: list[int], *, close_delta: int = 0) -> object:
    rows = [
        [
            str(open_time),
            "100.00",
            "105.0",
            "95.000",
            str(101 + close_delta),
            "10.000",
            "1000.00",
        ]
        for open_time in reversed(opens)
    ]
    return {
        "retCode": 0,
        "result": {"category": "linear", "symbol": symbol, "list": rows},
    }


def _binance_payload(opens: list[int], *, close_delta: int = 0) -> list[list[object]]:
    return [
        [
            open_time,
            "100.00",
            "105.0",
            "95.000",
            str(101 + close_delta),
            "10.000",
            open_time + TIMEFRAME_MS - 1,
            "1000.00",
        ]
        for open_time in opens
    ]


def _query_value(query: dict[str, list[str]], *names: str) -> str:
    for name in names:
        values = query.get(name)
        if values:
            return values[0]
    raise AssertionError(f"missing query parameter from {names}")


def _fake_fetch(*, missing_last: bool = False, changed_symbol: str | None = None):
    def fetch(url: str) -> object:
        query = parse_qs(urlparse(url).query)
        symbol = _query_value(query, "symbol")
        start = int(_query_value(query, "start", "startTime"))
        end = int(_query_value(query, "end", "endTime")) + 1
        opens = list(range(start, end, TIMEFRAME_MS))
        if missing_last and symbol == "BTCUSDT":
            opens = opens[:-1]
        close_delta = 1 if changed_symbol == symbol else 0
        if "bybit" in url:
            return _bybit_payload(symbol, opens, close_delta=close_delta)
        return _binance_payload(opens, close_delta=close_delta)

    return fetch


def test_source_parsers_preserve_identity_order_and_decimal_normalization() -> None:
    opens = [START_MS, START_MS + TIMEFRAME_MS]
    bybit = normalize_bybit_payload(
        _bybit_payload("BTCUSDT", opens),
        symbol="BTCUSDT",
        pair="BTC/USDT:USDT",
    )
    binance = normalize_binance_payload(
        _binance_payload(opens),
        symbol="BTCUSDT",
        pair="BTC/USDT:USDT",
    )
    assert [row["open_time_ms"] for row in bybit] == opens
    assert [row["open_time_ms"] for row in binance] == opens
    assert bybit[0]["source"] == "bybit-linear"
    assert binance[0]["source"] == "binance-usdm"
    assert bybit[0]["open"] == binance[0]["open"] == "100"
    assert bybit[0]["pair"] == binance[0]["pair"] == "BTC/USDT:USDT"


def test_source_identity_and_close_boundary_mismatch_are_rejected() -> None:
    payload = _bybit_payload("ETHUSDT", [START_MS])
    with pytest.raises(CandleArtifactError, match="identity mismatch"):
        normalize_bybit_payload(payload, symbol="BTCUSDT", pair="BTC/USDT:USDT")
    binance = _binance_payload([START_MS])
    binance[0][6] = START_MS + TIMEFRAME_MS
    with pytest.raises(CandleArtifactError, match="close boundary"):
        normalize_binance_payload(binance, symbol="BTCUSDT", pair="BTC/USDT:USDT")


def test_complete_coverage_rejects_missing_candle() -> None:
    records = normalize_binance_payload(
        _binance_payload([START_MS]),
        symbol="BTCUSDT",
        pair="BTC/USDT:USDT",
    )
    with pytest.raises(CandleArtifactError, match="incomplete candle coverage"):
        validate_complete_coverage(
            records,
            source="binance-usdm",
            symbol="BTCUSDT",
            start_ms=START_MS,
            end_ms=START_MS + 2 * TIMEFRAME_MS,
        )


def test_contract_and_request_load_exact_frozen_membership(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    request = load_request(contract_path, request_path, repo_root=repo)
    assert request.expected_rows_per_file == 2
    assert tuple(symbol for symbol, _ in request.pair_mapping) == SYMBOLS
    assert tuple(source.source for source in request.sources) == (
        "bybit-linear",
        "binance-usdm",
    )


def test_performance_secret_and_source_drift_fail_closed(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["performance_research_authorized"] = True
    _write_json(request_path, payload)
    with pytest.raises(CandleArtifactError, match="cannot authorize performance research"):
        load_request(contract_path, request_path, repo_root=repo)

    _, _, request_path = _fixture_repo(tmp_path / "secret")
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["api_key"] = "forbidden"
    _write_json(request_path, payload)
    with pytest.raises(CandleArtifactError, match="secret-shaped"):
        load_request(
            request_path.parents[1] / "liquid20-candle-artifact-contract-v1.json",
            request_path,
            repo_root=request_path.parents[5],
        )

    repo, contract_path, request_path = _fixture_repo(tmp_path / "source")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["sources"][0]["endpoint"] = "https://example.invalid"
    _write_json(contract_path, contract)
    with pytest.raises(CandleArtifactError, match="endpoint drifted"):
        load_request(contract_path, request_path, repo_root=repo)


def test_pair_order_and_protected_holdout_are_rejected(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["pair_mapping"][0], request["pair_mapping"][1] = (
        request["pair_mapping"][1],
        request["pair_mapping"][0],
    )
    _write_json(request_path, request)
    with pytest.raises(CandleArtifactError, match="ordered liquid20-v1"):
        load_request(contract_path, request_path, repo_root=repo)

    repo, contract_path, request_path = _fixture_repo(tmp_path / "holdout")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["window"] = {
        "start_ms": HOLDOUT_START_MS,
        "end_ms": HOLDOUT_START_MS + 2 * TIMEFRAME_MS,
        "start": _iso(HOLDOUT_START_MS),
        "end": _iso(HOLDOUT_START_MS + 2 * TIMEFRAME_MS),
        "timeframe": "5m",
        "expected_rows_per_file": 2,
    }
    _write_json(request_path, request)
    with pytest.raises(CandleArtifactError, match="overlaps protected holdout"):
        load_request(contract_path, request_path, repo_root=repo)


def test_build_is_deterministic_source_separated_and_self_hashed(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    first = build_artifact(
        contract_path=contract_path,
        request_path=request_path,
        output_root=tmp_path / "first",
        repo_root=repo,
        code_commit="a" * 40,
        fetch_json=_fake_fetch(),
        env={},
    )
    second = build_artifact(
        contract_path=contract_path,
        request_path=request_path,
        output_root=tmp_path / "second",
        repo_root=repo,
        code_commit="a" * 40,
        fetch_json=_fake_fetch(),
        env={},
    )
    assert first == second
    assert len(first["artifacts"]) == 40
    assert {item["source"] for item in first["artifacts"]} == {
        "bybit-linear",
        "binance-usdm",
    }
    assert first["performance_research_authorized"] is False
    assert first["cross_exchange_deduplication"] is False
    without_hash = dict(first)
    digest = without_hash.pop("manifest_sha256")
    assert digest == sha256_bytes(canonical_json_bytes(without_hash))
    assert len((tmp_path / "first/artifact-sha256.txt").read_text().splitlines()) == 41


def test_changed_source_data_changes_hash(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    baseline = build_artifact(
        contract_path=contract_path,
        request_path=request_path,
        output_root=tmp_path / "baseline",
        repo_root=repo,
        code_commit="b" * 40,
        fetch_json=_fake_fetch(),
        env={},
    )
    changed = build_artifact(
        contract_path=contract_path,
        request_path=request_path,
        output_root=tmp_path / "changed",
        repo_root=repo,
        code_commit="b" * 40,
        fetch_json=_fake_fetch(changed_symbol="BTCUSDT"),
        env={},
    )
    baseline_hashes = {
        (item["source"], item["symbol"]): item["sha256"] for item in baseline["artifacts"]
    }
    changed_hashes = {
        (item["source"], item["symbol"]): item["sha256"] for item in changed["artifacts"]
    }
    assert (
        baseline_hashes[("bybit-linear", "BTCUSDT")] != changed_hashes[("bybit-linear", "BTCUSDT")]
    )
    assert (
        baseline_hashes[("binance-usdm", "BTCUSDT")] != changed_hashes[("binance-usdm", "BTCUSDT")]
    )


def test_failure_is_atomic_and_existing_output_is_not_mutated(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    failed_output = tmp_path / "missing"
    with pytest.raises(CandleArtifactError, match="incomplete candle coverage"):
        build_artifact(
            contract_path=contract_path,
            request_path=request_path,
            output_root=failed_output,
            repo_root=repo,
            code_commit="c" * 40,
            fetch_json=_fake_fetch(missing_last=True),
            env={},
        )
    assert not failed_output.exists()
    assert not (tmp_path / ".missing.partial").exists()

    existing = tmp_path / "existing"
    existing.mkdir()
    marker = existing / "marker"
    marker.write_text("unchanged", encoding="utf-8")
    with pytest.raises(CandleArtifactError, match="output_root already exists"):
        build_artifact(
            contract_path=contract_path,
            request_path=request_path,
            output_root=existing,
            repo_root=repo,
            code_commit="c" * 40,
            fetch_json=_fake_fetch(),
            env={},
        )
    assert marker.read_text(encoding="utf-8") == "unchanged"


def test_credentials_catalog_tamper_and_malformed_json_are_rejected(tmp_path: Path) -> None:
    repo, contract_path, request_path = _fixture_repo(tmp_path)
    with pytest.raises(CandleArtifactError, match="credentials are present"):
        build_artifact(
            contract_path=contract_path,
            request_path=request_path,
            output_root=tmp_path / "credential",
            repo_root=repo,
            code_commit="d" * 40,
            fetch_json=_fake_fetch(),
            env={"BINANCE_API_KEY": "present"},
        )
    catalog = repo / "ai_platform/research/liquidations/source-catalog-v1.json"
    catalog.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CandleArtifactError, match="source_catalog SHA-256 mismatch"):
        load_request(contract_path, request_path, repo_root=repo)

    repo, contract_path, request_path = _fixture_repo(tmp_path / "malformed")
    request_path.write_text("{broken", encoding="utf-8")
    with pytest.raises(CandleArtifactError, match="unable to read request"):
        load_request(contract_path, request_path, repo_root=repo)
