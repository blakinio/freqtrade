from __future__ import annotations

import json
from pathlib import Path

from ai_platform.research.liquidations.staging import sha256_file, write_json_atomic
from ai_platform.scripts.liquidation_okx_shadow_smoke import (
    EVENTS_NAME,
    INSTRUMENTS_NAME,
    MANIFEST_NAME,
    SUMMARY_NAME,
    OkxShadowSmokePolicy,
    _artifact_entry,
    _validate_request,
    _write_manifest,
    evaluate_run,
)


POLICY_PATH = Path("ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json")


def _clock() -> dict[str, object]:
    return {
        "checked_at_ms": 1_000,
        "server_time_url": "https://www.okx.com/api/v5/public/time",
        "round_trip_ms": 20,
        "absolute_skew_ms": 5,
        "tolerance_ms": 2_000,
        "synchronized": True,
        "error": None,
    }


def _prepare_run(tmp_path: Path) -> tuple[Path, OkxShadowSmokePolicy]:
    policy = OkxShadowSmokePolicy.load(POLICY_PATH)
    run_root = tmp_path / "run"
    run_root.mkdir()
    events_path = run_root / EVENTS_NAME
    summary_path = run_root / SUMMARY_NAME
    instruments_path = run_root / INSTRUMENTS_NAME
    events_path.write_text("", encoding="utf-8")
    snapshot = {
        "schema_version": 1,
        "snapshot_type": "okx_public_swap_instruments",
        "source": "okx-usdt-swap",
        "fetched_at_ms": 900,
        "endpoint": policy.instruments_endpoint,
        "contracts": [
            {
                "inst_id": "BTC-USDT-SWAP",
                "canonical_symbol": "BTCUSDT",
                "contract_value": "0.01",
                "contract_multiplier": "1",
                "contract_value_currency": "BTC",
                "settle_currency": "USDT",
                "contract_type": "linear",
                "state": "live",
            },
            {
                "inst_id": "ETH-USDT-SWAP",
                "canonical_symbol": "ETHUSDT",
                "contract_value": "0.1",
                "contract_multiplier": "1",
                "contract_value_currency": "ETH",
                "settle_currency": "USDT",
                "contract_type": "linear",
                "state": "live",
            },
        ],
        "normalization_policy": {
            "supported_contract_type": "linear",
            "supported_settle_currency": "USDT",
            "required_contract_multiplier": "1",
            "quantity_formula": "base_quantity = contracts * ctVal",
            "notional_formula": "notional_usd = base_quantity * bankruptcy_price",
        },
    }
    write_json_atomic(instruments_path, snapshot)
    summary = {
        "schema_version": 1,
        "summary_type": "liquidation_data_only_staging",
        "execution_enabled": False,
        "trading_credentials_present": False,
        "collector_commit": "1" * 40,
        "source": {
            "id": "okx-usdt-swap",
            "endpoint": policy.websocket_endpoint,
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "semantics": {
                "stream": "liquidation-orders",
                "subscription_scope": (
                    "all SWAP instruments with local canonical-symbol filtering"
                ),
                "price": "bankruptcy price (bkPx)",
                "raw_quantity": "contract count (sz)",
                "normalized_quantity": ("base quantity using frozen public ctVal metadata"),
                "status": "shadow_only_not_in_liquid20_v1",
            },
        },
        "clock_probe": _clock(),
        "output": {
            "file_name": EVENTS_NAME,
            "initial_size_bytes": 0,
            "final_size_bytes": 0,
            "sha256": sha256_file(events_path),
            "line_count": 0,
        },
        "stats": {
            "run_status": "completed_duration",
            "started_at_ms": 1_000,
            "ended_at_ms": 121_000,
            "duration_ms": 120_000,
            "connected_duration_ms": 120_000,
            "availability_ratio": 1.0,
            "messages_received": 1,
            "control_messages": 1,
            "liquidation_messages": 0,
            "events_parsed": 0,
            "events_written": 0,
            "duplicates": 0,
            "parse_failures": 0,
            "connections": 1,
            "disconnects": 0,
            "disconnects_per_hour": 0.0,
            "first_message_at_ms": 1_010,
            "last_message_at_ms": 1_010,
            "first_event_at_ms": None,
            "last_event_at_ms": None,
            "events_by_symbol": {},
            "latency": {
                "count": 0,
                "minimum_ms": None,
                "maximum_ms": None,
                "mean_ms": None,
                "buckets": {
                    "le_100_ms": 0,
                    "le_250_ms": 0,
                    "le_500_ms": 0,
                    "le_1000_ms": 0,
                    "le_2000_ms": 0,
                    "le_5000_ms": 0,
                    "le_10000_ms": 0,
                    "gt_10000_ms": 0,
                },
            },
            "connection_intervals": [
                {
                    "opened_at_ms": 1_000,
                    "closed_at_ms": 121_000,
                    "duration_ms": 120_000,
                    "close_reason": "completed_duration",
                    "disconnected": False,
                }
            ],
        },
        "instrument_metadata": {
            "file_name": INSTRUMENTS_NAME,
            "endpoint": policy.instruments_endpoint,
            "sha256": sha256_file(instruments_path),
            "contract_count": 2,
        },
    }
    write_json_atomic(summary_path, summary)
    _write_manifest(
        run_root / MANIFEST_NAME,
        request_id="okx-shadow-smoke-20260726-v1",
        run_id="okx-shadow-smoke-20260726-v1",
        host_id="github-hosted-ubuntu-24.04",
        collector_commit="1" * 40,
        policy=policy,
        started_at_ms=900,
        ended_at_ms=121_100,
        start_clock=_clock(),
        end_clock=_clock(),
        status="completed",
        collector_error=None,
        artifacts={
            "events": _artifact_entry(events_path),
            "summary": _artifact_entry(summary_path),
            "instruments": _artifact_entry(instruments_path),
        },
    )
    return run_root, policy


def test_zero_event_transport_smoke_can_pass(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path)

    report = evaluate_run(run_root, policy=policy)

    assert report["passed"] is True
    assert report["failed_gates"] == []
    assert report["performance_research_authorized"] is False
    assert report["orders_submitted"] == 0


def test_tampered_event_artifact_fails_closed(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path)
    (run_root / EVENTS_NAME).write_text(
        json.dumps({"schema_version": 1, "source": "wrong"}) + "\n",
        encoding="utf-8",
    )

    report = evaluate_run(run_root, policy=policy)

    assert report["passed"] is False
    assert "events_sha256" in report["failed_gates"]
    assert "event_records_valid" in report["failed_gates"]


def test_request_must_match_frozen_symbols() -> None:
    policy = OkxShadowSmokePolicy.load(POLICY_PATH)
    request = {
        "schema_version": 1,
        "request_id": "request",
        "run_id": "okx-shadow-smoke-20260726-v1",
        "host_id": "github-hosted-ubuntu-24.04",
        "policy_id": policy.policy_id,
        "symbols": ["ETHUSDT", "BTCUSDT"],
        "duration_seconds": policy.duration_seconds,
        "execution_enabled": False,
        "performance_research_authorized": False,
        "orders_submitted": 0,
    }

    try:
        _validate_request(request, policy=policy)
    except ValueError as exc:
        assert "symbols" in str(exc)
    else:
        raise AssertionError("reordered symbols must fail")
