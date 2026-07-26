"""Run the bounded Residual PyTorch P2 data/target audit preflight."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH = REPO_ROOT / "ai_platform/experimental_model_research"
CONTRACT_PATH = RESEARCH / "residual-pytorch-data-target-audit-contract-v1.json"
FOUNDATION_PATH = RESEARCH / "residual-pytorch-research-contract-v1.json"
RUNTIME_PATH = RESEARCH / "residual-pytorch-runtime-smoke-contract-v1.json"
CONFIG_PATH = REPO_ROOT / "ai_platform/configs/freqai-residual-pytorch-research.example.json"
EXPERIMENT_PATH = REPO_ROOT / "ai_platform/experiments/residual-pytorch-research-v1.json"
STRATEGY_PATH = REPO_ROOT / "ai_platform/strategies/AiFrozenCandidateStrategy.py"
OUTCOMES = ["audit_supported", "audit_not_supported", "audit_inconclusive"]


class ResidualDataTargetAuditError(RuntimeError):
    """Raised when P2 boundaries or target semantics drift."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResidualDataTargetAuditError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualDataTargetAuditError(f"Unable to read {path}: {exc}") from exc
    require(isinstance(payload, dict), f"{path} must contain a JSON object")
    return payload


def nested(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for key in path.split("."):
        require(isinstance(value, dict) and key in value, f"Missing contract field: {path}")
        value = value[key]
    return value


def validate_contract(contract: dict[str, Any]) -> None:
    expected = {
        "schema_version": 1,
        "stage": "P2",
        "contract_id": "residual-pytorch-data-target-audit-v1",
        "model": "ResidualPyTorchRegressor",
        "strategy": "AiFrozenCandidateStrategy",
        "outcomes": OUTCOMES,
        "development_window.semantic_start": "2025-12-01T00:00:00Z",
        "development_window.semantic_stop_exclusive": "2026-05-01T00:00:00Z",
        "development_window.freqtrade_timerange": "20251201-20260501",
        "development_window.consumed_historical_oos": "20260501-20260630",
        "development_window.protected_final_holdout": "20260801-20260930",
        "data_geometry.pairs": ["BTC/USDT", "ETH/USDT"],
        "data_geometry.base_timeframe": "15m",
        "data_geometry.include_timeframes": ["15m", "1h", "4h"],
        "data_geometry.indicator_periods_candles": [14, 50],
        "data_geometry.include_shifted_candles": 2,
        "data_geometry.startup_candle_count": 200,
        "data_geometry.shuffle": False,
        "target.column": "&-future_return",
        "target.horizon_candles": 12,
        "target.semantic_formula": "mean(close[t+1:t+13]) / close[t] - 1",
        "target.first_future_offset": 1,
        "target.last_future_offset": 12,
        "target.leading_unavailable_rows": 11,
        "target.trailing_unavailable_rows": 12,
        "current_execution.historical_market_data": False,
        "current_execution.freqai_expanded_feature_matrix": False,
        "current_execution.expected_outcome": "audit_inconclusive",
    }
    for path, value in expected.items():
        require(nested(contract, path) == value, f"Contract drifted: {path}")

    required = nested(contract, "required_audits")
    require(isinstance(required, dict) and bool(required), "Required audits are missing")
    require(all(value is True for value in required.values()), "A required audit was disabled")
    require(bool(nested(contract, "current_execution.inconclusive_reasons")), "Reasons missing")

    authorization = nested(contract, "authorization")
    require(authorization.get("synthetic_target_fixture") is True, "Synthetic fixture disabled")
    forbidden = [
        key
        for key, value in authorization.items()
        if key != "synthetic_target_fixture" and value is not False
    ]
    require(not forbidden, "Forbidden authorization enabled: " + ", ".join(forbidden))


def validate_bindings(contract: dict[str, Any]) -> None:
    for relative in nested(contract, "paths").values():
        require(isinstance(relative, str), "Invalid bound path")
        require((REPO_ROOT / relative).is_file(), f"Missing bound path: {relative}")

    foundation = read_json(FOUNDATION_PATH)
    runtime = read_json(RUNTIME_PATH)
    for payload, label, fields in (
        (foundation, "foundation", ("market_data_access", "training", "backtesting")),
        (runtime, "runtime", ("market_data_access", "backtesting")),
    ):
        authorization = payload.get("authorization", {})
        require(
            all(authorization.get(field) is False for field in fields),
            f"{label} authorization drifted",
        )

    config = read_json(CONFIG_PATH)
    freqai = config.get("freqai", {})
    features = freqai.get("feature_parameters", {})
    split = freqai.get("data_split_parameters", {})
    require(config.get("timeframe") == "15m", "Config timeframe drifted")
    require(
        config.get("exchange", {}).get("pair_whitelist") == ["BTC/USDT", "ETH/USDT"],
        "Config pairs drifted",
    )
    require(features.get("include_timeframes") == ["15m", "1h", "4h"], "Timeframes drifted")
    require(features.get("label_period_candles") == 12, "Label horizon drifted")
    require(features.get("indicator_periods_candles") == [14, 50], "Periods drifted")
    require(features.get("include_shifted_candles") == 2, "Shift count drifted")
    require(split.get("shuffle") is False, "Chronological split drifted")
    require(freqai.get("continual_learning") is False, "Continual learning enabled")

    experiment = read_json(EXPERIMENT_PATH)
    require(experiment.get("target") == "&-future_return", "Experiment target drifted")
    require(
        experiment.get("target_semantics")
        == "future average close over 12 candles divided by current close minus one",
        "Experiment target semantics drifted",
    )
    require(
        all(
            experiment.get(key) is None
            for key in ("execution_timerange", "download_timerange", "run_request")
        ),
        "Experiment execution was enabled",
    )

    strategy = STRATEGY_PATH.read_text(encoding="utf-8")
    markers = (
        'horizon = self.freqai_info["feature_parameters"]["label_period_candles"]',
        'dataframe["close"].shift(-horizon).rolling(horizon).mean()',
        'dataframe["&-future_return"] = future_average_close / dataframe["close"] - 1',
        "entry_prediction_threshold = 0.006",
        "exit_prediction_threshold = -0.009",
    )
    require(all(marker in strategy for marker in markers), "Strategy target or threshold drifted")
    require("liquidation" not in strategy.casefold(), "Liquidation feature entered strategy")


def strategy_target(close: Sequence[float], horizon: int) -> list[float | None]:
    require(horizon > 0, "Horizon must be positive")
    require(len(close) > horizon * 2, "Close series is too short")
    require(all(math.isfinite(value) and value > 0 for value in close), "Invalid close series")

    shifted: list[float | None] = [*close[horizon:], *([None] * horizon)]
    result: list[float | None] = []
    for index, current in enumerate(close):
        start = index - horizon + 1
        window = shifted[start : index + 1] if start >= 0 else []
        if len(window) != horizon or any(value is None for value in window):
            result.append(None)
            continue
        numeric_window = [value for value in window if value is not None]
        result.append(sum(numeric_window) / horizon / current - 1)
    return result


def target_value(value: float | None, message: str) -> float:
    if value is None:
        raise ResidualDataTargetAuditError(message)
    return value


def explicit_target(close: Sequence[float], index: int, horizon: int) -> float:
    future = close[index + 1 : index + horizon + 1]
    require(len(future) == horizon, "Explicit future window is incomplete")
    return sum(future) / horizon / close[index] - 1


def run_synthetic_audit(horizon: int = 12, rows: int = 64) -> dict[str, Any]:
    close = [100 + index * 0.5 for index in range(rows)]
    actual = strategy_target(close, horizon)
    valid = [index for index, value in enumerate(actual) if value is not None]
    require(bool(valid), "No valid synthetic targets")
    errors = [
        abs(
            target_value(actual[index], "Synthetic target unexpectedly missing")
            - explicit_target(close, index, horizon)
        )
        for index in valid
    ]
    leading = valid[0]
    trailing = rows - 1 - valid[-1]
    require((leading, trailing) == (horizon - 1, horizon), "Target edge geometry drifted")
    require(max(errors) <= 1e-15, "Target look-forward alignment drifted")

    probe = valid[len(valid) // 2]
    baseline = target_value(actual[probe], "Probe target unexpectedly missing")
    past = list(close)
    past[probe - 1] *= 1.5
    require(
        math.isclose(
            target_value(strategy_target(past, horizon)[probe], "Past probe target missing"),
            baseline,
            abs_tol=1e-15,
        ),
        "Past close leaked into target numerator",
    )

    influence: dict[str, bool] = {}
    for offset in range(1, horizon + 1):
        changed = list(close)
        changed[probe + offset] *= 1.01
        candidate = target_value(
            strategy_target(changed, horizon)[probe], "Future-offset probe target missing"
        )
        influence[str(offset)] = not math.isclose(candidate, baseline, abs_tol=1e-15)
    require(all(influence.values()), "A declared future offset does not influence target")

    outside = list(close)
    outside[probe + horizon + 1] *= 1.5
    require(
        math.isclose(
            target_value(strategy_target(outside, horizon)[probe], "Outside probe target missing"),
            baseline,
            abs_tol=1e-15,
        ),
        "A close beyond the horizon influenced target",
    )
    return {
        "fixture_rows": rows,
        "horizon_candles": horizon,
        "valid_target_rows": len(valid),
        "leading_unavailable_rows": leading,
        "trailing_unavailable_rows": trailing,
        "max_absolute_alignment_error": max(errors),
        "past_close_influences_target_numerator": False,
        "future_offset_influence": influence,
        "offset_after_horizon_influences_target": False,
    }


def build_report() -> dict[str, Any]:
    contract = read_json(CONTRACT_PATH)
    validate_contract(contract)
    validate_bindings(contract)
    audit = run_synthetic_audit(nested(contract, "target.horizon_candles"))
    return {
        "schema_version": 1,
        "stage": "P2",
        "outcome": "audit_inconclusive",
        "contract_id": contract["contract_id"],
        "development_window": deepcopy(contract["development_window"]),
        "target": {
            "column": nested(contract, "target.column"),
            "semantic_formula": nested(contract, "target.semantic_formula"),
            "synthetic_alignment_supported": True,
            "audit": audit,
        },
        "feature_audit": {
            "freqai_expanded_feature_count": None,
            "nan_distribution": None,
            "outlier_distribution": None,
            "status": "not_measured_without_authorized_historical_feature_matrix",
        },
        "historical_label_distribution": {
            "summary": None,
            "status": "not_measured_without_authorized_market_data",
        },
        "liquidation_features_used": False,
        "market_data_used": False,
        "exchange_download_performed": False,
        "training_performed": False,
        "backtest_performed": False,
        "historical_oos_used": False,
        "protected_holdout_used": False,
        "inconclusive_reasons": list(nested(contract, "current_execution.inconclusive_reasons")),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("residual-pytorch-data-target-audit.json"),
    )
    args = parser.parse_args()
    try:
        report = build_report()
    except (OSError, ResidualDataTargetAuditError, KeyError, TypeError, ValueError) as exc:
        report = {
            "schema_version": 1,
            "stage": "P2",
            "outcome": "audit_not_supported",
            "error": str(exc),
            "market_data_used": False,
            "training_performed": False,
            "backtest_performed": False,
            "historical_oos_used": False,
            "protected_holdout_used": False,
        }
        write_report(args.output, report)
        print(f"Residual data/target audit failed: {exc}", file=sys.stderr)
        return 2
    write_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
