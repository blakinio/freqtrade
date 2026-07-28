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
from ai_platform.scripts.wickhunter_live_archive_conversion import (
    convert_production_archive,
    select_closed_run,
    verify_operation,
)


SOURCE_SHA = "1" * 40
HOLDOUT_START_MS = 2_000_000_000_000


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _event(*, source: str, occurred_at_ms: int, index: int) -> LiquidationEvent:
    price = Decimal("100")
    quantity = Decimal(str(index))
    return LiquidationEvent(
        schema_version=1,
        source=source,
        source_event_id=sha256(f"{source}-{occurred_at_ms}-{index}".encode()).hexdigest(),
        symbol="BTCUSDT" if index % 2 else "ETHUSDT",
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


def _source_stats(event: LiquidationEvent) -> dict[str, object]:
    return {
        "configured": True,
        "connected": False,
        "last_event_at_ms": event.occurred_at_ms,
        "last_event_received_at_ms": event.received_at_ms,
        "last_heartbeat_at_ms": event.received_at_ms,
        "ingest_lag_ms": event.ingest_latency_ms,
        "reconnect_count": 0,
        "observed_symbol_count": 1,
        "subscription_symbol_count": 2,
        "events_written": 1,
        "error_count": 0,
        "parse_error_count": 0,
        "latest_error": None,
    }


def _write_closed_run(
    runs_root: Path,
    *,
    run_id: str,
    completed_at_ms: int,
    event_seed: int,
    active: bool = False,
) -> Path:
    run_root = runs_root / run_id
    run_root.mkdir()
    source_states: dict[str, object] = {}
    last_event_ms = 0
    for source, offset in (("bybit-linear", 1), ("binance-usdm", 2)):
        event = _event(
            source=source,
            occurred_at_ms=completed_at_ms - 10_000 + offset,
            index=event_seed + offset,
        )
        last_event_ms = max(last_event_ms, event.occurred_at_ms)
        (run_root / f"{source}.ndjson").write_text(
            json.dumps(event.as_json_dict(), separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stats = _source_stats(event)
        source_states[source] = stats
        _write_json(
            run_root / f"{source}-summary.json",
            {
                "schema_version": 1,
                "source": {"id": source},
                "run_id": run_id,
                "run_state": "active" if active else "completed",
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
            "run_id": run_id,
            "run_state": "active" if active else "completed",
            "data_mode": "live" if active else "historical",
            "collector_started_at_ms": completed_at_ms - 100_000,
            "collector_heartbeat_at_ms": completed_at_ms,
            "last_event_at_ms": last_event_ms,
            "last_event_received_at_ms": last_event_ms + 250,
            "completed_at_ms": completed_at_ms,
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


def _write_request(path: Path, *, data_root: Path, output_root: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "wickhunter-production-live-archive-conversion-request-v1",
            "operation_id": "wickhunter-first-production-archive-v1",
            "created_at_utc": "2026-07-28T00:00:00Z",
            "selection_policy": "latest-completed-nonempty-before-holdout",
            "protected_holdout_start_utc": "2033-05-18T03:33:20Z",
            "live_data_root": str(data_root),
            "accepted_state_root": str(output_root),
            "storage_root": "synology:///volume1/docker/freqtrade-liquidations/data/live/runs",
            "execution_enabled": False,
            "trading_authorized": False,
            "trading_credentials_present": False,
            "model_execution_authorized": False,
            "live_capital_authorized": False,
        },
    )


def test_selects_latest_completed_run_and_verifies_wh01(tmp_path: Path) -> None:
    data_root = tmp_path / "liquid20"
    runs_root = data_root / "live" / "runs"
    runs_root.mkdir(parents=True)
    output_root = tmp_path / "accepted-state"
    output_root.mkdir()
    _write_closed_run(
        runs_root,
        run_id="liquid20-20260726T000000Z-0",
        completed_at_ms=1_785_024_100_000,
        event_seed=10,
    )
    selected = _write_closed_run(
        runs_root,
        run_id="liquid20-20260727T000000Z-0",
        completed_at_ms=1_785_110_500_000,
        event_seed=20,
    )
    _write_closed_run(
        runs_root,
        run_id="liquid20-20260728T000000Z-0",
        completed_at_ms=1_785_196_900_000,
        event_seed=30,
        active=True,
    )
    request_path = tmp_path / "request.json"
    _write_request(request_path, data_root=data_root, output_root=output_root)
    contract_path = tmp_path / "contract.md"
    contract_path.write_text("frozen conversion contract\n", encoding="utf-8")

    operation_root = convert_production_archive(
        request_path=request_path,
        source_commit_sha=SOURCE_SHA,
        decision_contract_path=contract_path,
    )
    result = verify_operation(operation_root)
    report = json.loads((operation_root / "report.json").read_text(encoding="utf-8"))

    assert report["selected_run_id"] == selected.name
    assert result["verified"] is True
    assert result["accepted_records"] == 2
    assert result["trading_authorized"] is False
    assert not (operation_root / "accepted" / "events.jsonl").is_symlink()


def test_conversion_is_no_overwrite_and_tamper_evident(tmp_path: Path) -> None:
    data_root = tmp_path / "liquid20"
    runs_root = data_root / "live" / "runs"
    runs_root.mkdir(parents=True)
    output_root = tmp_path / "accepted-state"
    output_root.mkdir()
    _write_closed_run(
        runs_root,
        run_id="liquid20-20260727T000000Z-1",
        completed_at_ms=1_785_110_500_000,
        event_seed=40,
    )
    request_path = tmp_path / "request.json"
    _write_request(request_path, data_root=data_root, output_root=output_root)
    contract_path = tmp_path / "contract.md"
    contract_path.write_text("frozen conversion contract\n", encoding="utf-8")

    operation_root = convert_production_archive(
        request_path=request_path,
        source_commit_sha=SOURCE_SHA,
        decision_contract_path=contract_path,
    )
    with pytest.raises(FileExistsError):
        convert_production_archive(
            request_path=request_path,
            source_commit_sha=SOURCE_SHA,
            decision_contract_path=contract_path,
        )

    report_path = operation_root / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["profitability_claimed"] = True
    _write_json(report_path, report)
    with pytest.raises(ValueError, match="artifact hashes"):
        verify_operation(operation_root)


def test_selection_fails_closed_without_completed_nonempty_run(tmp_path: Path) -> None:
    data_root = tmp_path / "liquid20"
    runs_root = data_root / "live" / "runs"
    runs_root.mkdir(parents=True)
    _write_closed_run(
        runs_root,
        run_id="liquid20-20260728T000000Z-2",
        completed_at_ms=1_785_196_900_000,
        event_seed=50,
        active=True,
    )

    with pytest.raises(ValueError, match="no completed non-empty"):
        select_closed_run(data_root=data_root, holdout_start_ms=HOLDOUT_START_MS)


def test_workflow_is_exact_request_scoped_and_metadata_only() -> None:
    workflow = Path(
        ".github/workflows/wickhunter-production-live-archive-conversion.yml"
    ).read_text(encoding="utf-8")

    assert "production-live-archive-conversion-v1.json" in workflow
    assert "git merge-base" in workflow
    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "--network none" in workflow
    assert "dst=/liquid20-data,readonly" in workflow
    assert "dst=/output,readonly" in workflow
    assert "trading credential environment" in workflow
    upload_section = workflow.split("name: Upload bounded metadata evidence", maxsplit=1)[1]
    assert "events.jsonl" not in upload_section
