#!/usr/bin/env python3
"""Manage the durable AI-platform experiment definition and run registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_platform.scripts.run_experiment import REPO_ROOT, load_manifest, validate_research_config


DEFAULT_DB_PATH = REPO_ROOT / "ai_platform" / "artifacts" / "registry" / "registry.sqlite3"
ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_DEFINITION_FIELDS = {
    "schema_version",
    "definition_id",
    "experiment_manifest",
    "strategy_version",
    "feature_set_id",
    "feature_set_description",
    "target_id",
    "target_description",
}


class RegistryError(RuntimeError):
    """Raised when registry input is invalid or cannot be persisted safely."""


class DuplicateRunError(RegistryError):
    """Raised when a run is already present for a definition fingerprint."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_repo_path(value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RegistryError(f"Path escapes repository root: {value}") from exc
    return candidate


def _relative_repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_registry_definition(path: Path) -> dict[str, Any]:
    try:
        definition = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Unable to read registry definition {path}: {exc}") from exc

    missing = sorted(REQUIRED_DEFINITION_FIELDS - definition.keys())
    if missing:
        raise RegistryError(f"Registry definition is missing fields: {', '.join(missing)}")
    if definition["schema_version"] != 1:
        raise RegistryError("Only registry definition schema_version 1 is supported")

    for field in ("definition_id", "feature_set_id", "target_id"):
        value = definition[field]
        if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
            raise RegistryError(f"{field} contains unsupported characters")

    for field in (
        "experiment_manifest",
        "strategy_version",
        "feature_set_description",
        "target_description",
    ):
        if not isinstance(definition[field], str) or not definition[field]:
            raise RegistryError(f"{field} must be a non-empty string")

    return definition


def build_definition_record(definition_path: Path) -> dict[str, Any]:
    definition_path = definition_path.resolve()
    definition = load_registry_definition(definition_path)
    manifest_path = _resolve_repo_path(definition["experiment_manifest"])
    manifest = load_manifest(manifest_path)
    config_path = _resolve_repo_path(manifest["config"])
    strategy_path = _resolve_repo_path(manifest["strategy_path"])
    config = validate_research_config(config_path)

    strategy_file = strategy_path / f"{manifest['strategy']}.py"
    if not strategy_file.is_file():
        raise RegistryError(f"Strategy file does not exist: {strategy_file}")

    freqai = config.get("freqai", {})
    freqai_identifier = freqai.get("identifier")
    if not isinstance(freqai_identifier, str) or not freqai_identifier:
        raise RegistryError("FreqAI config must contain a non-empty identifier")

    model_parameters = freqai.get("model_training_parameters", {})
    if not isinstance(model_parameters, dict):
        raise RegistryError("freqai.model_training_parameters must be an object")

    semantic_definition = {
        "strategy_name": manifest["strategy"],
        "strategy_version": definition["strategy_version"],
        "strategy_sha256": _sha256_file(strategy_file),
        "config_sha256": _sha256_file(config_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "freqai_identifier": freqai_identifier,
        "model_type": manifest["freqai_model"],
        "feature_set_id": definition["feature_set_id"],
        "target_id": definition["target_id"],
        "training_window_days": freqai.get("train_period_days"),
        "evaluation_timerange": manifest["timerange"],
        "download_timerange": manifest["download_timerange"],
        "pairs": sorted(manifest["pairs"]),
        "timeframes": sorted(manifest["timeframes"]),
        "model_parameters": model_parameters,
        "fee_assumption": manifest["fee"],
    }
    fingerprint = _sha256_bytes(_canonical_json(semantic_definition).encode("utf-8"))

    return {
        "schema_version": 1,
        "fingerprint": fingerprint,
        "definition_id": definition["definition_id"],
        "experiment_id": manifest["experiment_id"],
        "strategy_name": manifest["strategy"],
        "strategy_version": definition["strategy_version"],
        "strategy_sha256": semantic_definition["strategy_sha256"],
        "config_sha256": semantic_definition["config_sha256"],
        "manifest_sha256": semantic_definition["manifest_sha256"],
        "freqai_identifier": freqai_identifier,
        "model_type": manifest["freqai_model"],
        "feature_set_id": definition["feature_set_id"],
        "feature_set_description": definition["feature_set_description"],
        "target_id": definition["target_id"],
        "target_description": definition["target_description"],
        "training_window_days": freqai.get("train_period_days"),
        "evaluation_timerange": manifest["timerange"],
        "download_timerange": manifest["download_timerange"],
        "pairs": sorted(manifest["pairs"]),
        "timeframes": sorted(manifest["timeframes"]),
        "model_parameters": model_parameters,
        "fee_assumption": manifest["fee"],
        "manifest_path": _relative_repo_path(manifest_path),
        "definition_path": _relative_repo_path(definition_path),
    }


def resolve_freqtrade_version(freqtrade_bin: str) -> str:
    try:
        output = subprocess.check_output(
            [freqtrade_bin, "--version"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        message = f"Unable to resolve Freqtrade version using {freqtrade_bin}: {exc}"
        raise RegistryError(message) from exc

    if not output:
        raise RegistryError("Freqtrade version command returned empty output")
    return " | ".join(line.strip() for line in output.splitlines() if line.strip())


class RegistryStore:
    def __init__(self, db_path: Path):
        self.db_path = _resolve_repo_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> RegistryStore:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS experiment_definitions (
                fingerprint TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                definition_id TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                strategy_version TEXT NOT NULL,
                strategy_sha256 TEXT NOT NULL,
                config_sha256 TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL,
                freqai_identifier TEXT NOT NULL,
                model_type TEXT NOT NULL,
                feature_set_id TEXT NOT NULL,
                feature_set_description TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_description TEXT NOT NULL,
                training_window_days INTEGER,
                evaluation_timerange TEXT NOT NULL,
                download_timerange TEXT NOT NULL,
                pairs_json TEXT NOT NULL,
                timeframes_json TEXT NOT NULL,
                model_parameters_json TEXT NOT NULL,
                fee_assumption REAL NOT NULL,
                manifest_path TEXT NOT NULL,
                definition_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS experiment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL,
                run_id TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                git_commit TEXT NOT NULL,
                freqtrade_version TEXT NOT NULL,
                run_status TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                promotion_status TEXT NOT NULL,
                trade_count INTEGER,
                profit REAL,
                max_drawdown REAL,
                holdout_trade_count INTEGER,
                holdout_profit REAL,
                holdout_drawdown REAL,
                lookahead_status TEXT NOT NULL,
                recursive_status TEXT NOT NULL,
                run_summary_path TEXT NOT NULL,
                validation_report_path TEXT,
                raw_run_summary_json TEXT NOT NULL,
                raw_validation_report_json TEXT,
                FOREIGN KEY (fingerprint) REFERENCES experiment_definitions(fingerprint),
                UNIQUE (fingerprint, run_id)
            );

            CREATE INDEX IF NOT EXISTS idx_registry_model
                ON experiment_definitions(model_type);
            CREATE INDEX IF NOT EXISTS idx_registry_feature_set
                ON experiment_definitions(feature_set_id);
            CREATE INDEX IF NOT EXISTS idx_registry_target
                ON experiment_definitions(target_id);
            CREATE INDEX IF NOT EXISTS idx_registry_promotion
                ON experiment_runs(promotion_status);
            """
        )
        self.connection.commit()

    def definition_exists(self, fingerprint: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM experiment_definitions WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        return row is not None

    def insert_definition(self, record: dict[str, Any]) -> bool:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO experiment_definitions (
                fingerprint, schema_version, definition_id, experiment_id,
                strategy_name, strategy_version, strategy_sha256, config_sha256,
                manifest_sha256, freqai_identifier, model_type, feature_set_id,
                feature_set_description, target_id, target_description,
                training_window_days, evaluation_timerange, download_timerange,
                pairs_json, timeframes_json, model_parameters_json, fee_assumption,
                manifest_path, definition_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["fingerprint"],
                record["schema_version"],
                record["definition_id"],
                record["experiment_id"],
                record["strategy_name"],
                record["strategy_version"],
                record["strategy_sha256"],
                record["config_sha256"],
                record["manifest_sha256"],
                record["freqai_identifier"],
                record["model_type"],
                record["feature_set_id"],
                record["feature_set_description"],
                record["target_id"],
                record["target_description"],
                record["training_window_days"],
                record["evaluation_timerange"],
                record["download_timerange"],
                _canonical_json(record["pairs"]),
                _canonical_json(record["timeframes"]),
                _canonical_json(record["model_parameters"]),
                record["fee_assumption"],
                record["manifest_path"],
                record["definition_path"],
                _utc_now(),
            ),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def insert_run(self, record: dict[str, Any]) -> None:
        try:
            self.connection.execute(
                """
                INSERT INTO experiment_runs (
                    fingerprint, run_id, registered_at, git_commit, freqtrade_version,
                    run_status, validation_status, promotion_status, trade_count,
                    profit, max_drawdown, holdout_trade_count, holdout_profit,
                    holdout_drawdown, lookahead_status, recursive_status,
                    run_summary_path, validation_report_path, raw_run_summary_json,
                    raw_validation_report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["fingerprint"],
                    record["run_id"],
                    record["registered_at"],
                    record["git_commit"],
                    record["freqtrade_version"],
                    record["run_status"],
                    record["validation_status"],
                    record["promotion_status"],
                    record["trade_count"],
                    record["profit"],
                    record["max_drawdown"],
                    record["holdout_trade_count"],
                    record["holdout_profit"],
                    record["holdout_drawdown"],
                    record["lookahead_status"],
                    record["recursive_status"],
                    record["run_summary_path"],
                    record["validation_report_path"],
                    _canonical_json(record["raw_run_summary"]),
                    _canonical_json(record["raw_validation_report"])
                    if record["raw_validation_report"] is not None
                    else None,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateRunError(
                f"Run {record['run_id']} is already registered for {record['fingerprint']}"
            ) from exc
        self.connection.commit()

    def compare(
        self,
        *,
        model_type: str | None = None,
        feature_set_id: str | None = None,
        target_id: str | None = None,
        timeframe: str | None = None,
        promotion_status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT d.*, r.run_id, r.registered_at, r.git_commit, r.freqtrade_version,
                   r.run_status, r.validation_status, r.promotion_status,
                   r.trade_count, r.profit, r.max_drawdown,
                   r.holdout_trade_count, r.holdout_profit, r.holdout_drawdown,
                   r.lookahead_status, r.recursive_status,
                   r.run_summary_path, r.validation_report_path
            FROM experiment_definitions d
            JOIN experiment_runs r ON r.fingerprint = d.fingerprint
            ORDER BY COALESCE(r.holdout_profit, r.profit, -999999.0) DESC,
                     r.registered_at DESC
            """
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["pairs"] = json.loads(item.pop("pairs_json"))
            item["timeframes"] = json.loads(item.pop("timeframes_json"))
            item["model_parameters"] = json.loads(item.pop("model_parameters_json"))

            if model_type and item["model_type"] != model_type:
                continue
            if feature_set_id and item["feature_set_id"] != feature_set_id:
                continue
            if target_id and item["target_id"] != target_id:
                continue
            if timeframe and timeframe not in item["timeframes"]:
                continue
            if promotion_status and item["promotion_status"] != promotion_status:
                continue

            results.append(item)
            if len(results) >= limit:
                break
        return results


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegistryError(f"{label} must contain a JSON object")
    return payload


def _metric(metrics: dict[str, Any], key: str) -> int | float | None:
    value = metrics.get(key)
    return value if isinstance(value, (int, float)) else None


def _validate_run_summary_identity(
    definition: dict[str, Any],
    run_summary: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    if run_summary.get("experiment_id") != definition["experiment_id"]:
        raise RegistryError("Run summary experiment_id does not match registry definition")

    hash_fields = (
        ("manifest_sha256", "manifest hash"),
        ("config_sha256", "config hash"),
        ("strategy_sha256", "strategy hash"),
    )
    for field, label in hash_fields:
        if run_summary.get(field) != definition[field]:
            raise RegistryError(f"Run summary {label} does not match current definition")

    run_id = run_summary.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise RegistryError("Run summary must contain a non-empty run_id")

    git_commit = run_summary.get("git_commit")
    if not isinstance(git_commit, str) or not git_commit:
        raise RegistryError("Run summary must contain a git_commit")

    metrics = run_summary.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}

    return run_id, git_commit, metrics


def _analysis_status(validation_report: dict[str, Any], key: str) -> str:
    payload = validation_report.get(key)
    if not isinstance(payload, dict):
        return "not_run"
    return "passed" if payload.get("passed") is True else "failed"


def _validate_promotable_identity(
    definition: dict[str, Any],
    git_commit: str,
    freqtrade_version: str,
) -> None:
    if not GIT_SHA_PATTERN.fullmatch(git_commit):
        raise RegistryError(
            "Validated candidates require a full 40-character Git commit SHA"
        )
    if not definition["freqai_identifier"]:
        raise RegistryError("Validated candidates require a FreqAI identifier")
    if not freqtrade_version or freqtrade_version == "unknown":
        raise RegistryError("Validated candidates require a resolved Freqtrade version")


def _validation_evidence(
    validation_report: dict[str, Any] | None,
    *,
    run_status: str,
    definition: dict[str, Any],
    git_commit: str,
    freqtrade_version: str,
) -> dict[str, Any]:
    if validation_report is None:
        return {
            "validation_status": "unvalidated",
            "promotion_status": "candidate" if run_status == "success" else "experiment",
            "holdout": {},
            "lookahead_status": "not_run",
            "recursive_status": "not_run",
        }

    holdout = validation_report.get("holdout")
    if not isinstance(holdout, dict):
        holdout = {}

    promotion_allowed = validation_report.get("promotion_allowed") is True
    if promotion_allowed:
        _validate_promotable_identity(definition, git_commit, freqtrade_version)

    return {
        "validation_status": str(validation_report.get("status", "unknown")),
        "promotion_status": "validated" if promotion_allowed else "candidate",
        "holdout": holdout,
        "lookahead_status": _analysis_status(validation_report, "lookahead"),
        "recursive_status": _analysis_status(validation_report, "recursive"),
    }


def build_run_record(
    definition: dict[str, Any],
    run_summary_path: Path,
    *,
    validation_report_path: Path | None,
    freqtrade_version: str,
) -> dict[str, Any]:
    run_summary_path = run_summary_path.resolve()
    run_summary = _read_json(run_summary_path, "run summary")
    validation_report = (
        _read_json(validation_report_path.resolve(), "validation report")
        if validation_report_path is not None
        else None
    )

    run_id, git_commit, metrics = _validate_run_summary_identity(definition, run_summary)
    run_status = str(run_summary.get("status", "unknown"))
    evidence = _validation_evidence(
        validation_report,
        run_status=run_status,
        definition=definition,
        git_commit=git_commit,
        freqtrade_version=freqtrade_version,
    )

    trade_count = metrics.get("total_trades", metrics.get("trade_count"))
    if not isinstance(trade_count, int):
        trade_count = None

    holdout = evidence["holdout"]
    return {
        "fingerprint": definition["fingerprint"],
        "run_id": run_id,
        "registered_at": _utc_now(),
        "git_commit": git_commit,
        "freqtrade_version": freqtrade_version,
        "run_status": run_status,
        "validation_status": evidence["validation_status"],
        "promotion_status": evidence["promotion_status"],
        "trade_count": trade_count,
        "profit": _metric(metrics, "profit_total"),
        "max_drawdown": _metric(metrics, "max_drawdown_account"),
        "holdout_trade_count": _metric(holdout, "trades"),
        "holdout_profit": _metric(holdout, "profit"),
        "holdout_drawdown": _metric(holdout, "drawdown"),
        "lookahead_status": evidence["lookahead_status"],
        "recursive_status": evidence["recursive_status"],
        "run_summary_path": _relative_repo_path(run_summary_path),
        "validation_report_path": _relative_repo_path(validation_report_path.resolve())
        if validation_report_path is not None
        else None,
        "raw_run_summary": run_summary,
        "raw_validation_report": validation_report,
    }


def register_run(
    db_path: Path,
    definition_path: Path,
    run_summary_path: Path,
    *,
    validation_report_path: Path | None = None,
    freqtrade_version: str,
) -> dict[str, Any]:
    definition = build_definition_record(definition_path.resolve())
    run = build_run_record(
        definition,
        run_summary_path,
        validation_report_path=validation_report_path,
        freqtrade_version=freqtrade_version,
    )

    with RegistryStore(db_path) as store:
        definition_created = store.insert_definition(definition)
        store.insert_run(run)

    return {
        "status": "registered",
        "definition_created": definition_created,
        "definition_fingerprint": definition["fingerprint"],
        "run_id": run["run_id"],
        "promotion_status": run["promotion_status"],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Registry SQLite database path inside the repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the registry database")

    check = subparsers.add_parser("check-definition", help="Detect an existing definition")
    check.add_argument("definition", type=Path)

    register = subparsers.add_parser("register", help="Register one experiment run")
    register.add_argument("definition", type=Path)
    register.add_argument("--run-summary", type=Path, required=True)
    register.add_argument("--validation-report", type=Path)
    register.add_argument("--freqtrade-bin", default="freqtrade")

    compare = subparsers.add_parser("compare", help="Compare registered experiment runs")
    compare.add_argument("--model")
    compare.add_argument("--feature-set")
    compare.add_argument("--target")
    compare.add_argument("--timeframe")
    compare.add_argument("--promotion-status")
    compare.add_argument("--limit", type=int, default=100)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        if args.command == "init":
            with RegistryStore(args.db):
                pass
            initialized = {
                "status": "initialized",
                "db": _relative_repo_path(_resolve_repo_path(args.db)),
            }
            print(_canonical_json(initialized))
            return 0

        if args.command == "check-definition":
            definition = build_definition_record(args.definition.resolve())
            with RegistryStore(args.db) as store:
                duplicate = store.definition_exists(definition["fingerprint"])
            print(
                _canonical_json(
                    {
                        "status": "duplicate" if duplicate else "new",
                        "definition_fingerprint": definition["fingerprint"],
                        "definition_id": definition["definition_id"],
                    }
                )
            )
            return 2 if duplicate else 0

        if args.command == "register":
            version = resolve_freqtrade_version(args.freqtrade_bin)
            result = register_run(
                args.db,
                args.definition.resolve(),
                args.run_summary.resolve(),
                validation_report_path=args.validation_report.resolve()
                if args.validation_report is not None
                else None,
                freqtrade_version=version,
            )
            print(_canonical_json(result))
            return 0

        if args.command == "compare":
            if args.limit < 1:
                raise RegistryError("--limit must be positive")
            with RegistryStore(args.db) as store:
                results = store.compare(
                    model_type=args.model,
                    feature_set_id=args.feature_set,
                    target_id=args.target,
                    timeframe=args.timeframe,
                    promotion_status=args.promotion_status,
                    limit=args.limit,
                )
            print(json.dumps(results, indent=2, sort_keys=True))
            return 0

        raise RegistryError(f"Unsupported command: {args.command}")
    except DuplicateRunError as exc:
        print(f"Registry duplicate: {exc}", file=sys.stderr)
        return 2
    except RegistryError as exc:
        print(f"Registry error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
