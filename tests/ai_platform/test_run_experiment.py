import json
import os
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.run_experiment import (
    ExperimentError,
    build_backtest_command,
    build_download_command,
    extract_backtest_metrics,
    load_manifest,
    run_logged,
    validate_research_config,
)


ROOT = Path(__file__).resolve().parents[2]
BASELINE_MANIFEST = ROOT / "ai_platform" / "experiments" / "baseline-v1.json"
RESIDUAL_AUDIT_MANIFEST = (
    ROOT / "ai_platform" / "experiments" / "residual-pytorch-m1-data-audit-v1.json"
)
MANIFEST_SCHEMA = ROOT / "ai_platform" / "experiments" / "schema-v1.json"


def test_baseline_manifest_matches_schema() -> None:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(manifest)


def test_residual_epoch_manifest_matches_schema() -> None:
    manifest = json.loads(RESIDUAL_AUDIT_MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(manifest)


def test_load_manifest_accepts_baseline() -> None:
    manifest = load_manifest(BASELINE_MANIFEST)

    assert manifest["schema_version"] == 1
    assert manifest["experiment_id"] == "freqai-baseline-v1"
    assert manifest["fee"] == 0.002


def test_load_manifest_accepts_unix_second_timeranges(tmp_path: Path) -> None:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    manifest["timerange"] = "1772323200-1777593599"
    manifest["download_timerange"] = "1754006400-1777593599"
    path = tmp_path / "epoch-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = load_manifest(path)

    assert loaded["timerange"] == "1772323200-1777593599"
    assert loaded["download_timerange"] == "1754006400-1777593599"


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


def test_run_logged_prepends_repo_root_to_pythonpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "success.log"
    existing_pythonpath = os.pathsep.join(("/existing/one", "/existing/two"))
    monkeypatch.setenv("PYTHONPATH", existing_pythonpath)
    captured: dict[str, object] = {}

    def fake_run(*args, env, **kwargs):
        captured["env"] = env
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("ai_platform.scripts.run_experiment.subprocess.run", fake_run)

    run_logged(["freqtrade", "backtesting"], log_path=log_path)

    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["PYTHONPATH"].split(os.pathsep) == [
        str(ROOT),
        "/existing/one",
        "/existing/two",
    ]


def test_run_logged_includes_only_bounded_failure_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "failed.log"

    def fake_run(*args, stdout, **kwargs):
        for index in range(80):
            stdout.write(f"line-{index:03d}\n")
        return SimpleNamespace(returncode=2)

    monkeypatch.setattr("ai_platform.scripts.run_experiment.subprocess.run", fake_run)

    with pytest.raises(ExperimentError) as exc_info:
        run_logged(["freqtrade", "backtesting"], log_path=log_path)

    message = str(exc_info.value)
    assert "--- bounded log tail ---" in message
    assert "line-079" in message
    assert "line-040" in message
    assert "line-039" not in message
    assert "line-000" not in message
