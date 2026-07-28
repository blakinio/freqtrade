from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
)
from ai_platform.wickhunter.dataset import load_accepted_import
from ai_platform.wickhunter.live_archive import (
    LiveArchiveAcceptanceRequest,
    accept_closed_live_run,
)


BRIDGE_SHA = "1" * 40
DECISION_SHA = "2" * 64
HOLDOUT_START_MS = 2_000_000_000_000
RUN_ID = "liquid20-20260726T000000Z-0"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _event(
    *,
    source: str,
    symbol: str,
    occurred_at_ms: int,
    index: int,
) -> LiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(str(index))
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=sha256(f"{source}-{symbol}-{index}".encode()).hexdigest(),
        symbol=symbol,
        liquidated_position_side=(
            LiquidatedPositionSide.LONG if index % 2 else LiquidatedPositionSide.SHORT
        ),
        occurred_at_ms=occurred_at_ms,
        received_at_ms=occurred_at_ms + 250,
        price=price,
        quantity=quantity,
        notional_usd=price * quantity,
        raw_side="Sell" if index % 2 else "Buy",
    )


def _source_stats(events: tuple[LiquidationEvent, ...]) -> dict[str, object]:
    last = max(events, key=lambda event: event.received_at_ms) if events else None
    return {
        "configured": True,
        "connected": False,
        "last_event_at_ms": None if last is None else last.occurred_at_ms,
        "last_event_received_at_ms": None if last is None else last.received_at_ms,
        "last_heartbeat_at_ms": 1_785_024_100_000,
        "ingest_lag_ms": None if last is None else last.ingest_latency_ms,
        "reconnect_count": 0,
        "observed_symbol_count": len({event.symbol for event in events}),
        "subscription_symbol_count": 2,
        "events_written": len(events),
        "error_count": 0,
        "parse_error_count": 0,
        "latest_error": None,
    }


def _write_closed_run(root: Path) -> Path:
    run_root = root / RUN_ID
    run_root.mkdir()
    events_by_source = {
        "bybit-linear": (
            _event(
                source="bybit-linear",
                symbol="BTCUSDT",
                occurred_at_ms=1_785_024_010_000,
                index=1,
            ),
            _event(
                source="bybit-linear",
                symbol="ETHUSDT",
                occurred_at_ms=1_785_024_020_000,
                index=2,
            ),
        ),
        "binance-usdm": (
            _event(
                source="binance-usdm",
                symbol="BTCUSDT",
                occurred_at_ms=1_785_024_030_000,
                index=3,
            ),
        ),
    }
    source_states: dict[str, object] = {}
    for source, events in events_by_source.items():
        events_path = run_root / f"{source}.ndjson"
        events_path.write_text(
            "".join(
                json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True) + "\n"
                for event in events
            ),
            encoding="utf-8",
        )
        stats = _source_stats(events)
        source_states[source] = stats
        _write_json(
            run_root / f"{source}-summary.json",
            {
                "schema_version": 1,
                "source": {"id": source},
                "run_id": RUN_ID,
                "run_state": "completed",
                "stats": stats,
                "trading_credentials_present": False,
                "execution_enabled": False,
            },
        )
    source_states["okx-swap"] = {
        "configured": False,
        "connected": False,
        "last_event_at_ms": None,
        "last_event_received_at_ms": None,
        "last_heartbeat_at_ms": None,
        "ingest_lag_ms": None,
        "reconnect_count": 0,
        "observed_symbol_count": 0,
        "subscription_symbol_count": 0,
        "events_written": 0,
        "error_count": 0,
        "parse_error_count": 0,
        "latest_error": None,
    }
    _write_json(
        run_root / "run-state-v1.json",
        {
            "schema_version": 1,
            "contract": "liquidation-live-state-v1",
            "run_id": RUN_ID,
            "run_state": "completed",
            "data_mode": "historical",
            "collector_started_at_ms": 1_785_024_000_000,
            "collector_heartbeat_at_ms": 1_785_024_100_000,
            "last_event_at_ms": 1_785_024_030_000,
            "last_event_received_at_ms": 1_785_024_030_250,
            "completed_at_ms": 1_785_024_100_000,
            "completion_reason": "daily-rotation",
            "collector_commit": "a" * 40,
            "host_id": "synology-01",
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "sources": source_states,
        },
    )
    return run_root


def _request(*, holdout: int = HOLDOUT_START_MS) -> LiveArchiveAcceptanceRequest:
    return LiveArchiveAcceptanceRequest(
        source_commit_sha=BRIDGE_SHA,
        decision_contract_sha256=DECISION_SHA,
        protected_holdout_start_ms=holdout,
        created_at_utc="2026-07-28T00:00:00Z",
        storage_root="synology://liquid20/data/live/runs",
    )


def test_accepts_closed_real_run_and_loads_through_wh01(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    output_root = tmp_path / "accepted"

    artifacts = accept_closed_live_run(
        run_root=run_root,
        output_root=output_root,
        request=_request(),
    )
    bundle = load_accepted_import(output_root)

    assert artifacts.acceptance.status == "pass"
    assert bundle.selection.provider_id == "first-party"
    assert bundle.selection.accepted_records == 3
    assert {event.historical_provider for event in bundle.events} == {"first-party"}
    assert all(event.available_at_ms > event.occurred_at_ms for event in bundle.events)
    provenance = json.loads((output_root / "source-run.json").read_text(encoding="utf-8"))
    assert provenance["model_execution_authorized"] is False
    assert provenance["trading_authorized"] is False


def test_rejects_active_run_without_publishing(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    state_path = run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["run_state"] = "active"
    state["data_mode"] = "live"
    _write_json(state_path, state)
    output_root = tmp_path / "accepted"

    with pytest.raises(ValueError, match="completed historical runs"):
        accept_closed_live_run(run_root=run_root, output_root=output_root, request=_request())

    assert not output_root.exists()


def test_rejects_summary_state_mismatch(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    summary_path = run_root / "bybit-linear-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stats"]["events_written"] = 999
    _write_json(summary_path, summary)

    with pytest.raises(ValueError, match="does not match final run state"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_invalid_live_availability_time(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    events_path = run_root / "binance-usdm.ndjson"
    payload = json.loads(events_path.read_text(encoding="utf-8"))
    payload["received_at_ms"] = payload["occurred_at_ms"] - 1
    _write_json(events_path, payload)

    with pytest.raises(ValueError, match="invalid canonical liquidation event"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_duplicate_source_identity(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    events_path = run_root / "binance-usdm.ndjson"
    line = events_path.read_text(encoding="utf-8")
    events_path.write_text(line + line, encoding="utf-8")
    summary_path = run_root / "binance-usdm-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stats"]["events_written"] = 2
    _write_json(summary_path, summary)
    state_path = run_root / "run-state-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["sources"]["binance-usdm"]["events_written"] = 2
    _write_json(state_path, state)

    with pytest.raises(ValueError, match="duplicate live source event identity"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_protected_holdout_overlap(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)

    with pytest.raises(ValueError, match="protected final holdout"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(holdout=1_785_024_020_000),
        )


def test_output_is_deterministic_and_never_overwritten(tmp_path: Path) -> None:
    run_root = _write_closed_run(tmp_path)
    first = tmp_path / "accepted-a"
    second = tmp_path / "accepted-b"
    request = _request()

    accept_closed_live_run(run_root=run_root, output_root=first, request=request)
    accept_closed_live_run(run_root=run_root, output_root=second, request=request)

    names = (
        "manifest.json",
        "events.jsonl",
        "rejections.json",
        "acceptance.json",
        "source-run.json",
        "artifacts.json",
    )
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in names)
    with pytest.raises(FileExistsError):
        accept_closed_live_run(run_root=run_root, output_root=first, request=request)
