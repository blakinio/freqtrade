#!/usr/bin/env python3
"""Run staged Phase 5 signal-threshold Hyperopt without touching the final holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_platform.scripts.run_experiment import (
    REPO_ROOT,
    ExperimentError,
    build_backtest_command,
    extract_backtest_metrics,
    find_backtest_archive,
    load_manifest,
    run_logged,
    validate_research_config,
    write_json,
)
from ai_platform.scripts.run_validation import load_validation_plan, summarize_backtest_metrics


ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")
REQUIRED_PLAN_FIELDS = {
    "schema_version",
    "optimization_id",
    "stage",
    "experiment_manifest",
    "validation_plan",
    "training",
    "tuning",
    "final_holdout",
    "hyperopt",
    "parameter_stability",
    "output_root",
}


class OptimizationError(RuntimeError):
    """Raised when optimization would violate the Phase 5 research contract."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _resolve_repo_path(value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise OptimizationError(f"Path escapes repository root: {value}") from exc
    return candidate


def _relative_repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _require_git_commit(value: str) -> str:
    if not GIT_SHA_PATTERN.fullmatch(value):
        raise OptimizationError(
            "Optimization selection requires a full 40-character lowercase Git commit SHA"
        )
    return value


def _parse_timerange(value: Any, label: str) -> tuple[datetime, datetime]:
    if not isinstance(value, str) or not TIMERANGE_PATTERN.fullmatch(value):
        raise OptimizationError(f"{label} must use YYYYMMDD-YYYYMMDD format")
    start_raw, end_raw = value.split("-", maxsplit=1)
    start = datetime.strptime(start_raw, "%Y%m%d").replace(tzinfo=UTC)
    end = datetime.strptime(end_raw, "%Y%m%d").replace(tzinfo=UTC)
    if start > end:
        raise OptimizationError(f"{label} starts after it ends")
    return start, end


def _validate_window(name: str, window: Any) -> tuple[datetime, datetime]:
    if not isinstance(window, dict):
        raise OptimizationError(f"{name} must be an object")
    window_name = window.get("name")
    if not isinstance(window_name, str) or not ID_PATTERN.fullmatch(window_name):
        raise OptimizationError(f"{name}.name contains unsupported characters")
    return _parse_timerange(window.get("timerange"), f"{name}.timerange")


def _validate_hyperopt_options(options: Any) -> None:
    if not isinstance(options, dict):
        raise OptimizationError("hyperopt must be an object")
    if options.get("spaces") != ["buy"]:
        raise OptimizationError("Signal-threshold stage is restricted to the buy Hyperopt space")
    if options.get("loss") != "MultiMetricHyperOptLoss":
        raise OptimizationError("Signal-threshold stage must use MultiMetricHyperOptLoss")
    for field in ("epochs", "random_state", "min_trades"):
        if not isinstance(options.get(field), int) or options[field] < 1:
            raise OptimizationError(f"hyperopt.{field} must be a positive integer")
    if not isinstance(options.get("job_workers"), int) or options["job_workers"] < -2:
        raise OptimizationError("hyperopt.job_workers must be an integer >= -2")


def _validate_stability_options(options: Any) -> None:
    if not isinstance(options, dict):
        raise OptimizationError("parameter_stability must be an object")
    if options.get("parameter") != "entry_prediction_threshold":
        raise OptimizationError("Phase 5.1 may only tune entry_prediction_threshold")
    for field in ("step", "minimum", "maximum", "maximum_profit_drop"):
        if not isinstance(options.get(field), (int, float)):
            raise OptimizationError(f"parameter_stability.{field} must be numeric")
    if options["step"] <= 0 or options["minimum"] >= options["maximum"]:
        raise OptimizationError("Invalid parameter stability range")
    if options["maximum_profit_drop"] < 0:
        raise OptimizationError("maximum_profit_drop cannot be negative")
    drawdown_increase = options.get("maximum_drawdown_increase")
    if not isinstance(drawdown_increase, (int, float)) or not 0 <= drawdown_increase <= 1:
        raise OptimizationError("maximum_drawdown_increase must be between 0 and 1")
    trade_ratio = options.get("minimum_trade_count_ratio")
    if not isinstance(trade_ratio, (int, float)) or not 0 < trade_ratio <= 1:
        raise OptimizationError("minimum_trade_count_ratio must be in (0, 1]")


def load_optimization_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OptimizationError(f"Unable to read optimization plan {path}: {exc}") from exc

    if not isinstance(plan, dict):
        raise OptimizationError("Optimization plan must contain a JSON object")
    missing = sorted(REQUIRED_PLAN_FIELDS - plan.keys())
    if missing:
        raise OptimizationError(f"Optimization plan is missing fields: {', '.join(missing)}")
    if plan["schema_version"] != 1:
        raise OptimizationError("Only optimization schema_version 1 is supported")
    optimization_id = plan["optimization_id"]
    if not isinstance(optimization_id, str) or not ID_PATTERN.fullmatch(optimization_id):
        raise OptimizationError("optimization_id contains unsupported characters")
    if plan["stage"] != "signal_thresholds":
        raise OptimizationError("This runner only supports the signal_thresholds stage")

    _, training_end = _validate_window("training", plan["training"])
    tuning_start, tuning_end = _validate_window("tuning", plan["tuning"])
    holdout_start, _ = _validate_window("final_holdout", plan["final_holdout"])
    if training_end >= tuning_start:
        raise OptimizationError("Training and tuning windows must not overlap")
    if tuning_end >= holdout_start:
        raise OptimizationError("Tuning and final holdout windows must not overlap")

    _validate_hyperopt_options(plan["hyperopt"])
    _validate_stability_options(plan["parameter_stability"])
    return plan


def validate_plan_against_repository(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    validation_plan: dict[str, Any],
    config: dict[str, Any],
) -> None:
    if validation_plan["experiment_manifest"] != plan["experiment_manifest"]:
        raise OptimizationError("Optimization and validation plans must reference the same manifest")
    if plan["final_holdout"] != validation_plan["holdout"]:
        raise OptimizationError("Final holdout must exactly match the frozen validation holdout")

    download_start, download_end = _parse_timerange(
        manifest["download_timerange"], "download_timerange"
    )
    training_start, training_end = _parse_timerange(
        plan["training"]["timerange"], "training.timerange"
    )
    tuning_start, tuning_end = _parse_timerange(
        plan["tuning"]["timerange"], "tuning.timerange"
    )
    _, holdout_end = _parse_timerange(
        plan["final_holdout"]["timerange"], "final_holdout.timerange"
    )
    if training_start < download_start or holdout_end > download_end:
        raise OptimizationError("Optimization windows exceed the manifest download coverage")

    train_period_days = config.get("freqai", {}).get("train_period_days")
    if not isinstance(train_period_days, int) or train_period_days < 1:
        raise OptimizationError("FreqAI train_period_days must be a positive integer")
    training_days = (training_end - training_start).days + 1
    if training_days < train_period_days:
        raise OptimizationError(
            "Training context is shorter than freqai.train_period_days "
            f"({training_days} < {train_period_days})"
        )

    manifest_start, manifest_end = _parse_timerange(manifest["timerange"], "manifest.timerange")
    if tuning_start < manifest_start or tuning_end > manifest_end:
        raise OptimizationError("Tuning window must remain inside the experiment evaluation timerange")


def build_hyperopt_command(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    *,
    freqtrade_bin: str,
    config_path: Path,
    strategy_path: Path,
    user_dir: Path,
) -> list[str]:
    return [
        freqtrade_bin,
        "hyperopt",
        "--config",
        str(config_path),
        "--strategy",
        manifest["strategy"],
        "--strategy-path",
        str(strategy_path),
        "--freqaimodel",
        manifest["freqai_model"],
        "--timerange",
        plan["tuning"]["timerange"],
        "--fee",
        str(manifest["fee"]),
        "--pairs",
        *manifest["pairs"],
        "--spaces",
        *plan["hyperopt"]["spaces"],
        "--epochs",
        str(plan["hyperopt"]["epochs"]),
        "--random-state",
        str(plan["hyperopt"]["random_state"]),
        "--min-trades",
        str(plan["hyperopt"]["min_trades"]),
        "--hyperopt-loss",
        plan["hyperopt"]["loss"],
        "--job-workers",
        str(plan["hyperopt"]["job_workers"]),
        "--userdir",
        str(user_dir),
        "--disable-param-export",
        "--no-color",
    ]


def find_hyperopt_result(user_dir: Path) -> Path:
    results = sorted((user_dir / "hyperopt_results").glob("*.fthypt"))
    if len(results) != 1:
        raise OptimizationError(
            f"Expected exactly one Hyperopt result file, found {len(results)} under {user_dir}"
        )
    return results[0]


def select_best_epoch(path: Path, *, parameter: str, min_trades: int) -> dict[str, Any]:
    epochs: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        epochs.append(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise OptimizationError(f"Unable to read Hyperopt result {path}: {exc}") from exc

    eligible: list[dict[str, Any]] = []
    for epoch in epochs:
        loss = epoch.get("loss")
        params = epoch.get("params_dict")
        metrics = epoch.get("results_metrics")
        if not isinstance(loss, (int, float)) or not math.isfinite(float(loss)):
            continue
        if not isinstance(params, dict) or parameter not in params:
            continue
        if not isinstance(metrics, dict) or metrics.get("total_trades", 0) < min_trades:
            continue
        eligible.append(epoch)

    if not eligible:
        raise OptimizationError("Hyperopt produced no eligible epoch with the required trade count")
    return min(eligible, key=lambda item: float(item["loss"]))


def selection_identity(
    plan: dict[str, Any],
    *,
    git_commit: str,
    parameter: str,
    value: float,
) -> str:
    git_commit = _require_git_commit(git_commit)
    semantic = {
        "optimization_id": plan["optimization_id"],
        "git_commit": git_commit,
        "stage": plan["stage"],
        "parameter": parameter,
        "value": value,
        "training": plan["training"],
        "tuning": plan["tuning"],
        "final_holdout": plan["final_holdout"],
    }
    digest = hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()
    return f"opt-{digest[:12]}"


def generate_local_perturbations(selected: float, stability: dict[str, Any]) -> list[float]:
    minimum = float(stability["minimum"])
    maximum = float(stability["maximum"])
    step = float(stability["step"])
    values = {
        round(selected - step, 12),
        round(selected + step, 12),
    }
    return sorted(value for value in values if minimum <= value <= maximum and value != selected)


def evaluate_parameter_stability(
    baseline: dict[str, float | int],
    perturbations: list[dict[str, Any]],
    stability: dict[str, Any],
) -> dict[str, Any]:
    profit_floor = float(baseline["profit"]) - float(stability["maximum_profit_drop"])
    drawdown_ceiling = float(baseline["drawdown"]) + float(stability["maximum_drawdown_increase"])
    trade_floor = float(baseline["trades"]) * float(stability["minimum_trade_count_ratio"])

    checks: list[dict[str, Any]] = []
    for item in perturbations:
        metrics = item["metrics"]
        passed = (
            float(metrics["profit"]) >= profit_floor
            and float(metrics["drawdown"]) <= drawdown_ceiling
            and float(metrics["trades"]) >= trade_floor
        )
        checks.append(
            {
                **item,
                "passed": passed,
                "limits": {
                    "minimum_profit": profit_floor,
                    "maximum_drawdown": drawdown_ceiling,
                    "minimum_trades": trade_floor,
                },
            }
        )

    return {
        "passed": bool(checks) and all(item["passed"] for item in checks),
        "baseline": baseline,
        "perturbations": checks,
    }


def _derived_config(base_config: dict[str, Any], identifier: str) -> dict[str, Any]:
    config = json.loads(json.dumps(base_config))
    freqai = config.setdefault("freqai", {})
    freqai["identifier"] = identifier[:240]
    return config


def _write_strategy_parameter_file(
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
            "params": {"buy": {parameter: value}},
            "ft_stratparam_v": 1,
        },
    )


def _run_perturbation(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    base_config: dict[str, Any],
    strategy_file: Path,
    *,
    selection_id: str,
    parameter: str,
    value: float,
    run_dir: Path,
    freqtrade_bin: str,
) -> dict[str, Any]:
    token = str(value).replace("-", "m").replace(".", "p")
    perturbation_dir = run_dir / "perturbations" / f"{parameter}-{token}"
    perturbation_dir.mkdir(parents=True, exist_ok=False)
    strategy_dir = perturbation_dir / "strategy"
    _write_strategy_parameter_file(
        strategy_dir,
        strategy_file,
        manifest["strategy"],
        parameter,
        value,
    )

    config = _derived_config(base_config, f"{selection_id}-perturb-{token}")
    config_path = perturbation_dir / "config.json"
    write_json(config_path, config)

    perturbation_manifest = dict(manifest)
    perturbation_manifest["timerange"] = plan["tuning"]["timerange"]
    command = build_backtest_command(
        perturbation_manifest,
        freqtrade_bin=freqtrade_bin,
        config_path=config_path,
        strategy_path=strategy_dir,
        run_dir=perturbation_dir,
    )
    run_logged(command, log_path=perturbation_dir / "backtest.log")
    archive = find_backtest_archive(perturbation_dir)
    metrics = summarize_backtest_metrics(extract_backtest_metrics(archive, manifest["strategy"]))
    return {
        "parameter": parameter,
        "value": value,
        "metrics": metrics,
        "archive": _relative_repo_path(archive),
    }


def _materialize_selected_candidate(
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
    selected_dir = run_dir / "selected"
    selected_dir.mkdir(parents=True, exist_ok=False)
    strategy_dir = selected_dir / "strategy"
    _write_strategy_parameter_file(
        strategy_dir,
        strategy_file,
        manifest["strategy"],
        parameter,
        value,
    )

    config = _derived_config(base_config, selection_id)
    config_path = selected_dir / "config.json"
    write_json(config_path, config)

    manifest_path = selected_dir / "experiment.json"
    selected_manifest = dict(manifest)
    selected_manifest["experiment_id"] = selection_id
    selected_manifest["description"] = (
        f"Phase 5 signal-threshold selection {selection_id}; final holdout remains frozen until "
        "separate final validation."
    )
    selected_manifest["config"] = _relative_repo_path(config_path)
    selected_manifest["strategy_path"] = _relative_repo_path(strategy_dir)
    write_json(manifest_path, selected_manifest)

    selected_validation = json.loads(json.dumps(validation_plan))
    selected_validation["validation_id"] = f"validation-{selection_id}"
    selected_validation["experiment_manifest"] = _relative_repo_path(manifest_path)
    validation_path = selected_dir / "validation.json"
    write_json(validation_path, selected_validation)

    registry_path = selected_dir / "registry.json"
    write_json(
        registry_path,
        {
            "schema_version": 1,
            "definition_id": selection_id,
            "experiment_manifest": _relative_repo_path(manifest_path),
            "strategy_version": "1-phase5-signal-thresholds",
            "feature_set_id": "baseline-price-trend-momentum-volume-v1",
            "feature_set_description": (
                "Baseline feature set with a Phase 5 selected entry prediction threshold."
            ),
            "target_id": "future-average-return-v1",
            "target_description": (
                "Average forward close return over the configured FreqAI "
                "label_period_candles horizon."
            ),
        },
    )

    return {
        "config": _relative_repo_path(config_path),
        "strategy_path": _relative_repo_path(strategy_dir),
        "experiment_manifest": _relative_repo_path(manifest_path),
        "validation_plan": _relative_repo_path(validation_path),
        "registry_definition": _relative_repo_path(registry_path),
    }


def _build_provenance(
    plan: dict[str, Any],
    *,
    run_id: str,
    git_commit: str,
    plan_path: Path,
    manifest_path: Path,
    validation_path: Path,
    config_path: Path,
    strategy_file: Path,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "optimization_id": plan["optimization_id"],
        "run_id": run_id,
        "git_commit": git_commit,
        "plan_sha256": _sha256_file(plan_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "validation_plan_sha256": _sha256_file(validation_path),
        "config_sha256": _sha256_file(config_path),
        "strategy_sha256": _sha256_file(strategy_file),
        "training": plan["training"],
        "tuning": plan["tuning"],
        "final_holdout": plan["final_holdout"],
        "final_holdout_used": False,
    }


def run_optimization(
    plan_path: Path,
    *,
    freqtrade_bin: str,
) -> tuple[Path, bool]:
    plan_path = plan_path.resolve()
    plan = load_optimization_plan(plan_path)
    manifest_path = _resolve_repo_path(plan["experiment_manifest"])
    validation_path = _resolve_repo_path(plan["validation_plan"])
    manifest = load_manifest(manifest_path)
    validation_plan = load_validation_plan(validation_path)
    config_path = _resolve_repo_path(manifest["config"])
    strategy_path = _resolve_repo_path(manifest["strategy_path"])
    strategy_file = strategy_path / f"{manifest['strategy']}.py"
    if not strategy_file.is_file():
        raise OptimizationError(f"Strategy file does not exist: {strategy_file}")
    base_config = validate_research_config(config_path)
    validate_plan_against_repository(plan, manifest, validation_plan, base_config)
    git_commit = _require_git_commit(_git_commit())

    output_root = _resolve_repo_path(plan["output_root"])
    run_id = f"{_utc_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    run_dir = output_root / plan["optimization_id"] / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(plan_path, run_dir / "optimization-plan.json")

    provenance = _build_provenance(
        plan,
        run_id=run_id,
        git_commit=git_commit,
        plan_path=plan_path,
        manifest_path=manifest_path,
        validation_path=validation_path,
        config_path=config_path,
        strategy_file=strategy_file,
    )
    write_json(run_dir / "provenance.json", provenance)

    user_dir = run_dir / "hyperopt-userdata"
    user_dir.mkdir(parents=True, exist_ok=False)
    command = build_hyperopt_command(
        manifest,
        plan,
        freqtrade_bin=freqtrade_bin,
        config_path=config_path,
        strategy_path=strategy_path,
        user_dir=user_dir,
    )
    if plan["final_holdout"]["timerange"] in command:
        raise OptimizationError("Final holdout timerange must never be passed to Hyperopt")
    run_logged(command, log_path=run_dir / "hyperopt.log")

    hyperopt_result = find_hyperopt_result(user_dir)
    stability_config = plan["parameter_stability"]
    parameter = stability_config["parameter"]
    best_epoch = select_best_epoch(
        hyperopt_result,
        parameter=parameter,
        min_trades=plan["hyperopt"]["min_trades"],
    )
    selected_value = float(best_epoch["params_dict"][parameter])
    if not stability_config["minimum"] <= selected_value <= stability_config["maximum"]:
        raise OptimizationError("Selected parameter lies outside the declared stability bounds")

    selection_id = selection_identity(
        plan,
        git_commit=git_commit,
        parameter=parameter,
        value=selected_value,
    )
    baseline_metrics = summarize_backtest_metrics(best_epoch["results_metrics"])
    perturbation_results = [
        _run_perturbation(
            manifest,
            plan,
            base_config,
            strategy_file,
            selection_id=selection_id,
            parameter=parameter,
            value=value,
            run_dir=run_dir,
            freqtrade_bin=freqtrade_bin,
        )
        for value in generate_local_perturbations(selected_value, stability_config)
    ]
    stability_report = evaluate_parameter_stability(
        baseline_metrics,
        perturbation_results,
        stability_config,
    )
    write_json(run_dir / "stability-report.json", stability_report)

    selected_paths = _materialize_selected_candidate(
        manifest,
        validation_plan,
        base_config,
        strategy_file,
        selection_id=selection_id,
        parameter=parameter,
        value=selected_value,
        run_dir=run_dir,
    )
    selection = {
        **provenance,
        "selection_id": selection_id,
        "experiment_id": selection_id,
        "registry_definition_id": selection_id,
        "selected_parameters": {parameter: selected_value},
        "hyperopt_loss": best_epoch["loss"],
        "tuning_metrics": baseline_metrics,
        "hyperopt_result": _relative_repo_path(hyperopt_result),
        "stability_passed": stability_report["passed"],
        "eligible_for_final_validation": stability_report["passed"],
        "promotion_allowed": False,
        "selected_artifacts": selected_paths,
    }
    write_json(run_dir / "selection.json", selection)

    report = {
        "schema_version": 1,
        "optimization_id": plan["optimization_id"],
        "run_id": run_id,
        "selection_id": selection_id,
        "status": "selected_stable" if stability_report["passed"] else "rejected_unstable",
        "final_holdout_used": False,
        "promotion_allowed": False,
        "eligible_for_final_validation": stability_report["passed"],
        "selection_path": _relative_repo_path(run_dir / "selection.json"),
        "stability_report_path": _relative_repo_path(run_dir / "stability-report.json"),
        "next_step": (
            "Run the materialized selected validation plan exactly once for final evaluation, then "
            "register the resulting experiment and validation evidence. Do not retune on holdout "
            "results."
        ),
        "finished_at": _iso_utc(_utc_now()),
    }
    write_json(run_dir / "optimization-report.json", report)
    return run_dir, bool(stability_report["passed"])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Path to optimization plan JSON")
    parser.add_argument("--freqtrade-bin", default="freqtrade")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_dir, stable = run_optimization(args.plan, freqtrade_bin=args.freqtrade_bin)
    except (OptimizationError, ExperimentError) as exc:
        print(f"Optimization failed: {exc}", file=sys.stderr)
        return 1

    print(run_dir)
    return 0 if stable else 2


if __name__ == "__main__":
    raise SystemExit(main())
