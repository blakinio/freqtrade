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
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from ai_platform.research.liquidations.okx import (
    OkxInstrumentContract,
    canonical_symbol_from_inst_id,
    parse_okx_instruments_response,
)
from ai_platform.wickhunter.production_market_evidence import EXPECTED_SYMBOLS


SCHEMA_VERSION = 2
CONTRACT_ID = "wickhunter-production-market-evidence-v2"
TIMEFRAME = "5m"
TIMEFRAME_MS = 300_000
EXPECTED_SAMPLES = 144
EXPECTED_CANDLES = 432
BASE_SOURCES = ("bybit-linear", "binance-usdm")
EXPECTED_SOURCES = (*BASE_SOURCES, "okx-swap")
OKX_SOURCE = "okx-swap"
EXPECTED_SOURCE_CATALOG_SHA256 = "f4afd993df84441d34639d1b149e42cdba1613569ab9828e1f3bf5e30983f641"
EXPECTED_SYMBOL_UNIVERSE_SHA256 = "a75bd2734275b837a14db359ff8d380936e01eab93af436433682e47442582f4"
OKX_INSTRUMENTS_URL = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
OKX_TICKERS_URL = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
OKX_CANDLES_URL = "https://www.okx.com/api/v5/market/history-candles"
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
ACTIVE_POINTER_NAME = "active-wickhunter-production-market-evidence-v2.json"
REQUEST_NAME = "run-request.json"
STATE_NAME = "incremental-state.json"
LOCK_NAME = ".wickhunter-production-market-evidence-v2.lock"
SUPPLEMENT_DIR_NAME = "immutable-okx-supplement"
SUPPLEMENT_PARTIAL_DIR_NAME = ".immutable-okx-supplement.partial"

AUTHORITY = {
    "execution_enabled": False,
    "orders_submitted": 0,
    "trading_credentials_present": False,
    "model_execution_authorized": False,
    "replay_authorized": False,
    "performance_research_authorized": False,
    "live_capital_authorized": False,
}
REQUEST_ONLY_SAFETY = {
    "trading_authorized": False,
    "production_source_enabled": False,
}
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
_ALLOWED_HOSTS = {"www.okx.com"}
_FETCH_JSON = Callable[[str], object]
_CLOCK_MS = Callable[[], int]


class ProductionMarketEvidenceV2Error(RuntimeError):
    """Raised when the prospective OKX supplement cannot be proven safely."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None


@dataclass(frozen=True, slots=True)
class CaptureRequestV2:
    request_id: str
    run_id: str
    base_v1_run_id: str
    profile: str
    symbols: tuple[str, ...]
    sources: tuple[str, ...]
    pre_roll_start_ms: int
    decision_start_ms: int
    decision_end_ms: int
    sample_interval_seconds: int
    max_sample_lateness_seconds: int
    maximum_source_age_ms: int
    protected_holdout_start_ms: int
    source_catalog_sha256: str
    symbol_universe_sha256: str
    durable_storage_uri: str

    @property
    def expected_sample_count(self) -> int:
        interval_ms = self.sample_interval_seconds * 1000
        return (self.decision_end_ms - self.decision_start_ms) // interval_ms

    def as_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_id": CONTRACT_ID,
            "request_id": self.request_id,
            "run_id": self.run_id,
            "base_v1_run_id": self.base_v1_run_id,
            "profile": self.profile,
            "symbols": list(self.symbols),
            "sources": list(self.sources),
            "timeframe": TIMEFRAME,
            "pre_roll_start_ms": self.pre_roll_start_ms,
            "decision_start_ms": self.decision_start_ms,
            "decision_end_ms": self.decision_end_ms,
            "sample_interval_seconds": self.sample_interval_seconds,
            "max_sample_lateness_seconds": self.max_sample_lateness_seconds,
            "maximum_source_age_ms": self.maximum_source_age_ms,
            "protected_holdout_start_ms": self.protected_holdout_start_ms,
            "source_catalog_sha256": self.source_catalog_sha256,
            "symbol_universe_sha256": self.symbol_universe_sha256,
            "durable_storage_uri": self.durable_storage_uri,
            "public_only": True,
            "proxy_routing_present": False,
            **REQUEST_ONLY_SAFETY,
            **AUTHORITY,
        }


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
        raise ProductionMarketEvidenceV2Error(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProductionMarketEvidenceV2Error(f"{field} must be a list")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ProductionMarketEvidenceV2Error(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise ProductionMarketEvidenceV2Error(f"{field} must be an integer") from exc


def _decimal(value: object, *, field: str, positive: bool = False) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProductionMarketEvidenceV2Error(f"{field} must be decimal-compatible") from exc
    invalid = not parsed.is_finite() or (parsed <= 0 if positive else parsed < 0)
    if invalid:
        qualifier = "positive" if positive else "non-negative"
        raise ProductionMarketEvidenceV2Error(f"{field} must be finite and {qualifier}")
    return parsed


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ProductionMarketEvidenceV2Error(f"{field} must be a regular file")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceV2Error(f"unable to read {field}: {exc}") from exc
    return _object(parsed, field=field)


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ProductionMarketEvidenceV2Error(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: object, *, replace: bool = False) -> None:
    content = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if not replace:
        _write_new(path, content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ProductionMarketEvidenceV2Error(f"temporary file already exists: {temporary}")
    with temporary.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _write_ndjson(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    content = b"".join(_canonical_bytes(dict(row)) + b"\n" for row in rows)
    _write_new(path, content)


def _self_hashed(value: Mapping[str, object], *, hash_field: str) -> dict[str, object]:
    result = dict(value)
    result[hash_field] = _canonical_hash(result)
    return result


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
        raise ProductionMarketEvidenceV2Error(f"{field} self hash mismatch")


def _refuse_environment(environment: Mapping[str, str]) -> None:
    credentials = sorted(name for name in _CREDENTIAL_ENV if environment.get(name, "").strip())
    if credentials:
        raise ProductionMarketEvidenceV2Error(
            f"recognized trading credentials are present: {credentials}"
        )
    proxies = sorted(name for name in _PROXY_ENV if environment.get(name, "").strip())
    if proxies:
        raise ProductionMarketEvidenceV2Error(f"proxy routing is present: {proxies}")


def _require_false(payload: Mapping[str, object], field: str) -> None:
    if payload.get(field) is not False:
        raise ProductionMarketEvidenceV2Error(f"{field} must be false")


def load_capture_request(path: Path) -> CaptureRequestV2:
    payload = _load_json(path, field="v2 capture request")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ProductionMarketEvidenceV2Error("schema_version must be 2")
    if payload.get("contract_id") != CONTRACT_ID:
        raise ProductionMarketEvidenceV2Error("contract_id mismatch")
    request_id = str(payload.get("request_id", ""))
    run_id = str(payload.get("run_id", ""))
    base_v1_run_id = str(payload.get("base_v1_run_id", ""))
    request_pattern = r"wickhunter-production-market-evidence-\d{8}-v2"
    if not re.fullmatch(request_pattern, request_id):
        raise ProductionMarketEvidenceV2Error("request_id is invalid")
    if run_id != f"{request_id}-r1":
        raise ProductionMarketEvidenceV2Error("run_id must be the first immutable v2 run")
    base_pattern = r"wickhunter-production-market-evidence-\d{8}-v1-r1"
    if not re.fullmatch(base_pattern, base_v1_run_id):
        raise ProductionMarketEvidenceV2Error("base_v1_run_id is invalid")
    symbols = tuple(str(item) for item in _sequence(payload.get("symbols"), field="symbols"))
    sources = tuple(str(item) for item in _sequence(payload.get("sources"), field="sources"))
    if symbols != EXPECTED_SYMBOLS:
        raise ProductionMarketEvidenceV2Error("symbol universe does not match Liquid20 v1")
    if sources != EXPECTED_SOURCES:
        raise ProductionMarketEvidenceV2Error("sources must contain the exact three-source order")
    if payload.get("profile") != "liquid20-v1":
        raise ProductionMarketEvidenceV2Error("profile mismatch")
    if payload.get("timeframe") != TIMEFRAME:
        raise ProductionMarketEvidenceV2Error("timeframe mismatch")
    pre_roll_start_ms = _integer(payload.get("pre_roll_start_ms"), field="pre_roll_start_ms")
    decision_start_ms = _integer(payload.get("decision_start_ms"), field="decision_start_ms")
    decision_end_ms = _integer(payload.get("decision_end_ms"), field="decision_end_ms")
    sample_interval_seconds = _integer(
        payload.get("sample_interval_seconds"),
        field="sample_interval_seconds",
    )
    max_sample_lateness_seconds = _integer(
        payload.get("max_sample_lateness_seconds"),
        field="max_sample_lateness_seconds",
    )
    maximum_source_age_ms = _integer(
        payload.get("maximum_source_age_ms"), field="maximum_source_age_ms"
    )
    protected_holdout_start_ms = _integer(
        payload.get("protected_holdout_start_ms"),
        field="protected_holdout_start_ms",
    )
    if sample_interval_seconds != 300 or max_sample_lateness_seconds != 420:
        raise ProductionMarketEvidenceV2Error("sample cadence or lateness contract mismatch")
    if maximum_source_age_ms <= 0 or maximum_source_age_ms > 900_000:
        raise ProductionMarketEvidenceV2Error("maximum_source_age_ms is outside the safe range")
    if decision_start_ms - pre_roll_start_ms < 86_400_000:
        raise ProductionMarketEvidenceV2Error("at least 24 hours of pre-roll are required")
    if decision_end_ms - decision_start_ms != 43_200_000:
        raise ProductionMarketEvidenceV2Error("decision interval must be exactly 12 hours")
    if decision_start_ms % TIMEFRAME_MS or decision_end_ms % TIMEFRAME_MS:
        raise ProductionMarketEvidenceV2Error("decision geometry must align to 5m")
    if decision_end_ms > protected_holdout_start_ms:
        raise ProductionMarketEvidenceV2Error("decision interval overlaps the protected holdout")
    if payload.get("source_catalog_sha256") != EXPECTED_SOURCE_CATALOG_SHA256:
        raise ProductionMarketEvidenceV2Error("source catalog identity mismatch")
    if payload.get("symbol_universe_sha256") != EXPECTED_SYMBOL_UNIVERSE_SHA256:
        raise ProductionMarketEvidenceV2Error("symbol universe identity mismatch")
    if payload.get("public_only") is not True:
        raise ProductionMarketEvidenceV2Error("public_only must be true")
    for field in (
        "proxy_routing_present",
        "production_source_enabled",
        "execution_enabled",
        "trading_authorized",
        "trading_credentials_present",
        "model_execution_authorized",
        "replay_authorized",
        "performance_research_authorized",
        "live_capital_authorized",
    ):
        _require_false(payload, field)
    if payload.get("orders_submitted") != 0:
        raise ProductionMarketEvidenceV2Error("orders_submitted must equal zero")
    request = CaptureRequestV2(
        request_id=request_id,
        run_id=run_id,
        base_v1_run_id=base_v1_run_id,
        profile="liquid20-v1",
        symbols=symbols,
        sources=sources,
        pre_roll_start_ms=pre_roll_start_ms,
        decision_start_ms=decision_start_ms,
        decision_end_ms=decision_end_ms,
        sample_interval_seconds=sample_interval_seconds,
        max_sample_lateness_seconds=max_sample_lateness_seconds,
        maximum_source_age_ms=maximum_source_age_ms,
        protected_holdout_start_ms=protected_holdout_start_ms,
        source_catalog_sha256=EXPECTED_SOURCE_CATALOG_SHA256,
        symbol_universe_sha256=EXPECTED_SYMBOL_UNIVERSE_SHA256,
        durable_storage_uri=str(payload.get("durable_storage_uri", "")),
    )
    if request.expected_sample_count != EXPECTED_SAMPLES:
        raise ProductionMarketEvidenceV2Error("expected sample geometry mismatch")
    parsed = urlsplit(request.durable_storage_uri)
    invalid_uri = (
        parsed.scheme != "file"
        or bool(parsed.netloc)
        or not parsed.path.startswith("/")
        or bool(parsed.query)
        or bool(parsed.fragment)
    )
    if invalid_uri:
        raise ProductionMarketEvidenceV2Error("durable_storage_uri must be an absolute file URI")
    return request


def okx_native_symbol(canonical_symbol: str) -> str:
    normalized = canonical_symbol.strip().upper()
    if normalized not in EXPECTED_SYMBOLS or not normalized.endswith("USDT"):
        raise ProductionMarketEvidenceV2Error("unsupported canonical OKX symbol")
    return f"{normalized[:-4]}-USDT-SWAP"


def _instrument_rows_by_id(
    payload: Mapping[str, object],
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    raw_rows = _sequence(payload.get("data"), field="OKX instruments.data")
    for index, raw in enumerate(raw_rows):
        row = _object(raw, field=f"OKX instruments.data[{index}]")
        inst_id = str(row.get("instId", "")).strip().upper()
        if inst_id in rows and rows[inst_id] != row:
            raise ProductionMarketEvidenceV2Error(f"conflicting OKX instrument row for {inst_id}")
        rows[inst_id] = row
    return rows


def normalize_okx_instruments(
    payload: object,
    *,
    available_at_ms: int,
) -> tuple[dict[str, OkxInstrumentContract], list[dict[str, object]]]:
    root = _object(payload, field="OKX instruments response")
    try:
        contracts = parse_okx_instruments_response(
            root,
            requested_symbols=EXPECTED_SYMBOLS,
        )
    except (TypeError, ValueError) as exc:
        raise ProductionMarketEvidenceV2Error(f"invalid OKX instrument response: {exc}") from exc
    raw_rows = _instrument_rows_by_id(root)
    normalized: list[dict[str, object]] = []
    for canonical_symbol in EXPECTED_SYMBOLS:
        inst_id = okx_native_symbol(canonical_symbol)
        contract = contracts.get(inst_id)
        raw = raw_rows.get(inst_id)
        if contract is None or raw is None:
            raise ProductionMarketEvidenceV2Error(f"missing verified OKX instrument {inst_id}")
        row: dict[str, object] = {
            "schema_version": 2,
            "source": OKX_SOURCE,
            "native_symbol": inst_id,
            "canonical_symbol": canonical_symbol,
            "market": "USDT-margined perpetual swap",
            "settlement": "USDT",
            "quote": "USDT",
            "active": True,
            "captured_at_ms": available_at_ms,
            "available_at_ms": available_at_ms,
            "contract_metadata": contract.as_json_dict(),
            "source_payload_sha256": _canonical_hash(raw),
        }
        row["normalized_snapshot_sha256"] = _canonical_hash(row)
        normalized.append(row)
    return contracts, normalized


def _spread_bps(bid: Decimal, ask: Decimal, *, field: str) -> Decimal:
    if ask < bid:
        raise ProductionMarketEvidenceV2Error(f"{field} ask is below bid")
    midpoint = (ask + bid) / Decimal(2)
    if midpoint <= 0:
        raise ProductionMarketEvidenceV2Error(f"{field} midpoint is not positive")
    return (ask - bid) / midpoint * Decimal(10_000)


def normalize_okx_market_snapshot(
    *,
    scheduled_at_ms: int,
    available_at_ms: int,
    ticker_payload: object,
    instruments: Mapping[str, OkxInstrumentContract],
    maximum_source_age_ms: int,
) -> dict[str, object]:
    root = _object(ticker_payload, field="OKX ticker response")
    if str(root.get("code", "")) != "0":
        raise ProductionMarketEvidenceV2Error("OKX ticker response code must be 0")
    tickers: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_sequence(root.get("data"), field="OKX ticker data")):
        row = _object(raw, field=f"OKX ticker data[{index}]")
        if str(row.get("instType", "")).upper() != "SWAP":
            continue
        inst_id = str(row.get("instId", "")).strip().upper()
        try:
            canonical = canonical_symbol_from_inst_id(inst_id)
        except ValueError:
            continue
        if canonical not in EXPECTED_SYMBOLS:
            continue
        if canonical in tickers and tickers[canonical] != row:
            raise ProductionMarketEvidenceV2Error(f"conflicting OKX ticker for {canonical}")
        tickers[canonical] = row
    records: list[dict[str, object]] = []
    for canonical in EXPECTED_SYMBOLS:
        ticker = tickers.get(canonical)
        contract = instruments.get(okx_native_symbol(canonical))
        if ticker is None or contract is None:
            raise ProductionMarketEvidenceV2Error(f"OKX market snapshot is missing {canonical}")
        event_at_ms = _integer(ticker.get("ts"), field=f"OKX {canonical} ticker timestamp")
        if event_at_ms > available_at_ms:
            raise ProductionMarketEvidenceV2Error("OKX ticker timestamp is in the future")
        if available_at_ms - event_at_ms > maximum_source_age_ms:
            raise ProductionMarketEvidenceV2Error(f"OKX ticker is stale for {canonical}")
        last = _decimal(ticker.get("last"), field=f"OKX {canonical} last", positive=True)
        bid = _decimal(ticker.get("bidPx"), field=f"OKX {canonical} bid", positive=True)
        ask = _decimal(ticker.get("askPx"), field=f"OKX {canonical} ask", positive=True)
        base_volume = _decimal(ticker.get("volCcy24h"), field=f"OKX {canonical} base volume")
        records.append(
            {
                "schema_version": 2,
                "source": OKX_SOURCE,
                "market": "USDT-margined perpetual swap",
                "symbol": canonical,
                "canonical_symbol": canonical,
                "native_symbol": contract.inst_id,
                "pair": f"{canonical[:-4]}/USDT:USDT",
                "scheduled_at_ms": scheduled_at_ms,
                "event_at_ms": event_at_ms,
                "received_at_ms": available_at_ms,
                "available_at_ms": available_at_ms,
                "last_price": _decimal_text(last),
                "bid_price": _decimal_text(bid),
                "ask_price": _decimal_text(ask),
                "spread_bps": _decimal_text(_spread_bps(bid, ask, field=canonical)),
                "base_volume_24h": _decimal_text(base_volume),
                "quote_volume_24h_usd": _decimal_text(base_volume * last),
                "market_available": True,
                "decision_safe": True,
            }
        )
    records.sort(key=lambda item: str(item["symbol"]))
    snapshot: dict[str, object] = {
        "schema_version": 2,
        "snapshot_type": "WickHunterOkxMarketQualitySnapshot",
        "source": OKX_SOURCE,
        "scheduled_at_ms": scheduled_at_ms,
        "available_at_ms": available_at_ms,
        "source_separated": True,
        "cross_exchange_deduplication": False,
        "records": records,
        **AUTHORITY,
    }
    snapshot["snapshot_sha256"] = _canonical_hash(snapshot)
    return snapshot


def normalize_okx_candle_page(
    payload: object,
    *,
    canonical_symbol: str,
    fetched_at_ms: int,
) -> list[dict[str, object]]:
    root = _object(payload, field="OKX candle response")
    if str(root.get("code", "")) != "0":
        raise ProductionMarketEvidenceV2Error("OKX candle response code must be 0")
    records: list[dict[str, object]] = []
    for index, raw in enumerate(_sequence(root.get("data"), field="OKX candle data")):
        row = _sequence(raw, field=f"OKX candle data[{index}]")
        if len(row) < 9:
            raise ProductionMarketEvidenceV2Error("OKX candle row must contain nine fields")
        if str(row[8]) != "1":
            raise ProductionMarketEvidenceV2Error("uncompleted OKX candle was returned")
        open_time_ms = _integer(row[0], field="OKX candle open time")
        if open_time_ms % TIMEFRAME_MS:
            raise ProductionMarketEvidenceV2Error("OKX candle open time is not aligned to 5m")
        open_price = _decimal(row[1], field="OKX candle open", positive=True)
        high = _decimal(row[2], field="OKX candle high", positive=True)
        low = _decimal(row[3], field="OKX candle low", positive=True)
        close = _decimal(row[4], field="OKX candle close", positive=True)
        base_volume = _decimal(row[6], field="OKX candle base volume")
        quote_volume = _decimal(row[7], field="OKX candle quote volume")
        if high < max(open_price, low, close) or low > min(
            open_price,
            high,
            close,
        ):
            raise ProductionMarketEvidenceV2Error("OKX candle OHLC geometry is invalid")
        close_time_ms = open_time_ms + TIMEFRAME_MS
        records.append(
            {
                "schema_version": 2,
                "source": OKX_SOURCE,
                "symbol": canonical_symbol,
                "canonical_symbol": canonical_symbol,
                "native_symbol": okx_native_symbol(canonical_symbol),
                "pair": f"{canonical_symbol[:-4]}/USDT:USDT",
                "timeframe": TIMEFRAME,
                "open_time_ms": open_time_ms,
                "close_time_ms_exclusive": close_time_ms,
                "available_at_ms": close_time_ms,
                "fetched_at_ms": fetched_at_ms,
                "open": _decimal_text(open_price),
                "high": _decimal_text(high),
                "low": _decimal_text(low),
                "close": _decimal_text(close),
                "base_volume": _decimal_text(base_volume),
                "quote_volume": _decimal_text(quote_volume),
                "confirmed": True,
            }
        )
    records.sort(key=lambda item: _integer(item["open_time_ms"], field="open time"))
    return records


def validate_okx_candle_coverage(
    records: Sequence[Mapping[str, object]],
    *,
    canonical_symbol: str,
    start_ms: int,
    end_ms: int,
) -> None:
    actual = [_integer(row.get("open_time_ms"), field="open time") for row in records]
    expected = list(range(start_ms, end_ms, TIMEFRAME_MS))
    if actual != expected or len(actual) != len(set(actual)):
        raise ProductionMarketEvidenceV2Error(
            f"incomplete OKX candle coverage for {canonical_symbol}: "
            f"rows={len(actual)} expected={len(expected)}"
        )
    for row in records:
        if row.get("source") != OKX_SOURCE or row.get("symbol") != canonical_symbol:
            raise ProductionMarketEvidenceV2Error("OKX candle source or symbol mismatch")
        open_ms = _integer(row.get("open_time_ms"), field="open time")
        close_ms = _integer(row.get("close_time_ms_exclusive"), field="close time")
        if close_ms != open_ms + TIMEFRAME_MS or close_ms > end_ms:
            raise ProductionMarketEvidenceV2Error("OKX candle close boundary is invalid")


def okx_candle_url(canonical_symbol: str, *, before_open_ms: int) -> str:
    params = {
        "instId": okx_native_symbol(canonical_symbol),
        "bar": "5m",
        "after": str(before_open_ms),
        "limit": "100",
    }
    return f"{OKX_CANDLES_URL}?{urlencode(params)}"


def capture_okx_candles(
    *,
    canonical_symbol: str,
    start_ms: int,
    end_ms: int,
    fetch_json: _FETCH_JSON,
    wall_clock_ms: _CLOCK_MS,
) -> list[dict[str, object]]:
    by_open: dict[int, dict[str, object]] = {}
    cursor = end_ms
    for _ in range(8):
        fetched_at_ms = wall_clock_ms()
        page = normalize_okx_candle_page(
            fetch_json(okx_candle_url(canonical_symbol, before_open_ms=cursor)),
            canonical_symbol=canonical_symbol,
            fetched_at_ms=fetched_at_ms,
        )
        if not page:
            raise ProductionMarketEvidenceV2Error("OKX candle page is empty")
        earliest = min(_integer(row["open_time_ms"], field="open time") for row in page)
        if earliest >= cursor:
            raise ProductionMarketEvidenceV2Error("OKX candle pagination did not move backward")
        for row in page:
            open_ms = _integer(row["open_time_ms"], field="open time")
            if not start_ms <= open_ms < end_ms:
                continue
            previous = by_open.get(open_ms)
            if previous is not None:
                previous_copy = dict(previous)
                row_copy = dict(row)
                previous_copy.pop("fetched_at_ms", None)
                row_copy.pop("fetched_at_ms", None)
                if previous_copy != row_copy:
                    raise ProductionMarketEvidenceV2Error("conflicting duplicate OKX candle")
            by_open[open_ms] = row
        if earliest <= start_ms:
            break
        cursor = earliest
    records = [by_open[key] for key in sorted(by_open)]
    validate_okx_candle_coverage(
        records,
        canonical_symbol=canonical_symbol,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    return records


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ProductionMarketEvidenceV2Error("public endpoint is outside the OKX allowlist")
    if parsed.username or parsed.password or parsed.fragment:
        raise ProductionMarketEvidenceV2Error("public endpoint contains forbidden URL fields")
    forbidden = ("/api/v5/account", "/api/v5/trade", "/api/v5/asset")
    if parsed.path.startswith(forbidden):
        raise ProductionMarketEvidenceV2Error("private or mutating OKX endpoint is forbidden")


def fetch_public_bytes(url: str, timeout_seconds: int = 30) -> bytes:
    _validate_public_url(url)
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(  # noqa: S310
        url,
        headers={"User-Agent": "freqtrade-wickhunter-okx-evidence/2"},
    )
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            if response.status != 200 or response.geturl() != url:
                raise ProductionMarketEvidenceV2Error("public response status or URL drifted")
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise ProductionMarketEvidenceV2Error(f"public endpoint returned HTTP {exc.code}") from exc
    except (OSError, TimeoutError, URLError) as exc:
        raise ProductionMarketEvidenceV2Error(f"public endpoint failed: {exc}") from exc
    if len(content) > MAX_RESPONSE_BYTES:
        raise ProductionMarketEvidenceV2Error("public response exceeds size limit")
    return content


def fetch_public_json(url: str) -> object:
    try:
        return json.loads(fetch_public_bytes(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionMarketEvidenceV2Error("public response is not valid UTF-8 JSON") from exc


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


def _durable_path(request: CaptureRequestV2) -> Path:
    return Path(urlsplit(request.durable_storage_uri).path)


def _pointer_path(root: Path) -> Path:
    return root / ACTIVE_POINTER_NAME


def _state_path(run_root: Path) -> Path:
    return run_root / STATE_NAME


def _write_state(
    root: Path,
    run_root: Path,
    seed: Mapping[str, object],
) -> dict[str, object]:
    state = _self_hashed(seed, hash_field="state_sha256")
    _write_json(_state_path(run_root), state, replace=True)
    pointer = _self_hashed(
        {
            "pointer_version": ("wickhunter-production-market-evidence-active-pointer-v2"),
            "run_id": state["run_id"],
            "run_root": str(run_root),
            "state_sha256": state["state_sha256"],
        },
        hash_field="pointer_sha256",
    )
    _write_json(_pointer_path(root), pointer, replace=True)
    return state


def _load_active(root: Path) -> tuple[Path, dict[str, Any]]:
    pointer = _load_json(_pointer_path(root), field="v2 active pointer")
    _verify_self_hash(
        pointer,
        hash_field="pointer_sha256",
        field="v2 active pointer",
    )
    run_id = str(pointer.get("run_id", ""))
    run_root = Path(str(pointer.get("run_root", "")))
    if run_root != root / run_id:
        raise ProductionMarketEvidenceV2Error("active run root escapes durable root")
    state = _load_json(_state_path(run_root), field="v2 incremental state")
    _verify_self_hash(
        state,
        hash_field="state_sha256",
        field="v2 incremental state",
    )
    identity_mismatch = state.get("run_id") != run_id or state.get("state_sha256") != pointer.get(
        "state_sha256"
    )
    if identity_mismatch:
        raise ProductionMarketEvidenceV2Error("active state identity mismatch")
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
        raise ProductionMarketEvidenceV2Error("collector_commit must be a lowercase commit SHA")
    request = load_capture_request(request_path)
    if _durable_path(request) != durable_root:
        raise ProductionMarketEvidenceV2Error("request durable root does not match runtime root")
    with _exclusive_lock(durable_root):
        if _pointer_path(durable_root).exists():
            raise ProductionMarketEvidenceV2Error("an active v2 capture already exists")
        run_root = durable_root / request.run_id
        if run_root.exists() or run_root.is_symlink():
            raise ProductionMarketEvidenceV2Error("v2 run root already exists")
        (run_root / "market-samples").mkdir(parents=True)
        _write_json(run_root / REQUEST_NAME, request.as_json_dict())
        _write_state(
            durable_root,
            run_root,
            {
                "state_version": ("wickhunter-production-market-evidence-state-v2"),
                "status": "active",
                "run_id": request.run_id,
                "base_v1_run_id": request.base_v1_run_id,
                "collector_commit": collector_commit,
                "next_sample_index": 0,
                "sample_failures": 0,
                **AUTHORITY,
            },
        )
    return {
        "status": "initialized",
        "run_id": request.run_id,
        "run_root": str(run_root),
        "next_sample_index": 0,
        "due_ms": request.decision_start_ms,
    }


def _sample_root(run_root: Path, index: int) -> Path:
    return run_root / "market-samples" / f"{index:04d}"


def _sample_rows(
    run_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    quality: list[dict[str, Any]] = []
    instruments: list[dict[str, Any]] = []
    for index in range(EXPECTED_SAMPLES):
        root = _sample_root(run_root, index)
        snapshot = _load_json(
            root / "market-snapshot.json",
            field=f"market snapshot {index}",
        )
        instrument = _load_json(
            root / "instrument-snapshot.json",
            field=f"instrument snapshot {index}",
        )
        _verify_self_hash(
            snapshot,
            hash_field="snapshot_sha256",
            field=f"snapshot {index}",
        )
        _verify_self_hash(
            instrument,
            hash_field="snapshot_sha256",
            field=f"instrument snapshot {index}",
        )
        records = _sequence(snapshot.get("records"), field=f"snapshot {index} records")
        instrument_records = _sequence(
            instrument.get("records"),
            field=f"instrument snapshot {index} records",
        )
        valid_geometry = len(records) == len(EXPECTED_SYMBOLS) and len(instrument_records) == len(
            EXPECTED_SYMBOLS
        )
        if not valid_geometry:
            raise ProductionMarketEvidenceV2Error("sample source-symbol geometry mismatch")
        quality.extend(_object(row, field="quality row") for row in records)
        instruments.extend(_object(row, field="instrument row") for row in instrument_records)
    return quality, instruments


def collect_due_sample(
    *,
    durable_root: Path,
    environment: Mapping[str, str] | None = None,
    fetch_json: _FETCH_JSON = fetch_public_json,
    wall_clock_ms: _CLOCK_MS = lambda: time.time_ns() // 1_000_000,
) -> dict[str, object]:
    _refuse_environment(environment if environment is not None else os.environ)
    with _exclusive_lock(durable_root):
        run_root, state = _load_active(durable_root)
        request = load_capture_request(run_root / REQUEST_NAME)
        if state.get("status") != "active":
            return {
                "status": str(state.get("status")),
                "run_id": request.run_id,
            }
        index = _integer(state.get("next_sample_index"), field="next_sample_index")
        if index >= EXPECTED_SAMPLES:
            return finalize_supplement(
                durable_root=durable_root,
                run_root=run_root,
                request=request,
                state=state,
                fetch_json=fetch_json,
                wall_clock_ms=wall_clock_ms,
            )
        due_ms = request.decision_start_ms + (index * request.sample_interval_seconds * 1000)
        now_ms = wall_clock_ms()
        if now_ms < due_ms:
            return {
                "status": "waiting",
                "run_id": request.run_id,
                "due_ms": due_ms,
            }
        latest_ms = due_ms + request.max_sample_lateness_seconds * 1000
        if now_ms > latest_ms:
            failed = dict(state)
            failed.pop("state_sha256", None)
            failed.update(
                {
                    "status": "failed",
                    "failure_code": "OKX_SAMPLE_WINDOW_MISSED",
                    "failed_sample_index": index,
                    "failed_at_ms": now_ms,
                }
            )
            _write_state(durable_root, run_root, failed)
            raise ProductionMarketEvidenceV2Error(f"sample {index} exceeded the lateness window")
        instruments_payload = fetch_json(OKX_INSTRUMENTS_URL)
        tickers_payload = fetch_json(OKX_TICKERS_URL)
        available_at_ms = wall_clock_ms()
        if available_at_ms > latest_ms:
            raise ProductionMarketEvidenceV2Error(
                "OKX responses completed after the lateness window"
            )
        contracts, instrument_rows = normalize_okx_instruments(
            instruments_payload,
            available_at_ms=available_at_ms,
        )
        snapshot = normalize_okx_market_snapshot(
            scheduled_at_ms=due_ms,
            available_at_ms=available_at_ms,
            ticker_payload=tickers_payload,
            instruments=contracts,
            maximum_source_age_ms=request.maximum_source_age_ms,
        )
        sample_root = _sample_root(run_root, index)
        if sample_root.exists() or sample_root.is_symlink():
            raise ProductionMarketEvidenceV2Error("sample root already exists")
        sample_root.mkdir()
        _write_json(sample_root / "market-snapshot.json", snapshot)
        instrument_snapshot = _self_hashed(
            {
                "schema_version": 2,
                "snapshot_type": ("WickHunterOkxInstrumentHistorySnapshot"),
                "sample_index": index,
                "scheduled_at_ms": due_ms,
                "available_at_ms": available_at_ms,
                "records": instrument_rows,
                **AUTHORITY,
            },
            hash_field="snapshot_sha256",
        )
        _write_json(
            sample_root / "instrument-snapshot.json",
            instrument_snapshot,
        )
        _write_json(
            sample_root / "source-health.json",
            {
                "schema_version": 2,
                "source": OKX_SOURCE,
                "sample_index": index,
                "scheduled_at_ms": due_ms,
                "available_at_ms": available_at_ms,
                "connected": True,
                "healthy": True,
                "last_ticker_at_ms": max(
                    _integer(row.get("event_at_ms"), field="event_at_ms")
                    for row in _sequence(snapshot.get("records"), field="records")
                ),
                "last_completed_candle_at_ms": due_ms,
                "freshness_ms": available_at_ms - due_ms,
                "active_symbols": len(EXPECTED_SYMBOLS),
                "errors": [],
                "reconnect_count": 0,
                "gaps": 0,
                "records_written": len(EXPECTED_SYMBOLS),
                "required_scope": (
                    "ticker, spread, rolling quote volume, completed 5m "
                    "candles and instrument history"
                ),
                "wickhunter_available": True,
                "exclusion_reason": None,
                **AUTHORITY,
            },
        )
        updated = dict(state)
        updated.pop("state_sha256", None)
        updated["next_sample_index"] = index + 1
        updated["last_sample_available_at_ms"] = available_at_ms
        _write_state(durable_root, run_root, updated)
        return {
            "status": "sampled",
            "run_id": request.run_id,
            "sample_index": index,
            "next_sample_index": index + 1,
            "available_at_ms": available_at_ms,
        }


def _artifact_identity(path: Path, *, root: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ProductionMarketEvidenceV2Error("artifact is not a regular file")
    try:
        logical_name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ProductionMarketEvidenceV2Error("artifact path escapes supplement root") from exc
    return {
        "logical_name": logical_name,
        "sha256": _file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _candle_artifact_path(
    artifact: Mapping[str, object],
    *,
    root: Path,
) -> Path:
    normalized = _object(artifact.get("normalized_file"), field="normalized candle file")
    logical_name = str(normalized.get("logical_name", ""))
    return root / logical_name


def finalize_supplement(
    *,
    durable_root: Path,
    run_root: Path,
    request: CaptureRequestV2,
    state: Mapping[str, object],
    fetch_json: _FETCH_JSON,
    wall_clock_ms: _CLOCK_MS,
) -> dict[str, object]:
    sample_index = _integer(state.get("next_sample_index"), field="next_sample_index")
    if sample_index != EXPECTED_SAMPLES:
        raise ProductionMarketEvidenceV2Error("not all prospective OKX samples are complete")
    if wall_clock_ms() < request.decision_end_ms:
        return {
            "status": "waiting_for_interval_end",
            "run_id": request.run_id,
            "due_ms": request.decision_end_ms,
        }
    final_root = run_root / SUPPLEMENT_DIR_NAME
    if final_root.exists() and not final_root.is_symlink():
        return verify_supplement(final_root)
    partial_root = run_root / SUPPLEMENT_PARTIAL_DIR_NAME
    if partial_root.exists() or partial_root.is_symlink():
        raise ProductionMarketEvidenceV2Error("partial supplement root already exists")
    partial_root.mkdir()
    try:
        quality_rows, instrument_rows = _sample_rows(run_root)
        source_rows = [
            _load_json(
                _sample_root(run_root, index) / "source-health.json",
                field=f"source health {index}",
            )
            for index in range(EXPECTED_SAMPLES)
        ]
        candle_artifacts: list[dict[str, object]] = []
        for symbol in EXPECTED_SYMBOLS:
            records = capture_okx_candles(
                canonical_symbol=symbol,
                start_ms=request.pre_roll_start_ms,
                end_ms=request.decision_end_ms,
                fetch_json=fetch_json,
                wall_clock_ms=wall_clock_ms,
            )
            relative = Path("candles") / OKX_SOURCE / f"{symbol}-5m.ndjson"
            path = partial_root / relative
            _write_ndjson(path, records)
            candle_artifacts.append(
                {
                    "source": OKX_SOURCE,
                    "market": "USDT-margined perpetual swap",
                    "symbol": symbol,
                    "native_symbol": okx_native_symbol(symbol),
                    "pair": f"{symbol[:-4]}/USDT:USDT",
                    "timeframe": TIMEFRAME,
                    "record_count": len(records),
                    "start_ms": request.pre_roll_start_ms,
                    "end_ms": request.decision_end_ms,
                    "normalized_file": _artifact_identity(
                        path,
                        root=partial_root,
                    ),
                }
            )
        _write_json(partial_root / "request.json", request.as_json_dict())
        _write_ndjson(
            partial_root / "source-snapshots.ndjson",
            source_rows,
        )
        _write_ndjson(
            partial_root / "market-quality-observations.ndjson",
            quality_rows,
        )
        _write_ndjson(
            partial_root / "instrument-snapshots.ndjson",
            instrument_rows,
        )
        _write_json(
            partial_root / "completed-candles-index.json",
            {"schema_version": 2, "artifacts": candle_artifacts},
        )
        artifact_names = (
            "request.json",
            "source-snapshots.ndjson",
            "market-quality-observations.ndjson",
            "instrument-snapshots.ndjson",
            "completed-candles-index.json",
        )
        artifacts = [
            _artifact_identity(partial_root / name, root=partial_root) for name in artifact_names
        ]
        artifacts.extend(
            _artifact_identity(
                _candle_artifact_path(artifact, root=partial_root),
                root=partial_root,
            )
            for artifact in candle_artifacts
        )
        manifest: dict[str, object] = {
            "schema_version": 2,
            "artifact_type": ("WickHunterProductionMarketEvidenceOkxSupplement"),
            "contract_id": CONTRACT_ID,
            "request_id": request.request_id,
            "run_id": request.run_id,
            "base_v1_run_id": request.base_v1_run_id,
            "collector_commit": state["collector_commit"],
            "source": OKX_SOURCE,
            "symbols": list(EXPECTED_SYMBOLS),
            "capture": {
                "pre_roll_start_ms": request.pre_roll_start_ms,
                "decision_start_ms": request.decision_start_ms,
                "decision_end_ms": request.decision_end_ms,
                "sample_interval_seconds": request.sample_interval_seconds,
                "sample_count": EXPECTED_SAMPLES,
            },
            "record_counts": {
                "market_quality_observations": len(quality_rows),
                "instrument_snapshots": len(instrument_rows),
                "source_health_snapshots": len(source_rows),
                "completed_candles": (len(EXPECTED_SYMBOLS) * EXPECTED_CANDLES),
            },
            "gaps": [],
            "artifacts": artifacts,
            "base_package_bound": False,
            "merge_blocker": "BASE_V1_PACKAGE_NOT_BOUND",
            **AUTHORITY,
        }
        manifest["manifest_sha256"] = _canonical_hash(manifest)
        _write_json(partial_root / "manifest.json", manifest)
        checksum_identities = [
            *artifacts,
            _artifact_identity(
                partial_root / "manifest.json",
                root=partial_root,
            ),
        ]
        checksum_lines = sorted(
            f"{item['sha256']}  {item['logical_name']}" for item in checksum_identities
        )
        _write_new(
            partial_root / "artifact-sha256.txt",
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        _write_json(
            partial_root / "verification-report.json",
            {
                "schema_version": 2,
                "outcome": "accepted",
                "run_id": request.run_id,
                "manifest_sha256": manifest["manifest_sha256"],
                "artifact_count": len(artifacts),
                "base_package_bound": False,
                "merge_blocker": "BASE_V1_PACKAGE_NOT_BOUND",
                **AUTHORITY,
            },
        )
        verify_supplement(partial_root)
        partial_root.replace(final_root)
        updated = dict(state)
        updated.pop("state_sha256", None)
        updated["status"] = "supplement_completed"
        updated["supplement_manifest_sha256"] = manifest["manifest_sha256"]
        _write_state(durable_root, run_root, updated)
        return verify_supplement(final_root)
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise


def verify_supplement(root: Path) -> dict[str, object]:
    if root.is_symlink() or not root.is_dir():
        raise ProductionMarketEvidenceV2Error("supplement root must be a regular directory")
    manifest = _load_json(root / "manifest.json", field="supplement manifest")
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if not isinstance(claimed, str) or _canonical_hash(seed) != claimed:
        raise ProductionMarketEvidenceV2Error("supplement manifest self hash mismatch")
    coverage_mismatch = manifest.get("source") != OKX_SOURCE or manifest.get("symbols") != list(
        EXPECTED_SYMBOLS
    )
    if coverage_mismatch:
        raise ProductionMarketEvidenceV2Error("supplement source or symbol coverage mismatch")
    if any(manifest.get(key) != value for key, value in AUTHORITY.items()):
        raise ProductionMarketEvidenceV2Error("supplement authority boundary mismatch")
    expected_counts = {
        "market_quality_observations": EXPECTED_SAMPLES * len(EXPECTED_SYMBOLS),
        "instrument_snapshots": EXPECTED_SAMPLES * len(EXPECTED_SYMBOLS),
        "source_health_snapshots": EXPECTED_SAMPLES,
        "completed_candles": EXPECTED_CANDLES * len(EXPECTED_SYMBOLS),
    }
    counts = _object(manifest.get("record_counts"), field="record counts")
    if counts != expected_counts:
        raise ProductionMarketEvidenceV2Error("supplement record counts mismatch")
    expected_lines: set[str] = set()
    artifacts = _sequence(manifest.get("artifacts"), field="supplement artifacts")
    for raw in artifacts:
        identity = _object(raw, field="artifact identity")
        logical_name = str(identity.get("logical_name", ""))
        relative = Path(logical_name)
        unsafe = relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts)
        if unsafe:
            raise ProductionMarketEvidenceV2Error("artifact path is unsafe")
        path = root / relative
        identity_mismatch = (
            path.is_symlink()
            or not path.is_file()
            or _file_hash(path) != identity.get("sha256")
            or path.stat().st_size != identity.get("size_bytes")
        )
        if identity_mismatch:
            raise ProductionMarketEvidenceV2Error("supplement artifact identity mismatch")
        expected_lines.add(f"{identity['sha256']}  {logical_name}")
    manifest_identity = _artifact_identity(root / "manifest.json", root=root)
    expected_lines.add(f"{manifest_identity['sha256']}  {manifest_identity['logical_name']}")
    checksum = root / "artifact-sha256.txt"
    if checksum.is_symlink() or not checksum.is_file():
        raise ProductionMarketEvidenceV2Error("supplement checksum is missing")
    if set(checksum.read_text(encoding="utf-8").splitlines()) != expected_lines:
        raise ProductionMarketEvidenceV2Error("supplement checksum mismatch")
    verification = _load_json(
        root / "verification-report.json",
        field="verification report",
    )
    invalid_verification = (
        verification.get("outcome") != "accepted" or verification.get("manifest_sha256") != claimed
    )
    if invalid_verification:
        raise ProductionMarketEvidenceV2Error("supplement verification mismatch")
    if any(verification.get(key) != value for key, value in AUTHORITY.items()):
        raise ProductionMarketEvidenceV2Error("verification authority boundary mismatch")
    return {
        "status": "supplement_completed",
        "outcome": "accepted",
        "run_id": manifest["run_id"],
        "base_v1_run_id": manifest["base_v1_run_id"],
        "supplement_root": str(root),
        "manifest_sha256": claimed,
        "base_package_bound": False,
        "merge_blocker": "BASE_V1_PACKAGE_NOT_BOUND",
        **AUTHORITY,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Capture and verify the public OKX Market Evidence v2 supplement.")
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("initialize")
    initialize.add_argument("--request", type=Path, required=True)
    initialize.add_argument("--durable-root", type=Path, required=True)
    initialize.add_argument("--collector-commit", required=True)
    sample = subparsers.add_parser("sample")
    sample.add_argument("--durable-root", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--supplement-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "initialize":
        result = initialize_capture(
            request_path=args.request,
            durable_root=args.durable_root,
            collector_commit=args.collector_commit,
        )
    elif args.command == "sample":
        result = collect_due_sample(durable_root=args.durable_root)
    else:
        result = verify_supplement(args.supplement_root)
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
