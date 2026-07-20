#!/usr/bin/env python3
"""Run reproducible FreqAI data-download and backtest experiments from a manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from ai_platform.scripts.protected_final_holdout import (
    ProtectedFinalHoldoutError,
    validate_manifest_holdout_isolation,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")
REQUIRED_FIELDS = {
    "schema_version",
    "experiment_id",
    "description",
    "config",
    "strategy",
    "strategy_path",
    "freqai_model",
    "timerange",
    "download_timerange",
    "pairs",
    "timeframes",
    "fee",
    "output_root",
}


class ExperimentError(RuntimeError):
    """Raised when an experiment cannot be executed safely or reproducibly."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentError(f"Path escapes repository root: {value}") from exc
    return candidate


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


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"Unable to read manifest {path}: {exc}") from exc

    missing = sorted(REQUIRED_FIELDS - manifest.keys())
    if missing:
        raise ExperimentError(f"Manifest is missing required fields: {', '.join(missing)}")

    if manifest["schema_version"] != 1:
        raise ExperimentError("Only experiment manifest schema_version 1 is supported")

    experiment_id = manifest["experiment_id"]
    if not isinstance(experiment_id, str) or not EXPERIMENT_ID_PATTERN.fullmatch(experiment_id):
        raise ExperimentError("experiment_id may contain only letters, digits, '.', '_' and '-'")

    for field in ("config", "strategy", "strategy_path", "freqai_model", "output_root"):
        if not isinstance(manifest[field], str) or not manifest[field]:
            raise ExperimentError(f"{field} must be a non-empty string")

    for field in ("timerange", "download_timerange"):
        value = manifest[field]
        if not isinstance(value, str) or not TIMERANGE_PATTERN.fullmatch(value):
            raise ExperimentError(f"{field} must use YYYYMMDD-YYYYMMDD format")

    for field in ("pairs", "timeframes"):
        value = manifest[field]
        if not isinstance(value, list) or not value or not all(isinstance(x, str) for x in value):
            raise ExperimentError(f"{field} must be a non-empty list of strings")

    fee = manifest["fee"]
    if not isinstance(fee, (int, float)) or not 0 <= fee <= 0.05:
        raise ExperimentError("fee must be a numeric ratio between 0 and 0.05")

    try:
        validate_manifest_holdout_isolation(path, manifest)
    except ProtectedFinalHoldoutError as exc:
        raise ExperimentError(str(exc)) from exc

    return manifest


def validate_research_config(config_path: Path) -> dict[str, Any]:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"Unable to read config {config_path}: {exc}") from exc

    if config.get("dry_run") is not True:
        raise ExperimentError("Research experiment config must set dry_run=true")

    exchange = config.get("exchange", {})
    if exchange.get("key") or exchange.get("secret"):
        raise ExperimentError("Research experiment config must not contain exchange credentials")

    return config


def build_download_command(
    manifest: dict[str, Any],
    *,
    freqtrade_bin: str,
    config_path: Path,
) -> list[str]:
    return [
        freqtrade_bin,
        "download-data",
        "--config",
        str(config_path),
        "--pairs",
        *manifest["pairs"],
        "--timeframes",
        *manifest["timeframes"],
        "--timerange",
        manifest["download_timerange"],
    ]


def build_backtest_command(
    manifest: dict[str, Any],
    *,
    freqtrade_bin: str,
    config_path: Path,
    strategy_path: Path,
    run_dir: Path,
) -> list[str]:
    return [
        freqtrade_bin,
        "backtesting",
        "--config",
        str(config_path),
        "--strategy",
        manifest["strategy"],
        "--strategy-path",
        str(strategy_path),
        "--freqaimodel",
        manifest["freqai_model"],
        "--timerange",
        manifest["timerange"],
        "--fee",
        str(manifest["fee"]),
        "--export",
        "trades",
        "--backtest-directory",
        str(run_dir),
        "--notes",
        manifest["experiment_id"],
    ]


def run_logged(command: list[str], *, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {shlex.join(command)}\n\n")
        log_file.flush()
        try:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                check=False,
            )
        except OSError as exc:
            raise ExperimentError(f"Unable to execute {command[0]}: {exc}") from exc

    if result.returncode != 0:
        raise ExperimentError(f"Command failed with exit code {result.returncode}. See {log_path}")


def find_backtest_archive(run_dir: Path) -> Path:
    archives = sorted(run_dir.glob("backtest-result-*.zip"))
    if len(archives) != 1:
        raise ExperimentError(
            f"Expected exactly one backtest archive in {run_dir}, found {len(archives)}"
        )
    return archives[0]


def extract_backtest_metrics(archive: Path, strategy: str) -> dict[str, Any]:
    expected_result_name = f"{archive.stem}.json"
    with ZipFile(archive) as zip_file:
        if expected_result_name not in zip_file.namelist():
            raise ExperimentError(f"Result JSON {expected_result_name} not found in {archive}")
        payload = json.loads(zip_file.read(expected_result_name))

    strategy_metrics = payload.get("strategy", {}).get(strategy)
    if not isinstance(strategy_metrics, dict):
        raise ExperimentError(f"Strategy {strategy} not found in backtest archive")

    scalar_metrics = {
        key: value
        for key, value in strategy_metrics.items()
        if value is None or isinstance(value, (bool, int, float, str))
    }
    trades = strategy_metrics.get("trades")
    if isinstance(trades, list):
        scalar_metrics["trade_count"] = len(trades)

    return scalar_metrics


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_experiment(
    manifest_path: Path,
    *,
    stage: str,
    freqtrade_bin: str,
) -> Path:
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)

    config_path = _resolve_repo_path(manifest["config"])
    strategy_path = _resolve_repo_path(manifest["strategy_path"])
    output_root = _resolve_repo_path(manifest["output_root"])
    validate_research_config(config_path)

    strategy_file = strategy_path / f"{manifest['strategy']}.py"
    if not strategy_file.is_file():
        raise ExperimentError(f"Strategy file does not exist: {strategy_file}")

    commit = _git_commit()
    run_id = f"{_utc_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    run_dir = output_root / manifest["experiment_id"] / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    shutil.copy2(manifest_path, run_dir / "manifest.json")

    provenance = {
        "schema_version": 1,
        "experiment_id": manifest["experiment_id"],
        "run_id": run_id,
        "git_commit": commit,
        "manifest_sha256": _sha256(manifest_path),
        "config_sha256": _sha256(config_path),
        "strategy_sha256": _sha256(strategy_file),
        "stage": stage,
    }
    write_json(run_dir / "provenance.json", provenance)

    started_at = _utc_now()
    commands: list[list[str]] = []

    try:
        if stage in {"download", "all"}:
            download_command = build_download_command(
                manifest,
                freqtrade_bin=freqtrade_bin,
                config_path=config_path,
            )
            commands.append(download_command)
            run_logged(download_command, log_path=run_dir / "download.log")

        metrics: dict[str, Any] | None = None
        archive: Path | None = None
        if stage in {"backtest", "all"}:
            backtest_command = build_backtest_command(
                manifest,
                freqtrade_bin=freqtrade_bin,
                config_path=config_path,
                strategy_path=strategy_path,
                run_dir=run_dir,
            )
            commands.append(backtest_command)
            run_logged(backtest_command, log_path=run_dir / "backtest.log")
            archive = find_backtest_archive(run_dir)
            metrics = extract_backtest_metrics(archive, manifest["strategy"])

        finished_at = _utc_now()
        summary = {
            **provenance,
            "status": "success",
            "started_at": _iso_utc(started_at),
            "finished_at": _iso_utc(finished_at),
            "duration_seconds": (finished_at - started_at).total_seconds(),
            "fee_ratio_per_side": manifest["fee"],
            "timerange": manifest["timerange"],
            "download_timerange": manifest["download_timerange"],
            "commands": commands,
            "result_archive": archive.name if archive else None,
            "metrics": metrics,
        }
        write_json(run_dir / "run-summary.json", summary)
        return run_dir
    except Exception as exc:
        finished_at = _utc_now()
        failure = {
            **provenance,
            "status": "failed",
            "started_at": _iso_utc(started_at),
            "finished_at": _iso_utc(finished_at),
            "duration_seconds": (finished_at - started_at).total_seconds(),
            "commands": commands,
            "error": str(exc),
        }
        write_json(run_dir / "run-summary.json", failure)
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to experiment manifest JSON")
    parser.add_argument(
        "--stage",
        choices=("download", "backtest", "all"),
        default="backtest",
        help="Experiment stage to execute",
    )
    parser.add_argument(
        "--freqtrade-bin",
        default="freqtrade",
        help="Freqtrade executable name or path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_dir = run_experiment(
            args.manifest,
            stage=args.stage,
            freqtrade_bin=args.freqtrade_bin,
        )
    except ExperimentError as exc:
        print(f"Experiment failed: {exc}", file=sys.stderr)
        return 1

    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
