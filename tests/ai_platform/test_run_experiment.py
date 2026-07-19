import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.run_experiment import (
    ExperimentError,
    build_backtest_command,
    build_download_command,
    extract_backtest_metrics,
    load_manifest,
    validate_research_config,
)


ROOT = Path(__file__).resolve().parents[2]
BASELINE_MANIFEST = ROOT / "ai_platform" / "experiments" / "baseline-v1.json"
MANIFEST_SCHEMA = ROOT / "ai_platform" / "experiments" / "schema-v1.json"


def test_baseline_manifest_matches_schema() -> None:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(manifest)


def test_load_manifest_accepts_baseline() -> None:
    manifest = load_manifest(BASELINE_MANIFEST)

    assert manifest["schema_version"] == 1
    assert manifest["experiment_id"] == "freqai-baseline-v1"
    assert manifest["fee"] == 0.002


def test_load_manifest_rejects_missing_required_fields(tmp_path: Path) -> None:
    manifest_path = tmp_path / "invalid.json"
    manifest_path.write_text('{"schema_version": 1}\n', encoding="utf-8")

    with pytest.raises(ExperimentError, match="missing required fields"):
        load_manifest(manifest_path)


def test_validate_research_config_rejects_live_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "dry_run": False,
                "exchange": {
                    "key": "",
                    "secret": "",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ExperimentError, match="dry_run=true"):
        validate_research_config(config_path)


def test_validate_research_config_rejects_credentials(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "dry_run": True,
                "exchange": {
                    "key": "not-allowed",
                    "secret": "",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ExperimentError, match="must not contain exchange credentials"):
        validate_research_config(config_path)


def test_command_builders_pin_manifest_inputs(tmp_path: Path) -> None:
    manifest = load_manifest(BASELINE_MANIFEST)
    config_path = tmp_path / "config.json"
    strategy_path = tmp_path / "strategies"
    run_dir = tmp_path / "results"

    download_command = build_download_command(
        manifest,
        freqtrade_bin="freqtrade",
        config_path=config_path,
    )
    backtest_command = build_backtest_command(
        manifest,
        freqtrade_bin="freqtrade",
        config_path=config_path,
        strategy_path=strategy_path,
        run_dir=run_dir,
    )

    assert download_command[:2] == ["freqtrade", "download-data"]
    assert manifest["download_timerange"] in download_command
    assert all(pair in download_command for pair in manifest["pairs"])
    assert all(timeframe in download_command for timeframe in manifest["timeframes"])

    assert backtest_command[:2] == ["freqtrade", "backtesting"]
    assert manifest["strategy"] in backtest_command
    assert manifest["freqai_model"] in backtest_command
    assert str(manifest["fee"]) in backtest_command
    assert manifest["timerange"] in backtest_command


def test_extract_backtest_metrics_returns_scalar_summary(tmp_path: Path) -> None:
    archive = tmp_path / "backtest-result-test.zip"
    payload = {
        "strategy": {
            "AiBaselineStrategy": {
                "profit_total": 0.12,
                "max_drawdown_account": 0.08,
                "trades": [
                    {"pair": "BTC/USDT"},
                    {"pair": "ETH/USDT"},
                ],
            }
        },
        "strategy_comparison": [],
    }

    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        zip_file.writestr("backtest-result-test.json", json.dumps(payload))
        zip_file.writestr("backtest-result-test_config.json", "{}")

    metrics = extract_backtest_metrics(archive, "AiBaselineStrategy")

    assert metrics["profit_total"] == 0.12
    assert metrics["max_drawdown_account"] == 0.08
    assert metrics["trade_count"] == 2
    assert "trades" not in metrics
