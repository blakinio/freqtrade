from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, OpenerDirector, ProxyHandler, Request, build_opener

from ai_platform.research.liquidations.contracts import LiquidationEvent, event_from_json_dict
from ai_platform.wickhunter.candidate_paper_runtime_service import (
    CandidatePaperRuntimeService,
    CandidatePaperRuntimeServiceError,
)
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    DriftState,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    SourceHealth,
    StrategyHypothesis,
)
from ai_platform.wickhunter.parameters import DEFAULT_RESEARCH_BOUNDS
from ai_platform.wickhunter.risk import WickHunterRiskContext, WickHunterRiskLimits
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import ShadowRuntimePolicy, ShadowRuntimeTick
from ai_platform.wickhunter.strategy import SignalMemory
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot, UniverseInstrumentDecision

LIQUID20_SCHEMA_VERSION = "wickhunter-liquid20-public-snapshot-v1"
HEALTH_SCHEMA_VERSION = "wickhunter-paper-runtime-operator-health-v1"
DEFAULT_PUBLIC_MARKET_BASE_URL = "https://fapi.binance.com"
DEFAULT_POLL_SECONDS = 600
DEFAULT_MAX_SOURCE_AGE_MS = 300_000
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_HTTP_BYTES = 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,30}$")
FORBIDDEN_ENVIRONMENT_NAMES = (
    "OKX_API_KEY", "OKX_API_SECRET", "OKX_SECRET_KEY", "OKX_PASSPHRASE",
    "BYBIT_API_KEY", "BYBIT_API_SECRET", "BINANCE_API_KEY", "BINANCE_API_SECRET",
    "FT_EXCHANGE_KEY", "FT_EXCHANGE_SECRET", "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
)
ZERO_AUTHORITY = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


class CandidatePaperRuntimeOperatorError(RuntimeError):
    """Raised when the persistent PAPER operator must fail closed."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        del req, fp, code, msg, headers, newurl
        return None


@dataclass(frozen=True, slots=True)
class Liquid20Snapshot:
    snapshot_id: str
    observed_at_ms: int
    events: tuple[LiquidationEvent, ...]
    histories: tuple[LiquidationHistorySnapshot, ...]
    source_states: tuple[LiquidationSourceState, ...]
    universe: DynamicUniverseSnapshot

    def history_for(self, symbol: str) -> LiquidationHistorySnapshot:
        normalized = symbol.upper()
        matches = [item for item in self.histories if item.symbol.upper() == normalized]
        if len(matches) != 1:
            raise CandidatePaperRuntimeOperatorError(
                f"Liquid20 history must contain exactly one row for {normalized}"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class PublicMarketSnapshot:
    symbol: str
    observed_at_ms: int
    decision_price: Decimal
    completed_candle_close_ms: int
    quote_volume_24h_usd: Decimal
    spread_bps: Decimal
    volatility_ratio: Decimal
    wick_ratio: Decimal
    open_interest_usd: Decimal
    funding_rate: Decimal

    def market_context(self) -> MarketContextSnapshot:
        metrics = (
            AvailableMetric("funding_rate", self.funding_rate, self.observed_at_ms, "binance-usdm-public"),
            AvailableMetric("open_interest_usd", self.open_interest_usd, self.observed_at_ms, "binance-usdm-public"),
            AvailableMetric("quote_volume_24h_usd", self.quote_volume_24h_usd, self.observed_at_ms, "binance-usdm-public"),
            AvailableMetric("volatility_ratio", self.volatility_ratio, self.completed_candle_close_ms, "binance-usdm-public"),
            AvailableMetric("wick_ratio", self.wick_ratio, self.completed_candle_close_ms, "binance-usdm-public"),
        )
        return MarketContextSnapshot(
            symbol=self.symbol,
            decision_timestamp_ms=self.observed_at_ms,
            decision_price=self.decision_price,
            completed_candle_close_ms=self.completed_candle_close_ms,
            metrics=metrics,
        )


def _require_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidatePaperRuntimeOperatorError(f"{field} must contain an object")
    return value


def _require_list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise CandidatePaperRuntimeOperatorError(f"{field} must contain an array")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool):
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be an integer") from exc
    if parsed <= 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be > 0")
    return parsed


def _decimal(value: object, *, field: str, positive: bool = False, non_negative: bool = False) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be finite")
    if positive and parsed <= 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be > 0")
    if non_negative and parsed < 0:
        raise CandidatePaperRuntimeOperatorError(f"{field} must be >= 0")
    return parsed


def _assert_regular_absolute(path: Path, *, field: str, must_exist: bool = True) -> None:
    if not path.is_absolute():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be absolute")
    if path.is_symlink():
        raise CandidatePaperRuntimeOperatorError(f"{field} cannot be a symlink")
    if must_exist and not path.exists():
        raise CandidatePaperRuntimeOperatorError(f"{field} does not exist")


def assert_closed_authority_environment(environment: dict[str, str] | os._Environ[str] | None = None) -> None:
    values = os.environ if environment is None else environment
    present = sorted(name for name in FORBIDDEN_ENVIRONMENT_NAMES if values.get(name))
    if present:
        raise CandidatePaperRuntimeOperatorError(
            f"forbidden credential or proxy environment present: {','.join(present)}"
        )


def _read_bounded_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeOperatorError(f"{field} must be a regular file")
    size = path.stat().st_size
    if size <= 0 or size > MAX_INPUT_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} size is outside the accepted bound")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to read {field}") from exc
    return _require_object(payload, field=field)


def _source_health(value: object) -> SourceHealth:
    try:
        return SourceHealth(str(value))
    except ValueError as exc:
        raise CandidatePaperRuntimeOperatorError("invalid Liquid20 source health") from exc


def _history_from_payload(payload: dict[str, Any]) -> LiquidationHistorySnapshot:
    event_notionals = tuple(
        _decimal(item, field="history event notional", positive=True)
        for item in _require_list(payload.get("event_notionals_usd"), field="history event notionals")
    )
    burst_notionals = tuple(
        _decimal(item, field="history burst notional", positive=True)
        for item in _require_list(payload.get("burst_window_notionals_usd"), field="history burst notionals")
    )
    previous = payload.get("previous_burst_received_at_ms")
    previous_ms = None if previous is None else _integer(previous, field="previous burst")
    return LiquidationHistorySnapshot(
        symbol=str(payload.get("symbol", "")).upper(),
        event_notionals_usd=event_notionals,
        burst_window_notionals_usd=burst_notionals,
        previous_burst_received_at_ms=previous_ms,
        available_at_ms=_integer(payload.get("available_at_ms"), field="history availability"),
        history_id=str(payload.get("history_id", "")),
        history_sha256=str(payload.get("history_sha256", "")),
    )


def load_liquid20_snapshot(  # noqa: C901
    path: Path,
    *,
    now_ms: int,
    maximum_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS,
) -> Liquid20Snapshot:
    if maximum_age_ms < 1:
        raise CandidatePaperRuntimeOperatorError("maximum Liquid20 age must be positive")
    payload = _read_bounded_json(path, field="Liquid20 snapshot")
    claimed_hash = payload.get("snapshot_sha256")
    body = {key: value for key, value in payload.items() if key != "snapshot_sha256"}
    if payload.get("schema_version") != LIQUID20_SCHEMA_VERSION:
        raise CandidatePaperRuntimeOperatorError("Liquid20 schema mismatch")
    if not isinstance(claimed_hash, str) or not SHA256_RE.fullmatch(claimed_hash):
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot hash is invalid")
    if canonical_sha256(body) != claimed_hash:
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot self-hash mismatch")
    observed_at_ms = _integer(payload.get("observed_at_ms"), field="Liquid20 observed_at_ms")
    age_ms = now_ms - observed_at_ms
    if age_ms < 0:
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot is from the future")
    if age_ms > maximum_age_ms:
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot is stale")
    try:
        events = tuple(
            event_from_json_dict(_require_object(item, field="Liquid20 event"))
            for item in _require_list(payload.get("events"), field="Liquid20 events")
        )
    except ValueError as exc:
        raise CandidatePaperRuntimeOperatorError("Liquid20 event is invalid") from exc
    if not events:
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot contains no events")
    event_ids = [item.source_event_id for item in events]
    if event_ids != sorted(event_ids) or len(event_ids) != len(set(event_ids)):
        raise CandidatePaperRuntimeOperatorError("Liquid20 events must be unique and sorted by source_event_id")
    if any(item.received_at_ms > observed_at_ms for item in events):
        raise CandidatePaperRuntimeOperatorError("Liquid20 event was unavailable at snapshot observation time")
    histories = tuple(
        _history_from_payload(_require_object(item, field="Liquid20 history"))
        for item in _require_list(payload.get("histories"), field="Liquid20 histories")
    )
    history_symbols = [item.symbol for item in histories]
    if history_symbols != sorted(history_symbols) or len(history_symbols) != len(set(history_symbols)):
        raise CandidatePaperRuntimeOperatorError("Liquid20 histories must be unique and sorted by symbol")
    if any(item.available_at_ms > observed_at_ms for item in histories):
        raise CandidatePaperRuntimeOperatorError("Liquid20 history was unavailable at snapshot observation time")
    source_states: list[LiquidationSourceState] = []
    for item in _require_list(payload.get("source_states"), field="Liquid20 source states"):
        row = _require_object(item, field="Liquid20 source state")
        last_received = row.get("last_received_at_ms")
        source_states.append(
            LiquidationSourceState(
                source=str(row.get("source", "")),
                health=_source_health(row.get("health")),
                coverage_available=row.get("coverage_available") is True,
                last_received_at_ms=None if last_received is None else _integer(last_received, field="source last_received_at_ms"),
                observed_at_ms=_integer(row.get("observed_at_ms"), field="source observed_at_ms"),
            )
        )
    source_tuple = tuple(source_states)
    source_names = [item.source for item in source_tuple]
    if source_names != sorted(source_names) or len(source_names) != len(set(source_names)):
        raise CandidatePaperRuntimeOperatorError("Liquid20 source states must be unique and sorted")
    if not source_tuple:
        raise CandidatePaperRuntimeOperatorError("Liquid20 source states are empty")
    if any(item.observed_at_ms > observed_at_ms for item in source_tuple):
        raise CandidatePaperRuntimeOperatorError("Liquid20 source state was unavailable at snapshot observation time")
    universe_rows: list[UniverseInstrumentDecision] = []
    for item in _require_list(payload.get("universe"), field="Liquid20 universe"):
        row = _require_object(item, field="Liquid20 universe decision")
        symbol = str(row.get("symbol", "")).upper()
        if not SYMBOL_RE.fullmatch(symbol):
            raise CandidatePaperRuntimeOperatorError("Liquid20 universe symbol is invalid")
        reasons = tuple(sorted({str(value) for value in _require_list(row.get("reason_codes"), field="universe reason codes") if str(value).strip()}))
        universe_rows.append(
            UniverseInstrumentDecision(
                canonical_instrument_id=str(row.get("canonical_instrument_id", "")),
                canonical_symbol=symbol,
                included=row.get("included") is True,
                reason_codes=reasons,
            )
        )
    universe = DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version=str(payload.get("universe_policy_version", "")),
        selected_at_ms=observed_at_ms,
        decisions=tuple(sorted(universe_rows, key=lambda item: item.canonical_instrument_id)),
    )
    if not universe.selected_symbols:
        raise CandidatePaperRuntimeOperatorError("Liquid20 snapshot contains no selected symbols")
    event_symbols = {item.symbol.upper() for item in events}
    history_set = {item.symbol.upper() for item in histories}
    missing = sorted(symbol for symbol in universe.selected_symbols if symbol not in event_symbols or symbol not in history_set)
    if missing:
        raise CandidatePaperRuntimeOperatorError(f"Liquid20 universe lacks usable evidence for: {','.join(missing)}")
    return Liquid20Snapshot(claimed_hash, observed_at_ms, events, histories, source_tuple, universe)


def _public_url(base_url: str, path: str, parameters: dict[str, object]) -> str:
    parsed = urlparse(base_url)
    if (parsed.scheme != "https" or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or parsed.path not in {"", "/"} or not parsed.hostname):
        raise CandidatePaperRuntimeOperatorError("public market base URL is not allowed")
    if parsed.hostname.lower() not in {"fapi.binance.com", "testnet.binancefuture.com"}:
        raise CandidatePaperRuntimeOperatorError("public market host is not allowlisted")
    return f"{base_url.rstrip('/')}{path}?{urlencode(parameters)}"


def _read_public_json(opener: OpenerDirector, *, url: str, field: str) -> object:
    request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "wickhunter-paper-runtime-operator/1"})
    try:
        with opener.open(request, timeout=15) as response:  # noqa: S310
            if response.geturl() != url:
                raise CandidatePaperRuntimeOperatorError(f"{field} redirected unexpectedly")
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if "application/json" not in content_type:
                raise CandidatePaperRuntimeOperatorError(f"{field} returned a non-JSON content type")
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > MAX_HTTP_BYTES:
                raise CandidatePaperRuntimeOperatorError(f"{field} response is too large")
            body = response.read(MAX_HTTP_BYTES + 1)
    except CandidatePaperRuntimeOperatorError:
        raise
    except Exception as exc:
        raise CandidatePaperRuntimeOperatorError(f"unable to fetch {field}") from exc
    if len(body) > MAX_HTTP_BYTES:
        raise CandidatePaperRuntimeOperatorError(f"{field} response is too large")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeOperatorError(f"{field} returned malformed JSON") from exc


def fetch_public_market_snapshot(  # noqa: C901
    *, symbol: str, observed_at_ms: int, base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL, opener: OpenerDirector | None = None
) -> PublicMarketSnapshot:
    normalized = symbol.upper()
    if not SYMBOL_RE.fullmatch(normalized):
        raise CandidatePaperRuntimeOperatorError("public market symbol is invalid")
    assert_closed_authority_environment()
    client = opener or build_opener(ProxyHandler({}), _NoRedirectHandler())
    premium = _require_object(_read_public_json(client, url=_public_url(base_url, "/fapi/v1/premiumIndex", {"symbol": normalized}), field="public premium index"), field="public premium index")
    ticker = _require_object(_read_public_json(client, url=_public_url(base_url, "/fapi/v1/ticker/24hr", {"symbol": normalized}), field="public 24h ticker"), field="public 24h ticker")
    open_interest = _require_object(_read_public_json(client, url=_public_url(base_url, "/fapi/v1/openInterest", {"symbol": normalized}), field="public open interest"), field="public open interest")
    klines = _require_list(_read_public_json(client, url=_public_url(base_url, "/fapi/v1/klines", {"symbol": normalized, "interval": "1m", "limit": 2}), field="public klines"), field="public klines")
    if len(klines) != 2:
        raise CandidatePaperRuntimeOperatorError("public klines must contain exactly two rows")
    candle = _require_list(klines[0], field="completed public kline")
    if len(candle) < 7:
        raise CandidatePaperRuntimeOperatorError("completed public kline is malformed")
    candle_open = _decimal(candle[1], field="candle open", positive=True)
    candle_high = _decimal(candle[2], field="candle high", positive=True)
    candle_low = _decimal(candle[3], field="candle low", positive=True)
    candle_close = _decimal(candle[4], field="candle close", positive=True)
    completed_close_ms = _integer(candle[6], field="completed candle close")
    if completed_close_ms > observed_at_ms:
        raise CandidatePaperRuntimeOperatorError("public completed candle was unavailable at decision time")
    if observed_at_ms - completed_close_ms > DEFAULT_MAX_SOURCE_AGE_MS:
        raise CandidatePaperRuntimeOperatorError("public completed candle is stale")
    if not candle_low <= min(candle_open, candle_close) <= max(candle_open, candle_close) <= candle_high:
        raise CandidatePaperRuntimeOperatorError("public completed candle is inconsistent")
    candle_range = candle_high - candle_low
    volatility_ratio = candle_range / candle_close
    wick_total = (candle_high - max(candle_open, candle_close)) + (min(candle_open, candle_close) - candle_low)
    wick_ratio = Decimal("0") if candle_range == 0 else wick_total / candle_range
    decision_price = _decimal(premium.get("markPrice"), field="public mark price", positive=True)
    quote_volume = _decimal(ticker.get("quoteVolume"), field="public quote volume", non_negative=True)
    bid = _decimal(ticker.get("bidPrice"), field="public bid", positive=True)
    ask = _decimal(ticker.get("askPrice"), field="public ask", positive=True)
    if ask < bid:
        raise CandidatePaperRuntimeOperatorError("public bid/ask spread is inverted")
    spread_bps = ((ask - bid) / decision_price) * Decimal("10000")
    open_interest_quantity = _decimal(open_interest.get("openInterest"), field="public open interest", non_negative=True)
    funding_rate = _decimal(premium.get("lastFundingRate"), field="public funding rate")
    return PublicMarketSnapshot(
        normalized, observed_at_ms, decision_price, completed_close_ms, quote_volume,
        spread_bps, volatility_ratio, wick_ratio, open_interest_quantity * decision_price,
        funding_rate,
    )


def _runtime_policy() -> ShadowRuntimePolicy:
    return ShadowRuntimePolicy(
        policy_version="wickhunter-paper-runtime-v1",
        simulated_initial_equity_quote=Decimal("10000"),
        maximum_universe_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_source_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        minimum_healthy_sources=1,
        maximum_open_positions=4,
        maximum_drawdown_ratio=Decimal("0.20"),
        decision_history_limit=1000,
    )


def _risk_limits() -> WickHunterRiskLimits:
    return WickHunterRiskLimits(
        risk_policy_version="wickhunter-paper-risk-v1",
        maximum_base_risk_ratio=Decimal("0.02"),
        maximum_effective_exposure_ratio=Decimal("0.20"),
        maximum_leverage=Decimal("5"),
        maximum_dca_count=4,
        maximum_total_dca_risk_ratio=Decimal("0.04"),
        maximum_concurrent_positions=4,
        maximum_symbol_exposure_ratio=Decimal("0.20"),
        maximum_correlated_exposure_ratio=Decimal("0.40"),
        maximum_directional_exposure_ratio=Decimal("0.60"),
        maximum_daily_loss_ratio=Decimal("0.10"),
        maximum_drawdown_ratio=Decimal("0.20"),
        maximum_consecutive_losses=5,
        maximum_liquidation_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_candle_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_open_interest_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_funding_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_spread_bps=Decimal("50"),
        minimum_quote_volume_usd=Decimal("1000000"),
        minimum_confidence=Decimal("0"),
    )


def _atomic_health(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise CandidatePaperRuntimeOperatorError("health path cannot be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


@dataclass(slots=True)
class CandidatePaperRuntimeOperator:
    service: CandidatePaperRuntimeService
    liquid20_snapshot_path: Path
    health_path: Path
    operator_commit: str
    public_market_base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL
    maximum_source_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS
    opener: OpenerDirector | None = None
    last_success_at_ms: int | None = None

    def __post_init__(self) -> None:
        if not GIT_SHA_RE.fullmatch(self.operator_commit):
            raise CandidatePaperRuntimeOperatorError("operator commit must be an exact lowercase Git SHA")
        _assert_regular_absolute(self.liquid20_snapshot_path, field="Liquid20 snapshot")
        if not self.health_path.is_absolute():
            raise CandidatePaperRuntimeOperatorError("health path must be absolute")
        if self.health_path.parent.is_symlink():
            raise CandidatePaperRuntimeOperatorError("health root cannot be a symlink")
        if self.maximum_source_age_ms < 1:
            raise CandidatePaperRuntimeOperatorError("maximum source age must be positive")
        assert_closed_authority_environment()

    def _compose_tick(  # noqa: C901
        self, *, liquid20: Liquid20Snapshot, markets: tuple[PublicMarketSnapshot, ...], observed_at_ms: int
    ) -> ShadowRuntimeTick:
        market_by_symbol = {item.symbol: item for item in markets}
        if set(market_by_symbol) != set(liquid20.universe.selected_symbols):
            raise CandidatePaperRuntimeOperatorError("public market symbols do not match the selected Liquid20 universe")
        latest_state = self.service.runtime.state
        requests: list[ShadowDecisionRequest] = []
        for symbol in liquid20.universe.selected_symbols:
            events = tuple(item for item in liquid20.events if item.symbol.upper() == symbol)
            if not events:
                continue
            market = market_by_symbol[symbol]
            requests.append(
                ShadowDecisionRequest(
                    bot_instance=self.service.binding.request.bot_instance,
                    mode=self.service.binding.request.mode,
                    events=events,
                    market=market.market_context(),
                    history=liquid20.history_for(symbol),
                    source_states=liquid20.source_states,
                    universe=liquid20.universe,
                    parameters=self.service.binding.parameters,
                    parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
                    hypothesis=StrategyHypothesis.REVERSAL,
                    scorer=self.service.binding.scorer,
                    signal_memory=SignalMemory(),
                    risk_limits=_risk_limits(),
                    risk_context=WickHunterRiskContext(
                        evaluated_at_ms=observed_at_ms,
                        global_kill_switch_active=False,
                        circuit_breaker_active=False,
                        model_drift=DriftState.HEALTHY,
                        data_drift=DriftState.HEALTHY,
                        projected_concurrent_positions=len(latest_state.positions) + 1,
                        projected_symbol_exposure_ratio=Decimal("0"),
                        projected_correlated_exposure_ratio=Decimal("0"),
                        projected_directional_exposure_ratio=Decimal("0"),
                        daily_loss_ratio=Decimal("0"),
                        drawdown_ratio=latest_state.drawdown_ratio,
                        consecutive_losses=0,
                        consecutive_loss_cooldown_until_ms=None,
                        symbol_cooldown_until_ms=None,
                        setup_still_valid=True,
                        dca_adverse_condition_met=True,
                        dca_timing_condition_met=True,
                        spread_bps=market.spread_bps,
                        quote_volume_usd=market.quote_volume_24h_usd,
                        candidate_paper_validation_authorized=False,
                    ),
                    dataset_hash=self.service.binding.request.dataset_hash,
                    code_sha=self.service.binding.request.code_sha,
                )
            )
        return ShadowRuntimeTick(
            observed_at_ms=observed_at_ms,
            universe=liquid20.universe,
            decision_requests=tuple(requests),
            mark_prices=tuple(sorted((item.symbol, item.decision_price) for item in markets)),
            source_states=liquid20.source_states,
            model_drift=DriftState.HEALTHY,
            data_drift=DriftState.HEALTHY,
            validation_state="collecting",
            retraining_state="disabled",
        )

    def _health_payload(self, *, status: str, checked_at_ms: int, liquid20_snapshot_id: str | None, error_code: str | None, error_message: str | None) -> dict[str, object]:
        state = self.service.runtime.state
        request = self.service.binding.request
        payload: dict[str, object] = {
            "schema_version": HEALTH_SCHEMA_VERSION,
            "status": status,
            "checked_at_ms": checked_at_ms,
            "last_success_at_ms": self.last_success_at_ms,
            "operator_commit": self.operator_commit,
            "binding_id": self.service.binding.binding_id,
            "run_id": request.run_id,
            "window_start_ms": request.window_start_ms,
            "window_end_ms": request.window_end_ms,
            "generation": state.generation,
            "last_observed_at_ms": state.last_observed_at_ms,
            "liquid20_snapshot_id": liquid20_snapshot_id,
            "error_code": error_code,
            "error_message": None if error_message is None else error_message[:240],
            **ZERO_AUTHORITY,
        }
        payload["health_sha256"] = canonical_sha256(payload)
        return payload

    def run_once(self, *, observed_at_ms: int | None = None) -> int:
        now_ms = time.time_ns() // 1_000_000 if observed_at_ms is None else observed_at_ms
        request = self.service.binding.request
        if not request.window_start_ms <= now_ms < request.window_end_ms:
            raise CandidatePaperRuntimeOperatorError("current time is outside the immutable activation window")
        liquid20 = load_liquid20_snapshot(self.liquid20_snapshot_path, now_ms=now_ms, maximum_age_ms=self.maximum_source_age_ms)
        markets = tuple(
            fetch_public_market_snapshot(symbol=symbol, observed_at_ms=now_ms, base_url=self.public_market_base_url, opener=self.opener)
            for symbol in liquid20.universe.selected_symbols
        )
        tick = self._compose_tick(liquid20=liquid20, markets=markets, observed_at_ms=now_ms)
        result = self.service.step(tick)
        self.last_success_at_ms = now_ms
        _atomic_health(self.health_path, self._health_payload(status="healthy", checked_at_ms=now_ms, liquid20_snapshot_id=liquid20.snapshot_id, error_code=None, error_message=None))
        return result.state.generation

    def publish_failure(self, error: BaseException, *, checked_at_ms: int) -> None:
        _atomic_health(self.health_path, self._health_payload(status="fail_closed", checked_at_ms=checked_at_ms, liquid20_snapshot_id=None, error_code=type(error).__name__, error_message=str(error)))

    def run_forever(self, *, poll_seconds: int) -> None:
        if not 60 <= poll_seconds <= 900:
            raise CandidatePaperRuntimeOperatorError("poll cadence must be within 60..900 seconds")
        while True:
            checked_at_ms = time.time_ns() // 1_000_000
            try:
                self.run_once(observed_at_ms=checked_at_ms)
            except (CandidatePaperRuntimeOperatorError, CandidatePaperRuntimeServiceError, OSError, ValueError) as exc:
                self.publish_failure(exc, checked_at_ms=checked_at_ms)
            time.sleep(poll_seconds)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent fail-closed WickHunter candidate PAPER operator")
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--activation-root", type=Path, required=True)
    parser.add_argument("--journal-root", type=Path, required=True)
    parser.add_argument("--liquid20-snapshot", type=Path, required=True)
    parser.add_argument("--health-root", type=Path, required=True)
    parser.add_argument("--operator-commit", required=True)
    parser.add_argument("--public-market-base-url", default=DEFAULT_PUBLIC_MARKET_BASE_URL)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--maximum-source-age-ms", type=int, default=DEFAULT_MAX_SOURCE_AGE_MS)
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    assert_closed_authority_environment()
    for path, field in (
        (args.candidate_root, "candidate root"),
        (args.activation_root, "activation root"),
        (args.journal_root, "journal root"),
        (args.liquid20_snapshot, "Liquid20 snapshot"),
        (args.health_root, "health root"),
    ):
        _assert_regular_absolute(path, field=field, must_exist=field not in {"journal root", "health root"})
    args.journal_root.mkdir(parents=True, exist_ok=True)
    args.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_candidate_paper_runtime_binding(candidate_root=args.candidate_root, activation_root=args.activation_root)
    service = CandidatePaperRuntimeService(binding=binding, runtime_policy=_runtime_policy(), journal_root=args.journal_root)
    operator = CandidatePaperRuntimeOperator(
        service=service,
        liquid20_snapshot_path=args.liquid20_snapshot,
        health_path=args.health_root / "health.json",
        operator_commit=args.operator_commit,
        public_market_base_url=args.public_market_base_url,
        maximum_source_age_ms=args.maximum_source_age_ms,
    )
    if args.once:
        operator.run_once()
        return 0
    operator.run_forever(poll_seconds=args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
