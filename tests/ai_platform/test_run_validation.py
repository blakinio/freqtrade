import csv
import json
from pathlib import Path

from ai_platform.scripts.run_experiment import load_manifest
from ai_platform.scripts.run_validation import (
    build_lookahead_command,
    build_recursive_command,
    evaluate_performance_gates,
    load_validation_plan,
    parse_lookahead_csv,
    parse_recursive_max_abs_variance,
    summarize_backtest_metrics,
)
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "ai_platform" / "validation" / "baseline-validation-v1.json"
SCHEMA_PATH = ROOT / "ai_platform" / "validation" / "schema-v1.json"
MANIFEST_PATH = ROOT / "ai_platform" / "experiments" / "baseline-v1.json"
CONFIG_PATH = ROOT / "ai_platform" / "configs" / "freqai-baseline.example.json"
STRATEGY_PATH = ROOT / "ai_platform" / "strategies"


def test_baseline_validation_plan_matches_schema() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(plan)


def test_load_validation_plan_accepts_baseline() -> None:
    plan = load_validation_plan(PLAN_PATH)

    assert plan["schema_version"] == 1
    assert len(plan["walk_forward_folds"]) == 2
    assert plan["holdout"]["name"].startswith("holdout-")


def test_summarize_backtest_metrics_uses_required_metrics() -> None:
    summary = summarize_backtest_metrics(
        {
            "total_trades": 42,
            "profit_total": 0.12,
            "max_drawdown_account": 0.08,
        }
    )

    assert summary == {"trades": 42, "profit": 0.12, "drawdown": 0.08}


def test_parse_lookahead_csv_ignores_freqai_target_indicators(tmp_path: Path) -> None:
    csv_path = tmp_path / "lookahead.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "filename",
                "strategy",
                "has_bias",
                "total_signals",
                "biased_entry_signals",
                "biased_exit_signals",
                "biased_indicators",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "filename": "AiBaselineStrategy.py",
                "strategy": "AiBaselineStrategy",
                "has_bias": "True",
                "total_signals": "50",
                "biased_entry_signals": "0",
                "biased_exit_signals": "0",
                "biased_indicators": "&-future_return",
            }
        )

    result = parse_lookahead_csv(csv_path, "AiBaselineStrategy")

    assert result["passed"] is True
    assert result["effective_biased_indicators"] == []
    assert result["ignored_freqai_targets"] == ["&-future_return"]


def test_parse_recursive_variance_ignores_freqai_targets() -> None:
    output = """
│ Indicators        │ 199    │ 499    │ 999   │
│ &-future_return   │ 9.000% │ 8.000% │ 7.0%  │
│ %-rsi-period      │ 0.500% │ 0.100% │ 0.0%  │
│ %-ema-period      │ -0.75% │ 0.050% │ -     │
"""

    assert parse_recursive_max_abs_variance(output) == 0.0075


def test_evaluate_performance_gates_can_pass() -> None:
    fold_summaries = [
        {"trades": 20, "profit": 0.04, "drawdown": 0.10},
        {"trades": 18, "profit": -0.01, "drawdown": 0.12},
    ]
    holdout = {"trades": 12, "profit": 0.02, "drawdown": 0.11}
    gates = {
        "minimum_total_trades": 30,
        "minimum_profitable_folds": 1,
        "maximum_fold_drawdown": 0.25,
        "minimum_mean_fold_profit": 0.0,
        "minimum_holdout_trades": 10,
        "minimum_holdout_profit": 0.0,
        "maximum_holdout_drawdown": 0.25,
    }

    results = evaluate_performance_gates(fold_summaries, holdout, gates)

    assert all(result["passed"] for result in results)


def test_validation_command_builders_pin_analysis_inputs(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    plan = load_validation_plan(PLAN_PATH)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    lookahead = build_lookahead_command(
        manifest,
        plan,
        freqtrade_bin="freqtrade",
        config_path=CONFIG_PATH,
        strategy_path=STRATEGY_PATH,
        csv_path=tmp_path / "lookahead.csv",
    )
    recursive = build_recursive_command(
        manifest,
        plan,
        config,
        freqtrade_bin="freqtrade",
        config_path=CONFIG_PATH,
        strategy_path=STRATEGY_PATH,
    )

    assert lookahead[:2] == ["freqtrade", "lookahead-analysis"]
    assert manifest["freqai_model"] in lookahead
    assert "--lookahead-analysis-exportfilename" in lookahead
    assert all(pair in lookahead for pair in manifest["pairs"])

    assert recursive[:2] == ["freqtrade", "recursive-analysis"]
    assert plan["recursive"]["pair"] in recursive
    assert all(str(value) in recursive for value in plan["recursive"]["startup_candles"])
