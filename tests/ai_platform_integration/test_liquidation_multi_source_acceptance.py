from __future__ import annotations

import json
from pathlib import Path

from ai_platform.research.liquidations.multi_source_acceptance import (
    DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH,
    MultiSourceAcceptancePolicy,
    evaluate_multi_source_run,
)
from ai_platform.research.liquidations.staging import sha256_file
from ai_platform.scripts.liquidation_multi_source_runner import (
    SOURCE_SEMANTICS,
    _normalize_summary,
    _source_manifest,
)


def _clock(url: str, *, synchronized: bool = True) -> dict[str, object]:
    return {
        "checked_at_ms": 1_750_000_000_000,
        "server_time_url": url,
        "round_trip_ms": 100,
        "absolute_skew_ms": 25,
        "tolerance_ms": 2_000,
        "synchronized": synchronized,
        "error": None,
    }


def _stats(events_by_symbol: dict[str, int]) -> dict[str, object]:
    event_count = sum(events_by_symbol.values())
    return {
        "run_status": "completed_duration",
        "started_at_ms": 1_750_000_000_000,
        "ended_at_ms": 1_750_086_401_000,
        "duration_ms": 86_401_000,
        "connected_duration_ms": 86_401_000,
        "availability_ratio": 1.0,
        "messages_received": event_count + 1,
        "control_messages": 1,
        "liquidation_messages": event_count,
        "events_parsed": event_count,
        "events_written": event_count,
        "duplicates": 0,
        "parse_failures": 0,
        "connections": 1,
        "disconnects": 0,
        "disconnects_per_hour": 0.0,
        "first_message_at_ms": 1_750_000_000_100,
        "last_message_at_ms": 1_750_086_400_900,
        "first_event_at_ms": 1_750_000_000_200,
        "last_event_at_ms": 1_750_086_400_800,
        "events_by_symbol": events_by_symbol,
        "latency": {
            "count": event_count,
            "minimum_ms": 10,
            "maximum_ms": 100,
            "mean_ms": 50.0,
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
                "opened_at_ms": 1_750_000_000_000,
                "closed_at_ms": 1_750_086_401_000,
                "duration_ms": 86_401_000,
                "close_reason": "completed_duration",
                "disconnected": False,
            }
        ],
    }


def _write_source(
    run_root: Path,
    *,
    source_id: str,
    endpoint: str,
    clock_url: str,
    symbols: tuple[str, ...],
    observed: tuple[str, ...],
    count_per_symbol: int,
    commit: str,
) -> tuple[dict[str, object], dict[str, object]]:
    output_name = f"{source_id}.ndjson"
    summary_name = f"{source_id}-summary.json"
    output_path = run_root / output_name
    events_by_symbol = {symbol: count_per_symbol for symbol in observed}
    event_count = sum(events_by_symbol.values())
    output_path.write_text(
        "".join(json.dumps({"event": index}) + "\n" for index in range(event_count)),
        encoding="utf-8",
    )
    stats = _stats(events_by_symbol)
    start_clock = _clock(clock_url)
    summary = {
        "schema_version": 1,
        "summary_type": "liquidation_data_only_staging",
        "execution_enabled": False,
        "trading_credentials_present": False,
        "collector_commit": commit,
        "source": {
            "id": source_id,
            "endpoint": endpoint,
            "symbols": list(symbols),
        },
        "source_semantics": SOURCE_SEMANTICS[source_id],
        "clock_probe": start_clock,
        "output": {
            "file_name": output_name,
            "initial_size_bytes": 0,
            "final_size_bytes": output_path.stat().st_size,
            "sha256": sha256_file(output_path),
            "line_count": event_count,
        },
        "stats": stats,
    }
    (run_root / summary_name).write_text(
        json.dumps(summary),
        encoding="utf-8",
    )
    manifest_source = {
        "endpoint": endpoint,
        "source_semantics": SOURCE_SEMANTICS[source_id],
        "output": output_name,
        "summary": summary_name,
        "collector_status": "completed",
        "collector_error": None,
        "clock_probes": {
            "start": start_clock,
            "end": _clock(clock_url),
        },
        "stats": stats,
    }
    return manifest_source, summary


def _write_run(
    run_root: Path,
    *,
    bybit_observed: tuple[str, ...] | None = None,
    binance_observed: tuple[str, ...] | None = None,
) -> MultiSourceAcceptancePolicy:
    policy = MultiSourceAcceptancePolicy.load(DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH)
    run_root.mkdir()
    symbols = policy.symbols
    bybit_observed = bybit_observed or symbols[:10]
    binance_observed = binance_observed or symbols[5:13]
    commit = "a" * 40
    bybit_policy = next(source for source in policy.sources if source.source_id == "bybit-linear")
    binance_policy = next(source for source in policy.sources if source.source_id == "binance-usdm")
    bybit, _ = _write_source(
        run_root,
        source_id="bybit-linear",
        endpoint=bybit_policy.endpoint,
        clock_url=bybit_policy.clock_endpoint,
        symbols=symbols,
        observed=bybit_observed,
        count_per_symbol=3,
        commit=commit,
    )
    binance, _ = _write_source(
        run_root,
        source_id="binance-usdm",
        endpoint=binance_policy.endpoint,
        clock_url=binance_policy.clock_endpoint,
        symbols=symbols,
        observed=binance_observed,
        count_per_symbol=2,
        commit=commit,
    )
    manifest = {
        "schema_version": 1,
        "manifest_type": policy.manifest_type,
        "run_status": "completed",
        "run_id": "liquid20-20260724T120000Z",
        "host_id": "staging-eu-01",
        "execution_enabled": False,
        "trading_credentials_present": False,
        "collector_commit": commit,
        "started_at_ms": 1_750_000_000_000,
        "ended_at_ms": 1_750_086_401_000,
        "duration_ms": 86_401_000,
        "symbol_profile": {
            "name": policy.profile_name,
            "frozen_at": "2026-07-24",
            "selection_basis": "test fixture",
            "symbol_count": len(symbols),
            "symbols": list(symbols),
        },
        "sources": {
            "bybit-linear": bybit,
            "binance-usdm": binance,
        },
        "cross_source_policy": {
            "deduplicate_between_exchanges": False,
            "sum_events_without_source_labels": False,
        },
    }
    (run_root / "multi-source-manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return policy


def test_policy_declares_prospective_twenty_symbol_acceptance() -> None:
    policy = MultiSourceAcceptancePolicy.load(DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH)

    assert policy.policy_id == "liquid20-multi-source-acceptance-v1"
    assert policy.profile_name == "liquid20-v1"
    assert len(policy.symbols) == 20
    assert policy.minimum_duration_seconds == 86_400
    assert {source.source_id for source in policy.sources} == {
        "bybit-linear",
        "binance-usdm",
    }


def test_complete_multi_source_package_passes(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    policy = _write_run(run_root)

    report = evaluate_multi_source_run(run_root, policy=policy)

    assert report["passed"] is True
    assert report["failed_gates"] == []
    assert len(report["coverage"]["union_observed_symbols"]) == 13
    assert len(report["coverage"]["intersection_observed_symbols"]) == 5


def test_end_clock_failure_is_rejected(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    policy = _write_run(run_root)
    manifest_path = run_root / "multi-source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"]["binance-usdm"]["clock_probes"]["end"]["synchronized"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = evaluate_multi_source_run(run_root, policy=policy)

    assert report["passed"] is False
    assert "binance-usdm.clock_end_synchronized" in report["failed_gates"]


def test_tampered_output_is_rejected(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    policy = _write_run(run_root)
    with (run_root / "bybit-linear.ndjson").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")

    report = evaluate_multi_source_run(run_root, policy=policy)

    assert report["passed"] is False
    assert "bybit-linear.output_hash" in report["failed_gates"]
    assert "bybit-linear.event_line_count" in report["failed_gates"]


def test_union_coverage_gate_is_prospective_and_deterministic(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    policy = MultiSourceAcceptancePolicy.load(DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH)
    _write_run(
        run_root,
        bybit_observed=policy.symbols[:8],
        binance_observed=policy.symbols[:5],
    )

    report = evaluate_multi_source_run(run_root, policy=policy)

    assert report["passed"] is False
    assert "minimum_union_observed_symbols" in report["failed_gates"]
    assert "minimum_intersection_observed_symbols" not in report["failed_gates"]


def test_normalize_summary_replaces_legacy_source_shape(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"source": "binance-usdm"}), encoding="utf-8")

    _normalize_summary(
        summary_path,
        source_id="binance-usdm",
        endpoint="wss://fstream.binance.com/market/ws",
        symbols=("BTCUSDT", "ETHUSDT"),
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["source"] == {
        "id": "binance-usdm",
        "endpoint": "wss://fstream.binance.com/market/ws",
        "symbols": ["BTCUSDT", "ETHUSDT"],
    }
    assert summary["source_semantics"] == SOURCE_SEMANTICS["binance-usdm"]


def test_source_manifest_preserves_failure_evidence(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    output_path = tmp_path / "events.ndjson"

    source = _source_manifest(
        endpoint="wss://example.invalid",
        output_path=output_path,
        summary_path=summary_path,
        start_clock=_clock("https://example.invalid/time"),
        end_clock=_clock("https://example.invalid/time"),
        result=RuntimeError("collector failed"),
        normalization_result=FileNotFoundError("summary missing"),
        source_id="bybit-linear",
    )

    assert source["collector_status"] == "failed"
    assert "collector failed" in str(source["collector_error"])
    assert "summary missing" in str(source["collector_error"])
    assert source["stats"] is None
