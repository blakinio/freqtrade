from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCHEMA_VERSION = 1
PROFILE_NAME = "liquid20-v1"
TIMEFRAME = "5m"
TIMEFRAME_MS = 5 * 60 * 1000
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
SOURCE_ORDER = ("bybit-linear", "binance-usdm")
RUN_ID_PATTERN = re.compile(r"^liquid20-\d{8}T\d{6}Z-\d+$")
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]+USDT$")
EXPECTED_SOURCE_CONFIG: dict[str, dict[str, object]] = {
    "bybit-linear": {
        "endpoint": "https://api.bybit.com/v5/market/kline",
        "market": "linear perpetual trade-price candles",
        "interval_parameter": "5",
        "response_order": "reverse_start_time",
        "public_market_data": True,
    },
    "binance-usdm": {
        "endpoint": "https://fapi.binance.com/fapi/v1/klines",
        "market": "USD-M perpetual trade-price candles",
        "interval_parameter": "5m",
        "response_order": "ascending_start_time",
        "public_market_data": True,
    },
}
EXPECTED_POLICIES = {
    "credentials_allowed": False,
    "orders_allowed": False,
    "cross_exchange_deduplication": False,
    "missing_candle_is_zero": False,
    "containing_incomplete_candle_allowed": False,
    "performance_research_authorized": False,
}
RECOGNIZED_CREDENTIAL_ENV = (
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "FT_EXCHANGE_KEY",
    "FT_EXCHANGE_SECRET",
    "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET",
)
FORBIDDEN_REQUEST_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "token",
)


class CandleArtifactError(RuntimeError):
    """Raised when candle evidence cannot be produced without ambiguity."""


@dataclass(frozen=True, slots=True)
class SourceSpec:
    source: str
    endpoint: str
    interval_parameter: str
    market: str
    response_order: str


@dataclass(frozen=True, slots=True)
class BoundIdentity:
    logical_path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactRequest:
    request_id: str
    purpose_classification: str
    target_run_ids: tuple[str, ...]
    start_ms: int
    end_ms: int
    timeframe: str
    expected_rows_per_file: int
    pair_mapping: tuple[tuple[str, str], ...]
    sources: tuple[SourceSpec, ...]
    source_catalog: BoundIdentity
    symbol_universe: BoundIdentity
    protected_holdout_start_ms: int
    protected_holdout_end_ms: int
    performance_research_authorized: bool


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise CandleArtifactError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise CandleArtifactError(f"{field} must be a list")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CandleArtifactError(f"{field} must be a non-empty string")
    return value.strip()


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CandleArtifactError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise CandleArtifactError(f"{field} must be an integer") from exc


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise CandleArtifactError(f"{field} must be a boolean")
    return value


def _decimal_text(value: object, *, field: str, positive: bool) -> str:
    if isinstance(value, bool):
        raise CandleArtifactError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CandleArtifactError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite() or (parsed <= 0 if positive else parsed < 0):
        comparator = "> 0" if positive else ">= 0"
        raise CandleArtifactError(f"{field} must be finite and {comparator}")
    text = format(parsed, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _iso_to_ms(value: object, *, field: str) -> int:
    text = _text(value, field=field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CandleArtifactError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise CandleArtifactError(f"{field} must include a timezone")
    return int(parsed.astimezone(UTC).timestamp() * 1000)


def load_json(path: Path, *, field: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandleArtifactError(f"unable to read {field} {path}: {exc}") from exc
    return _mapping(payload, field=field)


def _repo_file(path: Path, *, repo_root: Path, field: str) -> Path:
    candidate = path.resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise CandleArtifactError(f"{field} escapes repository root") from exc
    if not candidate.is_file():
        raise CandleArtifactError(f"{field} file is missing: {candidate}")
    return candidate


def _load_bound_identity(
    payload: Mapping[str, Any],
    *,
    repo_root: Path,
    field: str,
) -> tuple[BoundIdentity, Mapping[str, Any]]:
    logical_path = _text(payload.get("logical_path"), field=f"{field}.logical_path")
    expected_hash = _text(payload.get("sha256"), field=f"{field}.sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise CandleArtifactError(f"{field}.sha256 must be 64 lowercase hexadecimal characters")
    candidate = _repo_file(repo_root / logical_path, repo_root=repo_root, field=field)
    actual_hash = sha256_file(candidate)
    if actual_hash != expected_hash:
        raise CandleArtifactError(
            f"{field} SHA-256 mismatch: expected {expected_hash}, got {actual_hash}"
        )
    return BoundIdentity(logical_path, expected_hash), load_json(candidate, field=field)


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        mapping_result = {str(key).casefold() for key in value}
        for child in value.values():
            mapping_result.update(_collect_keys(child))
        return mapping_result
    if isinstance(value, list):
        list_result: set[str] = set()
        for child in value:
            list_result.update(_collect_keys(child))
        return list_result
    return set()


def _validate_no_secret_fields(request: Mapping[str, Any]) -> None:
    forbidden = sorted(
        key
        for key in _collect_keys(request)
        if any(fragment in key for fragment in FORBIDDEN_REQUEST_KEY_FRAGMENTS)
    )
    if forbidden:
        raise CandleArtifactError(f"request contains forbidden secret-shaped fields: {forbidden}")


def _profile_symbols(universe: Mapping[str, Any]) -> tuple[str, ...]:
    profiles = _sequence(universe.get("profiles"), field="symbol_universe.profiles")
    matches = [
        _mapping(raw, field="symbol_universe.profiles[]")
        for raw in profiles
        if isinstance(raw, dict) and raw.get("name") == PROFILE_NAME
    ]
    if len(matches) != 1:
        raise CandleArtifactError(
            f"symbol universe must contain exactly one {PROFILE_NAME} profile"
        )
    profile = matches[0]
    symbols = tuple(
        _text(value, field="symbol_universe.symbols[]")
        for value in _sequence(profile.get("symbols"), field="symbol_universe.symbols")
    )
    if profile.get("symbol_count") != len(symbols):
        raise CandleArtifactError("symbol universe count does not match ordered symbols")
    if len(symbols) != 20 or len(set(symbols)) != 20:
        raise CandleArtifactError("liquid20-v1 must contain exactly 20 unique symbols")
    if any(not SYMBOL_PATTERN.fullmatch(symbol) for symbol in symbols):
        raise CandleArtifactError("liquid20-v1 contains an invalid USDT symbol")
    return symbols


def _validate_catalog(catalog: Mapping[str, Any]) -> None:
    sources = _sequence(catalog.get("sources"), field="source_catalog.sources")
    source_ids = tuple(
        _text(_mapping(raw, field="source_catalog.sources[]").get("source"), field="source")
        for raw in sources
    )
    if not all(source in source_ids for source in SOURCE_ORDER):
        raise CandleArtifactError("source catalog does not contain both Liquid20 sources")
    cross = _mapping(catalog.get("cross_source_policy"), field="source_catalog.cross_source_policy")
    if cross.get("deduplicate_between_exchanges") is not False:
        raise CandleArtifactError("source catalog cross-exchange deduplication must remain false")
    if cross.get("sum_events_without_source_labels") is not False:
        raise CandleArtifactError("source catalog unlabeled summation must remain false")


def _validate_contract_sources(contract: Mapping[str, Any]) -> tuple[SourceSpec, ...]:
    raw_sources = _sequence(contract.get("sources"), field="contract.sources")
    parsed: dict[str, SourceSpec] = {}
    for index, raw in enumerate(raw_sources):
        item = _mapping(raw, field=f"contract.sources[{index}]")
        source_id = _text(item.get("source"), field=f"contract.sources[{index}].source")
        if source_id in parsed:
            raise CandleArtifactError(f"duplicate contract source: {source_id}")
        expected = EXPECTED_SOURCE_CONFIG.get(source_id)
        if expected is None:
            raise CandleArtifactError(f"unsupported contract source: {source_id}")
        for key, expected_value in expected.items():
            if item.get(key) != expected_value:
                raise CandleArtifactError(
                    f"contract source {source_id}.{key} drifted from the frozen value"
                )
        parsed[source_id] = SourceSpec(
            source=source_id,
            endpoint=str(expected["endpoint"]),
            interval_parameter=str(expected["interval_parameter"]),
            market=str(expected["market"]),
            response_order=str(expected["response_order"]),
        )
    if tuple(parsed) != SOURCE_ORDER:
        raise CandleArtifactError("contract sources must preserve Bybit then Binance order")
    return tuple(parsed[source] for source in SOURCE_ORDER)


def load_request(contract_path: Path, request_path: Path, *, repo_root: Path) -> ArtifactRequest:
    contract_path = _repo_file(contract_path, repo_root=repo_root, field="contract")
    request_path = _repo_file(request_path, repo_root=repo_root, field="request")
    contract = load_json(contract_path, field="contract")
    request = load_json(request_path, field="request")
    _validate_no_secret_fields(request)

    if contract.get("schema_version") != SCHEMA_VERSION:
        raise CandleArtifactError("contract schema_version must be 1")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise CandleArtifactError("request schema_version must be 1")
    if contract.get("classification") != "diagnostic_public_market_data_only":
        raise CandleArtifactError("contract classification drifted")
    contract_id = _text(contract.get("contract_id"), field="contract.contract_id")
    if request.get("contract_id") != contract_id:
        raise CandleArtifactError("request contract_id does not match contract")
    if _mapping(contract.get("policies"), field="contract.policies") != EXPECTED_POLICIES:
        raise CandleArtifactError("contract safety policies drifted")

    source_identity, catalog = _load_bound_identity(
        _mapping(contract.get("source_catalog"), field="contract.source_catalog"),
        repo_root=repo_root,
        field="contract.source_catalog",
    )
    universe_identity, universe = _load_bound_identity(
        _mapping(contract.get("symbol_universe"), field="contract.symbol_universe"),
        repo_root=repo_root,
        field="contract.symbol_universe",
    )
    if contract["symbol_universe"].get("profile") != PROFILE_NAME:
        raise CandleArtifactError("contract symbol universe profile drifted")
    _validate_catalog(catalog)
    universe_symbols = _profile_symbols(universe)
    contract_sources = _validate_contract_sources(contract)

    purpose = _text(request.get("purpose_classification"), field="request.purpose_classification")
    if purpose != "diagnostic_only":
        raise CandleArtifactError("initial candle request must remain diagnostic_only")
    performance_authorized = _boolean(
        request.get("performance_research_authorized"),
        field="request.performance_research_authorized",
    )
    if performance_authorized:
        raise CandleArtifactError("diagnostic candle request cannot authorize performance research")

    target_runs = tuple(
        _text(value, field="request.target_run_ids[]")
        for value in _sequence(request.get("target_run_ids"), field="request.target_run_ids")
    )
    if len(target_runs) != 1 or not RUN_ID_PATTERN.fullmatch(target_runs[0]):
        raise CandleArtifactError("initial request must bind exactly one valid Liquid20 run ID")

    window = _mapping(request.get("window"), field="request.window")
    start_ms = _integer(window.get("start_ms"), field="request.window.start_ms")
    end_ms = _integer(window.get("end_ms"), field="request.window.end_ms")
    if _iso_to_ms(window.get("start"), field="request.window.start") != start_ms:
        raise CandleArtifactError("request.window.start does not match start_ms")
    if _iso_to_ms(window.get("end"), field="request.window.end") != end_ms:
        raise CandleArtifactError("request.window.end does not match end_ms")
    timeframe = _text(window.get("timeframe"), field="request.window.timeframe")
    expected_rows = _integer(
        window.get("expected_rows_per_file"),
        field="request.window.expected_rows_per_file",
    )
    if timeframe != TIMEFRAME:
        raise CandleArtifactError(f"timeframe must be {TIMEFRAME}")
    if start_ms <= 0 or end_ms <= start_ms:
        raise CandleArtifactError("request window must be positive and bounded")
    if start_ms % TIMEFRAME_MS or end_ms % TIMEFRAME_MS:
        raise CandleArtifactError("request window must align to 5m boundaries")
    calculated_rows = (end_ms - start_ms) // TIMEFRAME_MS
    if expected_rows != calculated_rows:
        raise CandleArtifactError(f"expected_rows_per_file must equal {calculated_rows}")
    if expected_rows > 1000:
        raise CandleArtifactError("v1 request exceeds one-page source limits")

    holdout = _mapping(contract.get("protected_holdout"), field="contract.protected_holdout")
    holdout_start = _integer(holdout.get("start_ms"), field="protected_holdout.start_ms")
    holdout_end = _integer(holdout.get("end_ms"), field="protected_holdout.end_ms")
    if _iso_to_ms(holdout.get("start"), field="protected_holdout.start") != holdout_start:
        raise CandleArtifactError("protected holdout start identity drifted")
    if _iso_to_ms(holdout.get("end"), field="protected_holdout.end") != holdout_end:
        raise CandleArtifactError("protected holdout end identity drifted")
    if max(start_ms, holdout_start) < min(end_ms, holdout_end):
        raise CandleArtifactError("request window overlaps protected holdout")

    mappings: list[tuple[str, str]] = []
    pair_mapping = _sequence(request.get("pair_mapping"), field="request.pair_mapping")
    for index, raw in enumerate(pair_mapping):
        item = _mapping(raw, field=f"request.pair_mapping[{index}]")
        raw_symbol = _text(item.get("symbol"), field=f"pair_mapping[{index}].symbol")
        if raw_symbol != raw_symbol.upper() or not SYMBOL_PATTERN.fullmatch(raw_symbol):
            raise CandleArtifactError(f"invalid Liquid20 symbol: {raw_symbol}")
        pair = _text(item.get("pair"), field=f"pair_mapping[{index}].pair")
        expected_pair = f"{raw_symbol[:-4]}/USDT:USDT"
        if pair != expected_pair:
            raise CandleArtifactError(
                f"pair mapping mismatch for {raw_symbol}: expected {expected_pair}, got {pair}"
            )
        mappings.append((raw_symbol, pair))
    if tuple(symbol for symbol, _ in mappings) != universe_symbols:
        raise CandleArtifactError(
            "pair_mapping must exactly preserve ordered liquid20-v1 membership"
        )

    requested_sources = tuple(
        _text(value, field="request.sources[]")
        for value in _sequence(request.get("sources"), field="request.sources")
    )
    if requested_sources != SOURCE_ORDER:
        raise CandleArtifactError("request sources must preserve bybit-linear then binance-usdm")

    return ArtifactRequest(
        request_id=_text(request.get("request_id"), field="request.request_id"),
        purpose_classification=purpose,
        target_run_ids=target_runs,
        start_ms=start_ms,
        end_ms=end_ms,
        timeframe=timeframe,
        expected_rows_per_file=expected_rows,
        pair_mapping=tuple(mappings),
        sources=contract_sources,
        source_catalog=source_identity,
        symbol_universe=universe_identity,
        protected_holdout_start_ms=holdout_start,
        protected_holdout_end_ms=holdout_end,
        performance_research_authorized=performance_authorized,
    )


def _validate_ohlcv(
    *,
    open_price: str,
    high_price: str,
    low_price: str,
    close_price: str,
    base_volume: str,
    quote_volume: str,
    field: str,
) -> None:
    open_decimal = Decimal(open_price)
    high_decimal = Decimal(high_price)
    low_decimal = Decimal(low_price)
    close_decimal = Decimal(close_price)
    if high_decimal < max(open_decimal, low_decimal, close_decimal):
        raise CandleArtifactError(f"{field}.high is below another OHLC value")
    if low_decimal > min(open_decimal, high_decimal, close_decimal):
        raise CandleArtifactError(f"{field}.low is above another OHLC value")
    if Decimal(base_volume) < 0 or Decimal(quote_volume) < 0:
        raise CandleArtifactError(f"{field}.volume must be non-negative")


def _record(
    *,
    source: str,
    symbol: str,
    pair: str,
    open_time_ms: object,
    open_price: object,
    high_price: object,
    low_price: object,
    close_price: object,
    base_volume: object,
    quote_volume: object,
    field: str,
    reported_close_time_ms: object | None = None,
) -> dict[str, object]:
    open_time = _integer(open_time_ms, field=f"{field}.open_time_ms")
    if open_time % TIMEFRAME_MS:
        raise CandleArtifactError(f"{field}.open_time_ms is not aligned to 5m")
    if reported_close_time_ms is not None:
        reported_close = _integer(reported_close_time_ms, field=f"{field}.close_time_ms")
        if reported_close != open_time + TIMEFRAME_MS - 1:
            raise CandleArtifactError(f"{field}.reported close boundary is invalid")
    open_text = _decimal_text(open_price, field=f"{field}.open", positive=True)
    high_text = _decimal_text(high_price, field=f"{field}.high", positive=True)
    low_text = _decimal_text(low_price, field=f"{field}.low", positive=True)
    close_text = _decimal_text(close_price, field=f"{field}.close", positive=True)
    base_text = _decimal_text(base_volume, field=f"{field}.base_volume", positive=False)
    quote_text = _decimal_text(quote_volume, field=f"{field}.quote_volume", positive=False)
    _validate_ohlcv(
        open_price=open_text,
        high_price=high_text,
        low_price=low_text,
        close_price=close_text,
        base_volume=base_text,
        quote_volume=quote_text,
        field=field,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "symbol": symbol,
        "pair": pair,
        "timeframe": TIMEFRAME,
        "open_time_ms": open_time,
        "close_time_ms_exclusive": open_time + TIMEFRAME_MS,
        "open": open_text,
        "high": high_text,
        "low": low_text,
        "close": close_text,
        "base_volume": base_text,
        "quote_volume": quote_text,
    }


def normalize_bybit_payload(
    payload: object,
    *,
    symbol: str,
    pair: str,
) -> list[dict[str, object]]:
    root = _mapping(payload, field="bybit response")
    if root.get("retCode") != 0:
        raise CandleArtifactError(f"Bybit returned retCode={root.get('retCode')}")
    result = _mapping(root.get("result"), field="bybit result")
    if result.get("symbol") != symbol or result.get("category") != "linear":
        raise CandleArtifactError("Bybit response identity mismatch")
    records: list[dict[str, object]] = []
    for index, raw in enumerate(_sequence(result.get("list"), field="bybit result.list")):
        row = _sequence(raw, field=f"bybit result.list[{index}]")
        if len(row) < 7:
            raise CandleArtifactError("Bybit kline row must contain at least 7 fields")
        records.append(
            _record(
                source="bybit-linear",
                symbol=symbol,
                pair=pair,
                open_time_ms=row[0],
                open_price=row[1],
                high_price=row[2],
                low_price=row[3],
                close_price=row[4],
                base_volume=row[5],
                quote_volume=row[6],
                field=f"bybit row {index}",
            )
        )
    return sorted(
        records,
        key=lambda item: _integer(item["open_time_ms"], field="record.open_time_ms"),
    )


def normalize_binance_payload(
    payload: object,
    *,
    symbol: str,
    pair: str,
) -> list[dict[str, object]]:
    rows = _sequence(payload, field="binance response")
    records: list[dict[str, object]] = []
    for index, raw in enumerate(rows):
        row = _sequence(raw, field=f"binance response[{index}]")
        if len(row) < 8:
            raise CandleArtifactError("Binance kline row must contain at least 8 fields")
        records.append(
            _record(
                source="binance-usdm",
                symbol=symbol,
                pair=pair,
                open_time_ms=row[0],
                open_price=row[1],
                high_price=row[2],
                low_price=row[3],
                close_price=row[4],
                base_volume=row[5],
                reported_close_time_ms=row[6],
                quote_volume=row[7],
                field=f"binance row {index}",
            )
        )
    return sorted(
        records,
        key=lambda item: _integer(item["open_time_ms"], field="record.open_time_ms"),
    )


def validate_complete_coverage(
    records: Sequence[Mapping[str, object]],
    *,
    source: str,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> None:
    actual = [_integer(record["open_time_ms"], field="record.open_time_ms") for record in records]
    if len(actual) != len(set(actual)):
        raise CandleArtifactError(f"duplicate candle open time for {source} {symbol}")
    expected = list(range(start_ms, end_ms, TIMEFRAME_MS))
    if actual != expected:
        actual_set = set(actual)
        expected_set = set(expected)
        missing = sorted(expected_set - actual_set)[:5]
        extra = sorted(actual_set - expected_set)[:5]
        raise CandleArtifactError(
            f"incomplete candle coverage for {source} {symbol}: "
            f"rows={len(actual)} expected={len(expected)} missing={missing} extra={extra}"
        )
    for record in records:
        if record.get("source") != source or record.get("symbol") != symbol:
            raise CandleArtifactError(f"source or symbol mismatch for {source} {symbol}")
        open_time = _integer(record["open_time_ms"], field="record.open_time_ms")
        if (
            _integer(
                record["close_time_ms_exclusive"],
                field="record.close_time_ms_exclusive",
            )
            != open_time + TIMEFRAME_MS
        ):
            raise CandleArtifactError(f"invalid candle close boundary for {source} {symbol}")


def http_json(url: str, *, attempts: int = 3, timeout_seconds: int = 30) -> object:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(url, headers={"User-Agent": "freqtrade-liquid20-candle-evidence/1"})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
                if response.status != 200:
                    raise CandleArtifactError(
                        f"unexpected HTTP status {response.status} for public candle endpoint"
                    )
                content = response.read(MAX_RESPONSE_BYTES + 1)
                if len(content) > MAX_RESPONSE_BYTES:
                    raise CandleArtifactError("public candle response exceeds size limit")
                return json.loads(content.decode("utf-8"))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {418, 429, 500, 502, 503, 504} or attempt + 1 == attempts:
                break
        except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            last_error = exc
            if attempt + 1 == attempts:
                break
        time.sleep(2**attempt)
    raise CandleArtifactError(f"unable to fetch public candle data: {last_error}")


def source_url(source: SourceSpec, *, symbol: str, start_ms: int, end_ms: int) -> str:
    if source.source == "bybit-linear":
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": source.interval_parameter,
            "start": start_ms,
            "end": end_ms - 1,
            "limit": 1000,
        }
    elif source.source == "binance-usdm":
        params = {
            "symbol": symbol,
            "interval": source.interval_parameter,
            "startTime": start_ms,
            "endTime": end_ms - 1,
            "limit": 1000,
        }
    else:
        raise CandleArtifactError(f"unsupported source: {source.source}")
    return f"{source.endpoint}?{urlencode(params)}"


def _write_records(path: Path, records: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        for record in records:
            handle.write(canonical_json_bytes(dict(record)) + b"\n")


def _assert_no_credentials(env: Mapping[str, str]) -> None:
    present = sorted(name for name in RECOGNIZED_CREDENTIAL_ENV if env.get(name))
    if present:
        raise CandleArtifactError(f"recognized trading credentials are present: {present}")


def _repo_relative(path: Path, *, repo_root: Path, field: str) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise CandleArtifactError(f"{field} escapes repository root") from exc


def _manifest(
    *,
    request: ArtifactRequest,
    contract_path: Path,
    request_path: Path,
    repo_root: Path,
    code_commit: str,
    artifacts: list[dict[str, object]],
) -> dict[str, object]:
    source_identities = [
        {
            "source": source.source,
            "endpoint": source.endpoint,
            "market": source.market,
            "interval_parameter": source.interval_parameter,
            "response_order": source.response_order,
        }
        for source in request.sources
    ]
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "Liquid20CandleArtifactManifest",
        "document_id": request.request_id,
        "purpose_classification": request.purpose_classification,
        "target_run_ids": list(request.target_run_ids),
        "code_commit": code_commit,
        "contract": {
            "logical_name": _repo_relative(
                contract_path,
                repo_root=repo_root,
                field="contract",
            ),
            "sha256": sha256_file(contract_path),
        },
        "request": {
            "logical_name": _repo_relative(
                request_path,
                repo_root=repo_root,
                field="request",
            ),
            "sha256": sha256_file(request_path),
        },
        "source_catalog": {
            "logical_name": request.source_catalog.logical_path,
            "sha256": request.source_catalog.sha256,
        },
        "symbol_universe": {
            "logical_name": request.symbol_universe.logical_path,
            "sha256": request.symbol_universe.sha256,
            "profile": PROFILE_NAME,
        },
        "source_identities": source_identities,
        "pair_mapping": [{"symbol": symbol, "pair": pair} for symbol, pair in request.pair_mapping],
        "window": {
            "start_ms": request.start_ms,
            "end_ms": request.end_ms,
            "timeframe": request.timeframe,
            "expected_rows_per_file": request.expected_rows_per_file,
        },
        "source_separated": True,
        "cross_exchange_deduplication": False,
        "missing_candle_is_zero": False,
        "artifacts": artifacts,
        "protected_holdout_check": {
            "start_ms": request.protected_holdout_start_ms,
            "end_ms": request.protected_holdout_end_ms,
            "overlap_detected": False,
            "passed": True,
        },
        "data_use": {
            "diagnostic_only": True,
            "strict_oos": False,
            "performance_research_authorized": False,
        },
        "execution_safety": {
            "trading_credentials_present": False,
            "orders_submitted": 0,
        },
        "performance_research_authorized": request.performance_research_authorized,
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def build_artifact(
    *,
    contract_path: Path,
    request_path: Path,
    output_root: Path,
    repo_root: Path,
    code_commit: str,
    fetch_json: Callable[[str], object] = http_json,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    _assert_no_credentials(env or os.environ)
    if not re.fullmatch(r"[0-9a-f]{40}", code_commit):
        raise CandleArtifactError("code_commit must be 40 lowercase hexadecimal characters")
    request = load_request(contract_path, request_path, repo_root=repo_root)
    output_root = output_root.resolve()
    if output_root.exists():
        raise CandleArtifactError(f"output_root already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    partial_root = output_root.with_name(f".{output_root.name}.partial")
    if partial_root.exists():
        raise CandleArtifactError(f"partial output already exists: {partial_root}")
    partial_root.mkdir()

    try:
        artifacts: list[dict[str, object]] = []
        for source in request.sources:
            for symbol, pair in request.pair_mapping:
                url = source_url(
                    source,
                    symbol=symbol,
                    start_ms=request.start_ms,
                    end_ms=request.end_ms,
                )
                payload = fetch_json(url)
                if source.source == "bybit-linear":
                    records = normalize_bybit_payload(payload, symbol=symbol, pair=pair)
                else:
                    records = normalize_binance_payload(payload, symbol=symbol, pair=pair)
                validate_complete_coverage(
                    records,
                    source=source.source,
                    symbol=symbol,
                    start_ms=request.start_ms,
                    end_ms=request.end_ms,
                )
                relative = Path(source.source) / f"{symbol}-{TIMEFRAME}.ndjson"
                path = partial_root / relative
                _write_records(path, records)
                artifacts.append(
                    {
                        "source": source.source,
                        "market": source.market,
                        "symbol": symbol,
                        "pair": pair,
                        "timeframe": TIMEFRAME,
                        "logical_name": relative.as_posix(),
                        "request_url": url,
                        "sha256": sha256_file(path),
                        "size_bytes": path.stat().st_size,
                        "record_count": len(records),
                        "start_ms": request.start_ms,
                        "end_ms": request.end_ms,
                        "first_open_ms": _integer(
                            records[0]["open_time_ms"],
                            field="record.open_time_ms",
                        ),
                        "last_open_ms": _integer(
                            records[-1]["open_time_ms"],
                            field="record.open_time_ms",
                        ),
                    }
                )

        manifest = _manifest(
            request=request,
            contract_path=contract_path,
            request_path=request_path,
            repo_root=repo_root,
            code_commit=code_commit,
            artifacts=artifacts,
        )
        manifest_path = partial_root / "candle-artifact-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        hash_lines = [f"{artifact['sha256']}  {artifact['logical_name']}" for artifact in artifacts]
        hash_lines.append(f"{sha256_file(manifest_path)}  candle-artifact-manifest.json")
        (partial_root / "artifact-sha256.txt").write_text(
            "\n".join(hash_lines) + "\n",
            encoding="utf-8",
        )
        os.replace(partial_root, output_root)
        return manifest
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise
