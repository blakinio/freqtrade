#!/usr/bin/env python3
"""Generate, validate, execute, and rank bounded FreqAI strategy candidates."""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from ai_platform.scripts.registry import (
    DEFAULT_DB_PATH,
    RegistryStore,
    build_definition_record,
    register_run,
    resolve_freqtrade_version,
)
from ai_platform.scripts.run_experiment import REPO_ROOT, ExperimentError, run_experiment
from ai_platform.scripts.run_validation import run_validation


DEFAULT_SEARCH_SPACE = REPO_ROOT / "ai_platform" / "discovery" / "search-space-v1.json"
DISCOVERY_ROOT = REPO_ROOT / "ai_platform" / "artifacts" / "discovery"
ALLOWED_FEATURE_GROUPS = {
    "price_action",
    "momentum",
    "trend",
    "volatility_volume",
    "time_context",
}
REQUIRED_SEARCH_FIELDS = {
    "schema_version",
    "search_id",
    "base_config",
    "base_experiment_manifest",
    "base_validation_plan",
    "base_registry_definition",
    "model_type",
    "target_id",
    "target_description",
    "feature_group_sets",
    "entry_prediction_thresholds",
    "exit_prediction_thresholds",
    "stoplosses",
    "max_candidates",
}


class DiscoveryError(RuntimeError):
    """Raised when a discovery candidate cannot be generated or executed safely."""


@dataclass(frozen=True)
class CandidateArtifacts:
    candidate_id: str
    class_name: str
    directory: Path
    strategy_path: Path
    config_path: Path
    manifest_path: Path
    validation_plan_path: Path
    registry_definition_path: Path
    result_path: Path


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiscoveryError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DiscoveryError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise DiscoveryError(f"Path escapes repository root: {value}") from exc
    return candidate


def _relative_repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_search_space(path: Path) -> dict[str, Any]:
    search = _read_json(path.resolve(), "search space")
    missing = sorted(REQUIRED_SEARCH_FIELDS - search.keys())
    if missing:
        raise DiscoveryError(f"Search space is missing fields: {', '.join(missing)}")
    if search["schema_version"] != 1:
        raise DiscoveryError("Only discovery search schema_version 1 is supported")
    if search["model_type"] != "LightGBMRegressor":
        raise DiscoveryError("Phase 4 search space is restricted to LightGBMRegressor")

    max_candidates = search["max_candidates"]
    if not isinstance(max_candidates, int) or not 1 <= max_candidates <= 1000:
        raise DiscoveryError("max_candidates must be an integer between 1 and 1000")

    for group_set in search["feature_group_sets"]:
        if not isinstance(group_set, list) or not group_set:
            raise DiscoveryError("Each feature group set must be a non-empty list")
        unknown = set(group_set) - ALLOWED_FEATURE_GROUPS
        if unknown:
            raise DiscoveryError(f"Unsupported feature groups: {', '.join(sorted(unknown))}")
        if len(group_set) != len(set(group_set)):
            raise DiscoveryError("Feature groups inside one set must be unique")

    total = (
        len(search["feature_group_sets"])
        * len(search["entry_prediction_thresholds"])
        * len(search["exit_prediction_thresholds"])
        * len(search["stoplosses"])
    )
    if total > max_candidates:
        raise DiscoveryError(
            f"Search space expands to {total} candidates, above max_candidates={max_candidates}"
        )
    return search


def _candidate_identity(payload: dict[str, Any]) -> tuple[str, str]:
    digest = _sha256_text(_canonical_json(payload))
    return f"disc-{digest[:12]}", f"DiscoveryStrategy_{digest[:12]}"


def generate_candidate_specs(search: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    product = itertools.product(
        search["feature_group_sets"],
        search["entry_prediction_thresholds"],
        search["exit_prediction_thresholds"],
        search["stoplosses"],
    )
    for feature_groups, entry_threshold, exit_threshold, stoploss in product:
        semantic = {
            "search_id": search["search_id"],
            "model_type": search["model_type"],
            "target_id": search["target_id"],
            "feature_groups": sorted(feature_groups),
            "entry_prediction_threshold": float(entry_threshold),
            "exit_prediction_threshold": float(exit_threshold),
            "stoploss": float(stoploss),
        }
        candidate_id, class_name = _candidate_identity(semantic)
        specs.append(
            {
                "schema_version": 1,
                "candidate_id": candidate_id,
                "class_name": class_name,
                **semantic,
            }
        )
    return specs


def _render_feature_expand_all(feature_groups: set[str]) -> list[str]:
    lines: list[str] = []
    if "momentum" in feature_groups:
        lines.extend(
            [
                '        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)',
                '        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)',
            ]
        )
    if "trend" in feature_groups:
        lines.extend(
            [
                '        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)',
                '        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)',
            ]
        )
    if "volatility_volume" in feature_groups:
        lines.extend(
            [
                '        dataframe["%-relative-volume-period"] = (',
                '            dataframe["volume"] / dataframe["volume"].rolling(period).mean()',
                "        )",
                "        atr = ta.ATR(dataframe, timeperiod=period)",
                '        dataframe["%-atr-normalized-period"] = atr / dataframe["close"]',
            ]
        )
    if not lines:
        lines.append('        dataframe["%-raw-close-period"] = dataframe["close"]')
    return lines


def _render_feature_basic(feature_groups: set[str]) -> list[str]:
    lines: list[str] = []
    if "price_action" in feature_groups:
        lines.extend(
            [
                '        dataframe["%-pct-change"] = dataframe["close"].pct_change()',
                '        dataframe["%-volume-change"] = dataframe["volume"].pct_change()',
                '        dataframe["%-high-low-range"] = (',
                '            dataframe["high"] - dataframe["low"]',
                '        ) / dataframe["close"]',
            ]
        )
    if not lines:
        lines.append('        dataframe["%-raw-volume"] = dataframe["volume"]')
    return lines


def _render_feature_standard(feature_groups: set[str]) -> list[str]:
    if "time_context" not in feature_groups:
        return ["        return dataframe"]
    return [
        '        dataframe["%-day-of-week"] = dataframe["date"].dt.dayofweek / 6.0',
        '        dataframe["%-hour-of-day"] = dataframe["date"].dt.hour / 23.0',
        "        return dataframe",
    ]


def render_strategy(candidate: dict[str, Any]) -> str:
    feature_groups = set(candidate["feature_groups"])
    unknown = feature_groups - ALLOWED_FEATURE_GROUPS
    if unknown:
        raise DiscoveryError(f"Unsupported feature groups: {', '.join(sorted(unknown))}")

    expand_all = "\n".join(_render_feature_expand_all(feature_groups))
    expand_basic = "\n".join(_render_feature_basic(feature_groups))
    standard = "\n".join(_render_feature_standard(feature_groups))
    class_name = candidate["class_name"]
    entry_threshold = repr(float(candidate["entry_prediction_threshold"]))
    exit_threshold = repr(float(candidate["exit_prediction_threshold"]))
    stoploss = repr(float(candidate["stoploss"]))

    return f'''from functools import reduce

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


class {class_name}(IStrategy):
    """Deterministically generated research-only FreqAI strategy."""

    timeframe = "15m"
    can_short = False
    process_only_new_candles = True
    startup_candle_count: int = 200

    minimal_roi = {{"0": 0.03, "240": 0.015, "720": 0.0}}
    stoploss = {stoploss}
    use_exit_signal = True

    entry_prediction_threshold = {entry_threshold}
    exit_prediction_threshold = {exit_threshold}

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
{expand_all}
        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
{expand_basic}
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
{standard}

    def set_freqai_targets(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        horizon = self.freqai_info["feature_parameters"]["label_period_candles"]
        future_average_close = dataframe["close"].shift(-horizon).rolling(horizon).mean()
        dataframe["&-future_return"] = future_average_close / dataframe["close"] - 1
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-future_return"] > self.entry_prediction_threshold,
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda left, right: left & right, conditions),
            ["enter_long", "enter_tag"],
        ] = (1, "discovery_long")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-future_return"] < self.exit_prediction_threshold,
        ]
        dataframe.loc[
            reduce(lambda left, right: left & right, conditions),
            ["exit_long", "exit_tag"],
        ] = (1, "discovery_exit")
        return dataframe
'''


def validate_generated_strategy(source: str, class_name: str) -> None:
    try:
        tree = ast.parse(source)
        compile(tree, f"<{class_name}>", "exec")
    except SyntaxError as exc:
        raise DiscoveryError(f"Generated strategy does not compile: {exc}") from exc

    classes = [
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    if len(classes) != 1:
        raise DiscoveryError(f"Generated source must define exactly one {class_name} class")


def load_base_documents(search: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields = {
        "config": "base_config",
        "manifest": "base_experiment_manifest",
        "validation": "base_validation_plan",
        "registry": "base_registry_definition",
    }
    return {
        name: _read_json(_resolve_repo_path(search[field]), name) for name, field in fields.items()
    }


def build_candidate_payloads(
    candidate: dict[str, Any],
    search: dict[str, Any],
    base: dict[str, dict[str, Any]],
    candidate_dir_relative: str,
) -> dict[str, Any]:
    config = json.loads(json.dumps(base["config"]))
    manifest = json.loads(json.dumps(base["manifest"]))
    validation = json.loads(json.dumps(base["validation"]))
    registry = json.loads(json.dumps(base["registry"]))

    candidate_id = candidate["candidate_id"]
    class_name = candidate["class_name"]
    config["freqai"]["identifier"] = candidate_id

    config_path = f"{candidate_dir_relative}/config.json"
    manifest_path = f"{candidate_dir_relative}/experiment.json"
    strategy_path = candidate_dir_relative

    manifest["experiment_id"] = candidate_id
    manifest["description"] = (
        f"Bounded discovery candidate {candidate_id}: "
        f"features={','.join(candidate['feature_groups'])}; "
        f"entry={candidate['entry_prediction_threshold']}; "
        f"exit={candidate['exit_prediction_threshold']}; stoploss={candidate['stoploss']}"
    )
    manifest["config"] = config_path
    manifest["strategy"] = class_name
    manifest["strategy_path"] = strategy_path
    manifest["freqai_model"] = search["model_type"]

    validation["validation_id"] = f"validation-{candidate_id}"
    validation["experiment_manifest"] = manifest_path

    feature_token = "-".join(candidate["feature_groups"])
    feature_hash = _sha256_text(feature_token)[:8]
    registry["definition_id"] = candidate_id
    registry["experiment_manifest"] = manifest_path
    registry["strategy_version"] = "1"
    registry["feature_set_id"] = f"discovery-{feature_hash}"
    registry["feature_set_description"] = "Bounded discovery feature groups: " + ", ".join(
        candidate["feature_groups"]
    )
    registry["target_id"] = search["target_id"]
    registry["target_description"] = search["target_description"]

    return {
        "strategy_source": render_strategy(candidate),
        "config": config,
        "manifest": manifest,
        "validation": validation,
        "registry": registry,
    }


def _write_text_idempotent(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            raise DiscoveryError(f"Existing candidate artifact differs: {path}")
        return
    path.write_text(content, encoding="utf-8")


def _write_json_idempotent(path: Path, payload: dict[str, Any]) -> None:
    _write_text_idempotent(path, json.dumps(payload, indent=4, sort_keys=True) + "\n")


def materialize_candidate(
    candidate: dict[str, Any],
    search: dict[str, Any],
) -> CandidateArtifacts:
    directory = (DISCOVERY_ROOT / candidate["candidate_id"]).resolve()
    try:
        directory.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise DiscoveryError("Candidate directory escaped repository root") from exc

    relative = _relative_repo_path(directory)
    base = load_base_documents(search)
    payloads = build_candidate_payloads(candidate, search, base, relative)
    strategy_path = directory / f"{candidate['class_name']}.py"
    config_path = directory / "config.json"
    manifest_path = directory / "experiment.json"
    validation_path = directory / "validation.json"
    registry_path = directory / "registry.json"
    result_path = directory / "candidate-result.json"

    validate_generated_strategy(payloads["strategy_source"], candidate["class_name"])
    _write_text_idempotent(strategy_path, payloads["strategy_source"])
    _write_json_idempotent(config_path, payloads["config"])
    _write_json_idempotent(manifest_path, payloads["manifest"])
    _write_json_idempotent(validation_path, payloads["validation"])
    _write_json_idempotent(registry_path, payloads["registry"])

    return CandidateArtifacts(
        candidate_id=candidate["candidate_id"],
        class_name=candidate["class_name"],
        directory=directory,
        strategy_path=strategy_path,
        config_path=config_path,
        manifest_path=manifest_path,
        validation_plan_path=validation_path,
        registry_definition_path=registry_path,
        result_path=result_path,
    )


def build_import_validation_command(
    artifacts: CandidateArtifacts,
    *,
    freqtrade_bin: str,
) -> list[str]:
    return [
        freqtrade_bin,
        "list-strategies",
        "--strategy-path",
        str(artifacts.directory),
        "--one-column",
    ]


def validate_strategy_import(
    artifacts: CandidateArtifacts,
    *,
    freqtrade_bin: str,
) -> None:
    command = build_import_validation_command(artifacts, freqtrade_bin=freqtrade_bin)
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise DiscoveryError(f"Unable to execute strategy import validation: {exc}") from exc
    if result.returncode != 0 or artifacts.class_name not in result.stdout.splitlines():
        output = (result.stdout + "\n" + result.stderr).strip()
        raise DiscoveryError(f"Generated strategy import validation failed: {output}")


def is_duplicate_definition(artifacts: CandidateArtifacts, db_path: Path) -> bool:
    definition = build_definition_record(artifacts.registry_definition_path)
    with RegistryStore(db_path) as store:
        return store.definition_exists(definition["fingerprint"])


def _write_candidate_result(artifacts: CandidateArtifacts, payload: dict[str, Any]) -> None:
    artifacts.result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_candidate(
    candidate: dict[str, Any],
    search: dict[str, Any],
    *,
    freqtrade_bin: str,
    experiment_stage: str,
    registry_db: Path,
) -> dict[str, Any]:
    artifacts = materialize_candidate(candidate, search)
    validate_strategy_import(artifacts, freqtrade_bin=freqtrade_bin)

    if is_duplicate_definition(artifacts, registry_db):
        result = {
            "candidate_id": artifacts.candidate_id,
            "status": "duplicate",
            "executed": False,
        }
        _write_candidate_result(artifacts, result)
        return result

    run_dir = run_experiment(
        artifacts.manifest_path,
        stage=experiment_stage,
        freqtrade_bin=freqtrade_bin,
    )
    validation_dir, validation_passed = run_validation(
        artifacts.validation_plan_path,
        freqtrade_bin=freqtrade_bin,
    )
    run_summary = run_dir / "run-summary.json"
    validation_report = validation_dir / "validation-report.json"
    version = resolve_freqtrade_version(freqtrade_bin)
    registration = register_run(
        registry_db,
        artifacts.registry_definition_path,
        run_summary,
        validation_report_path=validation_report,
        freqtrade_version=version,
    )

    result = {
        "candidate_id": artifacts.candidate_id,
        "status": "completed",
        "executed": True,
        "validation_passed": validation_passed,
        "promotion_status": registration["promotion_status"],
        "run_summary_path": _relative_repo_path(run_summary),
        "validation_report_path": _relative_repo_path(validation_report),
        "definition_fingerprint": registration["definition_fingerprint"],
    }
    _write_candidate_result(artifacts, result)
    return result


def discover_candidates(
    search: dict[str, Any],
    *,
    limit: int,
    freqtrade_bin: str,
    experiment_stage: str,
    registry_db: Path,
) -> list[dict[str, Any]]:
    specs = generate_candidate_specs(search)
    selected = specs[: min(limit, len(specs))]
    results: list[dict[str, Any]] = []
    for candidate in selected:
        try:
            results.append(
                run_candidate(
                    candidate,
                    search,
                    freqtrade_bin=freqtrade_bin,
                    experiment_stage=experiment_stage,
                    registry_db=registry_db,
                )
            )
        except Exception as exc:
            artifacts = materialize_candidate(candidate, search)
            failure = {
                "candidate_id": candidate["candidate_id"],
                "status": "failed",
                "executed": False,
                "error": str(exc),
            }
            _write_candidate_result(artifacts, failure)
            results.append(failure)
    return results


def robustness_score(validation_report: dict[str, Any]) -> float | None:
    folds = validation_report.get("walk_forward")
    holdout = validation_report.get("holdout")
    if not isinstance(folds, list) or not folds or not isinstance(holdout, dict):
        return None
    if validation_report.get("promotion_allowed") is not True:
        return None

    try:
        fold_profits = [float(item["profit"]) for item in folds]
        fold_drawdowns = [float(item["drawdown"]) for item in folds]
        holdout_profit = float(holdout["profit"])
        holdout_drawdown = float(holdout["drawdown"])
    except (KeyError, TypeError, ValueError):
        return None

    mean_profit = mean(fold_profits)
    worst_profit = min(fold_profits)
    worst_drawdown = max([*fold_drawdowns, holdout_drawdown])
    return 0.5 * holdout_profit + 0.3 * mean_profit + 0.2 * worst_profit - 0.5 * worst_drawdown


def rank_candidate_results(root: Path = DISCOVERY_ROOT) -> list[dict[str, Any]]:
    ranking: list[dict[str, Any]] = []
    for result_path in sorted(root.glob("*/candidate-result.json")):
        result = _read_json(result_path, "candidate result")
        report_ref = result.get("validation_report_path")
        if not isinstance(report_ref, str):
            continue
        report = _read_json(_resolve_repo_path(report_ref), "validation report")
        score = robustness_score(report)
        if score is None:
            continue
        ranking.append(
            {
                "candidate_id": result.get("candidate_id"),
                "promotion_status": result.get("promotion_status"),
                "robustness_score": score,
                "holdout_profit": report["holdout"]["profit"],
                "holdout_drawdown": report["holdout"]["drawdown"],
                "validation_report_path": report_ref,
            }
        )
    ranking.sort(key=lambda item: item["robustness_score"], reverse=True)
    return ranking


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-space", type=Path, default=DEFAULT_SEARCH_SPACE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Print deterministic candidate specs")
    generate.add_argument("--limit", type=int)

    materialize = subparsers.add_parser("materialize", help="Materialize one candidate by index")
    materialize.add_argument("index", type=int)

    discover = subparsers.add_parser("discover", help="Execute bounded candidates sequentially")
    discover.add_argument("--limit", type=int, default=1)
    discover.add_argument("--freqtrade-bin", default="freqtrade")
    discover.add_argument("--experiment-stage", choices=("backtest", "all"), default="backtest")
    discover.add_argument("--registry-db", type=Path, default=DEFAULT_DB_PATH)

    subparsers.add_parser("rank", help="Rank validated candidates by robustness metrics")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        search = load_search_space(args.search_space.resolve())
        specs = generate_candidate_specs(search)

        if args.command == "generate":
            limit = len(specs) if args.limit is None else args.limit
            if limit < 1:
                raise DiscoveryError("--limit must be positive")
            print(json.dumps(specs[:limit], indent=2, sort_keys=True))
            return 0

        if args.command == "materialize":
            if not 0 <= args.index < len(specs):
                raise DiscoveryError(f"Candidate index must be between 0 and {len(specs) - 1}")
            artifacts = materialize_candidate(specs[args.index], search)
            print(_relative_repo_path(artifacts.directory))
            return 0

        if args.command == "discover":
            if args.limit < 1:
                raise DiscoveryError("--limit must be positive")
            results = discover_candidates(
                search,
                limit=args.limit,
                freqtrade_bin=args.freqtrade_bin,
                experiment_stage=args.experiment_stage,
                registry_db=args.registry_db,
            )
            print(json.dumps(results, indent=2, sort_keys=True))
            return 1 if any(item["status"] == "failed" for item in results) else 0

        if args.command == "rank":
            print(json.dumps(rank_candidate_results(), indent=2, sort_keys=True))
            return 0

        raise DiscoveryError(f"Unsupported command: {args.command}")
    except (DiscoveryError, ExperimentError) as exc:
        print(f"Discovery error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
