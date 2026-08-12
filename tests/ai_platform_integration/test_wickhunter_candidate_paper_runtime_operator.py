from __future__ import annotations

import json
import threading
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib.error import HTTPError
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


def _run_state(
    root: Path,
    *,
    run_id: str,
    run_state: str,
    heartbeat_ms: int,
    events: list[dict[str, object]],
    execution_enabled: bool,
    contract: str,
) -> dict[str, object]:
    run_root = root / "runs" / run_id
    run_root.mkdir(parents=True)
    sources: dict[str, object] = {}
    for source in operator_module.EXPECTED_LIVE_SOURCES:
        source_events = events if source == "binance-usdm" else []
        event_path = run_root / f"{source}.ndjson"
        event_path.write_text(
            "".join(json.dumps(item, sort_keys=True) + "\n" for item in source_events),
            encoding="utf-8",
        )
        last_received = (
            max(int(cast(int | str, item["received_at_ms"])) for item in source_events)
            if source_events
            else None
        )
        last_occurred = (
            int(cast(int | str, source_events[-1]["occurred_at_ms"])) if source_events else None
        )
        sources[source] = {
            "configured": True,
            "connected": run_state == "active",
            "events_written": len(source_events),
            "last_event_at_ms": last_occurred,
            "last_event_received_at_ms": last_received,
            "last_heartbeat_at_ms": heartbeat_ms,
        }
    state = {
        "schema_version": 1,
        "contract": contract,
        "run_id": run_id,
        "run_state": run_state,
        "data_mode": "live" if run_state == "active" else "historical",
        "collector_started_at_ms": heartbeat_ms - 60_000,
        "collector_heartbeat_at_ms": heartbeat_ms,
        "trading_credentials_present": False,
        "execution_enabled": execution_enabled,
        "trading_authorized": False,
        "orders_submitted": 0,
        "sources": sources,
    }
    (run_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state


def _write_live_root(
    root: Path,
    *,
    heartbeat_ms: int = NOW_MS,
    events: list[dict[str, object]] | None = None,
    previous_events: list[dict[str, object]] | None = None,
    execution_enabled: bool = False,
    contract: str = "liquidation-live-state-v1",
) -> Path:
    source_events = (
        events
        if events is not None
        else [
            _event("event-history", received_at_ms=NOW_MS - 120_000),
            _event("event-current", received_at_ms=NOW_MS - 1_000),
        ]
    )
    if previous_events is not None:
        _run_state(
            root,
            run_id="liquid20-20270114T000000Z-0",
            run_state="completed",
            heartbeat_ms=NOW_MS - 60_000,
            events=previous_events,
            execution_enabled=execution_enabled,
            contract=contract,
        )
    run_id = "liquid20-20270115T000000Z-0"
    state = _run_state(
        root,
        run_id=run_id,
        run_state="active",
        heartbeat_ms=heartbeat_ms,
        events=source_events,
        execution_enabled=execution_enabled,
        contract=contract,
    )
    pointer = {
        "schema_version": 1,
        "contract": contract,
        "active_run_id": run_id,
        "collector_heartbeat_at_ms": heartbeat_ms,
        "state": state,
    }
    (root / "live-state-v1.json").write_text(
        json.dumps(pointer, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def _write_legacy_restart_suffix_root(
    root: Path,
    *,
    suffix: dict[str, object] | None = None,
    completion_reason: str = "collector-restart",
) -> tuple[Path, Path, dict[str, object]]:
    committed = _event("previous-committed", received_at_ms=NOW_MS - 3_600_000)
    suffix_event = suffix or _event(
        "previous-uncommitted",
        received_at_ms=NOW_MS - 3_500_000,
    )
    live_root = _write_live_root(
        root,
        previous_events=[committed, suffix_event],
    )
    previous_root = live_root / "runs" / "liquid20-20270114T000000Z-0"
    state_path = previous_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["completion_reason"] = completion_reason
    state["completed_at_ms"] = NOW_MS - 20_000
    source_payloads = cast(dict[str, object], state["sources"])
    source_state = source_payloads["binance-usdm"]
    assert isinstance(source_state, dict)
    source_state["events_written"] = 1
    source_state["last_event_at_ms"] = committed["occurred_at_ms"]
    source_state["last_event_received_at_ms"] = committed["received_at_ms"]
    for source in ("bybit-linear", "binance-usdm"):
        source_row = source_payloads[source]
        assert isinstance(source_row, dict)
        source_row["connected"] = True
        summary = {
            "schema_version": 1,
            "source": {"id": source},
            "run_id": state["run_id"],
            "run_state": "active",
            "stats": source_row,
            "trading_credentials_present": False,
            "execution_enabled": False,
        }
        (previous_root / f"{source}-summary.json").write_text(
            json.dumps(summary, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    state_path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    return live_root, previous_root, state


def _market(*, symbol: str = "BTCUSDT", observed_at_ms: int = NOW_MS) -> PublicMarketSnapshot:
    return PublicMarketSnapshot(
        symbol=symbol,
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


def test_live_root_accepts_pointer_published_during_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "pointer-during-read")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    state["collector_heartbeat_at_ms"] = NOW_MS + 500
    (root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer["collector_heartbeat_at_ms"] = NOW_MS + 500
    pointer["state"] = state
    pointer_path.write_text(
        json.dumps(pointer, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert snapshot.observed_at_ms == NOW_MS + 500


def test_live_root_rejects_pointer_later_than_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "pointer-after-read")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    state["collector_heartbeat_at_ms"] = NOW_MS + 601
    (root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer["collector_heartbeat_at_ms"] = NOW_MS + 601
    pointer["state"] = state
    pointer_path.write_text(
        json.dumps(pointer, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monotonic_values = iter((10_000_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="live pointer is from the future",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_reads_only_committed_active_prefix(tmp_path: Path) -> None:
    root = _write_live_root(tmp_path / "active-suffix")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-uncommitted", received_at_ms=NOW_MS + 500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 1_000)

    assert {event.source_event_id for event in snapshot.events} == {
        "event-history",
        "event-current",
    }


def test_live_root_accepts_suffix_available_during_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "active-suffix-during-read")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-during-read", received_at_ms=NOW_MS + 500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")
    monotonic_values = iter((10_000_000_000, 10_100_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert "event-during-read" not in {event.source_event_id for event in snapshot.events}


def test_live_root_does_not_chase_suffix_appended_after_snapshot_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "active-suffix-growing")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    event_path = root / "runs" / run_id / "binance-usdm.ndjson"
    trigger = _event("event-trigger", received_at_ms=NOW_MS - 500)
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(trigger, sort_keys=True) + "\n")

    original_parse = operator_module._parse_live_source_event
    appended = False

    def parse_with_growth(row: dict[str, Any], *, source: str, observed_at_ms: int) -> Any:
        nonlocal appended
        if not appended and row.get("source_event_id") == "event-trigger":
            appended = True
            future = _event(
                "event-appended-during-read",
                received_at_ms=NOW_MS + 60_000,
            )
            with event_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(future, sort_keys=True) + "\n")
        return original_parse(row, source=source, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(operator_module, "_parse_live_source_event", parse_with_growth)
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: 10_000_000_000)

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert appended is True
    assert "event-appended-during-read" in event_path.read_text(encoding="utf-8")
    assert {event.source_event_id for event in snapshot.events} == {
        "event-history",
        "event-current",
    }


def test_live_root_rejects_suffix_later_than_bounded_snapshot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "active-suffix-after-read")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-after-read", received_at_ms=NOW_MS + 601)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")
    monotonic_values = iter((10_000_000_000, 10_100_000_000, 10_600_000_000))
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="unavailable at live observation time",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("invalid", "source event is invalid"),
        ("wrong-source", "source does not match"),
        ("future", "unavailable at live observation time"),
    ),
)
def test_live_root_rejects_invalid_uncommitted_active_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    root = _write_live_root(tmp_path / f"active-suffix-{mutation}")
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: 10_000_000_000)
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-uncommitted-invalid", received_at_ms=NOW_MS - 500)
    if mutation == "invalid":
        suffix["price"] = "0"
    elif mutation == "wrong-source":
        suffix["source"] = "bybit-linear"
    else:
        suffix["received_at_ms"] = NOW_MS + 1
        suffix["occurred_at_ms"] = NOW_MS
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")

    with pytest.raises(CandidatePaperRuntimeOperatorError, match=message):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_allows_uncommitted_first_event_for_configured_source(
    tmp_path: Path,
) -> None:
    root = _write_live_root(tmp_path / "configured-zero")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    bybit_event = _event(
        "bybit-uncommitted",
        received_at_ms=NOW_MS - 500,
        source="bybit-linear",
    )
    (root / "runs" / run_id / "bybit-linear.ndjson").write_text(
        json.dumps(bybit_event, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)
    source_states = {item.source: item for item in snapshot.source_states}

    assert "bybit-uncommitted" not in {event.source_event_id for event in snapshot.events}
    assert source_states["bybit-linear"].coverage_available is False


def test_live_root_rejects_suffix_for_completed_run(tmp_path: Path) -> None:
    root = _write_live_root(
        tmp_path / "completed-suffix",
        previous_events=[_event("previous-committed", received_at_ms=NOW_MS - 3_600_000)],
    )
    previous_root = root / "runs" / "liquid20-20270114T000000Z-0"
    with (previous_root / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event("previous-extra", received_at_ms=NOW_MS - 3_500_000),
                sort_keys=True,
            )
            + "\n"
        )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="contradicts events_written"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_accepts_bounded_legacy_restart_suffix_as_uncommitted(
    tmp_path: Path,
) -> None:
    root, _, _ = _write_legacy_restart_suffix_root(tmp_path / "legacy-restart-suffix")

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    event_ids = {event.source_event_id for event in snapshot.events}
    assert "previous-committed" in event_ids
    assert "previous-uncommitted" not in event_ids


def test_live_root_rejects_legacy_restart_suffix_for_unprovenanced_okx(
    tmp_path: Path,
) -> None:
    root, previous_root, state = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-okx-suffix"
    )
    committed = _event(
        "okx-committed",
        received_at_ms=NOW_MS - 3_600_000,
        source="okx-swap",
    )
    suffix = _event(
        "okx-uncommitted",
        received_at_ms=NOW_MS - 3_500_000,
        source="okx-swap",
    )
    (previous_root / "okx-swap.ndjson").write_text(
        json.dumps(committed, sort_keys=True) + "\n" + json.dumps(suffix, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    okx_state = cast(dict[str, object], state["sources"])["okx-swap"]
    assert isinstance(okx_state, dict)
    okx_state["events_written"] = 1
    okx_state["last_event_at_ms"] = committed["occurred_at_ms"]
    okx_state["last_event_received_at_ms"] = committed["received_at_ms"]
    (previous_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="contradicts events_written"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_accepts_legacy_suffix_after_heartbeat_before_completion(
    tmp_path: Path,
) -> None:
    suffix = _event("legacy-after-heartbeat", received_at_ms=NOW_MS - 30_000)
    root, _, _ = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-after-heartbeat",
        suffix=suffix,
    )

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)

    assert "legacy-after-heartbeat" not in {event.source_event_id for event in snapshot.events}


def test_live_root_rejects_restart_suffix_without_legacy_active_summary_provenance(
    tmp_path: Path,
) -> None:
    root, previous_root, _ = _write_legacy_restart_suffix_root(tmp_path / "modern-restart-mutation")
    for source in ("bybit-linear", "binance-usdm"):
        summary_path = previous_root / f"{source}-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["run_state"] = "completed"
        summary_path.write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="contradicts events_written"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


@pytest.mark.parametrize("checkpoint_field", ["last_event_at_ms", "last_event_received_at_ms"])
def test_live_root_rejects_legacy_suffix_when_committed_checkpoint_mismatches(
    tmp_path: Path,
    checkpoint_field: str,
) -> None:
    root, previous_root, state = _write_legacy_restart_suffix_root(
        tmp_path / f"legacy-checkpoint-{checkpoint_field}"
    )
    source_state = cast(dict[str, object], state["sources"])["binance-usdm"]
    assert isinstance(source_state, dict)
    source_state[checkpoint_field] = int(cast(int, source_state[checkpoint_field])) + 1
    (previous_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_path = previous_root / "binance-usdm-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stats"] = source_state
    summary_path.write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="committed prefix does not match the persisted checkpoint",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_zero_prefix_legacy_suffix_without_checkpoint(tmp_path: Path) -> None:
    root, previous_root, state = _write_legacy_restart_suffix_root(tmp_path / "legacy-zero-prefix")
    source_state = cast(dict[str, object], state["sources"])["binance-usdm"]
    assert isinstance(source_state, dict)
    source_state["events_written"] = 0
    source_state["last_event_at_ms"] = None
    source_state["last_event_received_at_ms"] = None
    (previous_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_path = previous_root / "binance-usdm-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stats"] = source_state
    summary_path.write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(
        CandidatePaperRuntimeOperatorError, match="legacy suffix has no committed checkpoint"
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_legacy_restart_suffix_after_completion_boundary(
    tmp_path: Path,
) -> None:
    suffix = _event(
        "legacy-after-completion",
        received_at_ms=NOW_MS - 10_000,
    )
    root, _, _ = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-after-completion",
        suffix=suffix,
    )

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="unavailable at live observation time",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_legacy_suffix_identity_duplicated_in_active_run(
    tmp_path: Path,
) -> None:
    suffix = _event(
        "event-history",
        received_at_ms=NOW_MS - 3_500_000,
    )
    root, _, _ = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-cross-run-duplicate",
        suffix=suffix,
    )

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="duplicate event identities",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("malformed", "source event is invalid"),
        ("foreign-source", "source does not match"),
        ("future", "unavailable at live observation time"),
        ("duplicate", "duplicate event identities"),
        ("reordered", "suffix reception order regressed"),
    ),
)
def test_live_root_rejects_unsafe_legacy_restart_suffix(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    suffix = _event("legacy-suffix", received_at_ms=NOW_MS - 3_500_000)
    if mutation == "malformed":
        suffix["price"] = "0"
    elif mutation == "foreign-source":
        suffix["source"] = "bybit-linear"
    elif mutation == "future":
        suffix["received_at_ms"] = NOW_MS + 1
        suffix["occurred_at_ms"] = NOW_MS
    elif mutation == "duplicate":
        suffix["source_event_id"] = "previous-committed"
    else:
        suffix["received_at_ms"] = NOW_MS - 3_700_000
        suffix["occurred_at_ms"] = NOW_MS - 3_700_100
    root, _, _ = _write_legacy_restart_suffix_root(
        tmp_path / f"legacy-restart-{mutation}",
        suffix=suffix,
    )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match=message):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_short_legacy_restart_file(tmp_path: Path) -> None:
    root, previous_root, state = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-restart-short"
    )
    source_state = cast(dict[str, object], state["sources"])["binance-usdm"]
    assert isinstance(source_state, dict)
    source_state["events_written"] = 3
    (previous_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="contradicts events_written"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_excessive_legacy_restart_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _write_legacy_restart_suffix_root(tmp_path / "legacy-restart-excess")
    monkeypatch.setattr(operator_module, "MAX_UNCOMMITTED_LIVE_EVENTS", 0)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="too many uncommitted events"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_oversized_legacy_restart_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suffix = _event("legacy-oversized", received_at_ms=NOW_MS - 3_500_000)
    suffix["padding"] = "x" * 512
    root, previous_root, _ = _write_legacy_restart_suffix_root(
        tmp_path / "legacy-restart-oversized",
        suffix=suffix,
    )
    committed_line = (previous_root / "binance-usdm.ndjson").read_bytes().splitlines()[0]
    monkeypatch.setattr(operator_module, "MAX_LIVE_EVENT_ROW_BYTES", len(committed_line) + 1)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="oversized event"):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_snapshot_identity_overflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(
        tmp_path / "snapshot-identity-overflow",
        previous_events=[_event("identity-bound", received_at_ms=NOW_MS - 3_600_000)],
    )
    monkeypatch.setattr(operator_module, "MAX_LIVE_SNAPSHOT_EVENT_IDENTITIES", 0)

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="snapshot contains too many event identities",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_rejects_oversized_source_event_identity(
    tmp_path: Path,
) -> None:
    oversized_event_id = "ż" * (operator_module.MAX_LIVE_SOURCE_EVENT_ID_BYTES // 2 + 1)
    root = _write_live_root(
        tmp_path / "oversized-source-event-id",
        previous_events=[_event(oversized_event_id, received_at_ms=NOW_MS - 3_600_000)],
    )

    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="source event identity is too large",
    ):
        load_liquid20_snapshot(root, now_ms=NOW_MS)


def test_live_root_retries_mid_publication_pointer_state_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "publication-race")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    def publish_pointer(_seconds: float) -> None:
        pointer["collector_heartbeat_at_ms"] = NOW_MS + 100
        pointer["state"] = newer_state
        pointer_path.write_text(
            json.dumps(pointer, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(operator_module.time, "sleep", publish_pointer)

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 100)

    assert snapshot.observed_at_ms == NOW_MS + 100


def test_live_root_retry_preserves_suffix_availability_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "retry-suffix-clock")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    suffix = _event("event-after-first-attempt", received_at_ms=NOW_MS + 1_500)
    with (root / "runs" / run_id / "binance-usdm.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(suffix, sort_keys=True) + "\n")

    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    def publish_pointer(_seconds: float) -> None:
        pointer["collector_heartbeat_at_ms"] = NOW_MS + 100
        pointer["state"] = newer_state
        pointer_path.write_text(
            json.dumps(pointer, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    monotonic_values = iter(
        (
            10_000_000_000,
            10_100_000_000,
            10_200_000_000,
            12_000_000_000,
        )
    )
    monkeypatch.setattr(operator_module.time, "monotonic_ns", lambda: next(monotonic_values))
    monkeypatch.setattr(operator_module.time, "sleep", publish_pointer)

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS + 100)

    assert "event-after-first-attempt" not in {event.source_event_id for event in snapshot.events}


def test_live_root_persistent_mid_publication_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _write_live_root(tmp_path / "persistent-publication-race")
    pointer = json.loads((root / "live-state-v1.json").read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    run_id = str(state["run_id"])
    run_state_path = root / "runs" / run_id / "run-state-v1.json"
    newer_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    newer_state["collector_heartbeat_at_ms"] = NOW_MS + 100
    run_state_path.write_text(
        json.dumps(newer_state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(operator_module.time, "sleep", lambda _seconds: None)

    with pytest.raises(CandidatePaperRuntimeOperatorError, match="stable Liquid20"):
        load_liquid20_snapshot(root, now_ms=NOW_MS + 100)


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


def test_live_root_allows_configured_source_with_zero_events(tmp_path: Path) -> None:
    snapshot = load_liquid20_snapshot(
        _write_live_root(tmp_path / "liquid20"),
        now_ms=NOW_MS,
    )
    source_states = {item.source: item for item in snapshot.source_states}

    assert snapshot.universe.selected_symbols == ("BTCUSDT",)
    assert source_states["binance-usdm"].health is SourceHealth.HEALTHY
    assert source_states["bybit-linear"].health is SourceHealth.STALE
    assert source_states["bybit-linear"].coverage_available is False
    assert source_states["okx-swap"].health is SourceHealth.STALE


def test_live_root_accepts_exact_producer_shape_for_unconfigured_source(
    tmp_path: Path,
) -> None:
    root = _write_live_root(tmp_path / "producer-shape")
    pointer_path = root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    state.pop("orders_submitted")
    sources = cast(dict[str, object], state["sources"])
    okx = cast(dict[str, object], sources["okx-swap"])
    okx["configured"] = False
    okx["connected"] = False
    okx["last_heartbeat_at_ms"] = None
    run_id = str(state["run_id"])
    run_root = root / "runs" / run_id
    (run_root / "okx-swap.ndjson").unlink()
    (run_root / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8")

    snapshot = load_liquid20_snapshot(root, now_ms=NOW_MS)
    source_states = {item.source: item for item in snapshot.source_states}

    assert snapshot.universe.selected_symbols == ("BTCUSDT",)
    assert source_states["okx-swap"].health is SourceHealth.OFFLINE
    assert source_states["okx-swap"].coverage_available is False


def test_live_root_reads_previous_completed_run_across_rotation(tmp_path: Path) -> None:
    snapshot = load_liquid20_snapshot(
        _write_live_root(
            tmp_path / "liquid20",
            events=[_event("event-current", received_at_ms=NOW_MS - 1_000)],
            previous_events=[_event("event-previous-run", received_at_ms=NOW_MS - 3_600_000)],
        ),
        now_ms=NOW_MS,
    )

    assert {event.source_event_id for event in snapshot.events} == {
        "event-current",
        "event-previous-run",
    }
    assert len(snapshot.history_for("BTCUSDT").event_notionals_usd) == 2


def test_live_root_rejects_run_source_and_receipt_substitution(tmp_path: Path) -> None:
    invalid_run_root = _write_live_root(tmp_path / "invalid-run")
    pointer_path = invalid_run_root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    old_run_id = str(state["run_id"])
    invalid_run_id = "run-20270115"
    (invalid_run_root / "runs" / old_run_id).rename(invalid_run_root / "runs" / invalid_run_id)
    state["run_id"] = invalid_run_id
    pointer["active_run_id"] = invalid_run_id
    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="run identity"):
        load_liquid20_snapshot(invalid_run_root, now_ms=NOW_MS)

    missing_source_root = _write_live_root(tmp_path / "missing-source")
    pointer_path = missing_source_root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    sources = cast(dict[str, object], state["sources"])
    del sources["okx-swap"]
    run_id = str(state["run_id"])
    (missing_source_root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="source set"):
        load_liquid20_snapshot(missing_source_root, now_ms=NOW_MS)

    receipt_root = _write_live_root(tmp_path / "receipt")
    pointer_path = receipt_root / "live-state-v1.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state = cast(dict[str, object], pointer["state"])
    sources = cast(dict[str, object], state["sources"])
    binance = cast(dict[str, object], sources["binance-usdm"])
    binance["last_event_received_at_ms"] = NOW_MS - 2_000
    run_id = str(state["run_id"])
    (receipt_root / "runs" / run_id / "run-state-v1.json").write_text(
        json.dumps(state, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pointer_path.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="state receipt"):
        load_liquid20_snapshot(receipt_root, now_ms=NOW_MS)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("stale", "stale"),
        ("authority", "forbidden authority"),
        ("contract", "contract mismatch"),
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
    elif mutation == "contract":
        _write_live_root(root, contract="liquidation-live-state-v0")
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
    def __init__(
        self,
        *,
        redirect: bool = False,
        gap: bool = False,
        future_rows: int = 0,
    ) -> None:
        if not 0 <= future_rows < operator_module.PUBLIC_KLINE_LIMIT:
            raise ValueError("future_rows is outside the bounded response")
        self.redirect = redirect
        self.gap = gap
        self.future_rows = future_rows
        self.requests: list[Any] = []

    def _klines(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for index in range(operator_module.PUBLIC_KLINE_LIMIT):
            close_ms = (
                NOW_MS
                - (operator_module.PUBLIC_KLINE_LIMIT - 1 - self.future_rows - index) * 60_000
                - 1_000
            )
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
            assert query["limit"] == [str(operator_module.PUBLIC_KLINE_LIMIT)]
            payload = self._klines()
        response_url = "https://redirect.invalid/" if self.redirect else request.full_url
        return _Response(response_url, payload)


class _HttpErrorOpener:
    def __init__(self, exchange_code: int) -> None:
        self.exchange_code = exchange_code

    def open(self, request: Any, timeout: int) -> _Response:
        assert timeout == 15
        body = json.dumps(
            {
                "code": self.exchange_code,
                "msg": "synthetic Binance public API error",
            }
        ).encode("utf-8")
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            {},
            BytesIO(body),
        )


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


@pytest.mark.parametrize("exchange_code", (-4108, -1121))
def test_public_market_terminal_symbol_lifecycle_is_classified(exchange_code: int) -> None:
    with pytest.raises(
        operator_module._PublicMarketSymbolUnavailable,
        match="public market symbol is unavailable",
    ) as error:
        fetch_public_market_snapshot(
            symbol="HFTUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _HttpErrorOpener(exchange_code)),
        )

    assert error.value.symbol == "HFTUSDT"
    assert error.value.exchange_code == exchange_code


def test_public_market_non_terminal_http_400_stays_fail_closed() -> None:
    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="unable to fetch public premium index",
    ):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _HttpErrorOpener(-1100)),
        )


def test_public_market_kline_margin_keeps_decision_time_completion_boundary() -> None:
    snapshot = fetch_public_market_snapshot(
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS,
        opener=cast(Any, _Opener(future_rows=10)),
    )

    assert snapshot.completed_candle_close_ms == NOW_MS - 1_000


def test_public_market_kline_margin_remains_bounded_and_fails_closed() -> None:
    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="must contain 1440 completed",
    ):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _Opener(future_rows=61)),
        )


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
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="allowed"):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            base_url="https://fapi.binance.com:8443",
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
    assert context.candidate_paper_validation_authorized is False
    assert _risk_limits().maximum_leverage >= INITIAL_COMPATIBILITY_PRIOR.leverage


def test_consecutive_loss_cooldown_is_anchored_to_latest_loss() -> None:
    latest_loss_closed_at_ms = NOW_MS - 100_000
    closed_positions = tuple(
        SimpleNamespace(
            closed_at_ms=latest_loss_closed_at_ms - index * 1_000,
            closed_position_id=f"{index + 1:064x}",
            symbol="BTCUSDT",
            realized_pnl_quote=Decimal("-10"),
        )
        for index in range(5)
    )
    state = SimpleNamespace(
        positions=(),
        closed_positions=closed_positions,
        cumulative_realized_pnl_quote=Decimal("-50"),
        drawdown_ratio=Decimal("0.01"),
    )
    policy = SimpleNamespace(simulated_initial_equity_quote=Decimal("10000"))
    expected_until = latest_loss_closed_at_ms + INITIAL_COMPATIBILITY_PRIOR.cooldown_ms

    active = _runtime_risk_context(
        state=state,
        policy=cast(Any, policy),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS,
        market=_market(),
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        circuit_breaker_active=False,
    )
    expired = _runtime_risk_context(
        state=state,
        policy=cast(Any, policy),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS + 300_000,
        market=_market(observed_at_ms=NOW_MS + 300_000),
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        circuit_breaker_active=False,
    )

    assert active.consecutive_losses == 5
    assert active.consecutive_loss_cooldown_until_ms == expected_until
    assert expired.consecutive_loss_cooldown_until_ms == expected_until
    assert expected_until > active.evaluated_at_ms
    assert expected_until <= expired.evaluated_at_ms


def _service(
    *,
    mode: BotMode = BotMode.PAPER,
    positions: tuple[SimpleNamespace, ...] = (),
) -> Any:
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
        positions=positions,
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


def test_tick_uses_only_current_burst_and_keeps_open_position_marks(
    tmp_path: Path,
) -> None:
    old_only = load_liquid20_snapshot(
        _write_live_root(
            tmp_path / "old-only",
            events=[_event("event-old", received_at_ms=NOW_MS - 120_000)],
        ),
        now_ms=NOW_MS,
    )
    operator = CandidatePaperRuntimeOperator(
        service=cast(Any, _service()),
        liquid20_root_path=(tmp_path / "old-only").resolve(),
        health_path=(tmp_path / "old-health.json").resolve(),
        operator_commit=CODE_SHA,
    )
    old_tick = operator._compose_tick(
        liquid20=old_only,
        markets=(_market(),),
        observed_at_ms=NOW_MS,
    )
    assert old_tick.decision_requests == ()

    open_position = SimpleNamespace(
        unrealized_pnl_quote=Decimal("0"),
        mark_price=Decimal("200"),
        quantity=Decimal("1"),
        symbol="ETHUSDT",
        side=TradeDirection.LONG,
    )
    current = load_liquid20_snapshot(
        _write_live_root(tmp_path / "current"),
        now_ms=NOW_MS,
    )
    operator = CandidatePaperRuntimeOperator(
        service=cast(Any, _service(positions=(open_position,))),
        liquid20_root_path=(tmp_path / "current").resolve(),
        health_path=(tmp_path / "current-health.json").resolve(),
        operator_commit=CODE_SHA,
    )
    tick = operator._compose_tick(
        liquid20=current,
        markets=(_market(), _market(symbol="ETHUSDT")),
        observed_at_ms=NOW_MS,
    )

    assert len(tick.decision_requests) == 1
    assert {symbol for symbol, _price in tick.mark_prices} == {"BTCUSDT", "ETHUSDT"}


def test_run_once_excludes_terminal_public_market_symbol_from_universe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterCompose(RuntimeError):
        pass

    events = [
        _event("btc-history", symbol="BTCUSDT", received_at_ms=NOW_MS - 3_600_000),
        _event("hft-history", symbol="HFTUSDT", received_at_ms=NOW_MS - 3_600_000),
        _event("btc-current", symbol="BTCUSDT", received_at_ms=NOW_MS - 1_000),
        _event("hft-current", symbol="HFTUSDT", received_at_ms=NOW_MS - 1_000),
    ]
    service = _service()
    captured_tick: object | None = None

    def stop_after_compose(tick: object) -> None:
        nonlocal captured_tick
        captured_tick = tick
        raise StopAfterCompose

    service.step = stop_after_compose
    root = _write_live_root(tmp_path / "terminal-symbol", events=events)
    runtime_operator = CandidatePaperRuntimeOperator(
        service=cast(Any, service),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "terminal-health.json").resolve(),
        operator_commit=CODE_SHA,
    )

    def fake_market_snapshot(
        *,
        symbol: str,
        observed_at_ms: int,
        base_url: str,
        opener: object,
    ) -> PublicMarketSnapshot:
        del base_url, opener
        if symbol == "HFTUSDT":
            raise operator_module._PublicMarketSymbolUnavailable(symbol, -4108)
        return _market(symbol=symbol, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(
        operator_module,
        "fetch_public_market_snapshot",
        fake_market_snapshot,
    )
    with pytest.raises(StopAfterCompose):
        runtime_operator.run_once(observed_at_ms=NOW_MS)

    assert captured_tick is not None
    tick = cast(Any, captured_tick)
    assert tick.universe.selected_symbols == ("BTCUSDT",)
    decisions = {item.canonical_symbol: item for item in tick.universe.decisions}
    assert decisions["BTCUSDT"].included is True
    assert "binance_usdm_public_market_available" in decisions["BTCUSDT"].reason_codes
    assert decisions["HFTUSDT"].included is False
    assert decisions["HFTUSDT"].reason_codes == ("binance_usdm_public_market_unavailable",)
    assert tuple(symbol for symbol, _price in tick.mark_prices) == ("BTCUSDT",)


def test_run_once_fails_closed_when_open_position_market_becomes_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    open_position = SimpleNamespace(
        unrealized_pnl_quote=Decimal("0"),
        mark_price=Decimal("100"),
        quantity=Decimal("1"),
        symbol="HFTUSDT",
        side=TradeDirection.LONG,
    )
    root = _write_live_root(tmp_path / "open-terminal")
    runtime_operator = CandidatePaperRuntimeOperator(
        service=cast(Any, _service(positions=(open_position,))),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "open-terminal-health.json").resolve(),
        operator_commit=CODE_SHA,
    )

    def fake_market_snapshot(
        *,
        symbol: str,
        observed_at_ms: int,
        base_url: str,
        opener: object,
    ) -> PublicMarketSnapshot:
        del base_url, opener
        if symbol == "HFTUSDT":
            raise operator_module._PublicMarketSymbolUnavailable(symbol, -4108)
        return _market(symbol=symbol, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(
        operator_module,
        "fetch_public_market_snapshot",
        fake_market_snapshot,
    )
    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="open PAPER position lacks Binance USD-M public market context: HFTUSDT",
    ):
        runtime_operator.run_once(observed_at_ms=NOW_MS)


def test_run_once_fetches_mark_for_open_position_outside_universe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterCompose(RuntimeError):
        pass

    open_position = SimpleNamespace(
        unrealized_pnl_quote=Decimal("0"),
        mark_price=Decimal("200"),
        quantity=Decimal("1"),
        symbol="ETHUSDT",
        side=TradeDirection.LONG,
    )
    service = _service(positions=(open_position,))

    def stop_after_compose(_tick: object) -> None:
        raise StopAfterCompose

    service.step = stop_after_compose
    root = _write_live_root(tmp_path / "liquid20")
    operator = CandidatePaperRuntimeOperator(
        service=cast(Any, service),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "health.json").resolve(),
        operator_commit=CODE_SHA,
    )
    fetched: list[str] = []

    def fake_market_snapshot(
        *,
        symbol: str,
        observed_at_ms: int,
        base_url: str,
        opener: object,
    ) -> PublicMarketSnapshot:
        del base_url, opener
        fetched.append(symbol)
        return _market(symbol=symbol, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(
        operator_module,
        "fetch_public_market_snapshot",
        fake_market_snapshot,
    )
    with pytest.raises(StopAfterCompose):
        operator.run_once(observed_at_ms=NOW_MS)

    assert fetched == ["BTCUSDT", "ETHUSDT"]


def test_run_once_bounds_parallel_public_market_fetches_and_preserves_result_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterCompose(RuntimeError):
        pass

    symbols = tuple(f"ASSET{index}USDT" for index in range(10))
    events: list[dict[str, object]] = []
    for index, symbol in enumerate(symbols):
        events.extend(
            (
                _event(
                    f"event-history-{index}",
                    symbol=symbol,
                    received_at_ms=NOW_MS - 3_600_000,
                ),
                _event(
                    f"event-current-{index}",
                    symbol=symbol,
                    received_at_ms=NOW_MS - 1_000,
                ),
            )
        )
    service = _service()
    captured_tick: object | None = None

    def stop_after_compose(tick: object) -> None:
        nonlocal captured_tick
        captured_tick = tick
        raise StopAfterCompose

    service.step = stop_after_compose
    root = _write_live_root(tmp_path / "parallel-liquid20", events=events)
    runtime_operator = CandidatePaperRuntimeOperator(
        service=cast(Any, service),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "parallel-health.json").resolve(),
        operator_commit=CODE_SHA,
    )
    lock = threading.Lock()
    release = threading.Event()
    started = 0
    active = 0
    maximum_active = 0
    fetched: list[str] = []

    def fake_market_snapshot(
        *,
        symbol: str,
        observed_at_ms: int,
        base_url: str,
        opener: object,
    ) -> PublicMarketSnapshot:
        del base_url, opener
        nonlocal started, active, maximum_active
        with lock:
            started += 1
            active += 1
            maximum_active = max(maximum_active, active)
            fetched.append(symbol)
            if started >= 4:
                release.set()
        if not release.wait(timeout=2):
            raise AssertionError("public market fetches did not overlap")
        with lock:
            active -= 1
        return _market(symbol=symbol, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(
        operator_module,
        "fetch_public_market_snapshot",
        fake_market_snapshot,
    )
    with pytest.raises(StopAfterCompose):
        runtime_operator.run_once(observed_at_ms=NOW_MS)

    assert maximum_active >= 4
    assert maximum_active <= operator_module.MAX_PUBLIC_MARKET_WORKERS
    assert set(fetched) == set(symbols)
    assert captured_tick is not None
    mark_prices = cast(Any, captured_tick).mark_prices
    assert tuple(symbol for symbol, _price in mark_prices) == tuple(sorted(symbols))


def test_operator_refuses_non_paper_binding(tmp_path: Path) -> None:
    with pytest.raises(CandidatePaperRuntimeOperatorError, match="mode must be PAPER"):
        _operator(tmp_path, mode=BotMode.SHADOW)


def test_health_is_bounded_self_hashed_and_truthful(tmp_path: Path) -> None:
    runtime_operator = _operator(tmp_path)
    payload = runtime_operator._health_payload(
        status="fail_closed",
        checked_at_ms=NOW_MS,
        liquid20_snapshot_id=None,
        runtime_health="fail_closed",
        circuit_breaker_reasons=("operator_circuit_breaker_active",),
        error_code="SyntheticError",
        error_message="x" * 1000,
    )
    claimed = payload.pop("health_sha256")

    assert payload["model_drift"] == "drifted"
    assert payload["data_drift"] == "unknown"
    assert payload["runtime_health"] == "fail_closed"
    assert payload["circuit_breaker_active"] is True
    assert payload["circuit_breaker_reasons"] == ["operator_circuit_breaker_active"]
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
            "true",
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
    assert "except Exception as exc" in source
    assert args.circuit_breaker_active is True


def test_synology_compose_keeps_zero_authority_container_boundary() -> None:
    compose = Path("deploy/synology/wickhunter-paper-runtime/compose.yaml").read_text(
        encoding="utf-8"
    )
    dockerfile = Path("deploy/synology/wickhunter-paper-runtime/Dockerfile").read_text(
        encoding="utf-8"
    )

    assert "--liquid20-root" in compose
    assert "CIRCUIT_BREAKER_ACTIVE" in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "docker.sock" not in compose
    assert "ports:" not in compose
    assert ("/app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py") in compose
    assert "candidate_paper_runtime_operator" in dockerfile
