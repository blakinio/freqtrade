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
from typing import Any, BinaryIO
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
ACTIVE_POINTER_NAME = "active-wickhunter-production-market-evidence-v1.json"
STATE_NAME = "incremental-state.json"
REQUEST_NAME = "run-request.json"
MANIFEST_NAME = "wickhunter-production-market-evidence-manifest.json"
REPORT_NAME = "wickhunter-production-market-evidence-report.json"
CHECKSUM_NAME = "artifact-sha256.txt"
LOCK_NAME = ".wickhunter-production-market-evidence-v1.lock"
FINALIZING_NAME = ".finalization-started.json"

EXPECTED_SYMBOLS = (
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
EXPECTED_SOURCES = ("bybit-linear", "binance-usdm")
EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": 1,
    "request_id": "wickhunter-production-market-evidence-20260730-v1",
    "run_id": "wickhunter-production-market-evidence-20260730-v1-r1",
    "profile": "liquid20-v1",
    "symbols": list(EXPECTED_SYMBOLS),
    "sources": list(EXPECTED_SOURCES),
    "timeframe": "5m",
    "pre_roll_start_ms": 1785391200000,
    "decision_start_ms": 1785477600000,
    "decision_end_ms": 1785520800000,
    "sample_interval_seconds": 300,
    "max_sample_lateness_seconds": 420,
    "protected_holdout_start_ms": 1785542400000,
    "source_catalog_sha256": (
        "4ead5a062bcd5516178cb954be2c5680610e78973d34688c2490173f23aee59c"
    ),
    "symbol_universe_sha256": (
        "a75bd2734275b837a14db359ff8d380936e01eab93af436433682e47442582f4"
    ),
    "durable_storage_uri": (
        "file:///var/lib/freqtrade-staging-state/"
        "wickhunter-production-market-evidence"
    ),
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

BYBIT_TICKERS_URL = "https://api.bybit.com/v5/market/tickers?category=linear"
BINANCE_24H_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"
BINANCE_BOOK_URL = "https://fapi.binance.com/fapi/v1/ticker/bookTicker"
BYBIT_KLINES_URL = "https://api.bybit.com/v5/market/kline"
BINANCE_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"

_CREDENTIAL_ENV = (
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "BINANCE_SECRET_KEY",
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
    "OKX_API_KEY",
    "OKX_API_SECRET",
    "OKX_SECRET_KEY",
    "OKX_PASSPHRASE",
    "EXCHANGE_API_KEY",
    "EXCHANGE_API_SECRET",
    "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET",
)
_PROXY_ENV = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_ALLOWED_HOSTS = {"api.bybit.com", "fapi.binance.com"}
_FETCH = Callable[[str], bytes]
_CLOCK_MS = Callable[[], int]


class ProductionMarketEvidenceError(RuntimeError):
    """Raised when prospective evidence cannot be captured unambiguously."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProductionMarketEvidenceError(f"{field} must be an object")
    return value


def _list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProductionMarketEvidenceError(f"{field} must be a list")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ProductionMarketEvidenceError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise ProductionMarketEvidenceError(f"{field} must be an integer") from exc


def _decimal(value: object, *, field: str, positive: bool = False) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProductionMarketEvidenceError(
            f"{field} must be decimal-compatible"
        ) from exc
    if not parsed.is_finite() or (parsed <= 0 if positive else parsed < 0):
        raise ProductionMarketEvidenceError(f"{field} has an invalid value")
    rendered = format(parsed, "f").rstrip("0").rstrip(".")
    return rendered or "0"


def _spread_bps(bid: str, ask: str, *, field: str) -> str:
    bid_value = Decimal(bid)
    ask_value = Decimal(ask)
    if ask_value < bid_value:
        raise ProductionMarketEvidenceError(f"{field} ask is below bid")
    midpoint = (bid_value + ask_value) / 2
    return _decimal(
        (ask_value - bid_value) / midpoint * 10_000,
        field=f"{field}.spread_bps",
    )


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    try:
        return _object(
            json.loads(path.read_text(encoding="utf-8")),
            field=field,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceError(
            f"unable to read {field}: {exc}"
        ) from exc


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _write_bytes(path: Path, content: bytes, *, replace: bool = False) -> None:
    if replace:
        _atomic_write(path, content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ProductionMarketEvidenceError(f"path already exists: {path}")
    with path.open("xb") as handle:
        handle.write(content)


def _write_json(path: Path, value: object, *, replace: bool = False) -> None:
    content = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _write_bytes(path, content, replace=replace)


def _self_hashed(
    seed: Mapping[str, object],
    *,
    hash_field: str,
) -> dict[str, object]:
    value = dict(seed)
    value[hash_field] = _canonical_hash(seed)
    return value


def _verify_self_hash(
    value: Mapping[str, object],
    *,
    hash_field: str,
    field: str,
) -> None:
    claimed = value.get(hash_field)
    seed = dict(value)
    seed.pop(hash_field, None)
    if not isinstance(claimed, str) or _canonical_hash(seed) != claimed:
        raise ProductionMarketEvidenceError(f"{field} self hash mismatch")


def _refuse_environment(environment: Mapping[str, str]) -> None:
    credentials = sorted(name for name in _CREDENTIAL_ENV if environment.get(name))
    proxies = sorted(name for name in _PROXY_ENV if environment.get(name))
    if credentials:
        raise ProductionMarketEvidenceError(
            f"credential environment is present: {credentials}"
        )
    if proxies:
        raise ProductionMarketEvidenceError(f"proxy environment is present: {proxies}")


def load_capture_request(path: Path) -> dict[str, Any]:
    request = _load_json(path, field="capture request")
    if request != EXPECTED_REQUEST:
        raise ProductionMarketEvidenceError(
            "production market evidence request contract mismatch"
        )
    pre_roll_start = _integer(
        request["pre_roll_start_ms"],
        field="pre_roll_start_ms",
    )
    decision_start = _integer(
        request["decision_start_ms"],
        field="decision_start_ms",
    )
    decision_end = _integer(
        request["decision_end_ms"],
        field="decision_end_ms",
    )
    holdout_start = _integer(
        request["protected_holdout_start_ms"],
        field="protected_holdout_start_ms",
    )
    boundaries = (pre_roll_start, decision_start, decision_end)
    if any(boundary % TIMEFRAME_MS for boundary in boundaries):
        raise ProductionMarketEvidenceError("capture geometry is not 5m aligned")
    if decision_start - pre_roll_start < 86_400_000:
        raise ProductionMarketEvidenceError("capture pre-roll is shorter than 24 hours")
    if decision_end >= holdout_start:
        raise ProductionMarketEvidenceError("capture overlaps the protected holdout")
    if (decision_end - decision_start) // TIMEFRAME_MS != 144:
        raise ProductionMarketEvidenceError("decision sample geometry mismatch")
    if (decision_end - pre_roll_start) // TIMEFRAME_MS != 432:
        raise ProductionMarketEvidenceError("completed-candle geometry mismatch")
    return request


load_request = load_capture_request


def _durable_path(request: Mapping[str, object]) -> Path:
    parsed = urlsplit(str(request["durable_storage_uri"]))
    if parsed.scheme != "file" or parsed.netloc or parsed.query or parsed.fragment:
        raise ProductionMarketEvidenceError(
            "durable_storage_uri must be an absolute local file URI"
        )
    return Path(parsed.path)


@contextmanager
def _exclusive_lock(root: Path) -> Iterator[BinaryIO]:
    root.mkdir(parents=True, exist_ok=True)
    handle = (root / LOCK_NAME).open("a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield handle
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _pointer_path(root: Path) -> Path:
    return root / ACTIVE_POINTER_NAME


def _state_path(run_root: Path) -> Path:
    return run_root / STATE_NAME


def _write_state(
    durable_root: Path,
    run_root: Path,
    seed: Mapping[str, object],
) -> dict[str, object]:
    state = _self_hashed(seed, hash_field="state_sha256")
    _write_json(_state_path(run_root), state, replace=True)
    pointer = _self_hashed(
        {
            "pointer_version": (
                "wickhunter-production-market-evidence-active-pointer-v1"
            ),
            "run_id": state["run_id"],
            "run_root": str(run_root),
            "state_sha256": state["state_sha256"],
        },
        hash_field="pointer_sha256",
    )
    _write_json(_pointer_path(durable_root), pointer, replace=True)
    return state


def _load_active_run(durable_root: Path) -> tuple[Path, dict[str, Any]]:
    pointer = _load_json(_pointer_path(durable_root), field="active pointer")
    _verify_self_hash(
        pointer,
        hash_field="pointer_sha256",
        field="active pointer",
    )
    run_root = Path(str(pointer.get("run_root", "")))
    run_id = str(pointer.get("run_id", ""))
    if run_root != durable_root / run_id:
        raise ProductionMarketEvidenceError("active run root escapes durable root")
    state = _load_json(_state_path(run_root), field="incremental state")
    _verify_self_hash(
        state,
        hash_field="state_sha256",
        field="incremental state",
    )
    if pointer.get("state_sha256") != state.get("state_sha256"):
        raise ProductionMarketEvidenceError("active pointer state identity is stale")
    if state.get("run_id") != run_id:
        raise ProductionMarketEvidenceError("active pointer run identity mismatch")
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
        raise ProductionMarketEvidenceError(
            "collector_commit must be a lowercase 40-character SHA"
        )
    request = load_capture_request(request_path)
    if _durable_path(request) != durable_root:
        raise ProductionMarketEvidenceError(
            "request durable root does not match runtime root"
        )
    with _exclusive_lock(durable_root):
        if _pointer_path(durable_root).exists():
            raise ProductionMarketEvidenceError("an active capture already exists")
        run_root = durable_root / str(request["run_id"])
        if run_root.exists():
            raise ProductionMarketEvidenceError(f"run root already exists: {run_root}")
        (run_root / "market-samples").mkdir(parents=True)
        _write_json(run_root / REQUEST_NAME, request)
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


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ProductionMarketEvidenceError("public endpoint is outside the allowlist")
    if parsed.username or parsed.password or parsed.fragment:
        raise ProductionMarketEvidenceError("public endpoint contains forbidden URL fields")


def fetch_public_bytes(url: str, timeout_seconds: int = 30) -> bytes:
    _validate_public_url(url)
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(  # noqa: S310
        url,
        headers={"User-Agent": "freqtrade-wickhunter-market-evidence/1"},
    )
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            if response.status != 200 or response.geturl() != url:
                raise ProductionMarketEvidenceError(
                    "public market response status or URL drifted"
                )
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise ProductionMarketEvidenceError(
            f"public endpoint returned HTTP {exc.code}"
        ) from exc
    except (OSError, TimeoutError, URLError) as exc:
        raise ProductionMarketEvidenceError(f"public endpoint failed: {exc}") from exc
    if len(content) > MAX_RESPONSE_BYTES:
        raise ProductionMarketEvidenceError("public response exceeds size limit")
    return content


def _decode_json(raw: bytes, *, field: str) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceError(
            f"{field} is not valid UTF-8 JSON"
        ) from exc


def _index_by_symbol(rows: object, *, field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(rows, field=field)):
        row = _object(raw, field=f"{field}[{index}]")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol or symbol in result:
            raise ProductionMarketEvidenceError(
                f"invalid or duplicate symbol identity in {field}"
            )
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
    bybit_root = _object(bybit_payload, field="Bybit response")
    bybit_result = _object(bybit_root.get("result"), field="Bybit result")
    if bybit_root.get("retCode") != 0 or bybit_result.get("category") != "linear":
        raise ProductionMarketEvidenceError(
            "Bybit ticker response identity mismatch"
        )
    bybit = _index_by_symbol(bybit_result.get("list"), field="Bybit tickers")
    binance_24h = _index_by_symbol(binance_24h_payload, field="Binance 24h")
    binance_book = _index_by_symbol(binance_book_payload, field="Binance book")
    records: list[dict[str, object]] = []
    for symbol in EXPECTED_SYMBOLS:
        if symbol not in bybit:
            raise ProductionMarketEvidenceError(
                f"Bybit market snapshot is missing {symbol}"
            )
        if symbol not in binance_24h or symbol not in binance_book:
            raise ProductionMarketEvidenceError(
                f"Binance market snapshot is missing {symbol}"
            )
        source_rows = (
            (
                "bybit-linear",
                "linear perpetual",
                bybit[symbol],
                bybit[symbol],
                "turnover24h",
                "bid1Price",
                "ask1Price",
            ),
            (
                "binance-usdm",
                "USD-M perpetual",
                binance_24h[symbol],
                binance_book[symbol],
                "quoteVolume",
                "bidPrice",
                "askPrice",
            ),
        )
        for source, market, ticker, book, volume_key, bid_key, ask_key in source_rows:
            bid = _decimal(
                book.get(bid_key),
                field=f"{source}.{symbol}.bid",
                positive=True,
            )
            ask = _decimal(
                book.get(ask_key),
                field=f"{source}.{symbol}.ask",
                positive=True,
            )
            records.append(
                {
                    "schema_version": 1,
                    "source": source,
                    "market": market,
                    "symbol": symbol,
                    "pair": f"{symbol[:-4]}/USDT:USDT",
                    "scheduled_at_ms": scheduled_at_ms,
                    "available_at_ms": available_at_ms,
                    "last_price": _decimal(
                        ticker.get("lastPrice"),
                        field=f"{source}.{symbol}.last_price",
                        positive=True,
                    ),
                    "bid_price": bid,
                    "ask_price": ask,
                    "spread_bps": _spread_bps(
                        bid,
                        ask,
                        field=f"{source}.{symbol}",
                    ),
                    "quote_volume_24h_usd": _decimal(
                        ticker.get(volume_key),
                        field=f"{source}.{symbol}.quote_volume_24h_usd",
                    ),
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
    snapshot["snapshot_sha256"] = _canonical_hash(snapshot)
    return snapshot


def _file_identity(path: Path, *, run_root: Path) -> dict[str, object]:
    try:
        logical_name = path.relative_to(run_root).as_posix()
    except ValueError as exc:
        raise ProductionMarketEvidenceError(
            "evidence path escapes run root"
        ) from exc
    return {
        "logical_name": logical_name,
        "sha256": _file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _sample_due_ms(request: Mapping[str, object], index: int) -> int:
    start = _integer(request["decision_start_ms"], field="decision_start_ms")
    interval_ms = _integer(
        request["sample_interval_seconds"],
        field="sample_interval_seconds",
    ) * 1000
    return start + index * interval_ms


def _collect_sample(
    *,
    run_root: Path,
    request: Mapping[str, Any],
    index: int,
    now_ms: int,
    fetch_bytes: _FETCH,
) -> dict[str, object]:
    due_ms = _sample_due_ms(request, index)
    sample_root = run_root / "market-samples" / f"{index:04d}"
    report_path = sample_root / "sample-report.json"
    attempt_path = sample_root / "attempt-started.json"
    if report_path.exists():
        report = _load_json(report_path, field="sample report")
        _verify_self_hash(
            report,
            hash_field="report_sha256",
            field="sample report",
        )
        return report
    sample_root.mkdir(parents=True, exist_ok=True)
    if attempt_path.exists():
        report = _self_hashed(
            {
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
            },
            hash_field="report_sha256",
        )
        _write_json(report_path, report)
        attempt_path.unlink()
        return report
    _write_json(
        attempt_path,
        {
            "sample_index": index,
            "attempt_started_ms": now_ms,
            "orders_submitted": 0,
        },
    )
    stage = "lateness"
    try:
        lateness_ms = _integer(
            request["max_sample_lateness_seconds"],
            field="max_sample_lateness_seconds",
        ) * 1000
        if now_ms > due_ms + lateness_ms:
            raise ProductionMarketEvidenceError(
                "sample exceeded the frozen lateness bound"
            )
        stage = "transport"
        fetched = (
            ("bybit-tickers.raw.json", BYBIT_TICKERS_URL),
            ("binance-24h.raw.json", BINANCE_24H_URL),
            ("binance-book.raw.json", BINANCE_BOOK_URL),
        )
        payloads: dict[str, bytes] = {}
        raw_files: list[dict[str, object]] = []
        for name, url in fetched:
            raw = fetch_bytes(url)
            path = sample_root / name
            _write_bytes(path, raw)
            payloads[name] = raw
            raw_files.append(
                {
                    **_file_identity(path, run_root=run_root),
                    "request_url": url,
                }
            )
        stage = "normalization"
        available_at_ms = int(time.time_ns() // 1_000_000)
        snapshot = normalize_market_snapshot(
            scheduled_at_ms=due_ms,
            available_at_ms=available_at_ms,
            bybit_payload=_decode_json(
                payloads["bybit-tickers.raw.json"],
                field="Bybit tickers",
            ),
            binance_24h_payload=_decode_json(
                payloads["binance-24h.raw.json"],
                field="Binance 24h",
            ),
            binance_book_payload=_decode_json(
                payloads["binance-book.raw.json"],
                field="Binance book",
            ),
        )
        snapshot_path = sample_root / "market-snapshot.json"
        _write_json(snapshot_path, snapshot)
        report_seed: dict[str, object] = {
            "schema_version": 1,
            "sample_index": index,
            "scheduled_at_ms": due_ms,
            "available_at_ms": available_at_ms,
            "status": "pass",
            "stage": "complete",
            "error": None,
            "raw_files": raw_files,
            "snapshot_file": _file_identity(
                snapshot_path,
                run_root=run_root,
            ),
            "orders_submitted": 0,
        }
    except Exception as exc:
        report_seed = {
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
    report = _self_hashed(report_seed, hash_field="report_sha256")
    _write_json(report_path, report)
    attempt_path.unlink()
    return report


def _candle_url(
    *,
    source: str,
    symbol: str,
    request: Mapping[str, Any],
) -> str:
    start_ms = request["pre_roll_start_ms"]
    end_ms = _integer(request["decision_end_ms"], field="decision_end_ms") - 1
    if source == "bybit-linear":
        parameters = {
            "category": "linear",
            "symbol": symbol,
            "interval": "5",
            "start": start_ms,
            "end": end_ms,
            "limit": 1000,
        }
        return f"{BYBIT_KLINES_URL}?{urlencode(parameters)}"
    if source == "binance-usdm":
        parameters = {
            "symbol": symbol,
            "interval": "5m",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }
        return f"{BINANCE_KLINES_URL}?{urlencode(parameters)}"
    raise ProductionMarketEvidenceError(f"unsupported candle source: {source}")


def _capture_candles(
    *,
    run_root: Path,
    request: Mapping[str, Any],
    fetch_bytes: _FETCH,
) -> list[dict[str, object]]:
    partial_root = run_root / ".candles.partial"
    final_root = run_root / "candles"
    if partial_root.exists() or final_root.exists():
        raise ProductionMarketEvidenceError("candle output already exists")
    partial_root.mkdir()
    artifacts: list[dict[str, object]] = []
    try:
        start_ms = _integer(
            request["pre_roll_start_ms"],
            field="pre_roll_start_ms",
        )
        end_ms = _integer(
            request["decision_end_ms"],
            field="decision_end_ms",
        )
        for source in EXPECTED_SOURCES:
            for symbol in EXPECTED_SYMBOLS:
                url = _candle_url(
                    source=source,
                    symbol=symbol,
                    request=request,
                )
                raw = fetch_bytes(url)
                payload = _decode_json(raw, field=f"{source} {symbol} candles")
                pair = f"{symbol[:-4]}/USDT:USDT"
                if source == "bybit-linear":
                    records = normalize_bybit_payload(
                        payload,
                        symbol=symbol,
                        pair=pair,
                    )
                else:
                    records = normalize_binance_payload(
                        payload,
                        symbol=symbol,
                        pair=pair,
                    )
                validate_complete_coverage(
                    records,
                    source=source,
                    symbol=symbol,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
                normalized = [
                    {
                        **record,
                        "available_at_ms": record["close_time_ms_exclusive"],
                        "availability_semantics": (
                            "completed_candle_close_exclusive"
                        ),
                    }
                    for record in records
                ]
                relative_root = Path(source) / symbol
                output_root = partial_root / relative_root
                raw_path = output_root / "candles.raw.json"
                normalized_path = output_root / "candles-5m.ndjson"
                _write_bytes(raw_path, raw)
                with normalized_path.open("xb") as handle:
                    for record in normalized:
                        handle.write(_canonical_bytes(record) + b"\n")
                published_raw = Path("candles") / raw_path.relative_to(partial_root)
                published_normalized = (
                    Path("candles") / normalized_path.relative_to(partial_root)
                )
                artifacts.append(
                    {
                        "source": source,
                        "symbol": symbol,
                        "pair": pair,
                        "record_count": len(normalized),
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "request_url": url,
                        "raw_file": {
                            "logical_name": published_raw.as_posix(),
                            "sha256": _file_hash(raw_path),
                            "size_bytes": raw_path.stat().st_size,
                        },
                        "normalized_file": {
                            "logical_name": published_normalized.as_posix(),
                            "sha256": _file_hash(normalized_path),
                            "size_bytes": normalized_path.stat().st_size,
                        },
                    }
                )
        partial_root.replace(final_root)
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise
    return artifacts


def _market_sample_evidence(run_root: Path) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for index in range(144):
        report_path = (
            run_root / "market-samples" / f"{index:04d}" / "sample-report.json"
        )
        report = _load_json(report_path, field=f"sample {index} report")
        _verify_self_hash(
            report,
            hash_field="report_sha256",
            field=f"sample {index} report",
        )
        evidence.append(
            {
                "sample_index": index,
                "status": report["status"],
                "scheduled_at_ms": report["scheduled_at_ms"],
                "available_at_ms": report["available_at_ms"],
                "report_file": _file_identity(
                    report_path,
                    run_root=run_root,
                ),
                "raw_files": report["raw_files"],
                "snapshot_file": report["snapshot_file"],
            }
        )
    return evidence


def _manifest_identities(
    manifest: Mapping[str, Any],
) -> Iterator[Mapping[str, Any]]:
    yield _object(manifest["request"], field="manifest request")
    for raw_sample in _list(manifest["market_samples"], field="market samples"):
        sample = _object(raw_sample, field="market sample")
        yield _object(sample["report_file"], field="sample report file")
        for raw_file in _list(sample["raw_files"], field="sample raw files"):
            yield _object(raw_file, field="sample raw file")
        yield _object(sample["snapshot_file"], field="sample snapshot file")
    for raw_candle in _list(
        manifest["candle_artifacts"],
        field="candle artifacts",
    ):
        candle = _object(raw_candle, field="candle artifact")
        yield _object(candle["raw_file"], field="candle raw file")
        yield _object(candle["normalized_file"], field="candle normalized file")


def _verify_file_identity(
    run_root: Path,
    identity: Mapping[str, Any],
) -> None:
    path = (run_root / str(identity["logical_name"])).resolve()
    try:
        path.relative_to(run_root.resolve())
    except ValueError as exc:
        raise ProductionMarketEvidenceError(
            "manifest path escapes run root"
        ) from exc
    if not path.is_file() or path.is_symlink():
        raise ProductionMarketEvidenceError(f"manifest file is missing: {path}")
    if _file_hash(path) != identity.get("sha256"):
        raise ProductionMarketEvidenceError(f"manifest hash mismatch: {path}")
    if path.stat().st_size != identity.get("size_bytes"):
        raise ProductionMarketEvidenceError(f"manifest size mismatch: {path}")


def verify_capture_package(run_root: Path) -> dict[str, object]:
    manifest_path = run_root / MANIFEST_NAME
    manifest = _load_json(manifest_path, field="manifest")
    _verify_self_hash(
        manifest,
        hash_field="manifest_sha256",
        field="manifest",
    )
    load_capture_request(run_root / REQUEST_NAME)
    samples = _list(manifest["market_samples"], field="market samples")
    candles = _list(manifest["candle_artifacts"], field="candle artifacts")
    if len(samples) != 144:
        raise ProductionMarketEvidenceError("market sample count is incomplete")
    if any(_object(item, field="sample").get("status") != "pass" for item in samples):
        raise ProductionMarketEvidenceError("market sample coverage is incomplete")
    if len(candles) != 40:
        raise ProductionMarketEvidenceError("candle artifact count is incomplete")
    if any(
        _object(item, field="candle").get("record_count") != 432
        for item in candles
    ):
        raise ProductionMarketEvidenceError("candle coverage is incomplete")
    identities = list(_manifest_identities(manifest))
    for identity in identities:
        _verify_file_identity(run_root, identity)
    expected_checksums = {
        f"{identity['sha256']}  {identity['logical_name']}"
        for identity in identities
    }
    expected_checksums.add(f"{_file_hash(manifest_path)}  {MANIFEST_NAME}")
    try:
        actual_checksums = set(
            (run_root / CHECKSUM_NAME).read_text(encoding="utf-8").splitlines()
        )
    except OSError as exc:
        raise ProductionMarketEvidenceError(
            f"unable to read checksum index: {exc}"
        ) from exc
    if actual_checksums != expected_checksums:
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


def _terminal_rejection(
    *,
    durable_root: Path,
    run_root: Path,
    state: Mapping[str, Any],
    error: Exception,
) -> dict[str, object]:
    _write_json(
        run_root / REPORT_NAME,
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
    state_seed = dict(state)
    state_seed.pop("state_sha256", None)
    state_seed.update({"status": "failed", "outcome": "rejected"})
    _write_state(durable_root, run_root, state_seed)
    _pointer_path(durable_root).unlink(missing_ok=True)
    (run_root / FINALIZING_NAME).unlink(missing_ok=True)
    shutil.rmtree(run_root / ".candles.partial", ignore_errors=True)
    return {
        "status": "finalized",
        "outcome": "rejected",
        "run_id": state["run_id"],
        "run_root": str(run_root),
    }


def _finalize_capture(
    *,
    durable_root: Path,
    run_root: Path,
    state: Mapping[str, Any],
    fetch_bytes: _FETCH,
) -> dict[str, object]:
    marker_path = run_root / FINALIZING_NAME
    if marker_path.exists():
        error = ProductionMarketEvidenceError("finalization was interrupted")
        return _terminal_rejection(
            durable_root=durable_root,
            run_root=run_root,
            state=state,
            error=error,
        )
    _write_json(
        marker_path,
        {
            "started_at_ms": int(time.time_ns() // 1_000_000),
            "orders_submitted": 0,
        },
    )
    try:
        request = load_capture_request(run_root / REQUEST_NAME)
        market_samples = _market_sample_evidence(run_root)
        if any(sample["status"] != "pass" for sample in market_samples):
            raise ProductionMarketEvidenceError(
                "market-quality capture contains failed samples"
            )
        candle_artifacts = _capture_candles(
            run_root=run_root,
            request=request,
            fetch_bytes=fetch_bytes,
        )
        manifest_seed: dict[str, object] = {
            "schema_version": 1,
            "artifact_type": "WickHunterProductionMarketEvidenceManifest",
            "document_id": request["request_id"],
            "run_id": request["run_id"],
            "collector_commit": state["collector_commit"],
            "request": _file_identity(
                run_root / REQUEST_NAME,
                run_root=run_root,
            ),
            "profile": request["profile"],
            "sources": list(EXPECTED_SOURCES),
            "symbols": list(EXPECTED_SYMBOLS),
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
            "market_samples": market_samples,
            "candle_artifacts": candle_artifacts,
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
        manifest = _self_hashed(
            manifest_seed,
            hash_field="manifest_sha256",
        )
        manifest_path = run_root / MANIFEST_NAME
        _write_json(manifest_path, manifest)
        checksum_lines = sorted(
            f"{identity['sha256']}  {identity['logical_name']}"
            for identity in _manifest_identities(manifest)
        )
        checksum_lines.append(f"{_file_hash(manifest_path)}  {MANIFEST_NAME}")
        _write_bytes(
            run_root / CHECKSUM_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        verification = verify_capture_package(run_root)
        _write_json(
            run_root / REPORT_NAME,
            {
                "schema_version": 1,
                "status": "accepted",
                "outcome": "accepted",
                "run_id": request["run_id"],
                "manifest_sha256": manifest["manifest_sha256"],
                "verification": verification,
                "execution_enabled": False,
                "replay_authorized": False,
                "model_training_authorized": False,
                "orders_submitted": 0,
            },
        )
        state_seed = dict(state)
        state_seed.pop("state_sha256", None)
        state_seed.update(
            {
                "status": "completed",
                "outcome": "accepted",
                "manifest_sha256": manifest["manifest_sha256"],
            }
        )
        _write_state(durable_root, run_root, state_seed)
        _pointer_path(durable_root).unlink()
        marker_path.unlink()
        return {
            "status": "finalized",
            "outcome": "accepted",
            "run_id": request["run_id"],
            "run_root": str(run_root),
            "manifest_sha256": manifest["manifest_sha256"],
        }
    except Exception as exc:
        return _terminal_rejection(
            durable_root=durable_root,
            run_root=run_root,
            state=state,
            error=exc,
        )


def _wall_clock_ms() -> int:
    return int(time.time_ns() // 1_000_000)


def collect_due_sample(
    *,
    durable_root: Path,
    environment: Mapping[str, str] | None = None,
    fetch_bytes: _FETCH = fetch_public_bytes,
    wall_clock_ms: _CLOCK_MS = _wall_clock_ms,
) -> dict[str, object]:
    _refuse_environment(environment if environment is not None else os.environ)
    pointer_path = _pointer_path(durable_root)
    if not pointer_path.exists():
        return {"status": "idle"}
    with _exclusive_lock(durable_root):
        if not pointer_path.exists():
            return {"status": "idle"}
        run_root, state = _load_active_run(durable_root)
        if state.get("status") == "ready_to_finalize":
            return _finalize_capture(
                durable_root=durable_root,
                run_root=run_root,
                state=state,
                fetch_bytes=fetch_bytes,
            )
        if state.get("status") != "active":
            raise ProductionMarketEvidenceError("capture state is not active")
        request = load_capture_request(run_root / REQUEST_NAME)
        sample_index = _integer(
            state["next_sample_index"],
            field="next_sample_index",
        )
        due_ms = _sample_due_ms(request, sample_index)
        now_ms = wall_clock_ms()
        if now_ms < due_ms:
            return {
                "status": "not_due",
                "run_id": request["run_id"],
                "run_root": str(run_root),
                "next_sample_index": sample_index,
                "due_ms": due_ms,
            }
        report = _collect_sample(
            run_root=run_root,
            request=request,
            index=sample_index,
            now_ms=now_ms,
            fetch_bytes=fetch_bytes,
        )
        state_seed = dict(state)
        state_seed.pop("state_sha256", None)
        state_seed["next_sample_index"] = sample_index + 1
        if report["status"] != "pass":
            state_seed["sample_failures"] = _integer(
                state["sample_failures"],
                field="sample_failures",
            ) + 1
        if sample_index + 1 == 144:
            state_seed["status"] = "ready_to_finalize"
        _write_state(durable_root, run_root, state_seed)
        return {
            "status": "sampled",
            "sample_status": report["status"],
            "run_id": request["run_id"],
            "run_root": str(run_root),
            "sample_index": sample_index,
            "next_sample_index": sample_index + 1,
            "due_ms": due_ms,
        }


def _write_github_outputs(result: Mapping[str, object]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not output_path:
        return
    allowed = {
        "status",
        "outcome",
        "run_id",
        "run_root",
        "sample_index",
        "next_sample_index",
        "due_ms",
        "manifest_sha256",
    }
    with Path(output_path).open("a", encoding="utf-8") as output:
        for key in sorted(allowed):
            if key in result:
                output.write(f"{key}={result[key]}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture WickHunter prospective production market evidence"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--request", type=Path, required=True)
    initialize.add_argument("--durable-root", type=Path, required=True)
    initialize.add_argument("--collector-commit", required=True)
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
        _write_github_outputs(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get("outcome") == "rejected" else 0
    except ProductionMarketEvidenceError as exc:
        print(f"WickHunter production market evidence failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
