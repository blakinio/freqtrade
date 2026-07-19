#!/usr/bin/env python3
"""Run isolated Phase 5.2 exit-threshold optimization."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts import run_optimization as base
from ai_platform.scripts.run_experiment import REPO_ROOT, ExperimentError, write_json

EXPECTED_TRAINING = "20251201-20260228"
EXPECTED_TUNING = "20260301-20260430"
CONSUMED_HOLDOUT = "20260501-20260630"
FROZEN_ENTRY = 0.006
FINAL_EVIDENCE = (
    REPO_ROOT / "ai_platform/validation/evidence/freqai-baseline-final-holdout-v1.json"
)
BASE_VALIDATION = "ai_platform/validation/baseline-validation-v1.json"


class ExitOptimizationError(RuntimeError):
    """Raised when the Phase 5.2 contract is violated."""


def _validate_hyperopt(options: Any) -> None:
    if not isinstance(options, dict):
        raise ExitOptimizationError("hyperopt must be an object")
    if options.get("spaces") != ["sell"]:
        raise ExitOptimizationError("Phase 5.2 may use only the sell Hyperopt space")
    if options.get("loss") != "MultiMetricHyperOptLoss":
        raise ExitOptimizationError("Phase 5.2 must use MultiMetricHyperOptLoss")
    for field in ("epochs", "random_state", "min_trades"):
        if not isinstance(options.get(field), int) or options[field] < 1:
            raise ExitOptimizationError(f"hyperopt.{field} must be a positive integer")
    if not isinstance(options.get("job_workers"), int) or options["job_workers"] < -2:
        raise ExitOptimizationError("hyperopt.job_workers must be an integer >= -2")


def _validate_stability(options: Any) -> None:
    if not isinstance(options, dict):
        raise ExitOptimizationError("parameter_stability must be an object")
    if options.get("parameter") != "exit_prediction_threshold":
        raise ExitOptimizationError("Phase 5.2 may tune only exit_prediction_threshold")
    if options.get("minimum") != -0.02 or options.get("maximum") != 0.01:
        raise ExitOptimizationError("Phase 5.2 exit threshold bounds must remain [-0.02, 0.01]")
    if not isinstance(options.get("step"), (int, float)) or options["step"] <= 0:
        raise ExitOptimizationError("parameter_stability.step must be positive")
    if not isinstance(options.get("maximum_profit_drop"), (int, float)):
        raise ExitOptimizationError("parameter_stability.maximum_profit_drop must be numeric")
    if not isinstance(options.get("maximum_drawdown_increase"), (int, float)):
        raise ExitOptimizationError("parameter_stability.maximum_drawdown_increase must be numeric")
    if not isinstance(options.get("minimum_trade_count_ratio"), (int, float)):
        raise ExitOptimizationError("parameter_stability.minimum_trade_count_ratio must be numeric")


def load_exit_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExitOptimizationError(f"Unable to read exit optimization plan: {exc}") from exc

    required = {
        "schema_version",
        "optimization_id",
        "stage",
        "experiment_manifest",
        "training",
        "tuning",
        "consumed_holdout_reference",
        "future_final_holdout",
        "fixed_parameters",
        "hyperopt",
        "parameter_stability",
        "output_root",
    }
    missing = sorted(required - plan.keys())
    if missing:
        raise ExitOptimizationError(
            f"Exit optimization plan is missing fields: {', '.join(missing)}"
        )
    if plan["schema_version"] != 1 or plan["stage"] != "exit_thresholds":
        raise ExitOptimizationError("Unsupported Phase 5.2 plan")
    if plan["training"]["timerange"] != EXPECTED_TRAINING:
        raise ExitOptimizationError("Phase 5.2 training context drifted")
    if plan["tuning"]["timerange"] != EXPECTED_TUNING:
        raise ExitOptimizationError("Phase 5.2 tuning window drifted")
    if plan["consumed_holdout_reference"]["timerange"] != CONSUMED_HOLDOUT:
        raise ExitOptimizationError("Consumed holdout reference drifted")
    if plan["future_final_holdout"] != {
        "status": "pending_new_unseen_window",
        "final_validation_authorized": False,
    }:
        raise ExitOptimizationError("A new unseen final holdout is not yet authorized")
    if plan["fixed_parameters"] != {"entry_prediction_threshold": FROZEN_ENTRY}:
        raise ExitOptimizationError("entry_prediction_threshold must remain frozen at 0.006")

    _validate_hyperopt(plan["hyperopt"])
    _validate_stability(plan["parameter_stability"])
    return {
        **plan,
        "validation_plan": BASE_VALIDATION,
        "final_holdout": plan["consumed_holdout_reference"],
    }


def validate_exit_repository(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    validation_plan: dict[str, Any],
    config: dict[str, Any],
) -> None:
    del plan, validation_plan
    if manifest.get("strategy") != "AiPhase52ExitStrategy":
        raise ExitOptimizationError("Phase 5.2 must use AiPhase52ExitStrategy")
    if manifest.get("timerange") != "20260101-20260430":
        raise ExitOptimizationError("Phase 5.2 manifest must exclude the consumed holdout")
    if config.get("dry_run") is not True:
        raise ExitOptimizationError("Phase 5.2 requires the research-only dry-run config")

    evidence = json.loads(FINAL_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("final_holdout", {}).get("used") is not True:
        raise ExitOptimizationError("Phase 5.1 holdout evidence is incomplete")
    if evidence.get("final_holdout", {}).get("timerange") != CONSUMED_HOLDOUT:
        raise ExitOptimizationError("Consumed holdout does not match Phase 5.1 evidence")
    entry = evidence.get("selection", {}).get("selected_parameters", {}).get(
        "entry_prediction_threshold"
    )
    if entry != FROZEN_ENTRY:
        raise ExitOptimizationError("Frozen entry threshold does not match Phase 5.1 evidence")


def write_sell_parameter_file(
    strategy_dir: Path,
    strategy_file: Path,
    strategy_name: str,
    parameter: str,
    value: float,
) -> None:
    strategy_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(strategy_file, strategy_dir / strategy_file.name)
    write_json(
        strategy_dir / f"{strategy_name}.json",
        {
            "strategy_name": strategy_name,
            "params": {"sell": {parameter: value}},
            "ft_stratparam_v": 1,
        },
    )


def exit_selection_identity(
    plan: dict[str, Any],
    *,
    git_commit: str,
    parameter: str,
    value: float,
) -> str:
    git_commit = base._require_git_commit(git_commit)
    semantic = {
        "optimization_id": plan["optimization_id"],
        "git_commit": git_commit,
        "stage": "exit_thresholds",
        "fixed_parameters": plan["fixed_parameters"],
        "parameter": parameter,
        "value": value,
        "training": plan["training"],
        "tuning": plan["tuning"],
        "consumed_holdout_reference": plan["consumed_holdout_reference"],
        "future_final_holdout": plan["future_final_holdout"],
    }
    digest = hashlib.sha256(base._canonical_json(semantic).encode("utf-8")).hexdigest()
    return f"opt-{digest[:12]}"


def materialize_exit_candidate(
    manifest: dict[str, Any],
    validation_plan: dict[str, Any],
    base_config: dict[str, Any],
    strategy_file: Path,
    *,
    selection_id: str,
    parameter: str,
    value: float,
    run_dir: Path,
) -> dict[str, str]:
    del validation_plan
    selected_dir = run_dir / "selected"
    selected_dir.mkdir(parents=True, exist_ok=False)
    strategy_dir = selected_dir / "strategy"
    write_sell_parameter_file(
        strategy_dir,
        strategy_file,
        manifest["strategy"],
        parameter,
        value,
    )

    config = base._derived_config(base_config, selection_id)
    config_path = selected_dir / "config.json"
    write_json(config_path, config)

    manifest_path = selected_dir / "experiment.json"
    selected_manifest = dict(manifest)
    selected_manifest["experiment_id"] = selection_id
    selected_manifest["description"] = (
        "Phase 5.2 exit-threshold selection with entry_prediction_threshold frozen at 0.006. "
        "Final validation awaits a new unseen window."
    )
    selected_manifest["config"] = base._relative_repo_path(config_path)
    selected_manifest["strategy_path"] = base._relative_repo_path(strategy_dir)
    write_json(manifest_path, selected_manifest)
    return {
        "config": base._relative_repo_path(config_path),
        "strategy_path": base._relative_repo_path(strategy_dir),
        "experiment_manifest": base._relative_repo_path(manifest_path),
    }


def _rewrite_result(run_dir: Path, plan: dict[str, Any]) -> None:
    provenance_path = run_dir / "provenance.json"
    selection_path = run_dir / "selection.json"
    report_path = run_dir / "optimization-report.json"

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance.pop("final_holdout", None)
    provenance.pop("final_holdout_used", None)
    provenance.update(
        {
            "fixed_parameters": plan["fixed_parameters"],
            "consumed_holdout_reference": plan["consumed_holdout_reference"],
            "consumed_holdout_used_in_phase52": False,
            "future_final_holdout": plan["future_final_holdout"],
            "final_validation_authorized": False,
        }
    )
    write_json(provenance_path, provenance)

    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection.update(provenance)
    selection["eligible_for_final_validation"] = False
    selection["final_validation_block_reason"] = "pending_new_unseen_window"
    selection["promotion_allowed"] = False
    write_json(selection_path, selection)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.pop("final_holdout_used", None)
    report["consumed_holdout_used_in_phase52"] = False
    report["future_final_holdout"] = plan["future_final_holdout"]
    report["eligible_for_final_validation"] = False
    report["promotion_allowed"] = False
    report["next_step"] = (
        "Preserve this result as research evidence only. Await a newly declared unseen final "
        "holdout; do not reuse 20260501-20260630."
    )
    write_json(report_path, report)


def run_exit_optimization(plan_path: Path, *, freqtrade_bin: str) -> tuple[Path, bool]:
    raw_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    transformed = load_exit_plan(plan_path)

    def load_transformed(_: Path) -> dict[str, Any]:
        return transformed

    original_load = base.load_optimization_plan
    original_validate = base.validate_plan_against_repository
    original_write = base._write_strategy_parameter_file
    original_identity = base.selection_identity
    original_materialize = base._materialize_selected_candidate
    try:
        base.load_optimization_plan = load_transformed
        base.validate_plan_against_repository = validate_exit_repository
        base._write_strategy_parameter_file = write_sell_parameter_file
        base.selection_identity = exit_selection_identity
        base._materialize_selected_candidate = materialize_exit_candidate
        run_dir, stable = base.run_optimization(plan_path, freqtrade_bin=freqtrade_bin)
    finally:
        base.load_optimization_plan = original_load
        base.validate_plan_against_repository = original_validate
        base._write_strategy_parameter_file = original_write
        base.selection_identity = original_identity
        base._materialize_selected_candidate = original_materialize

    _rewrite_result(run_dir, raw_plan)
    return run_dir, stable


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--freqtrade-bin", default="freqtrade")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_dir, stable = run_exit_optimization(args.plan, freqtrade_bin=args.freqtrade_bin)
    except (
        ExitOptimizationError,
        base.OptimizationError,
        ExperimentError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Exit optimization failed: {exc}", file=sys.stderr)
        return 1
    print(run_dir)
    return 0 if stable else 2


if __name__ == "__main__":
    raise SystemExit(main())
