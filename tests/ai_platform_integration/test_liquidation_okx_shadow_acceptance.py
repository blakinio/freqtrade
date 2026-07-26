from __future__ import annotations

import json
from pathlib import Path

from ai_platform.research.liquidations.staging import sha256_file, write_json_atomic
from ai_platform.scripts.liquidation_okx_shadow_acceptance import (
    EVENTS_NAME,
    INSTRUMENTS_NAME,
    MANIFEST_NAME,
    REPORT_NAME,
    SUMMARY_NAME,
    OkxShadowAcceptancePolicy,
    _artifact_entry,
    _write_manifest,
    evaluate_run,
    materialize_evidence_package,
    validate_request,
    verify_evidence_package,
)

POLICY_PATH = Path(
    "ai_platform/research/liquidations/"
    "okx-liquidation-shadow-acceptance-policy-v1.json"
)


def _clock(checked_at_ms: int) -> dict[str, object]:
    return {
        "checked_at_ms": checked_at_ms,
        "server_time_url": "https://www.okx.com/api/v5/public/time",
        "round_trip_ms": 20,
        "absolute_skew_ms": 5,
        "tolerance_ms": 2_000,
        "synchronized": True,
        "error": None,
    }


def _event(index: int, symbol: str) -> dict[str, object]:
    if symbol == "BTCUSDT":
        price = "50000"
        quantity = "0.01"
        notional = "500.00"
    else:
        price = "3000"
        quantity = "0.1"
        notional = "300.0"
    occurred_at_ms = 2_000 + index * 1_000
    return {
        "schema_version": 1,
        "source": "okx-usdt-swap",
        "source_event_id": f"event-{index}",
        "symbol": symbol,
        "liquidated_position_side": "long" if index % 2 == 0 else "short",
        "occurred_at_ms": occurred_at_ms,
        "received_at_ms": occurred_at_ms + 100,
        "price": price,
        "quantity": quantity,
        "notional_usd": notional,
        "raw_side": "sell:long" if index % 2 == 0 else "buy:short",
    }


def _prepare_run(
    tmp_path: Path,
    *,
    event_count: int = 10,
) -> tuple[Path, OkxShadowAcceptancePolicy]:
    policy = OkxShadowAcceptancePolicy.load(POLICY_PATH)
    run_root = tmp_path / "run"
    run_root.mkdir()
    events_path = run_root / EVENTS_NAME
    summary_path = run_root / SUMMARY_NAME
    instruments_path = run_root / INSTRUMENTS_NAME

    rows = [
        _event(index, "BTCUSDT" if index % 2 == 0 else "ETHUSDT")
        for index in range(event_count)
    ]
    events_path.write_text(
        "".join(
            json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

    snapshot = {
        "schema_version": 1,
        "snapshot_type": "okx_public_swap_instruments",
        "source": "okx-usdt-swap",
        "fetched_at_ms": 925,
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

    events_by_symbol: dict[str, int] = {}
    for row in rows:
        symbol = str(row["symbol"])
        events_by_symbol[symbol] = events_by_symbol.get(symbol, 0) + 1

    collection_started = 1_000
    collection_ended = collection_started + 86_400_000
    start_clock = _clock(950)
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
                "normalized_quantity": (
                    "base quantity using frozen public ctVal metadata"
                ),
                "status": "shadow_only_not_in_liquid20_v1",
            },
        },
        "clock_probe": start_clock,
        "output": {
            "file_name": EVENTS_NAME,
            "initial_size_bytes": 0,
            "final_size_bytes": events_path.stat().st_size,
            "sha256": sha256_file(events_path),
            "line_count": event_count,
        },
        "stats": {
            "run_status": "completed_duration",
            "started_at_ms": collection_started,
            "ended_at_ms": collection_ended,
            "duration_ms": 86_400_000,
            "connected_duration_ms": 86_400_000,
            "availability_ratio": 1.0,
            "messages_received": max(1, event_count + 1),
            "control_messages": 1,
            "liquidation_messages": event_count,
            "events_parsed": event_count,
            "events_written": event_count,
            "duplicates": 0,
            "parse_failures": 0,
            "connections": 1,
            "disconnects": 0,
            "disconnects_per_hour": 0.0,
            "first_message_at_ms": collection_started + 10,
            "last_message_at_ms": collection_ended - 10,
            "first_event_at_ms": rows[0]["occurred_at_ms"] if rows else None,
            "last_event_at_ms": rows[-1]["occurred_at_ms"] if rows else None,
            "events_by_symbol": events_by_symbol,
            "latency": {
                "count": event_count,
                "minimum_ms": 100 if rows else None,
                "maximum_ms": 100 if rows else None,
                "mean_ms": 100.0 if rows else None,
                "buckets": {
                    "le_100_ms": event_count,
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
                    "opened_at_ms": collection_started,
                    "closed_at_ms": collection_ended,
                    "duration_ms": 86_400_000,
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

    request = {
        "request_id": "okx-shadow-acceptance-20260727-v1",
        "run_id": "okx-shadow-acceptance-20260727-v1",
        "host_id": "synology-okx-staging-01",
        "host_class": policy.required_host_class,
        "duration_seconds": policy.minimum_duration_seconds,
        "durable_storage_uri": "file:///volume1/freqtrade/okx-shadow/run-v1",
    }
    _write_manifest(
        run_root / MANIFEST_NAME,
        request=request,
        collector_commit="1" * 40,
        policy=policy,
        started_at_ms=900,
        ended_at_ms=collection_ended + 100,
        start_clock=start_clock,
        end_clock=_clock(collection_ended + 50),
        status="completed",
        collector_error=None,
        artifacts={
            "events": _artifact_entry(events_path),
            "summary": _artifact_entry(summary_path),
            "instruments": _artifact_entry(instruments_path),
        },
    )
    return run_root, policy


def test_declared_long_run_acceptance_can_be_accepted(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path)

    report = materialize_evidence_package(run_root, policy=policy)
    verification = verify_evidence_package(run_root, policy=policy)

    assert report["outcome"] == "accepted"
    assert report["accepted"] is True
    assert report["failed_gates"] == []
    assert report["performance_research_authorized"] is False
    assert report["liquid20_membership_authorized"] is False
    assert verification["package_valid"] is True
    assert verification["checksum_entries"] == 5


def test_zero_event_healthy_run_is_inconclusive(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path, event_count=0)

    report = evaluate_run(run_root, policy=policy)

    assert report["outcome"] == "inconclusive_insufficient_activity"
    assert report["accepted"] is False
    assert report["non_activity_failed_gates"] == []
    assert "minimum_events_total" in report["activity_failed_gates"]
    assert "minimum_observed_symbols" in report["activity_failed_gates"]
    assert "minimum_latency_samples" in report["activity_failed_gates"]


def test_tampered_event_artifact_is_rejected(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path)
    with (run_root / EVENTS_NAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema_version": 1, "source": "wrong"}) + "\n")

    report = evaluate_run(run_root, policy=policy)

    assert report["outcome"] == "rejected"
    assert "events_sha256" in report["non_activity_failed_gates"]
    assert "maximum_invalid_normalized_events" in report["non_activity_failed_gates"]


def test_package_verifier_detects_report_tampering(tmp_path: Path) -> None:
    run_root, policy = _prepare_run(tmp_path)
    materialize_evidence_package(run_root, policy=policy)
    report_path = run_root / REPORT_NAME
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["orders_submitted"] = 1
    write_json_atomic(report_path, report)

    try:
        verify_evidence_package(run_root, policy=policy)
    except ValueError as exc:
        assert "self-hash" in str(exc)
    else:
        raise AssertionError("tampered report must fail verification")


def test_request_rejects_github_hosted_runner() -> None:
    policy = OkxShadowAcceptancePolicy.load(POLICY_PATH)
    request = {
        "schema_version": 1,
        "request_id": "request",
        "run_id": "okx-shadow-acceptance-20260727-v1",
        "host_id": "synology-okx-staging-01",
        "host_class": policy.required_host_class,
        "github_hosted_runner": True,
        "durable_storage_uri": "file:///volume1/freqtrade/okx-shadow/run-v1",
        "policy_id": policy.policy_id,
        "symbols": list(policy.symbols),
        "duration_seconds": policy.minimum_duration_seconds,
        "execution_enabled": False,
        "performance_research_authorized": False,
        "replay_authorized": False,
        "model_training_authorized": False,
        "orders_submitted": 0,
    }

    try:
        validate_request(request, policy=policy)
    except ValueError as exc:
        assert "github_hosted_runner" in str(exc)
    else:
        raise AssertionError("GitHub-hosted execution must fail")
