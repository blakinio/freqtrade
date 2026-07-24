from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.research.liquidations.staging import (
    ClockProbeResult,
    CollectorRunStats,
    LatencyHistogram,
    StagingPolicy,
    build_collector_summary,
    evaluate_staging_summary,
    parse_bybit_server_time_response,
    sha256_file,
)
from ai_platform.scripts.liquidation_collector import (
    RecentEventIds,
    _prepare_output_path,
    _process_payload,
)


POLICY_PATH = (
    Path(__file__).parents[2]
    / "ai_platform"
    / "research"
    / "liquidations"
    / "data-only-staging-policy-v1.json"
)


def _liquidation_message() -> dict[str, object]:
    return {
        "topic": "allLiquidation.BTCUSDT",
        "type": "snapshot",
        "ts": 1_750_000_000_500,
        "data": [
            {
                "T": 1_750_000_000_000,
                "s": "BTCUSDT",
                "S": "Buy",
                "v": "2",
                "p": "70000",
            }
        ],
    }


def _clock_probe() -> ClockProbeResult:
    return ClockProbeResult(
        checked_at_ms=1_750_000_030_000,
        server_time_url="https://api.bybit.com/v5/market/time",
        round_trip_ms=100,
        absolute_skew_ms=50,
        tolerance_ms=2_000,
        synchronized=True,
    )


def _completed_stats(*, duration_ms: int = 30_000) -> CollectorRunStats:
    stats = CollectorRunStats(started_at_ms=1_750_000_000_000)
    stats.connection_opened(1_750_000_000_000)
    stats.record_message(1_750_000_000_100, message_kind="control")
    stats.connection_closed(
        1_750_000_000_000 + duration_ms,
        reason="completed_duration",
        disconnected=False,
    )
    stats.finish(
        1_750_000_000_000 + duration_ms,
        status="completed_duration",
    )
    return stats


def test_latency_histogram_uses_exclusive_ordered_buckets() -> None:
    histogram = LatencyHistogram()

    for latency_ms in (50, 100, 101, 5_000, 5_001, 20_000):
        histogram.observe(latency_ms)

    payload = histogram.as_json_dict()
    assert payload["count"] == 6
    assert payload["minimum_ms"] == 50
    assert payload["maximum_ms"] == 20_000
    assert payload["buckets"]["le_100_ms"] == 2
    assert payload["buckets"]["le_250_ms"] == 1
    assert payload["buckets"]["le_5000_ms"] == 1
    assert payload["buckets"]["le_10000_ms"] == 1
    assert payload["buckets"]["gt_10000_ms"] == 1


def test_clock_probe_uses_request_midpoint() -> None:
    result = parse_bybit_server_time_response(
        {"result": {"timeSecond": "1750000000"}},
        request_started_at_ms=1_749_999_999_900,
        request_ended_at_ms=1_750_000_000_100,
        tolerance_ms=500,
    )

    assert result.round_trip_ms == 200
    assert result.absolute_skew_ms == 0
    assert result.synchronized is True


def test_process_payload_tracks_events_and_duplicates() -> None:
    stats = CollectorRunStats(started_at_ms=1_750_000_000_000)
    recent_ids = RecentEventIds()

    first = _process_payload(
        _liquidation_message(),
        received_at_ms=1_750_000_000_500,
        recent_ids=recent_ids,
        stats=stats,
    )
    second = _process_payload(
        _liquidation_message(),
        received_at_ms=1_750_000_000_500,
        recent_ids=recent_ids,
        stats=stats,
    )

    assert len(first) == 1
    assert second == ()
    assert stats.messages_received == 2
    assert stats.events_parsed == 2
    assert stats.events_written == 1
    assert stats.duplicates == 1
    assert stats.events_by_symbol == {"BTCUSDT": 2}


def test_process_payload_preserves_control_message_health() -> None:
    stats = CollectorRunStats(started_at_ms=1_750_000_000_000)

    events = _process_payload(
        {"success": True, "op": "subscribe"},
        received_at_ms=1_750_000_000_100,
        recent_ids=RecentEventIds(),
        stats=stats,
    )

    assert events == ()
    assert stats.messages_received == 1
    assert stats.control_messages == 1
    assert stats.parse_failures == 0


def test_require_new_output_rejects_existing_data(tmp_path: Path) -> None:
    output_path = tmp_path / "events.ndjson"
    output_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already contains data"):
        _prepare_output_path(output_path, require_new_output=True)


def test_summary_contains_immutable_output_evidence(tmp_path: Path) -> None:
    output_path = tmp_path / "events.ndjson"
    output_path.write_text("", encoding="utf-8")
    stats = _completed_stats()

    summary = build_collector_summary(
        stats=stats,
        endpoint="wss://stream.bybit.com/v5/public/linear",
        symbols=("BTCUSDT", "ETHUSDT"),
        output_path=output_path,
        output_initial_size_bytes=0,
        collector_commit="a" * 40,
        clock_probe=_clock_probe(),
        trading_credentials_present=False,
    )

    assert summary["execution_enabled"] is False
    assert summary["trading_credentials_present"] is False
    assert summary["output"]["sha256"] == sha256_file(output_path)
    assert summary["output"]["line_count"] == 0


def test_smoke_policy_accepts_connected_empty_event_run(tmp_path: Path) -> None:
    output_path = tmp_path / "events.ndjson"
    output_path.write_text("", encoding="utf-8")
    summary = build_collector_summary(
        stats=_completed_stats(),
        endpoint="wss://stream.bybit.com/v5/public/linear",
        symbols=("BTCUSDT", "ETHUSDT"),
        output_path=output_path,
        output_initial_size_bytes=0,
        collector_commit="b" * 40,
        clock_probe=_clock_probe(),
        trading_credentials_present=False,
    )
    policy = StagingPolicy.load(POLICY_PATH, mode="smoke")

    report = evaluate_staging_summary(summary, policy=policy, mode="smoke")

    assert report["passed"] is True
    assert report["failed_gates"] == []


def test_acceptance_policy_rejects_short_unrepresentative_run(tmp_path: Path) -> None:
    output_path = tmp_path / "events.ndjson"
    output_path.write_text("", encoding="utf-8")
    summary = build_collector_summary(
        stats=_completed_stats(),
        endpoint="wss://stream.bybit.com/v5/public/linear",
        symbols=("BTCUSDT", "ETHUSDT"),
        output_path=output_path,
        output_initial_size_bytes=0,
        collector_commit="c" * 40,
        clock_probe=_clock_probe(),
        trading_credentials_present=False,
    )
    policy = StagingPolicy.load(POLICY_PATH, mode="acceptance")

    report = evaluate_staging_summary(summary, policy=policy, mode="acceptance")

    assert report["passed"] is False
    assert "minimum_duration_seconds" in report["failed_gates"]
    assert "minimum_latency_samples" in report["failed_gates"]
    assert "minimum_events_BTCUSDT" in report["failed_gates"]
    assert "minimum_events_ETHUSDT" in report["failed_gates"]


def test_policy_is_valid_json_and_separates_smoke_from_acceptance() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    assert payload["modes"]["smoke"]["minimum_duration_seconds"] == 20
    assert payload["modes"]["acceptance"]["minimum_duration_seconds"] == 86_400
    assert payload["modes"]["acceptance"]["require_clock_synchronized"] is True
