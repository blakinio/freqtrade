from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_action_observability import (
    RLV2ActionObservabilityError,
    RLV2ActionObservabilityRecorder,
    validate_action_observability_artifacts,
)
from ai_platform.scripts.rl_v2_action_observability_execution_evidence import (
    aggregate_seed_evidence,
    analyze_rows_and_trades,
)
from ai_platform.scripts.rl_v2_action_observability_execution_run_request import (
    BASE_CONFIG_REPO_PATH,
    CONTRACT_REPO_PATH,
    EXPECTED_CLASSIFICATION,
    EXPECTED_GEOMETRY,
    NEW_SEEDS,
    REQUEST_REPO_PATH,
    WORKFLOW_REPO_PATH,
    _read_json,
    _repo_path,
    _validate_contract,
    canonical_request,
    materialize_runtime_config,
    runtime_identifier,
)


def _row(
    pair: str,
    timestamp: str,
    action: int,
    accepted: bool,
    ordinal: int,
) -> dict:
    label = "target_long" if action == 1 else "target_flat"
    enter = accepted and action == 1
    exit_long = accepted and action == 0
    return {
        "pair": pair,
        "timestamp_utc": timestamp,
        "source_row_ordinal": ordinal,
        "action_raw": action,
        "action_label": label,
        "do_predict_raw": 1 if accepted else 0,
        "prediction_accepted": accepted,
        "volume_positive": True,
        "pre_trade_enter_long": enter,
        "pre_trade_exit_long": exit_long,
        "pre_trade_enter_tag": "freqai_rl_v2_target_long" if enter else None,
        "pre_trade_exit_tag": "freqai_rl_v2_target_flat" if exit_long else None,
    }


def _trade(
    pair: str = "BTC/USDT",
    open_timestamp: int = 1_756_694_400_000,
    close_timestamp: int = 1_756_701_600_000,
) -> dict:
    return {
        "pair": pair,
        "is_short": False,
        "open_timestamp": open_timestamp,
        "close_timestamp": close_timestamp,
        "amount": 1.0,
        "open_rate": 100.0,
        "close_rate": 101.0,
        "fee_open": 0.001,
        "fee_close": 0.001,
        "profit_abs": 0.799,
        "exit_reason": "freqai_rl_v2_target_flat",
    }


def test_contract_request_and_geometry_are_frozen() -> None:
    contract, declaration, base_config = _validate_contract()
    assert contract["execution_geometry"] == EXPECTED_GEOMETRY
    assert contract["seed_matrix"]["ordered_execution_seeds"] == list(NEW_SEEDS)
    assert declaration["isolation"]["classification"] == EXPECTED_CLASSIFICATION
    assert base_config["freqai"]["data_split_parameters"]["shuffle"] is False
    assert not _repo_path(REQUEST_REPO_PATH).exists()

    request = canonical_request()
    assert request["execution_seeds"] == list(NEW_SEEDS)
    assert request["execution_count"] == 4
    assert request["cache_restore_allowed"] is False
    assert request["automatic_decision"] is False


def test_runtime_config_changes_only_declared_fields(tmp_path: Path) -> None:
    seed = NEW_SEEDS[0]
    output = materialize_runtime_config(tmp_path / "runtime.json", seed)
    actual = json.loads(output.read_text(encoding="utf-8"))
    base = _read_json(_repo_path(BASE_CONFIG_REPO_PATH), "base config")

    expected = json.loads(json.dumps(base))
    expected["strategy"] = (
        "AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy"
    )
    expected["freqai"]["identifier"] = runtime_identifier(seed)
    expected["freqai"]["train_period_days"] = 90
    expected["freqai"]["backtest_period_days"] = 61
    expected["freqai"]["model_training_parameters"]["seed"] = seed
    assert actual == expected


def test_action_trade_analysis_uses_declared_interval_semantics() -> None:
    rows = [
        _row("BTC/USDT", "2025-08-31T23:45:00Z", 1, True, 0),
        _row("BTC/USDT", "2025-09-01T00:15:00Z", 1, True, 1),
        _row("BTC/USDT", "2025-09-01T00:30:00Z", 0, False, 2),
        _row("BTC/USDT", "2025-09-01T02:15:00Z", 0, True, 3),
    ]
    evidence = analyze_rows_and_trades(rows, [_trade()])
    assert evidence["position_rows"] == {"flat": 2, "long": 2}
    assert evidence["transition_counts"] == {
        "hold_flat": 1,
        "enter_long": 1,
        "hold_long": 2,
        "exit_long": 0,
    }
    assert evidence["long_state_action_gate_counts"] == {
        "accepted_target_long": 1,
        "accepted_target_flat": 0,
        "rejected_target_long": 0,
        "rejected_target_flat": 1,
    }
    assert evidence["maximum_accepted_action_streaks_by_pair"]["BTC/USDT"] == {
        "target_flat": 1,
        "target_long": 2,
    }


def test_aggregate_is_exact_four_seed_and_has_no_decision(tmp_path: Path) -> None:
    paths: list[Path] = []
    for seed in NEW_SEEDS:
        payload = {
            "schema_version": 1,
            "classification": EXPECTED_CLASSIFICATION,
            "automatic_decision": False,
            "seed": seed,
            "timeline_row_count": 10,
            "timeline_sha256": f"{seed:064x}"[-64:],
            "action_summary": {
                "totals": {
                    "actions": {"target_flat": 4, "target_long": 6},
                    "do_predict": {"accepted": 8, "rejected": 2},
                }
            },
            "derived_position_action_evidence": {
                "transition_counts": {
                    "hold_flat": 2,
                    "enter_long": 1,
                    "hold_long": 6,
                    "exit_long": 1,
                },
                "long_state_action_gate_counts": {
                    "accepted_target_long": 4,
                    "accepted_target_flat": 1,
                    "rejected_target_long": 1,
                    "rejected_target_flat": 0,
                },
            },
            "descriptive_trade_metrics": {
                "trade_count": 3,
                "median_duration_minutes": 120.0,
            },
        }
        path = tmp_path / f"{seed}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths.append(path)

    aggregate = aggregate_seed_evidence(paths)
    assert aggregate["ordered_seeds"] == list(NEW_SEEDS)
    assert aggregate["seed_count"] == 4
    assert aggregate["decision"] is None
    assert aggregate["automatic_decision"] is False
    assert aggregate["aggregate_action_counts"] == {
        "target_flat": 16,
        "target_long": 24,
    }


def test_workflow_is_inert_and_exact_four_seed_only() -> None:
    workflow = _repo_path(WORKFLOW_REPO_PATH).read_text(encoding="utf-8")
    assert REQUEST_REPO_PATH in workflow
    assert "types: [opened]" in workflow
    assert "actions/cache/" not in workflow
    assert "cache restore" not in workflow.casefold()
    assert "20250601-20251101" in workflow
    assert "20250901-20251101" in workflow
    for seed in NEW_SEEDS:
        assert str(seed) in workflow
    for prior_seed in (42, 300538280, 1710810709, 1950377252, 1146911492):
        assert f"- {prior_seed}\n" not in workflow
    assert workflow.count("freqtrade backtesting") == 1
    assert '"decision": None' in workflow


def test_contract_json_path_and_request_absence() -> None:
    contract = _read_json(_repo_path(CONTRACT_REPO_PATH), "contract")
    assert contract["request_path"] == REQUEST_REPO_PATH
    assert contract["authorization"]["canonical_request_required"] is True
    assert (
        contract["authorization"]["infrastructure_merge_executes_model"]
        is False
    )
    assert not _repo_path(REQUEST_REPO_PATH).exists()


def test_observable_strategy_disabled_and_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pandas = pytest.importorskip("pandas")
    observable_module = importlib.import_module(
        "ai_platform.strategies."
        "AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy"
    )
    parent_module = importlib.import_module(
        "ai_platform.strategies."
        "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    )
    observable_strategy = (
        observable_module.AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy
    )
    parent_strategy = parent_module.AiDesiredPositionRLLifecycleAlignedResearchStrategy

    monkeypatch.setattr(
        parent_strategy,
        "populate_exit_trend",
        lambda self, dataframe, metadata: dataframe,
    )

    disabled = object.__new__(observable_strategy)
    disabled._action_observability_recorder = RLV2ActionObservabilityRecorder(
        enabled=False
    )
    disabled._action_observability_pairs = set()
    incomplete = pandas.DataFrame({"unrelated": [1]})
    assert disabled.populate_exit_trend(incomplete, {}) is incomplete

    enabled = object.__new__(observable_strategy)
    enabled._action_observability_recorder = RLV2ActionObservabilityRecorder(
        enabled=True
    )
    enabled._action_observability_pairs = set()
    environment = {
        "RL_V2_ACTION_OBSERVABILITY_OUTPUT_DIR": str(tmp_path),
        "RL_V2_ACTION_OBSERVABILITY_GIT_COMMIT": "c" * 40,
        "RL_V2_ACTION_OBSERVABILITY_STRATEGY_SHA256": "a" * 64,
        "RL_V2_ACTION_OBSERVABILITY_MODEL_NAME": "DesiredPositionReinforcementLearner",
        "RL_V2_ACTION_OBSERVABILITY_MODEL_SHA256": "b" * 64,
        "RL_V2_ACTION_OBSERVABILITY_CONFIG_SHA256": "d" * 64,
        "RL_V2_ACTION_OBSERVABILITY_IDENTIFIER": runtime_identifier(NEW_SEEDS[0]),
        "RL_V2_ACTION_OBSERVABILITY_SEED": str(NEW_SEEDS[0]),
        "RL_V2_ACTION_OBSERVABILITY_TIMERANGE": "20250901-20251101",
        "RL_V2_ACTION_OBSERVABILITY_TIMEFRAME": "15m",
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    frame = pandas.DataFrame(
        {
            "date": pandas.to_datetime(
                ["2025-09-01T00:00:00Z", "2025-09-01T00:15:00Z"],
                utc=True,
            ),
            "&-action": [1, 0],
            "do_predict": [1, 1],
            "volume": [2.0, 2.0],
        }
    )
    enabled.populate_exit_trend(frame.copy(), {"pair": "BTC/USDT"})
    enabled.populate_exit_trend(frame.copy(), {"pair": "ETH/USDT"})
    artifacts = validate_action_observability_artifacts(tmp_path)
    assert artifacts["manifest"]["pairs"] == ["BTC/USDT", "ETH/USDT"]
    assert artifacts["manifest"]["row_count"] == 4
    with pytest.raises(RLV2ActionObservabilityError, match="more than once"):
        enabled.populate_exit_trend(frame.copy(), {"pair": "BTC/USDT"})
