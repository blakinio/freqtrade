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


RUN_ID = "liquid20-20260727T000000Z-0"
EVENT_TIME_MS = 1_785_110_410_000


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _event(source: str, index: int) -> LiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(str(index))
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=sha256(f"{source}-{index}".encode()).hexdigest(),
        symbol="BTCUSDT",
        liquidated_position_side=LiquidatedPositionSide.LONG,
        occurred_at_ms=EVENT_TIME_MS + index,
        received_at_ms=EVENT_TIME_MS + index + 25,
        price=price,
        quantity=quantity,
        notional_usd=price * quantity,
        raw_side="Sell",
    )


def _stats(event: LiquidationEvent) -> dict[str, object]:
    return {
        "configured": True,
        "connected": False,
        "last_event_at_ms": event.occurred_at_ms,
        "last_event_received_at_ms": event.received_at_ms,
        "last_heartbeat_at_ms": EVENT_TIME_MS + 1_000,
        "ingest_lag_ms": event.ingest_latency_ms,
        "reconnect_count": 0,
        "observed_symbol_count": 1,
        "subscription_symbol_count": 1,
        "events_written": 1,
        "error_count": 0,
        "parse_error_count": 0,
        "latest_error": None,
    }


def _write_closed_run(
    root: Path,
    *,
    completion_reason: str,
    summary_run_state: str,
    summary_run_id: str = RUN_ID,
) -> Path:
    run_root = root / RUN_ID
    run_root.mkdir()
    source_states: dict[str, object] = {}
    for index, source in enumerate(("binance-usdm", "bybit-linear"), start=1):
        event = _event(source, index)
        (run_root / f"{source}.ndjson").write_text(
            json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stats = _stats(event)
        source_states[source] = stats
        _write_json(
            run_root / f"{source}-summary.json",
            {
                "schema_version": 1,
                "source": {"id": source},
                "run_id": summary_run_id,
                "run_state": summary_run_state,
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
            "collector_started_at_ms": EVENT_TIME_MS - 10_000,
            "collector_heartbeat_at_ms": EVENT_TIME_MS + 1_000,
            "last_event_at_ms": EVENT_TIME_MS + 2,
            "last_event_received_at_ms": EVENT_TIME_MS + 27,
            "completed_at_ms": EVENT_TIME_MS + 2_000,
            "completion_reason": completion_reason,
            "collector_commit": "a" * 40,
            "host_id": "synology-test",
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "sources": source_states,
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


def test_accepts_exact_legacy_collector_restart_summary_state(tmp_path: Path) -> None:
    run_root = _write_closed_run(
        tmp_path,
        completion_reason="collector-restart",
        summary_run_state="active",
    )
    output_root = tmp_path / "accepted"

    accept_closed_live_run(run_root=run_root, output_root=output_root, request=_request())
    bundle = load_accepted_import(output_root)
    provenance = json.loads((output_root / "source-run.json").read_text(encoding="utf-8"))

    assert bundle.selection.accepted_records == 2
    assert provenance["completion_reason"] == "collector-restart"
    assert all(source["summary_run_state"] == "active" for source in provenance["sources"])
    assert all(source["legacy_restart_state_accepted"] for source in provenance["sources"])


def test_rejects_active_summary_outside_collector_restart(tmp_path: Path) -> None:
    run_root = _write_closed_run(
        tmp_path,
        completion_reason="daily-rotation",
        summary_run_state="active",
    )

    with pytest.raises(ValueError, match="source summary run state mismatch"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )


def test_rejects_restart_summary_with_wrong_run_id(tmp_path: Path) -> None:
    run_root = _write_closed_run(
        tmp_path,
        completion_reason="collector-restart",
        summary_run_state="active",
        summary_run_id="liquid20-20260726T000000Z-0",
    )

    with pytest.raises(ValueError, match="source summary run state mismatch"):
        accept_closed_live_run(
            run_root=run_root,
            output_root=tmp_path / "accepted",
            request=_request(),
        )
