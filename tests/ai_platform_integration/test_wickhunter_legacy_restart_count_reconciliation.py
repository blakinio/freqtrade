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


RUN_ID = "liquid20-20260727T000000Z-1"
BASE_TIME_MS = 1_785_110_410_000


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _event(source: str, index: int, *, received_at_ms: int | None = None) -> LiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(str(index))
    occurred_at_ms = BASE_TIME_MS + index
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=sha256(f"{source}-{index}".encode()).hexdigest(),
        symbol="BTCUSDT",
        liquidated_position_side=LiquidatedPositionSide.LONG,
        occurred_at_ms=occurred_at_ms,
        received_at_ms=received_at_ms or occurred_at_ms + 25,
        price=price,
        quantity=quantity,
        notional_usd=price * quantity,
        raw_side="Sell",
    )


def _stats(
    events: list[LiquidationEvent],
    *,
    declared_events: int,
    checkpoint_index: int | None = None,
) -> dict[str, object]:
    checkpoint = None
    if checkpoint_index is not None:
        checkpoint = events[checkpoint_index]
    elif declared_events > 0 and events:
        checkpoint = events[min(declared_events, len(events)) - 1]
    return {
        "configured": True,
        "connected": False,
        "last_event_at_ms": None if checkpoint is None else checkpoint.occurred_at_ms,
        "last_event_received_at_ms": None if checkpoint is None else checkpoint.received_at_ms,
        "last_heartbeat_at_ms": BASE_TIME_MS + 1_000,
        "ingest_lag_ms": None if checkpoint is None else checkpoint.ingest_latency_ms,
        "reconnect_count": 0,
        "observed_symbol_count": 0 if checkpoint is None else 1,
        "subscription_symbol_count": 1,
        "events_written": declared_events,
        "error_count": 0,
        "parse_error_count": 0,
        "latest_error": None,
    }


def _write_source(
    run_root: Path,
    *,
    source: str,
    events: list[LiquidationEvent],
    declared_events: int,
    summary_run_state: str,
    checkpoint_index: int | None = None,
) -> dict[str, object]:
    (run_root / f"{source}.ndjson").write_text(
        "".join(
            json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True) + "\n"
            for event in events
        ),
        encoding="utf-8",
    )
    stats = _stats(
        events,
        declared_events=declared_events,
        checkpoint_index=checkpoint_index,
    )
    _write_json(
        run_root / f"{source}-summary.json",
        {
            "schema_version": 1,
            "source": {"id": source},
            "run_id": RUN_ID,
            "run_state": summary_run_state,
            "stats": stats,
            "trading_credentials_present": False,
            "execution_enabled": False,
        },
    )
    return stats


def _write_run(
    root: Path,
    *,
    completion_reason: str = "collector-restart",
    summary_run_state: str = "active",
    bybit_actual_events: int = 2,
    bybit_declared_events: int = 1,
    bybit_checkpoint_index: int | None = None,
    bybit_received_times: tuple[int, ...] | None = None,
) -> Path:
    run_root = root / RUN_ID
    run_root.mkdir()
    binance_events = [_event("binance-usdm", 1)]
    bybit_events = [
        _event(
            "bybit-linear",
            index,
            received_at_ms=(
                None if bybit_received_times is None else bybit_received_times[index - 1]
            ),
        )
        for index in range(1, bybit_actual_events + 1)
    ]
    sources = {
        "binance-usdm": _write_source(
            run_root,
            source="binance-usdm",
            events=binance_events,
            declared_events=1,
            summary_run_state=summary_run_state,
        ),
        "bybit-linear": _write_source(
            run_root,
            source="bybit-linear",
            events=bybit_events,
            declared_events=bybit_declared_events,
            summary_run_state=summary_run_state,
            checkpoint_index=bybit_checkpoint_index,
        ),
        "okx-swap": {
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
        },
    }
    all_events = binance_events + bybit_events
    _write_json(
        run_root / "run-state-v1.json",
        {
            "schema_version": 1,
            "contract": "liquidation-live-state-v1",
            "run_id": RUN_ID,
            "run_state": "completed",
            "data_mode": "historical",
            "collector_started_at_ms": BASE_TIME_MS - 10_000,
            "collector_heartbeat_at_ms": BASE_TIME_MS + 1_000,
            "last_event_at_ms": max(event.occurred_at_ms for event in all_events),
            "last_event_received_at_ms": max(event.received_at_ms for event in all_events),
            "completed_at_ms": BASE_TIME_MS + 2_000,
            "completion_reason": completion_reason,
            "collector_commit": "a" * 40,
            "host_id": "synology-test",
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "sources": sources,
        },
    )
    return run_root


def _request() -> LiveArchiveAcceptanceRequest:
    return LiveArchiveAcceptanceRequest(
        source_commit_sha="b" * 40,
        decision_contract_sha256="c" * 64,
        protected_holdout_start_ms=2_000_000_000_000,
        created_at_utc="2026-07-29T00:00:00Z",
        storage_root="synology://liquid20/data/live/runs",
    )


def test_accepts_only_valid_tail_after_restart_checkpoint(tmp_path: Path) -> None:
    run_root = _write_run(tmp_path)
    output_root = tmp_path / "accepted"

    accept_closed_live_run(run_root=run_root, output_root=output_root, request=_request())
    bundle = load_accepted_import(output_root)
    provenance = json.loads((output_root / "source-run.json").read_text(encoding="utf-8"))
    bybit = next(source for source in provenance["sources"] if source["source"] == "bybit-linear")

    assert bundle.selection.accepted_records == 3
    assert bybit["declared_events_written"] == 1
    assert bybit["events_written"] == 2
    assert bybit["reconciled_event_count_delta"] == 1
    assert bybit["legacy_restart_state_accepted"] is True
    assert bybit["legacy_restart_count_reconciled"] is True


def test_rejects_count_tail_outside_legacy_restart(tmp_path: Path) -> None:
    run_root = _write_run(
        tmp_path,
        completion_reason="daily-rotation",
        summary_run_state="completed",
    )

    with pytest.raises(ValueError, match="source event count does not match final run state"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_when_archive_has_fewer_events_than_checkpoint(tmp_path: Path) -> None:
    run_root = _write_run(
        tmp_path,
        bybit_actual_events=1,
        bybit_declared_events=2,
    )

    with pytest.raises(ValueError, match="source event count does not match final run state"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_restart_tail_when_checkpoint_does_not_match_prefix(tmp_path: Path) -> None:
    run_root = _write_run(
        tmp_path,
        bybit_checkpoint_index=1,
    )

    with pytest.raises(ValueError, match="source restart checkpoint does not match event prefix"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_restart_tail_with_regressed_reception_order(tmp_path: Path) -> None:
    run_root = _write_run(
        tmp_path,
        bybit_received_times=(BASE_TIME_MS + 100, BASE_TIME_MS + 50),
    )

    with pytest.raises(ValueError, match="source restart tail reception order regressed"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )
