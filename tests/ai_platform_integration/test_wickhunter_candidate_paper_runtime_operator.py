from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib.parse import urlparse

import pytest

import ai_platform.wickhunter.candidate_paper_runtime_operator as operator_module
from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    PublicMarketSnapshot,
    assert_closed_authority_environment,
    fetch_public_market_snapshot,
    load_liquid20_snapshot,
)
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.parameters import INITIAL_COMPATIBILITY_PRIOR
from ai_platform.wickhunter.shadow_runtime import ShadowRuntimeTick


NOW_MS = 1_800_000_000_000
CODE_SHA = "a" * 40
RUN_ID = "b" * 64
BINDING_ID = "c" * 64


def _liquid20_payload(*, observed_at_ms: int = NOW_MS) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "wickhunter-liquid20-public-snapshot-v1",
        "observed_at_ms": observed_at_ms,
        "universe_policy_version": "liquid20-public-v1",
        "events": [
            {
                "schema_version": 1,
                "source": "binance-usdm",
                "source_event_id": "event-0001",
                "symbol": "BTCUSDT",
                "liquidated_position_side": "long",
                "occurred_at_ms": observed_at_ms - 2_000,
                "received_at_ms": observed_at_ms - 1_000,
                "price": "100",
                "quantity": "10",
                "notional_usd": "1000",
                "raw_side": "SELL",
            }
        ],
        "histories": [
            {
                "symbol": "BTCUSDT",
                "event_notionals_usd": ["100", "200", "300"],
                "burst_window_notionals_usd": ["150", "250", "350"],
                "previous_burst_received_at_ms": observed_at_ms - 10_000,
                "available_at_ms": observed_at_ms - 500,
                "history_id": "history-btcusdt-v1",
                "history_sha256": "d" * 64,
            }
        ],
        "source_states": [
            {
                "source": "binance-usdm",
                "health": "healthy",
                "coverage_available": True,
                "last_received_at_ms": observed_at_ms - 1_000,
                "observed_at_ms": observed_at_ms,
            }
        ],
        "universe": [
            {
                "canonical_instrument_id": "perpetual:BTCUSDT",
                "symbol": "BTCUSDT",
                "included": True,
                "reason_codes": ["eligible"],
            }
        ],
    }
    return {**body, "snapshot_sha256": canonical_sha256(body)}


def _rehash_payload(payload: dict[str, object]) -> None:
    body = {key: value for key, value in payload.items() if key != "snapshot_sha256"}
    payload["snapshot_sha256"] = canonical_sha256(body)


def _stale_payload(payload: dict[str, object]) -> None:
    payload.clear()
    payload.update(_liquid20_payload(observed_at_ms=NOW_MS - 400_000))


def _future_event_payload(payload: dict[str, object]) -> None:
    events = cast(list[dict[str, object]], payload["events"])
    events[0]["received_at_ms"] = NOW_MS + 1
    _rehash_payload(payload)


def _write_snapshot(path: Path, payload: dict[str, object] | None = None) -> Path:
    path.write_text(canonical_json(payload or _liquid20_payload()) + "\n", encoding="utf-8")
    return path


def _market(*, observed_at_ms: int = NOW_MS) -> PublicMarketSnapshot:
    return PublicMarketSnapshot(
        symbol="BTCUSDT",
        observed_at_ms=observed_at_ms,
        decision_price=Decimal("100"),
        completed_candle_close_ms=observed_at_ms - 1_000,
        quote_volume_24h_usd=Decimal("100000000"),
        spread_bps=Decimal("1"),
        volatility_ratio=Decimal("0.02"),
        wick_ratio=Decimal("0.50"),
        open_interest_usd=Decimal("20000000"),
        funding_rate=Decimal("0.0001"),
    )


def _service() -> Any:
    request = SimpleNamespace(
        bot_instance="wickhunter-paper-v1",
        mode=BotMode.PAPER,
        run_id=RUN_ID,
        window_start_ms=NOW_MS - 10_000,
        window_end_ms=NOW_MS + 86_400_000,
        dataset_hash="e" * 64,
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
        drawdown_ratio=Decimal("0"),
    )
    runtime = SimpleNamespace(state=state)

    class Service:
        def __init__(self) -> None:
            self.binding = binding
            self.runtime = runtime
            self.ticks: list[ShadowRuntimeTick] = []

        def step(self, tick: ShadowRuntimeTick) -> Any:
            self.ticks.append(tick)
            generation = self.runtime.state.generation + 1
            self.runtime.state = SimpleNamespace(
                generation=generation,
                last_observed_at_ms=tick.observed_at_ms,
                positions=(),
                drawdown_ratio=Decimal("0"),
            )
            return SimpleNamespace(state=self.runtime.state)

    return Service()


def _operator(tmp_path: Path) -> CandidatePaperRuntimeOperator:
    snapshot_path = _write_snapshot(tmp_path / "liquid20.json")
    return CandidatePaperRuntimeOperator(
        service=cast(Any, _service()),
        liquid20_snapshot_path=snapshot_path.resolve(),
        health_path=(tmp_path / "health" / "health.json").resolve(),
        operator_commit=CODE_SHA,
    )


def test_load_liquid20_snapshot_verifies_hash_and_decision_time(tmp_path: Path) -> None:
    snapshot = load_liquid20_snapshot(
        _write_snapshot(tmp_path / "liquid20.json"),
        now_ms=NOW_MS + 1_000,
    )

    assert snapshot.snapshot_id == canonical_sha256(
        {key: value for key, value in _liquid20_payload().items() if key != "snapshot_sha256"}
    )
    assert snapshot.universe.selected_symbols == ("BTCUSDT",)
    assert snapshot.events[0].received_at_ms <= snapshot.observed_at_ms
    assert snapshot.history_for("btcusdt").available_at_ms <= snapshot.observed_at_ms


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (_stale_payload, "stale"),
        (_future_event_payload, "unavailable"),
        (lambda payload: payload.update({"snapshot_sha256": "0" * 64}), "self-hash"),
    ),
)
def test_liquid20_stale_future_or_tampered_input_fails_closed(
    tmp_path: Path,
    mutation: Any,
    message: str,
) -> None:
    payload = _liquid20_payload()
    mutation(payload)
    path = _write_snapshot(tmp_path / "liquid20.json", payload)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match=message):
        load_liquid20_snapshot(path, now_ms=NOW_MS + 1_000)


def test_credential_and_proxy_environment_is_rejected() -> None:
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="forbidden"):
        assert_closed_authority_environment({"BINANCE_API_KEY": "sentinel"})
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="forbidden"):
        assert_closed_authority_environment({"HTTPS_PROXY": "https://proxy.invalid"})


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
    def __init__(self, *, redirect: bool = False) -> None:
        self.redirect = redirect
        self.requests: list[Any] = []

    def open(self, request: Any, timeout: int) -> _Response:
        assert timeout == 15
        self.requests.append(request)
        parsed = urlparse(request.full_url)
        if parsed.path.endswith("premiumIndex"):
            payload: object = {"markPrice": "100", "lastFundingRate": "0.0001"}
        elif parsed.path.endswith("ticker/24hr"):
            payload = {"quoteVolume": "100000000", "bidPrice": "99.99", "askPrice": "100.01"}
        elif parsed.path.endswith("openInterest"):
            payload = {"openInterest": "200000"}
        else:
            payload = [
                [NOW_MS - 120_000, "99", "102", "98", "100", "10", NOW_MS - 60_001],
                [NOW_MS - 60_000, "100", "101", "99", "100", "10", NOW_MS - 1],
            ]
        url = "https://redirect.invalid/" if self.redirect else request.full_url
        return _Response(url, payload)


def test_public_market_fetch_is_network_free_and_uses_only_public_gets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    opener = _Opener()

    snapshot = fetch_public_market_snapshot(
        symbol="btcusdt",
        observed_at_ms=NOW_MS,
        opener=cast(Any, opener),
    )

    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.decision_price == Decimal("100")
    assert snapshot.open_interest_usd == Decimal("20000000")
    assert len(opener.requests) == 4
    assert all(request.get_method() == "GET" for request in opener.requests)
    assert all("Authorization" not in request.headers for request in opener.requests)


def test_public_market_redirect_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="redirected"):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _Opener(redirect=True)),
        )


def test_operator_composes_paper_tick_without_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    runtime_operator = _operator(tmp_path)
    liquid20 = load_liquid20_snapshot(runtime_operator.liquid20_snapshot_path, now_ms=NOW_MS)

    tick = runtime_operator._compose_tick(
        liquid20=liquid20,
        markets=(_market(),),
        observed_at_ms=NOW_MS,
    )

    assert tick.observed_at_ms == NOW_MS
    assert tick.mark_prices == (("BTCUSDT", Decimal("100")),)
    assert len(tick.decision_requests) == 1
    request = tick.decision_requests[0]
    assert request.mode is BotMode.PAPER
    assert request.risk_context.candidate_paper_validation_authorized is False
    assert request.dataset_hash == "e" * 64
    assert request.code_sha == CODE_SHA


def test_success_and_failure_health_are_truthful_and_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    runtime_operator = _operator(tmp_path)
    monkeypatch.setattr(
        operator_module,
        "load_liquid20_snapshot",
        lambda *_args, **_kwargs: SimpleNamespace(
            snapshot_id="f" * 64,
            universe=SimpleNamespace(selected_symbols=("BTCUSDT",)),
        ),
    )
    monkeypatch.setattr(
        operator_module, "fetch_public_market_snapshot", lambda **_kwargs: _market()
    )
    monkeypatch.setattr(
        CandidatePaperRuntimeOperator,
        "_compose_tick",
        lambda self, **_kwargs: cast(
            ShadowRuntimeTick,
            SimpleNamespace(observed_at_ms=NOW_MS),
        ),
    )

    assert runtime_operator.run_once(observed_at_ms=NOW_MS) == 1
    healthy = json.loads(runtime_operator.health_path.read_text(encoding="utf-8"))
    assert healthy["status"] == "healthy"
    assert healthy["generation"] == 1
    assert healthy["execution_enabled"] is False
    assert healthy["orders_submitted"] == 0
    claimed = healthy.pop("health_sha256")
    assert claimed == canonical_sha256(healthy)

    runtime_operator.publish_failure(RuntimeError("x" * 1000), checked_at_ms=NOW_MS + 1)
    failed = json.loads(runtime_operator.health_path.read_text(encoding="utf-8"))
    assert failed["status"] == "fail_closed"
    assert len(failed["error_message"]) == 240
    assert failed["generation"] == 1
    assert failed["live_capital_authorized"] is False


def test_poll_cadence_cannot_violate_ninety_six_snapshot_minimum(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in operator_module.FORBIDDEN_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    runtime_operator = _operator(tmp_path)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="60..900"):
        runtime_operator.run_forever(poll_seconds=901)
    assert 86_400 // operator_module.DEFAULT_POLL_SECONDS >= 96
