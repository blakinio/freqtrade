from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import IO, Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from ai_platform.research.liquidations.datasets.candle_artifact import (
    normalize_binance_payload,
    normalize_bybit_payload,
    validate_complete_coverage,
)

TIMEFRAME_MS = 300_000
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
ACTIVE_POINTER = "active-wickhunter-production-market-evidence-v1.json"
STATE_FILE = "incremental-state.json"
REQUEST_FILE = "run-request.json"
MANIFEST_FILE = "wickhunter-production-market-evidence-manifest.json"
REPORT_FILE = "wickhunter-production-market-evidence-report.json"
CHECKSUM_FILE = "artifact-sha256.txt"
LOCK_FILE = ".wickhunter-production-market-evidence-v1.lock"
FINALIZING_FILE = ".finalization-started.json"

# Stable public names used by integration tests and operator tooling.
ACTIVE_POINTER_NAME = ACTIVE_POINTER
STATE_NAME = STATE_FILE
MANIFEST_NAME = MANIFEST_FILE

SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
    "BNBUSDT", "ADAUSDT", "SUIUSDT", "LINKUSDT", "AVAXUSDT",
    "TRXUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT",
    "APTUSDT", "NEARUSDT", "UNIUSDT", "FILUSDT", "ATOMUSDT",
)
SOURCES = ("bybit-linear", "binance-usdm")
EXPECTED_SYMBOLS = SYMBOLS
EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": 1,
    "request_id": "wickhunter-production-market-evidence-20260730-v1",
    "run_id": "wickhunter-production-market-evidence-20260730-v1-r1",
    "profile": "liquid20-v1",
    "symbols": list(SYMBOLS),
    "sources": list(SOURCES),
    "timeframe": "5m",
    "pre_roll_start_ms": 1785391200000,
    "decision_start_ms": 1785477600000,
    "decision_end_ms": 1785520800000,
    "sample_interval_seconds": 300,
    "max_sample_lateness_seconds": 420,
    "protected_holdout_start_ms": 1785542400000,
    "source_catalog_sha256": "4ead5a062bcd5516178cb954be2c5680610e78973d34688c2490173f23aee59c",
    "symbol_universe_sha256": "a75bd2734275b837a14db359ff8d380936e01eab93af436433682e47442582f4",
    "durable_storage_uri": "file:///var/lib/freqtrade-staging-state/wickhunter-production-market-evidence",
    "public_only": True,
    "trading_credentials_present": False,
    "proxy_routing_present": False,
    "execution_enabled": False,
    "replay_authorized": False,
    "model_training_authorized": False,
    "strategy_research_authorized": False,
    "performance_research_authorized": False,
    "orders_submitted": 0,
    "production_source_enabled": False,
}

BYBIT_TICKERS = "https://api.bybit.com/v5/market/tickers?category=linear"
BINANCE_24H = "https://fapi.binance.com/fapi/v1/ticker/24hr"
BINANCE_BOOK = "https://fapi.binance.com/fapi/v1/ticker/bookTicker"
BYBIT_KLINES = "https://api.bybit.com/v5/market/kline"
BINANCE_KLINES = "https://fapi.binance.com/fapi/v1/klines"
BYBIT_TICKERS_URL = BYBIT_TICKERS
BINANCE_24H_URL = BINANCE_24H
BINANCE_BOOK_URL = BINANCE_BOOK
CREDENTIAL_ENV = (
    "BINANCE_API_KEY", "BINANCE_API_SECRET", "BINANCE_SECRET_KEY",
    "BYBIT_API_KEY", "BYBIT_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET",
    "OKX_SECRET_KEY", "OKX_PASSPHRASE", "EXCHANGE_API_KEY",
    "EXCHANGE_API_SECRET", "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET",
)
PROXY_ENV = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
FetchBytes = Callable[[str], bytes]
ClockMs = Callable[[], int]


class ProductionMarketEvidenceError(RuntimeError):
    """Fail-closed production evidence error."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProductionMarketEvidenceError(f"{field} must be an object")
    return value


def _list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProductionMarketEvidenceError(f"{field} must be a list")
    return value


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ProductionMarketEvidenceError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise ProductionMarketEvidenceError(f"{field} must be an integer") from exc


def _decimal(value: object, field: str, *, positive: bool = False) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProductionMarketEvidenceError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite() or (parsed <= 0 if positive else parsed < 0):
        raise ProductionMarketEvidenceError(f"{field} has an invalid value")
    rendered = format(parsed, "f").rstrip("0").rstrip(".")
    return rendered or "0"


def _spread(bid: str, ask: str, field: str) -> str:
    bid_value, ask_value = Decimal(bid), Decimal(ask)
    if ask_value < bid_value:
        raise ProductionMarketEvidenceError(f"{field} ask is below bid")
    midpoint = (bid_value + ask_value) / 2
    return _decimal((ask_value - bid_value) / midpoint * 10_000, f"{field} spread")


def _load(path: Path, field: str) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), field)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceError(f"unable to read {field}: {exc}") from exc


def _atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_json(path: Path, value: object, *, replace: bool = False) -> None:
    content = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    if replace:
        _atomic(path, content)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content) if not path.exists() else _raise_exists(path)


def _raise_exists(path: Path) -> None:
    raise ProductionMarketEvidenceError(f"path already exists: {path}")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _raise_exists(path)
    path.write_bytes(content)


def _self_hashed(seed: Mapping[str, object], field: str) -> dict[str, object]:
    value = dict(seed)
    value[field] = canonical_hash(seed)
    return value


def _verify_self_hash(value: Mapping[str, object], field: str, label: str) -> None:
    claimed = value.get(field)
    seed = dict(value)
    seed.pop(field, None)
    if not isinstance(claimed, str) or canonical_hash(seed) != claimed:
        raise ProductionMarketEvidenceError(f"{label} self hash mismatch")


def _refuse_environment(environment: Mapping[str, str]) -> None:
    credentials = sorted(name for name in CREDENTIAL_ENV if environment.get(name))
    proxies = sorted(name for name in PROXY_ENV if environment.get(name))
    if credentials:
        raise ProductionMarketEvidenceError(f"credential environment is present: {credentials}")
    if proxies:
        raise ProductionMarketEvidenceError(f"proxy environment is present: {proxies}")


def load_request(path: Path) -> dict[str, Any]:
    value = _load(path, "capture request")
    if value != EXPECTED_REQUEST:
        raise ProductionMarketEvidenceError("production market evidence request contract mismatch")
    pre_roll = _integer(value["pre_roll_start_ms"], "pre_roll_start_ms")
    start = _integer(value["decision_start_ms"], "decision_start_ms")
    end = _integer(value["decision_end_ms"], "decision_end_ms")
    holdout = _integer(value["protected_holdout_start_ms"], "protected_holdout_start_ms")
    if start - pre_roll < 86_400_000 or end >= holdout:
        raise ProductionMarketEvidenceError("capture geometry violates pre-roll or holdout")
    if any(boundary % TIMEFRAME_MS for boundary in (pre_roll, start, end)):
        raise ProductionMarketEvidenceError("capture geometry is not 5m aligned")
    if (end - start) // TIMEFRAME_MS != 144 or (end - pre_roll) // TIMEFRAME_MS != 432:
        raise ProductionMarketEvidenceError("frozen row geometry mismatch")
    return value


# Backward-stable descriptive alias used by the integration contract.
load_capture_request = load_request


def _durable_path(request: Mapping[str, object]) -> Path:
    parsed = urlsplit(str(request["durable_storage_uri"]))
    if parsed.scheme != "file" or parsed.netloc or parsed.query or parsed.fragment:
        raise ProductionMarketEvidenceError("durable_storage_uri must be a local file URI")
    return Path(parsed.path)


@contextmanager
def _lock(root: Path) -> Iterator[IO[bytes]]:
    root.mkdir(parents=True, exist_ok=True)
    handle = (root / LOCK_FILE).open("a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield handle
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _pointer_path(root: Path) -> Path:
    return root / ACTIVE_POINTER


def _state_path(run_root: Path) -> Path:
    return run_root / STATE_FILE


def _write_state(root: Path, run_root: Path, seed: Mapping[str, object]) -> dict[str, object]:
    state = _self_hashed(seed, "state_sha256")
    _write_json(_state_path(run_root), state, replace=True)
    pointer = _self_hashed(
        {
            "pointer_version": "wickhunter-production-market-evidence-pointer-v1",
            "run_id": state["run_id"],
            "run_root": str(run_root),
            "state_sha256": state["state_sha256"],
        },
        "pointer_sha256",
    )
    _write_json(_pointer_path(root), pointer, replace=True)
    return state


def _active(root: Path) -> tuple[Path, dict[str, Any]]:
    pointer = _load(_pointer_path(root), "active pointer")
    _verify_self_hash(pointer, "pointer_sha256", "active pointer")
    run_root = Path(str(pointer["run_root"]))
    if run_root != root / str(pointer["run_id"]):
        raise ProductionMarketEvidenceError("active run root escapes durable root")
    state = _load(_state_path(run_root), "incremental state")
    _verify_self_hash(state, "state_sha256", "incremental state")
    if pointer["state_sha256"] != state["state_sha256"]:
        raise ProductionMarketEvidenceError("active pointer state identity is stale")
    return run_root, state


def initialize_capture(
    *,
    request_path: Path,
    durable_root: Path,
    collector_commit: str,
    environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    _refuse_environment(environment if environment is not None else os.environ)
    if not re.fullmatch(r"[0-9a-f]{40}", collector_commit):
        raise ProductionMarketEvidenceError("collector_commit must be a lowercase SHA-1")
    request = load_request(request_path)
    if _durable_path(request) != durable_root:
        raise ProductionMarketEvidenceError("request durable root does not match runtime root")
    with _lock(durable_root):
        if _pointer_path(durable_root).exists():
            raise ProductionMarketEvidenceError("an active capture already exists")
        run_root = durable_root / str(request["run_id"])
        if run_root.exists():
            raise ProductionMarketEvidenceError("run root already exists")
        (run_root / "market-samples").mkdir(parents=True)
        _write_json(run_root / REQUEST_FILE, request)
        _write_state(
            durable_root,
            run_root,
            {
                "state_version": "wickhunter-production-market-evidence-state-v1",
                "status": "active",
                "run_id": request["run_id"],
                "collector_commit": collector_commit,
                "next_sample_index": 0,
                "sample_failures": 0,
                "orders_submitted": 0,
            },
        )
    return {
        "status": "initialized",
        "run_id": request["run_id"],
        "run_root": str(run_root),
        "next_sample_index": 0,
        "due_ms": request["decision_start_ms"],
    }


def fetch_public_bytes(url: str, timeout_seconds: int = 30) -> bytes:
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(url, headers={"User-Agent": "freqtrade-wickhunter-market-evidence/1"})
    try:
        with opener.open(request, timeout=timeout_seconds) as response:  # noqa: S310
            if response.status != 200 or response.geturl() != url:
                raise ProductionMarketEvidenceError("public market response status or URL drifted")
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise ProductionMarketEvidenceError(f"public endpoint returned HTTP {exc.code}") from exc
    except (OSError, TimeoutError, URLError) as exc:
        raise ProductionMarketEvidenceError(f"public endpoint failed: {exc}") from exc
    if len(content) > MAX_RESPONSE_BYTES:
        raise ProductionMarketEvidenceError("public response exceeds size limit")
    return content


def _decode(raw: bytes, field: str) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceError(f"{field} is not valid UTF-8 JSON") from exc


def _index(rows: object, field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(rows, field)):
        row = _object(raw, f"{field}[{index}]")
        symbol = str(row.get("symbol", ""))
        if not symbol or symbol in result:
            raise ProductionMarketEvidenceError(f"invalid symbol identity in {field}")
        result[symbol] = row
    return result


def normalize_market_snapshot(
    *,
    scheduled_at_ms: int,
    available_at_ms: int,
    bybit_payload: object,
    binance_24h_payload: object,
    binance_book_payload: object,
) -> dict[str, object]:
    bybit_root = _object(bybit_payload, "Bybit response")
    bybit_result = _object(bybit_root.get("result"), "Bybit result")
    if bybit_root.get("retCode") != 0 or bybit_result.get("category") != "linear":
        raise ProductionMarketEvidenceError("Bybit ticker response identity mismatch")
    bybit = _index(bybit_result.get("list"), "Bybit tickers")
    binance_24h = _index(binance_24h_payload, "Binance 24h")
    binance_book = _index(binance_book_payload, "Binance book")
    records: list[dict[str, object]] = []
    for symbol in SYMBOLS:
        if symbol not in bybit:
            raise ProductionMarketEvidenceError(f"Bybit market snapshot is missing {symbol}")
        if symbol not in binance_24h or symbol not in binance_book:
            raise ProductionMarketEvidenceError(f"Binance market snapshot is missing {symbol}")
        for source, ticker, book, market, volume_field, bid_field, ask_field in (
            (
                "bybit-linear", bybit[symbol], bybit[symbol], "linear perpetual",
                "turnover24h", "bid1Price", "ask1Price",
            ),
            (
                "binance-usdm", binance_24h[symbol], binance_book[symbol],
                "USD-M perpetual", "quoteVolume", "bidPrice", "askPrice",
            ),
        ):
            bid = _decimal(book.get(bid_field), f"{source} {symbol} bid", positive=True)
            ask = _decimal(book.get(ask_field), f"{source} {symbol} ask", positive=True)
            records.append(
                {
                    "schema_version": 1,
                    "source": source,
                    "market": market,
                    "symbol": symbol,
                    "pair": f"{symbol[:-4]}/USDT:USDT",
                    "scheduled_at_ms": scheduled_at_ms,
                    "available_at_ms": available_at_ms,
                    "last_price": _decimal(ticker.get("lastPrice"), f"{source} last", positive=True),
                    "bid_price": bid,
                    "ask_price": ask,
                    "spread_bps": _spread(bid, ask, f"{source} {symbol}"),
                    "quote_volume_24h_usd": _decimal(ticker.get(volume_field), f"{source} volume"),
                    "market_available": True,
                }
            )
    records.sort(key=lambda row: (str(row["source"]), str(row["symbol"])))
    snapshot: dict[str, object] = {
        "schema_version": 1,
        "snapshot_type": "WickHunterSourceSeparatedMarketQualitySnapshot",
        "scheduled_at_ms": scheduled_at_ms,
        "available_at_ms": available_at_ms,
        "source_separated": True,
        "cross_exchange_deduplication": False,
        "records": records,
        "execution_enabled": False,
        "replay_authorized": False,
        "model_training_authorized": False,
        "orders_submitted": 0,
    }
    snapshot["snapshot_sha256"] = canonical_hash(snapshot)
    return snapshot


def _identity(path: Path, run_root: Path) -> dict[str, object]:
    return {
        "logical_name": path.relative_to(run_root).as_posix(),
        "sha256": file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _collect_sample(
    run_root: Path,
    request: Mapping[str, Any],
    index: int,
    now_ms: int,
    fetch: FetchBytes,
) -> dict[str, object]:
    due_ms = _integer(request["decision_start_ms"], "decision_start_ms") + index * TIMEFRAME_MS
    directory = run_root / "market-samples" / f"{index:04d}"
    report_path = directory / "sample-report.json"
    marker = directory / "attempt-started.json"
    if report_path.exists():
        report = _load(report_path, "sample report")
        _verify_self_hash(report, "report_sha256", "sample report")
        return report
    directory.mkdir(parents=True, exist_ok=True)
    if marker.exists():
        report = {
            "schema_version": 1,
            "sample_index": index,
            "scheduled_at_ms": due_ms,
            "available_at_ms": now_ms,
            "status": "fail",
            "stage": "interrupted",
            "error": "previous sample attempt was interrupted",
            "raw_files": [],
            "snapshot_file": None,
            "orders_submitted": 0,
        }
        report = _self_hashed(report, "report_sha256")
        _write_json(report_path, report)
        marker.unlink()
        return report
    _write_json(marker, {"sample_index": index, "started_ms": now_ms, "orders_submitted": 0})
    stage = "lateness"
    try:
        if now_ms > due_ms + _integer(request["max_sample_lateness_seconds"], "lateness") * 1000:
            raise ProductionMarketEvidenceError("sample exceeded the frozen lateness bound")
        stage = "transport"
        fetched = (
            ("bybit-tickers.raw.json", BYBIT_TICKERS, fetch(BYBIT_TICKERS)),
            ("binance-24h.raw.json", BINANCE_24H, fetch(BINANCE_24H)),
            ("binance-book.raw.json", BINANCE_BOOK, fetch(BINANCE_BOOK)),
        )
        raw_files = []
        for name, url, raw in fetched:
            path = directory / name
            _write_bytes(path, raw)
            raw_files.append({**_identity(path, run_root), "request_url": url})
        stage = "normalization"
        snapshot = normalize_market_snapshot(
            scheduled_at_ms=due_ms,
            available_at_ms=int(time.time_ns() // 1_000_000),
            bybit_payload=_decode(fetched[0][2], "Bybit tickers"),
            binance_24h_payload=_decode(fetched[1][2], "Binance 24h"),
            binance_book_payload=_decode(fetched[2][2], "Binance book"),
        )
        snapshot_path = directory / "market-snapshot.json"
        _write_json(snapshot_path, snapshot)
        report = {
            "schema_version": 1,
            "sample_index": index,
            "scheduled_at_ms": due_ms,
            "available_at_ms": snapshot["available_at_ms"],
            "status": "pass",
            "stage": "complete",
            "error": None,
            "raw_files": raw_files,
            "snapshot_file": _identity(snapshot_path, run_root),
            "orders_submitted": 0,
        }
    except Exception as exc:
        report = {
            "schema_version": 1,
            "sample_index": index,
            "scheduled_at_ms": due_ms,
            "available_at_ms": now_ms,
            "status": "fail",
            "stage": stage,
            "error": f"{type(exc).__name__}: {exc}",
            "raw_files": [],
            "snapshot_file": None,
            "orders_submitted": 0,
        }
    report = _self_hashed(report, "report_sha256")
    _write_json(report_path, report)
    marker.unlink()
    return report


def _candle_url(source: str, symbol: str, request: Mapping[str, Any]) -> str:
    start = request["pre_roll_start_ms"]
    end = _integer(request["decision_end_ms"], "decision_end_ms") - 1
    if source == "bybit-linear":
        return f"{BYBIT_KLINES}?{urlencode({'category': 'linear', 'symbol': symbol, 'interval': '5', 'start': start, 'end': end, 'limit': 1000})}"
    return f"{BINANCE_KLINES}?{urlencode({'symbol': symbol, 'interval': '5m', 'startTime': start, 'endTime': end, 'limit': 1000})}"


def _capture_candles(run_root: Path, request: Mapping[str, Any], fetch: FetchBytes) -> list[dict[str, object]]:
    partial = run_root / ".candles.partial"
    final = run_root / "candles"
    if partial.exists() or final.exists():
        raise ProductionMarketEvidenceError("candle output already exists")
    partial.mkdir()
    artifacts = []
    try:
        for source in SOURCES:
            for symbol in SYMBOLS:
                url = _candle_url(source, symbol, request)
                raw = fetch(url)
                payload = _decode(raw, f"{source} {symbol} candles")
                pair = f"{symbol[:-4]}/USDT:USDT"
                rows = (
                    normalize_bybit_payload(payload, symbol=symbol, pair=pair)
                    if source == "bybit-linear"
                    else normalize_binance_payload(payload, symbol=symbol, pair=pair)
                )
                validate_complete_coverage(
                    rows,
                    source=source,
                    symbol=symbol,
                    start_ms=_integer(request["pre_roll_start_ms"], "pre_roll_start_ms"),
                    end_ms=_integer(request["decision_end_ms"], "decision_end_ms"),
                )
                normalized = [
                    {**row, "available_at_ms": row["close_time_ms_exclusive"],
                     "availability_semantics": "completed_candle_close_exclusive"}
                    for row in rows
                ]
                directory = partial / source / symbol
                raw_path = directory / "candles.raw.json"
                normalized_path = directory / "candles-5m.ndjson"
                _write_bytes(raw_path, raw)
                directory.mkdir(parents=True, exist_ok=True)
                with normalized_path.open("xb") as handle:
                    for row in normalized:
                        handle.write(canonical_bytes(row) + b"\n")
                artifacts.append(
                    {
                        "source": source,
                        "symbol": symbol,
                        "pair": pair,
                        "record_count": len(normalized),
                        "start_ms": request["pre_roll_start_ms"],
                        "end_ms": request["decision_end_ms"],
                        "request_url": url,
                        "raw_file": {
                            "logical_name": (Path("candles") / raw_path.relative_to(partial)).as_posix(),
                            "sha256": file_hash(raw_path),
                            "size_bytes": raw_path.stat().st_size,
                        },
                        "normalized_file": {
                            "logical_name": (Path("candles") / normalized_path.relative_to(partial)).as_posix(),
                            "sha256": file_hash(normalized_path),
                            "size_bytes": normalized_path.stat().st_size,
                        },
                    }
                )
        os.replace(partial, final)
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return artifacts


def _sample_evidence(run_root: Path) -> list[dict[str, object]]:
    evidence = []
    for index in range(144):
        path = run_root / "market-samples" / f"{index:04d}" / "sample-report.json"
        report = _load(path, f"sample {index} report")
        _verify_self_hash(report, "report_sha256", f"sample {index} report")
        evidence.append(
            {
                "sample_index": index,
                "status": report["status"],
                "scheduled_at_ms": report["scheduled_at_ms"],
                "available_at_ms": report["available_at_ms"],
                "report_file": _identity(path, run_root),
                "raw_files": report["raw_files"],
                "snapshot_file": report["snapshot_file"],
            }
        )
    return evidence


def _identities(manifest: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    yield _object(manifest["request"], "manifest request")
    for sample in _list(manifest["market_samples"], "market samples"):
        item = _object(sample, "market sample")
        yield _object(item["report_file"], "sample report file")
        for raw in _list(item["raw_files"], "sample raw files"):
            yield _object(raw, "sample raw file")
        yield _object(item["snapshot_file"], "sample snapshot file")
    for candle in _list(manifest["candle_artifacts"], "candle artifacts"):
        item = _object(candle, "candle artifact")
        yield _object(item["raw_file"], "candle raw file")
        yield _object(item["normalized_file"], "candle normalized file")


def _verify_identity(run_root: Path, identity: Mapping[str, Any]) -> None:
    path = (run_root / str(identity["logical_name"])).resolve()
    try:
        path.relative_to(run_root.resolve())
    except ValueError as exc:
        raise ProductionMarketEvidenceError("manifest path escapes run root") from exc
    if not path.is_file() or path.is_symlink():
        raise ProductionMarketEvidenceError("manifest file is missing")
    if file_hash(path) != identity["sha256"] or path.stat().st_size != identity["size_bytes"]:
        raise ProductionMarketEvidenceError("manifest file identity mismatch")


def verify_capture_package(run_root: Path) -> dict[str, object]:
    manifest_path = run_root / MANIFEST_FILE
    manifest = _load(manifest_path, "manifest")
    _verify_self_hash(manifest, "manifest_sha256", "manifest")
    load_request(run_root / REQUEST_FILE)
    samples = _list(manifest["market_samples"], "market samples")
    candles = _list(manifest["candle_artifacts"], "candle artifacts")
    if len(samples) != 144 or any(_object(item, "sample")["status"] != "pass" for item in samples):
        raise ProductionMarketEvidenceError("market sample coverage is incomplete")
    if len(candles) != 40 or any(_object(item, "candle")["record_count"] != 432 for item in candles):
        raise ProductionMarketEvidenceError("candle coverage is incomplete")
    for identity in _identities(manifest):
        _verify_identity(run_root, identity)
    expected = {f"{item['sha256']}  {item['logical_name']}" for item in _identities(manifest)}
    expected.add(f"{file_hash(manifest_path)}  {MANIFEST_FILE}")
    actual = set((run_root / CHECKSUM_FILE).read_text(encoding="utf-8").splitlines())
    if expected != actual:
        raise ProductionMarketEvidenceError("checksum index mismatch")
    return {
        "status": "verified",
        "outcome": "accepted",
        "run_id": manifest["run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "market_sample_count": 144,
        "candle_artifact_count": 40,
        "orders_submitted": 0,
    }


def _fail(root: Path, run_root: Path, state: Mapping[str, Any], error: Exception) -> dict[str, object]:
    _write_json(
        run_root / REPORT_FILE,
        {
            "schema_version": 1,
            "status": "rejected",
            "outcome": "rejected",
            "run_id": state["run_id"],
            "error": f"{type(error).__name__}: {error}",
            "execution_enabled": False,
            "replay_authorized": False,
            "model_training_authorized": False,
            "orders_submitted": 0,
        },
        replace=True,
    )
    seed = dict(state)
    seed.pop("state_sha256", None)
    seed.update({"status": "failed", "outcome": "rejected"})
    _write_state(root, run_root, seed)
    _pointer_path(root).unlink(missing_ok=True)
    (run_root / FINALIZING_FILE).unlink(missing_ok=True)
    shutil.rmtree(run_root / ".candles.partial", ignore_errors=True)
    return {"status": "finalized", "outcome": "rejected", "run_id": state["run_id"], "run_root": str(run_root)}


def _finalize(root: Path, run_root: Path, state: Mapping[str, Any], fetch: FetchBytes) -> dict[str, object]:
    marker = run_root / FINALIZING_FILE
    if marker.exists():
        return _fail(root, run_root, state, ProductionMarketEvidenceError("finalization was interrupted"))
    _write_json(marker, {"started_ms": int(time.time_ns() // 1_000_000), "orders_submitted": 0})
    try:
        request = load_request(run_root / REQUEST_FILE)
        samples = _sample_evidence(run_root)
        if any(item["status"] != "pass" for item in samples):
            raise ProductionMarketEvidenceError("market-quality capture contains failed samples")
        candles = _capture_candles(run_root, request, fetch)
        manifest: dict[str, object] = {
            "schema_version": 1,
            "artifact_type": "WickHunterProductionMarketEvidenceManifest",
            "document_id": request["request_id"],
            "run_id": request["run_id"],
            "collector_commit": state["collector_commit"],
            "request": _identity(run_root / REQUEST_FILE, run_root),
            "profile": request["profile"],
            "sources": list(SOURCES),
            "symbols": list(SYMBOLS),
            "source_catalog_sha256": request["source_catalog_sha256"],
            "symbol_universe_sha256": request["symbol_universe_sha256"],
            "pre_roll_start_ms": request["pre_roll_start_ms"],
            "decision_start_ms": request["decision_start_ms"],
            "decision_end_ms": request["decision_end_ms"],
            "protected_holdout_start_ms": request["protected_holdout_start_ms"],
            "expected_market_samples": 144,
            "expected_candles_per_file": 432,
            "source_separated": True,
            "cross_exchange_deduplication": False,
            "market_samples": samples,
            "candle_artifacts": candles,
            "availability_semantics": {
                "market_quality": "response_fully_received_at_ms",
                "completed_candle": "close_time_ms_exclusive",
            },
            "data_use": {
                "performance_research_authorized": False,
                "replay_authorized": False,
                "model_training_authorized": False,
                "strategy_research_authorized": False,
            },
            "execution_safety": {
                "trading_credentials_present": False,
                "proxy_routing_present": False,
                "execution_enabled": False,
                "production_source_enabled": False,
                "orders_submitted": 0,
            },
        }
        manifest = _self_hashed(manifest, "manifest_sha256")
        manifest_path = run_root / MANIFEST_FILE
        _write_json(manifest_path, manifest)
        lines = sorted(f"{item['sha256']}  {item['logical_name']}" for item in _identities(manifest))
        lines.append(f"{file_hash(manifest_path)}  {MANIFEST_FILE}")
        _write_bytes(run_root / CHECKSUM_FILE, ("\n".join(lines) + "\n").encode())
        verified = verify_capture_package(run_root)
        _write_json(
            run_root / REPORT_FILE,
            {
                "schema_version": 1,
                "status": "accepted",
                "outcome": "accepted",
                "run_id": request["run_id"],
                "manifest_sha256": manifest["manifest_sha256"],
                "verification": verified,
                "execution_enabled": False,
                "replay_authorized": False,
                "model_training_authorized": False,
                "orders_submitted": 0,
            },
        )
        seed = dict(state)
        seed.pop("state_sha256", None)
        seed.update({"status": "completed", "outcome": "accepted", "manifest_sha256": manifest["manifest_sha256"]})
        _write_state(root, run_root, seed)
        _pointer_path(root).unlink()
        marker.unlink()
        return {
            "status": "finalized",
            "outcome": "accepted",
            "run_id": request["run_id"],
            "run_root": str(run_root),
            "manifest_sha256": manifest["manifest_sha256"],
        }
    except Exception as exc:
        return _fail(root, run_root, state, exc)


def _now_ms() -> int:
    return int(time.time_ns() // 1_000_000)


def collect_due_sample(
    *,
    durable_root: Path,
    environment: Mapping[str, str] | None = None,
    fetch_bytes: FetchBytes = fetch_public_bytes,
    wall_clock_ms: ClockMs = _now_ms,
) -> dict[str, object]:
    _refuse_environment(environment if environment is not None else os.environ)
    if not _pointer_path(durable_root).exists():
        return {"status": "idle"}
    with _lock(durable_root):
        run_root, state = _active(durable_root)
        if state["status"] == "ready_to_finalize":
            return _finalize(durable_root, run_root, state, fetch_bytes)
        if state["status"] != "active":
            raise ProductionMarketEvidenceError("capture state is not active")
        request = load_request(run_root / REQUEST_FILE)
        index = _integer(state["next_sample_index"], "next_sample_index")
        due_ms = _integer(request["decision_start_ms"], "decision_start_ms") + index * TIMEFRAME_MS
        now_ms = wall_clock_ms()
        if now_ms < due_ms:
            return {
                "status": "not_due",
                "run_id": request["run_id"],
                "run_root": str(run_root),
                "next_sample_index": index,
                "due_ms": due_ms,
            }
        report = _collect_sample(run_root, request, index, now_ms, fetch_bytes)
        seed = dict(state)
        seed.pop("state_sha256", None)
        seed["next_sample_index"] = index + 1
        if report["status"] != "pass":
            seed["sample_failures"] = _integer(state["sample_failures"], "sample_failures") + 1
        if index + 1 == 144:
            seed["status"] = "ready_to_finalize"
        _write_state(durable_root, run_root, seed)
        return {
            "status": "sampled",
            "sample_status": report["status"],
            "run_id": request["run_id"],
            "run_root": str(run_root),
            "sample_index": index,
            "next_sample_index": index + 1,
            "due_ms": due_ms,
        }


def _outputs(result: Mapping[str, object]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    allowed = {"status", "outcome", "run_id", "run_root", "sample_index", "next_sample_index", "due_ms", "manifest_sha256"}
    with Path(output_path).open("a", encoding="utf-8") as output:
        for key in sorted(allowed):
            if key in result:
                output.write(f"{key}={result[key]}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WickHunter production market evidence capture")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--request", type=Path, required=True)
    init.add_argument("--durable-root", type=Path, required=True)
    init.add_argument("--collector-commit", required=True)
    sample = commands.add_parser("sample")
    sample.add_argument("--durable-root", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--run-root", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "init":
            result = initialize_capture(
                request_path=args.request.resolve(),
                durable_root=args.durable_root.resolve(),
                collector_commit=args.collector_commit,
            )
        elif args.command == "sample":
            result = collect_due_sample(durable_root=args.durable_root.resolve())
        else:
            result = verify_capture_package(args.run_root.resolve())
        _outputs(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get("outcome") == "rejected" else 0
    except ProductionMarketEvidenceError as exc:
        print(f"WickHunter production market evidence failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
