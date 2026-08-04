# ruff: noqa: I001, S101
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import pytest

import ai_platform.wickhunter.candidate_paper_runtime_operator as operator_module
from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    ZERO_AUTHORITY,
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    PublicMarketSnapshot,
    _risk_limits,
    _runtime_risk_context,
    assert_closed_authority_environment,
    fetch_public_market_snapshot,
    load_liquid20_snapshot,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    SourceHealth,
    TradeDirection,
)
from ai_platform.wickhunter.parameters import INITIAL_COMPATIBILITY_PRIOR


NOW_MS = 1_800_000_000_000
CODE_SHA = "a" * 40
RUN_ID = "b" * 64
BINDING_ID = "c" * 64
EXPECTED_MARKET_METRICS = {
    "atr_ratio",
    "funding_rate",
    "market_wide_liquidation_intensity",
    "open_interest_usd",
    "quote_volume_24h_usd",
    "spread_bps",
    "trend_return_ratio",
    "volatility_ratio",
    "vwap",
    "vwma",
    "wick_ratio",
}


@pytest.fixture(autouse=True)
def _clear_forbidden_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)


def _event(
    event_id: str,
    *,
    received_at_ms: int,
    source: str = "binance-usdm",
    symbol: str = "BTCUSDT",
    notional_usd: str = "1000",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source": source,
        "source_event_id": event_id,
        "symbol": symbol,
        "liquidated_position_side": "long",
        "occurred_at_ms": received_at_ms - 100,
        "received_at_ms": received_at_ms,
        "price": "100",
        "quantity": "10",
        "notional_usd": notional_usd,
        "raw_side": "SELL",
    }


def _write_live_root(
    root: Path,
    *,
    heartbeat_ms: int = NOW_MS,
    events: list[dict[str, object]] | None = None,
    execution_enabled: bool = False,
) -> Path:
    source_events = events or [
        _event("event-history", received_at_ms=NOW_MS - 120_000),
        _event("event-current", received_at_ms=NOW_MS - 1_000),
    ]
    run_id = "run-20260804"
    run_root = root / "runs" / run_id
    run_root.mkdir(parents=True)
    event_path = run_root / "binance-usdm.ndjson"
    event_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in source_events),
        encoding="utf-8",
    )
    last_received = max(
        int(cast(int | str, item["received_at_ms"])) for item in source_events
    )
    state = {
        "run_id": run_id,
        "collector_heartbeat_at_ms": heartbeat_ms,
        "trading_credentials_present": False,
        "execution_enabled": execution_enabled,
        "trading_authorized": False,
        "orders_submitted": 0,
        "sources": {
            "binance-usdm": {
                "configured": True,
                "connected": True,
                "events_written": len(source_events),
                "last_event_received_at_ms": last_received,
                "last_heartbeat_at_ms": heartbeat_ms,
            }
        },
    }
    pointer = {
        "contract": "liquid20-live-state-v1",
        "active_run_id": run_id,
        "collector_heartbeat_at_ms": heartbeat_ms,
        "state": state,
    }
    (root / "live-state-v1.json").write_text(
        json.dumps(pointer, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def _market(*, observed_at_ms: int = NOW_MS) -> PublicMarketSnapshot:
    return PublicMarketSnapshot(
        symbol="BTCUSDT",
        observed_at_ms=observed_at_ms,
        decision_price=Decimal("100"),
        completed_candle_close_ms=observed_at_ms - 1_000,
        quote_volume_24h_usd=Decimal("5000000"),
        spread_bps=Decimal("1.25"),
        trend_return_ratio=Decimal("0.02"),
        volatility_ratio=Decimal("0.003"),
        vwap=Decimal("99.5"),
        vwma=Decimal("99.7"),
        wick_ratio=Decimal("0.4"),
        atr_ratio=Decimal("0.01"),
        open_interest_usd=Decimal("2500000"),
        funding_rate=Decimal("0.0001"),
    )


def test_load_liquid20_live_root_is_root_only_and_decision_time_safe(
    tmp_path: Path,
) -> None:
    snapshot = load_liquid20_snapshot(
        _write_live_root(tmp_path / "liquid20"),
        now_ms=NOW_MS,
    )

    assert snapshot.universe.selected_symbols == ("BTCUSDT",)
    assert snapshot.source_states[0].health is SourceHealth.HEALTHY
    assert snapshot.source_states[0].coverage_available is True
    assert all(event.received_at_ms <= snapshot.observed_at_ms for event in snapshot.events)
    assert snapshot.history_for("btcusdt").available_at_ms <= snapshot.observed_at_ms
    assert len(snapshot.snapshot_id) == 64


def test_live_root_caps_per_symbol_history(tmp_path: Path) -> None:
    events = [
        _event(
            f"event-{index:04d}",
            received_at_ms=NOW_MS - 250_000 + index * 400,
            notional_usd=str(1000 + index),
        )
        for index in range(501)
    ]
    snapshot = load_liquid20_snapshot(
        _write_live_root(tmp_path / "liquid20", events=events),
        now_ms=NOW_MS,
    )

    assert len(snapshot.history_for("BTCUSDT").event_notionals_usd) == 500


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("stale", "stale"),
        ("authority", "forbidden authority"),
        ("source", "source does not match"),
    ),
)
def test_live_root_tamper_and_staleness_fail_closed(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    root = tmp_path / "liquid20"
    if mutation == "stale":
        _write_live_root(root, heartbeat_ms=NOW_MS - 400_000)
    elif mutation == "authority":
        _write_live_root(root, execution_enabled=True)
    else:
        _write_live_root(
            root,
            events=[
                _event(
                    "wrong-source",
                    received_at_ms=NOW_MS - 1_000,
                    source="bybit",
                )
            ],
        )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match=message):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_single_file_snapshot_fallback_is_removed(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="regular directory"):
        load_liquid20_snapshot(path, now_ms=NOW_MS)


class _Response:
    def __init__(self, url: str, payload: object) -> None:
        self._url = url
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(self._body)),
        }

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url

    def read(self, limit: int) -> bytes:
        return self._body[:limit]


class _Opener:
    def __init__(self, *, redirect: bool = False, gap: bool = False) -> None:
        self.redirect = redirect
        self.gap = gap
        self.requests: list[Any] = []

    def _klines(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for index in range(1441):
            close_ms = NOW_MS - (1440 - index) * 60_000 - 1_000
            if self.gap and index == 700:
                close_ms += 1
            close = Decimal("100") + Decimal(index) / Decimal("10000")
            rows.append(
                [
                    close_ms - 59_999,
                    str(close - Decimal("0.1")),
                    str(close + Decimal("0.2")),
                    str(close - Decimal("0.2")),
                    str(close),
                    "10",
                    close_ms,
                    str(close * Decimal("10")),
                ]
            )
        return rows

    def open(self, request: Any, timeout: int) -> _Response:
        assert timeout == 15
        self.requests.append(request)
        parsed = urlparse(request.full_url)
        query = parse_qs(parsed.query)
        assert query["symbol"] == ["BTCUSDT"]
        if parsed.path.endswith("premiumIndex"):
            payload: object = {
                "symbol": "BTCUSDT",
                "markPrice": "100",
                "lastFundingRate": "0.0001",
            }
        elif parsed.path.endswith("ticker/bookTicker"):
            payload = {
                "symbol": "BTCUSDT",
                "bidPrice": "99.99",
                "askPrice": "100.01",
            }
        elif parsed.path.endswith("openInterest"):
            payload = {"symbol": "BTCUSDT", "openInterest": "200000"}
        else:
            assert query["interval"] == ["1m"]
            assert query["limit"] == ["1441"]
            payload = self._klines()
        response_url = "https://redirect.invalid/" if self.redirect else request.full_url
        return _Response(response_url, payload)


def test_public_market_contract_uses_complete_contiguous_public_inputs() -> None:
    opener = _Opener()
    snapshot = fetch_public_market_snapshot(
        symbol="btcusdt",
        observed_at_ms=NOW_MS,
        opener=cast(Any, opener),
    )
    context = snapshot.market_context(market_wide_liquidation_intensity=Decimal("1.5"))
    metrics = {metric.name: metric for metric in context.metrics}

    assert snapshot.symbol == "BTCUSDT"
    assert set(metrics) == EXPECTED_MARKET_METRICS
    assert tuple(metrics) == tuple(sorted(EXPECTED_MARKET_METRICS))
    assert metrics["spread_bps"].source == "binance-usdm-public-book-ticker"
    assert metrics["atr_ratio"].source == "completed_candle:binance-usdm-public-1m"
    assert len(opener.requests) == 4
    assert all(request.get_method() == "GET" for request in opener.requests)
    assert all("Authorization" not in request.headers for request in opener.requests)


def test_public_market_gap_redirect_host_and_proxy_fail_closed() -> None:
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="history contains a gap"):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _Opener(gap=True)),
        )
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="redirected"):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _Opener(redirect=True)),
        )
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="allowlisted"):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            base_url="https://testnet.binancefuture.com",
            opener=cast(Any, _Opener()),
        )
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="forbidden"):
        assert_closed_authority_environment({"HTTPS_PROXY": "https://proxy.invalid"})


def test_runtime_risk_context_uses_open_and_closed_simulated_state() -> None:
    state = SimpleNamespace(
        positions=(
            SimpleNamespace(
                unrealized_pnl_quote=Decimal("10"),
                mark_price=Decimal("100"),
                quantity=Decimal("1"),
                symbol="BTCUSDT",
                side=TradeDirection.LONG,
            ),
        ),
        closed_positions=(
            SimpleNamespace(
                closed_at_ms=NOW_MS - 2_000,
                closed_position_id="a" * 64,
                symbol="BTCUSDT",
                realized_pnl_quote=Decimal("-50"),
            ),
            SimpleNamespace(
                closed_at_ms=NOW_MS - 1_000,
                closed_position_id="b" * 64,
                symbol="BTCUSDT",
                realized_pnl_quote=Decimal("-20"),
            ),
        ),
        cumulative_realized_pnl_quote=Decimal("-100"),
        drawdown_ratio=Decimal("0.05"),
    )
    policy = SimpleNamespace(simulated_initial_equity_quote=Decimal("10000"))

    context = _runtime_risk_context(
        state=state,
        policy=cast(Any, policy),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS,
        market=_market(),
        model_drift=DriftState.DRIFTED,
        data_drift=DriftState.UNKNOWN,
        circuit_breaker_active=True,
    )

    assert context.projected_concurrent_positions == 2
    assert context.projected_symbol_exposure_ratio > Decimal("0.15")
    assert context.projected_correlated_exposure_ratio > Decimal("0.15")
    assert context.projected_directional_exposure_ratio > Decimal("0.15")
    assert context.daily_loss_ratio == Decimal("0.007")
    assert context.drawdown_ratio == Decimal("0.05")
    assert context.consecutive_losses == 2
    assert context.symbol_cooldown_until_ms is not None
    assert context.model_drift is DriftState.DRIFTED
    assert context.data_drift is DriftState.UNKNOWN
    assert context.circuit_breaker_active is True
    assert context.candidate_paper_validation_authorized is True
    assert _risk_limits().maximum_leverage >= INITIAL_COMPATIBILITY_PRIOR.leverage


def _service(*, mode: BotMode = BotMode.PAPER) -> Any:
    request = SimpleNamespace(
        bot_instance="wickhunter-paper-v1",
        mode=mode,
        run_id=RUN_ID,
        window_start_ms=NOW_MS - 10_000,
        window_end_ms=NOW_MS + 86_400_000,
        dataset_hash="d" * 64,
        code_sha=CODE_SHA,
    )
    binding = SimpleNamespace(
        binding_id=BINDING_ID,
        request=request,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        scorer=cast(Any, object()),
    )
    state = SimpleNamespace(
        generation=0,
        last_observed_at_ms=None,
        positions=(),
        closed_positions=(),
        cumulative_realized_pnl_quote=Decimal("0"),
        drawdown_ratio=Decimal("0"),
    )
    runtime = SimpleNamespace(
        state=state,
        policy=SimpleNamespace(simulated_initial_equity_quote=Decimal("10000")),
    )
    return SimpleNamespace(binding=binding, runtime=runtime)


def _operator(tmp_path: Path, *, mode: BotMode = BotMode.PAPER) -> CandidatePaperRuntimeOperator:
    root = _write_live_root(tmp_path / "liquid20")
    return CandidatePaperRuntimeOperator(
        service=cast(Any, _service(mode=mode)),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "health" / "health.json").resolve(),
        operator_commit=CODE_SHA,
        model_drift=DriftState.DRIFTED,
        data_drift=DriftState.UNKNOWN,
        circuit_breaker_active=True,
    )


def test_operator_refuses_non_paper_binding(tmp_path: Path) -> None:
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="mode must be PAPER"):
        _operator(tmp_path, mode=BotMode.SHADOW)


def test_health_is_bounded_self_hashed_and_truthful(tmp_path: Path) -> None:
    runtime_operator = _operator(tmp_path)
    payload = runtime_operator._health_payload(
        status="fail_closed",
        checked_at_ms=NOW_MS,
        liquid20_snapshot_id=None,
        error_code="SyntheticError",
        error_message="x" * 1000,
    )
    claimed = payload.pop("health_sha256")

    assert payload["model_drift"] == "drifted"
    assert payload["data_drift"] == "unknown"
    assert payload["circuit_breaker_active"] is True
    assert len(cast(str, payload["error_message"])) == 240
    assert all(payload[key] == value for key, value in ZERO_AUTHORITY.items())
    assert claimed == canonical_sha256(payload)


def test_window_and_poll_cadence_fail_closed_before_external_io(tmp_path: Path) -> None:
    runtime_operator = _operator(tmp_path)
    window_end = runtime_operator.service.binding.request.window_end_ms
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="outside"):
        runtime_operator.run_once(observed_at_ms=window_end)
    with pytest.raises(CandidatePaperRuntimeOperatorError, match=r"60\.\.900"):
        runtime_operator.run_forever(poll_seconds=901)
    assert 86_400 // operator_module.DEFAULT_POLL_SECONDS >= 96


def test_cli_and_source_expose_only_root_contract_and_bounded_controls() -> None:
    parser = operator_module._parser()
    args = parser.parse_args(
        [
            "--candidate-root",
            "/candidate",
            "--activation-root",
            "/activation",
            "--journal-root",
            "/journal",
            "--liquid20-root",
            "/liquid20",
            "--health-root",
            "/health",
            "--operator-commit",
            CODE_SHA,
            "--model-drift",
            "drifted",
            "--data-drift",
            "unknown",
            "--circuit-breaker-active",
        ]
    )
    source = Path(operator_module.__file__).read_text(encoding="utf-8")

    assert args.liquid20_root == Path("/liquid20")
    assert args.model_drift == "drifted"
    assert args.data_drift == "unknown"
    assert args.circuit_breaker_active is True
    assert "--liquid20-snapshot" not in source
    assert "if path.is_dir():" not in source
    assert source.count("def _market_wide_liquidation_intensity(") == 1


def test_synology_compose_keeps_zero_authority_container_boundary() -> None:
    compose = Path("deploy/synology/wickhunter-paper-runtime/compose.yaml").read_text(
        encoding="utf-8"
    )
    dockerfile = Path("deploy/synology/wickhunter-paper-runtime/Dockerfile").read_text(
        encoding="utf-8"
    )

    assert "--liquid20-root" in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "docker.sock" not in compose
    assert "ports:" not in compose
    assert ("/app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py") in compose
    assert "candidate_paper_runtime_operator" in dockerfile
