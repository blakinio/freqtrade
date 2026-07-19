import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import ai_platform.scripts.registry as registry_module
from ai_platform.scripts.registry import (
    DuplicateRunError,
    RegistryError,
    RegistryStore,
    build_definition_record,
    build_run_record,
    load_registry_definition,
)


ROOT = Path(__file__).resolve().parents[2]
DEFINITION_PATH = ROOT / "ai_platform" / "registry" / "baseline-v1.json"
SCHEMA_PATH = ROOT / "ai_platform" / "registry" / "schema-v1.json"


def test_baseline_registry_definition_matches_schema() -> None:
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(definition)


def test_build_definition_record_is_stable() -> None:
    first = build_definition_record(DEFINITION_PATH)
    second = build_definition_record(DEFINITION_PATH)

    assert first["fingerprint"] == second["fingerprint"]
    assert len(first["fingerprint"]) == 64
    assert first["model_type"] == "LightGBMRegressor"
    assert first["feature_set_id"] == "baseline-price-trend-momentum-volume-v1"
    assert first["target_id"] == "future-average-return-v1"
    assert first["freqai_identifier"] == "ai-platform-baseline-v1"


def test_load_registry_definition_rejects_missing_fields(tmp_path: Path) -> None:
    definition_path = tmp_path / "invalid.json"
    definition_path.write_text('{"schema_version": 1}\n', encoding="utf-8")

    with pytest.raises(RegistryError, match="missing fields"):
        load_registry_definition(definition_path)


def _write_run_summary(path: Path, definition: dict, *, git_commit: str) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "experiment_id": definition["experiment_id"],
                "run_id": "20260719T120000Z-abc12345",
                "git_commit": git_commit,
                "manifest_sha256": definition["manifest_sha256"],
                "config_sha256": definition["config_sha256"],
                "strategy_sha256": definition["strategy_sha256"],
                "status": "success",
                "metrics": {
                    "total_trades": 42,
                    "profit_total": 0.12,
                    "max_drawdown_account": 0.08,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_validation_report(path: Path, *, promotion_allowed: bool) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "passed" if promotion_allowed else "failed_gates",
                "promotion_allowed": promotion_allowed,
                "holdout": {
                    "trades": 12,
                    "profit": 0.03,
                    "drawdown": 0.07,
                },
                "lookahead": {"passed": True},
                "recursive": {"passed": True},
            }
        ),
        encoding="utf-8",
    )


def test_registry_detects_duplicate_definition_and_run(tmp_path: Path, monkeypatch) -> None:
    definition = build_definition_record(DEFINITION_PATH)
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)

    run_summary = tmp_path / "run-summary.json"
    _write_run_summary(run_summary, definition, git_commit="a" * 40)
    run = build_run_record(
        definition,
        run_summary,
        validation_report_path=None,
        freqtrade_version="freqtrade 2026.7",
    )

    with RegistryStore(tmp_path / "registry.sqlite3") as store:
        assert store.insert_definition(definition) is True
        assert store.insert_definition(definition) is False
        store.insert_run(run)
        with pytest.raises(DuplicateRunError, match="already registered"):
            store.insert_run(run)


def test_validated_run_maps_to_git_and_freqai_identifier(tmp_path: Path, monkeypatch) -> None:
    definition = build_definition_record(DEFINITION_PATH)
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)

    run_summary = tmp_path / "run-summary.json"
    validation_report = tmp_path / "validation-report.json"
    _write_run_summary(run_summary, definition, git_commit="b" * 40)
    _write_validation_report(validation_report, promotion_allowed=True)

    run = build_run_record(
        definition,
        run_summary,
        validation_report_path=validation_report,
        freqtrade_version="freqtrade 2026.7",
    )

    assert run["git_commit"] == "b" * 40
    assert definition["freqai_identifier"] == "ai-platform-baseline-v1"
    assert run["promotion_status"] == "validated"
    assert run["validation_status"] == "passed"
    assert run["lookahead_status"] == "passed"
    assert run["recursive_status"] == "passed"


def test_validated_run_rejects_unknown_git_commit(tmp_path: Path, monkeypatch) -> None:
    definition = build_definition_record(DEFINITION_PATH)
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)

    run_summary = tmp_path / "run-summary.json"
    validation_report = tmp_path / "validation-report.json"
    _write_run_summary(run_summary, definition, git_commit="unknown")
    _write_validation_report(validation_report, promotion_allowed=True)

    with pytest.raises(RegistryError, match="40-character Git commit SHA"):
        build_run_record(
            definition,
            run_summary,
            validation_report_path=validation_report,
            freqtrade_version="freqtrade 2026.7",
        )


def test_run_summary_hash_mismatch_is_rejected(tmp_path: Path, monkeypatch) -> None:
    definition = build_definition_record(DEFINITION_PATH)
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)

    run_summary = tmp_path / "run-summary.json"
    _write_run_summary(run_summary, definition, git_commit="c" * 40)
    payload = json.loads(run_summary.read_text(encoding="utf-8"))
    payload["strategy_sha256"] = "0" * 64
    run_summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RegistryError, match="strategy hash"):
        build_run_record(
            definition,
            run_summary,
            validation_report_path=None,
            freqtrade_version="freqtrade 2026.7",
        )


def test_registry_comparison_filters_dimensions(tmp_path: Path, monkeypatch) -> None:
    definition = build_definition_record(DEFINITION_PATH)
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)

    run_summary = tmp_path / "run-summary.json"
    validation_report = tmp_path / "validation-report.json"
    _write_run_summary(run_summary, definition, git_commit="d" * 40)
    _write_validation_report(validation_report, promotion_allowed=True)
    run = build_run_record(
        definition,
        run_summary,
        validation_report_path=validation_report,
        freqtrade_version="freqtrade 2026.7",
    )

    with RegistryStore(tmp_path / "registry.sqlite3") as store:
        store.insert_definition(definition)
        store.insert_run(run)

        assert len(store.compare(model_type="LightGBMRegressor")) == 1
        assert len(store.compare(feature_set_id=definition["feature_set_id"])) == 1
        assert len(store.compare(target_id=definition["target_id"])) == 1
        assert len(store.compare(timeframe="1h")) == 1
        assert len(store.compare(promotion_status="validated")) == 1
        assert store.compare(model_type="XGBoostRegressor") == []
