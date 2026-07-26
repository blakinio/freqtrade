#!/usr/bin/env python3
"""Extract deterministic RL-v2 action-versus-trade observability evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_action_observability import (
    RLV2ActionObservabilityError,
    validate_action_observability_artifacts,
)
from ai_platform.scripts.rl_v2_action_observability_execution_run_request import (
    EXPECTED_CLASSIFICATION,
    EXPECTED_GEOMETRY,
    MODEL_REPO_PATH,
    NEW_SEEDS,
    OBSERVABLE_STRATEGY_REPO_PATH,
    RLV2ActionObservabilityExecutionError,
    _read_json,
    _repo_path,
    _sha256,
    _validate_contract,
    runtime_identifier,
    validate_seed,
)


EXPECTED_STRATEGY = "AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy"
EXPECTED_MODEL = "DesiredPositionReinforcementLearner"
EXPECTED_PAIRS = ("BTC/USDT", "ETH/USDT")
DURATION_BUCKETS = ("under_24h", "24h_to_72h", "over_72h")


class RLV2ActionObservabilityEvidenceError(RuntimeError):
    """Raised when action-versus-trade evidence is malformed or drifts."""


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RLV2ActionObservabilityEvidenceError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RLV2ActionObservabilityEvidenceError(f"{label} must be finite")
    return result


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RLV2ActionObservabilityEvidenceError(f"{label} must be an integer")
    return value


def _binary_sha256(path: Path) -> str:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise RLV2ActionObservabilityEvidenceError(
            f"Unable to hash immutable artifact {path}: {exc}"
        ) from exc
    return hashlib.sha256(content).hexdigest()


def _load_backtest_result(archive: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = sorted(
                name
                for name in bundle.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            )
            if len(names) != 1:
                raise RLV2ActionObservabilityEvidenceError(
                    f"Expected exactly one backtest result JSON, found {len(names)}"
                )
            payload = json.loads(bundle.read(names[0]))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise RLV2ActionObservabilityEvidenceError(
            f"Unable to read raw backtest archive {archive}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2ActionObservabilityEvidenceError("Backtest result root must be an object")
    return payload


def _load_backtest_config(archive: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = sorted(name for name in bundle.namelist() if name.endswith("_config.json"))
            if len(names) != 1:
                raise RLV2ActionObservabilityEvidenceError(
                    f"Expected exactly one backtest config JSON, found {len(names)}"
                )
            payload = json.loads(bundle.read(names[0]))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise RLV2ActionObservabilityEvidenceError(
            f"Unable to read embedded backtest config {archive}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2ActionObservabilityEvidenceError("Embedded backtest config must be an object")
    return payload


def _strategy_result(payload: dict[str, Any]) -> dict[str, Any]:
    strategies = payload.get("strategy")
    if not isinstance(strategies, dict) or set(strategies) != {EXPECTED_STRATEGY}:
        raise RLV2ActionObservabilityEvidenceError(
            "Backtest archive must contain only the observable lifecycle strategy"
        )
    result = strategies[EXPECTED_STRATEGY]
    if not isinstance(result, dict):
        raise RLV2ActionObservabilityEvidenceError("Observable strategy result must be an object")
    return result


def _validate_summary(result: dict[str, Any], seed: int) -> None:
    if result.get("strategy_name") != EXPECTED_STRATEGY:
        raise RLV2ActionObservabilityEvidenceError("Strategy name drifted")
    if result.get("freqaimodel") != EXPECTED_MODEL:
        raise RLV2ActionObservabilityEvidenceError("FreqAI model drifted")
    if result.get("freqai_identifier") != runtime_identifier(seed):
        raise RLV2ActionObservabilityEvidenceError("Runtime identifier drifted")
    if result.get("ignore_roi_if_entry_signal") is not True:
        raise RLV2ActionObservabilityEvidenceError("Lifecycle-alignment behavior drifted")
    if result.get("timerange") != EXPECTED_GEOMETRY["execution_timerange"]:
        raise RLV2ActionObservabilityEvidenceError("Execution timerange drifted")
    if result.get("timeframe") != "15m":
        raise RLV2ActionObservabilityEvidenceError("Base timeframe drifted")
    if result.get("trading_mode") != "spot":
        raise RLV2ActionObservabilityEvidenceError("Trading mode drifted")
    if result.get("trade_count_short") not in (0, None):
        raise RLV2ActionObservabilityEvidenceError("Short trades are forbidden")
    if result.get("minimal_roi") != {"0": 0.03, "240": 0.015, "720": 0.0}:
        raise RLV2ActionObservabilityEvidenceError("ROI schedule drifted")
    if _finite_number(result.get("stoploss"), "stoploss") != -0.05:
        raise RLV2ActionObservabilityEvidenceError("Hard stop-loss drifted")
    if result.get("use_exit_signal") is not True:
        raise RLV2ActionObservabilityEvidenceError("Exit-signal behavior drifted")


def _fee_amount(trade: dict[str, Any], side: str) -> float:
    amount = _finite_number(trade.get("amount"), "trade amount")
    rate = _finite_number(trade.get(f"{side}_rate"), f"{side} rate")
    fee = _finite_number(trade.get(f"fee_{side}"), f"{side} fee")
    if amount < 0 or rate < 0 or fee < 0:
        raise RLV2ActionObservabilityEvidenceError(
            "Trade amount, rate and fees must be non-negative"
        )
    return amount * rate * fee


def _validated_trades(result: dict[str, Any]) -> list[dict[str, Any]]:
    trades = result.get("trades")
    if not isinstance(trades, list):
        raise RLV2ActionObservabilityEvidenceError("Trades must be a list")
    validated: list[dict[str, Any]] = []
    for index, trade in enumerate(trades):
        if not isinstance(trade, dict):
            raise RLV2ActionObservabilityEvidenceError(f"Trade {index} must be an object")
        if trade.get("pair") not in EXPECTED_PAIRS:
            raise RLV2ActionObservabilityEvidenceError(f"Trade {index} pair drifted")
        if trade.get("is_short") is not False:
            raise RLV2ActionObservabilityEvidenceError(f"Trade {index} violates long-only scope")
        open_ts = _integer(
            trade.get("open_timestamp"),
            f"trade {index} open_timestamp",
        )
        close_ts = _integer(
            trade.get("close_timestamp"),
            f"trade {index} close_timestamp",
        )
        if close_ts < open_ts:
            raise RLV2ActionObservabilityEvidenceError(f"Trade {index} closes before it opens")
        amount = _finite_number(trade.get("amount"), f"trade {index} amount")
        open_rate = _finite_number(
            trade.get("open_rate"),
            f"trade {index} open_rate",
        )
        close_rate = _finite_number(
            trade.get("close_rate"),
            f"trade {index} close_rate",
        )
        gross = amount * (close_rate - open_rate)
        fees = _fee_amount(trade, "open") + _fee_amount(trade, "close")
        net = _finite_number(
            trade.get("profit_abs"),
            f"trade {index} profit_abs",
        )
        if not math.isclose(gross - fees, net, rel_tol=1e-8, abs_tol=1e-6):
            raise RLV2ActionObservabilityEvidenceError(
                f"Trade {index} accounting does not reconcile"
            )
        if not isinstance(trade.get("exit_reason"), str):
            raise RLV2ActionObservabilityEvidenceError(f"Trade {index} exit_reason is missing")
        validated.append(trade)
    if _integer(result.get("total_trades"), "total_trades") != len(validated):
        raise RLV2ActionObservabilityEvidenceError("Trade count does not reconcile")
    return validated


def _normalize_embedded_config(
    embedded: dict[str, Any],
    expected: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    embedded = deepcopy(embedded)
    expected = deepcopy(expected)
    embedded.pop("config_files", None)
    expected.pop("config_files", None)
    embedded_exchange = embedded.get("exchange")
    expected_exchange = expected.get("exchange")
    if not isinstance(embedded_exchange, dict) or not isinstance(expected_exchange, dict):
        raise RLV2ActionObservabilityEvidenceError("Embedded exchange configuration is missing")
    for field in ("key", "secret"):
        if embedded_exchange.get(field) not in (None, "", "REDACTED"):
            raise RLV2ActionObservabilityEvidenceError(f"Unexpected embedded exchange {field}")
        embedded_exchange[field] = expected_exchange.get(field, "")
    return embedded, expected


def _validate_runtime_config(
    archive: Path,
    runtime_config_path: Path,
    seed: int,
) -> tuple[dict[str, Any], str]:
    contract, _, base_config = _validate_contract()
    actual = _read_json(runtime_config_path.resolve(), "effective runtime config")
    expected = deepcopy(base_config)
    expected["strategy"] = contract["runtime_binding"]["observable_strategy"]
    freqai = expected.setdefault("freqai", {})
    freqai["identifier"] = runtime_identifier(seed)
    freqai["train_period_days"] = EXPECTED_GEOMETRY["train_period_days"]
    freqai["backtest_period_days"] = EXPECTED_GEOMETRY["backtest_period_days"]
    freqai.setdefault("model_training_parameters", {})["seed"] = seed
    if actual != expected:
        raise RLV2ActionObservabilityEvidenceError(
            f"Effective runtime config drifted for seed {seed}"
        )
    embedded, normalized_expected = _normalize_embedded_config(
        _load_backtest_config(archive),
        expected,
    )
    if embedded != normalized_expected:
        raise RLV2ActionObservabilityEvidenceError(
            f"Embedded runtime config drifted for seed {seed}"
        )
    return actual, _sha256(runtime_config_path.resolve())


def _timestamp_ms(value: str) -> int:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RLV2ActionObservabilityEvidenceError(f"Invalid telemetry timestamp: {value}") from exc
    return int(parsed.timestamp() * 1000)


def _trades_by_pair(
    trades: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(trade["pair"])].append(trade)
    for pair in grouped:
        grouped[pair].sort(key=lambda trade: int(trade["open_timestamp"]))
    return grouped


def _active_trade(
    pair_trades: list[dict[str, Any]],
    timestamp_ms: int,
) -> dict[str, Any] | None:
    active = [
        trade
        for trade in pair_trades
        if int(trade["open_timestamp"]) <= timestamp_ms < int(trade["close_timestamp"])
    ]
    if len(active) > 1:
        raise RLV2ActionObservabilityEvidenceError(
            "Overlapping same-pair long trades are ambiguous"
        )
    return active[0] if active else None


def _transition(position_long: bool, row: dict[str, Any]) -> str:
    if not row["prediction_accepted"]:
        return "hold_long" if position_long else "hold_flat"
    if position_long:
        return "hold_long" if row["action_label"] == "target_long" else "exit_long"
    return "enter_long" if row["action_label"] == "target_long" else "hold_flat"


def _duration_bucket(trade: dict[str, Any]) -> str:
    duration_ms = int(trade["close_timestamp"]) - int(trade["open_timestamp"])
    if duration_ms < 24 * 60 * 60 * 1000:
        return "under_24h"
    if duration_ms <= 72 * 60 * 60 * 1000:
        return "24h_to_72h"
    return "over_72h"


def _maximum_accepted_streaks(rows: list[dict[str, Any]]) -> dict[str, int]:
    maxima = {"target_flat": 0, "target_long": 0}
    current_label: str | None = None
    current_length = 0
    for row in rows:
        label = str(row["action_label"]) if row["prediction_accepted"] else None
        if label is None:
            current_label = None
            current_length = 0
            continue
        if label == current_label:
            current_length += 1
        else:
            current_label = label
            current_length = 1
        maxima[label] = max(maxima[label], current_length)
    return maxima


def analyze_rows_and_trades(
    rows: list[dict[str, Any]],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive deterministic position and transition classes from immutable inputs."""
    grouped_trades = _trades_by_pair(trades)
    transition_counts: Counter[str] = Counter()
    long_state_counts: Counter[str] = Counter()
    duration_conditioned = {
        bucket: {
            "rows": 0,
            "accepted_target_long": 0,
            "accepted_target_flat": 0,
            "rejected_target_long": 0,
            "rejected_target_flat": 0,
        }
        for bucket in DURATION_BUCKETS
    }
    pair_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    position_rows = {"flat": 0, "long": 0}

    for row in rows:
        pair = str(row["pair"])
        pair_rows[pair].append(row)
        trade = _active_trade(grouped_trades.get(pair, []), _timestamp_ms(row["timestamp_utc"]))
        position_long = trade is not None
        position_rows["long" if position_long else "flat"] += 1
        transition_counts[_transition(position_long, row)] += 1
        gate = "accepted" if row["prediction_accepted"] else "rejected"
        action = str(row["action_label"])
        state_key = f"{gate}_{action}"
        if position_long:
            long_state_counts[state_key] += 1
            bucket = _duration_bucket(trade)
            duration_conditioned[bucket]["rows"] += 1
            duration_conditioned[bucket][state_key] += 1

    pair_streaks = {
        pair: _maximum_accepted_streaks(sorted(values, key=lambda row: row["timestamp_utc"]))
        for pair, values in sorted(pair_rows.items())
    }
    return {
        "position_rows": position_rows,
        "transition_counts": {
            label: transition_counts[label]
            for label in ("hold_flat", "enter_long", "hold_long", "exit_long")
        },
        "long_state_action_gate_counts": {
            label: long_state_counts[label]
            for label in (
                "accepted_target_long",
                "accepted_target_flat",
                "rejected_target_long",
                "rejected_target_flat",
            )
        },
        "trade_duration_conditioned_long_rows": duration_conditioned,
        "maximum_accepted_action_streaks_by_pair": pair_streaks,
    }


def _trade_metrics(
    trades: list[dict[str, Any]],
    result: dict[str, Any],
) -> dict[str, Any]:
    fees = 0.0
    gross = 0.0
    net = 0.0
    durations: list[float] = []
    exits: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    for trade in trades:
        amount = float(trade["amount"])
        gross += amount * (float(trade["close_rate"]) - float(trade["open_rate"]))
        fees += _fee_amount(trade, "open") + _fee_amount(trade, "close")
        net += float(trade["profit_abs"])
        durations.append((int(trade["close_timestamp"]) - int(trade["open_timestamp"])) / 60000)
        exits[str(trade["exit_reason"])] += 1
        pair_counts[str(trade["pair"])] += 1
    return {
        "trade_count": len(trades),
        "pair_trade_counts": {pair: pair_counts[pair] for pair in EXPECTED_PAIRS},
        "median_duration_minutes": (round(statistics.median(durations), 6) if durations else None),
        "gross_price_pnl_usdt": round(gross, 6),
        "fees_usdt": round(fees, 6),
        "net_profit_usdt": round(net, 6),
        "profit_factor": round(
            _finite_number(result.get("profit_factor"), "profit_factor"),
            6,
        ),
        "max_drawdown_abs": round(
            _finite_number(result.get("max_drawdown_abs"), "max_drawdown_abs"),
            6,
        ),
        "exit_counts": dict(sorted(exits.items())),
    }


def extract_seed_evidence(
    archive: Path,
    telemetry_dir: Path,
    runtime_config: Path,
    seed: int,
) -> dict[str, Any]:
    """Validate and extract one declared fresh seed."""
    validate_seed(seed)
    contract, _, _ = _validate_contract()
    _, runtime_config_sha256 = _validate_runtime_config(
        archive,
        runtime_config,
        seed,
    )
    telemetry = validate_action_observability_artifacts(telemetry_dir)
    manifest = telemetry["manifest"]
    if manifest["strategy_name"] != EXPECTED_STRATEGY:
        raise RLV2ActionObservabilityEvidenceError("Telemetry strategy name drifted")
    if manifest["strategy_sha256"] != _sha256(_repo_path(OBSERVABLE_STRATEGY_REPO_PATH)):
        raise RLV2ActionObservabilityEvidenceError("Telemetry strategy hash drifted")
    if manifest["freqai_model"] != EXPECTED_MODEL:
        raise RLV2ActionObservabilityEvidenceError("Telemetry model drifted")
    if manifest["freqai_model_sha256"] != _sha256(_repo_path(MODEL_REPO_PATH)):
        raise RLV2ActionObservabilityEvidenceError("Telemetry model hash drifted")
    if manifest["config_sha256"] != runtime_config_sha256:
        raise RLV2ActionObservabilityEvidenceError("Telemetry config hash drifted")
    if manifest["freqai_identifier"] != runtime_identifier(seed):
        raise RLV2ActionObservabilityEvidenceError("Telemetry identifier drifted")
    if manifest["seed"] != seed:
        raise RLV2ActionObservabilityEvidenceError("Telemetry seed drifted")
    if manifest["timerange"] != EXPECTED_GEOMETRY["execution_timerange"]:
        raise RLV2ActionObservabilityEvidenceError("Telemetry timerange drifted")
    if manifest["timeframe"] != "15m":
        raise RLV2ActionObservabilityEvidenceError("Telemetry timeframe drifted")
    if manifest["pairs"] != list(EXPECTED_PAIRS):
        raise RLV2ActionObservabilityEvidenceError("Telemetry pair set drifted")

    result = _strategy_result(_load_backtest_result(archive))
    _validate_summary(result, seed)
    trades = _validated_trades(result)
    derived = analyze_rows_and_trades(telemetry["rows"], trades)
    return {
        "schema_version": 1,
        "evidence_id": f"rl-v2-action-observability-v1-seed-{seed}",
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_decision": False,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "seed": seed,
        "runtime_identifier": runtime_identifier(seed),
        "strategy": EXPECTED_STRATEGY,
        "strategy_sha256": contract["runtime_binding"].get(
            "observable_strategy_sha256",
            manifest["strategy_sha256"],
        ),
        "freqai_model": EXPECTED_MODEL,
        "freqai_model_sha256": manifest["freqai_model_sha256"],
        "runtime_config_sha256": runtime_config_sha256,
        "timeline_sha256": manifest["timeline_sha256"],
        "timeline_row_count": manifest["row_count"],
        "execution_timerange": EXPECTED_GEOMETRY["execution_timerange"],
        "semantic_evidence_window": EXPECTED_GEOMETRY["semantic_evidence_window"],
        "action_summary": telemetry["summary"],
        "derived_position_action_evidence": derived,
        "descriptive_trade_metrics": _trade_metrics(trades, result),
        "raw_backtest_sha256": _binary_sha256(archive.resolve()),
        "prior_seed_rerun": False,
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "phase6_authoritative_selected_model": None,
    }


def _load_seed_evidence(path: Path) -> dict[str, Any]:
    payload = _read_json(path.resolve(), "per-seed action evidence")
    if payload.get("classification") != EXPECTED_CLASSIFICATION:
        raise RLV2ActionObservabilityEvidenceError(f"Evidence classification drifted: {path}")
    if payload.get("automatic_decision") is not False:
        raise RLV2ActionObservabilityEvidenceError(f"Automatic decision is forbidden: {path}")
    return payload


def aggregate_seed_evidence(paths: list[Path]) -> dict[str, Any]:
    """Aggregate exactly four fresh seeds without producing a decision."""
    if len(paths) != len(NEW_SEEDS):
        raise RLV2ActionObservabilityEvidenceError(
            f"Expected exactly four seed evidence files, got {len(paths)}"
        )
    by_seed: dict[int, dict[str, Any]] = {}
    for path in paths:
        payload = _load_seed_evidence(path)
        seed = _integer(payload.get("seed"), "seed")
        validate_seed(seed)
        if seed in by_seed:
            raise RLV2ActionObservabilityEvidenceError(f"Duplicate seed evidence: {seed}")
        by_seed[seed] = payload
    if set(by_seed) != set(NEW_SEEDS):
        raise RLV2ActionObservabilityEvidenceError(
            "Aggregate seed set does not match the declaration"
        )

    transition_totals: Counter[str] = Counter()
    long_state_totals: Counter[str] = Counter()
    action_totals: Counter[str] = Counter()
    gate_totals: Counter[str] = Counter()
    trade_counts: list[int] = []
    duration_medians: list[float] = []
    per_seed: list[dict[str, Any]] = []
    for seed in NEW_SEEDS:
        payload = by_seed[seed]
        derived = payload["derived_position_action_evidence"]
        transition_totals.update(derived["transition_counts"])
        long_state_totals.update(derived["long_state_action_gate_counts"])
        totals = payload["action_summary"]["totals"]
        action_totals.update(totals["actions"])
        gate_totals.update(totals["do_predict"])
        metrics = payload["descriptive_trade_metrics"]
        trade_counts.append(int(metrics["trade_count"]))
        if metrics["median_duration_minutes"] is not None:
            duration_medians.append(float(metrics["median_duration_minutes"]))
        per_seed.append(
            {
                "seed": seed,
                "timeline_row_count": payload["timeline_row_count"],
                "timeline_sha256": payload["timeline_sha256"],
                "trade_count": metrics["trade_count"],
                "median_duration_minutes": metrics["median_duration_minutes"],
                "transition_counts": derived["transition_counts"],
                "long_state_action_gate_counts": (derived["long_state_action_gate_counts"]),
            }
        )

    return {
        "schema_version": 1,
        "evidence_id": "rl-v2-action-observability-fresh-v1-aggregate",
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_decision": False,
        "decision": None,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "ordered_seeds": list(NEW_SEEDS),
        "seed_count": len(NEW_SEEDS),
        "per_seed": per_seed,
        "aggregate_action_counts": {
            label: action_totals[label] for label in ("target_flat", "target_long")
        },
        "aggregate_prediction_gate_counts": {
            label: gate_totals[label] for label in ("accepted", "rejected")
        },
        "aggregate_transition_counts": {
            label: transition_totals[label]
            for label in ("hold_flat", "enter_long", "hold_long", "exit_long")
        },
        "aggregate_long_state_action_gate_counts": {
            label: long_state_totals[label]
            for label in (
                "accepted_target_long",
                "accepted_target_flat",
                "rejected_target_long",
                "rejected_target_flat",
            )
        },
        "descriptive_cross_seed_metrics": {
            "median_trade_count": statistics.median(trade_counts),
            "median_of_seed_median_duration_minutes": (
                round(statistics.median(duration_medians), 6) if duration_medians else None
            ),
        },
        "old_invalid_seed_causality_claim_allowed": False,
        "prior_seed_rerun": False,
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "phase6_authoritative_selected_model": None,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    extract = subcommands.add_parser("extract")
    extract.add_argument("archive", type=Path)
    extract.add_argument("--telemetry-dir", type=Path, required=True)
    extract.add_argument("--runtime-config", type=Path, required=True)
    extract.add_argument("--seed", type=int, required=True)
    extract.add_argument("--output", type=Path, required=True)
    aggregate = subcommands.add_parser("aggregate")
    aggregate.add_argument("evidence", nargs="+", type=Path)
    aggregate.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.command == "extract":
            payload = extract_seed_evidence(
                args.archive,
                args.telemetry_dir,
                args.runtime_config,
                args.seed,
            )
        else:
            payload = aggregate_seed_evidence(args.evidence)
        _write_json(args.output, payload)
        return 0
    except (
        RLV2ActionObservabilityEvidenceError,
        RLV2ActionObservabilityExecutionError,
        RLV2ActionObservabilityError,
    ) as exc:
        print(f"RL-v2 action-observability evidence failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
