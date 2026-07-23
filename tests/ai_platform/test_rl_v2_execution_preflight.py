from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_execution_preflight import (
    DESCRIPTOR_PATH,
    RLV2ExecutionPreflightError,
    build_ephemeral_config,
    validate_descriptor,
    validate_ephemeral_config,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "ai_platform" / "scripts" / "rl_v2_execution_preflight.py"


def test_descriptor_freezes_non_result_producing_scope() -> None:
    descriptor = validate_descriptor()

    assert DESCRIPTOR_PATH.name == "rl-v2-execution-preflight-v1.json"
    assert descriptor["runtime_resolution"]["model_type"] == "PPO"
    assert descriptor["runtime_resolution"]["policy_type"] == "MlpPolicy"
    assert descriptor["runtime_resolution"]["trading_mode"] == "spot"
    assert descriptor["semantic_binding"]["action_space"] == {
        "0": "target_flat",
        "1": "target_long",
    }
    assert descriptor["semantic_binding"]["action_space_size"] == 2
    assert descriptor["isolation"]["future_evaluation_window_selected"] is False
    assert descriptor["isolation"]["phase6_authoritative_selected_model"] is None

    forbidden_scope = (
        "training_config_commit_allowed",
        "experiment_manifest_allowed",
        "run_request_allowed",
        "training_allowed",
        "model_fitting_allowed",
        "backtest_allowed",
        "market_data_download_allowed",
        "exchange_data_access_allowed",
        "historical_evaluation_window_selection_allowed",
        "future_evaluation_window_selection_allowed",
        "strict_oos_execution_allowed",
        "performance_evaluation_allowed",
        "promotion_allowed",
        "live_trading_allowed",
    )
    assert all(descriptor["scope"][key] is False for key in forbidden_scope)


def test_ephemeral_config_has_no_execution_geometry(tmp_path: Path) -> None:
    descriptor = validate_descriptor()
    config = build_ephemeral_config(tmp_path)

    validate_ephemeral_config(config, descriptor)

    assert config["dry_run"] is True
    assert config["trading_mode"] == "spot"
    assert config["freqai"]["rl_config"]["model_type"] == "PPO"
    assert config["freqai"]["rl_config"]["policy_type"] == "MlpPolicy"
    assert "timerange" not in config
    assert "train_period_days" not in config["freqai"]
    assert "backtest_period_days" not in config["freqai"]
    assert "live_retrain_hours" not in config["freqai"]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("dry_run",), False),
        (("trading_mode",), "futures"),
        (("freqai", "rl_config", "model_type"), "A2C"),
        (("freqai", "rl_config", "policy_type"), "CnnPolicy"),
    ],
)
def test_ephemeral_config_fails_closed_on_frozen_runtime_drift(
    tmp_path: Path,
    path: tuple[str, ...],
    value: object,
) -> None:
    config = build_ephemeral_config(tmp_path)
    cursor = config
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value

    with pytest.raises(RLV2ExecutionPreflightError):
        validate_ephemeral_config(config)


@pytest.mark.parametrize(
    "dotted_path",
    [
        "timerange",
        "freqai.train_period_days",
        "freqai.backtest_period_days",
        "freqai.live_retrain_hours",
    ],
)
def test_ephemeral_config_rejects_execution_geometry(
    tmp_path: Path,
    dotted_path: str,
) -> None:
    config = build_ephemeral_config(tmp_path)
    parts = dotted_path.split(".")
    cursor = config
    for key in parts[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[parts[-1]] = "forbidden"

    with pytest.raises(RLV2ExecutionPreflightError, match="Execution geometry is forbidden"):
        validate_ephemeral_config(config)


def test_preflight_source_contains_no_training_or_backtest_invocation() -> None:
    tree = ast.parse(SCRIPT_PATH.read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    called_attributes = {
        node.func.attr
        for node in calls
        if isinstance(node.func, ast.Attribute)
    }

    assert "fit" not in called_attributes
    assert "learn" not in called_attributes
    assert "train" not in called_attributes
    assert "start_backtesting" not in called_attributes
    assert "download_data" not in called_attributes


def test_descriptor_validation_fails_closed_on_runtime_drift(tmp_path: Path) -> None:
    descriptor = validate_descriptor()
    drifted = copy.deepcopy(descriptor)
    drifted["runtime_resolution"]["model_type"] = "A2C"
    path = tmp_path / "drifted.json"
    import json

    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(RLV2ExecutionPreflightError, match="model_type"):
        validate_descriptor(path)
