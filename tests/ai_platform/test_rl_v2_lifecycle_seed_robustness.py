import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_lifecycle_seed_robustness_evidence import (
    RLV2SeedEvidenceError,
    aggregate_seed_evidence,
    extract_seed_evidence,
)
from ai_platform.scripts.rl_v2_lifecycle_seed_robustness_run_request import (
    ANCHOR_SEED,
    NEW_SEEDS,
    REQUEST_REPO_PATH,
    RLV2SeedRobustnessError,
    canonical_rl_v2_lifecycle_seed_robustness_request,
    materialize_seed_runtime_config,
    runtime_identifier,
)


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ai_platform/configs/rl_v2_training_research.json"
WORKFLOW = ROOT / ".github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml"


def _archive(path: Path, seed: int, count: int = 20) -> Path:
    trades = []
    for index in range(count):
        open_rate = 100.0 + index
        close_rate = open_rate + (1.0 if index % 3 == 0 else -0.25)
        fees = open_rate * 0.002 + close_rate * 0.002
        trades.append(
            {
                "pair": "BTC/USDT" if index % 2 == 0 else "ETH/USDT",
                "amount": 1.0,
                "open_timestamp": index * 180 * 60 * 1000,
                "close_timestamp": (index * 180 + 60) * 60 * 1000,
                "open_rate": open_rate,
                "close_rate": close_rate,
                "fee_open": 0.002,
                "fee_close": 0.002,
                "profit_abs": close_rate - open_rate - fees,
                "exit_reason": "freqai_rl_v2_target_flat",
                "is_short": False,
            }
        )
    strategy = "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    result = {
        "strategy": {
            strategy: {
                "strategy_name": strategy,
                "freqaimodel": "DesiredPositionReinforcementLearner",
                "freqai_identifier": runtime_identifier(seed),
                "ignore_roi_if_entry_signal": True,
                "timerange": "20260301-20260501",
                "timeframe": "15m",
                "trading_mode": "spot",
                "trade_count_short": 0,
                "minimal_roi": {"0": 0.03, "240": 0.015, "720": 0.0},
                "stoploss": -0.05,
                "use_exit_signal": True,
                "total_trades": len(trades),
                "profit_factor": 0.75,
                "max_drawdown_abs": 1.0,
                "rejected_signals": 0,
                "timedout_entry_orders": 0,
                "timedout_exit_orders": 0,
                "trades": trades,
            }
        }
    }
    with zipfile.ZipFile(path, "w") as bundle:
        bundle.writestr("result.json", json.dumps(result))
        bundle.writestr("result_config.json", "{}")
    return path


def _evidence_file(tmp_path: Path, seed: int, count: int = 20) -> Path:
    payload = extract_seed_evidence(_archive(tmp_path / f"{seed}.zip", seed, count), seed)
    path = tmp_path / f"{seed}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_request_and_materialization_are_seed_only(tmp_path: Path) -> None:
    request = canonical_rl_v2_lifecycle_seed_robustness_request()
    assert request["anchor_seed"] == ANCHOR_SEED
    assert request["new_execution_seeds"] == list(NEW_SEEDS)
    assert request["new_variant_execution_count"] == 4
    assert request["baseline_rerun_allowed"] is False
    assert request["strict_oos"] is False

    base = json.loads(BASE.read_text(encoding="utf-8"))
    output = tmp_path / "runtime.json"
    materialize_seed_runtime_config(output, NEW_SEEDS[0])
    runtime = json.loads(output.read_text(encoding="utf-8"))
    expected = deepcopy(base)
    expected["strategy"] = "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    expected["freqai"]["identifier"] = runtime_identifier(NEW_SEEDS[0])
    expected["freqai"]["train_period_days"] = 90
    expected["freqai"]["backtest_period_days"] = 61
    expected["freqai"]["model_training_parameters"]["seed"] = NEW_SEEDS[0]
    assert runtime == expected
    assert runtime["freqai"]["data_split_parameters"]["random_state"] == 42


def test_materialization_rejects_anchor_and_unknown_seed(tmp_path: Path) -> None:
    with pytest.raises(RLV2SeedRobustnessError, match="Anchor seed"):
        materialize_seed_runtime_config(tmp_path / "anchor.json", ANCHOR_SEED)
    with pytest.raises(RLV2SeedRobustnessError, match="outside"):
        materialize_seed_runtime_config(tmp_path / "unknown.json", 7)


def test_per_seed_validity_and_supported_aggregate(tmp_path: Path) -> None:
    paths = [_evidence_file(tmp_path, seed) for seed in NEW_SEEDS]
    seed_payload = json.loads(paths[0].read_text(encoding="utf-8"))
    assert seed_payload["valid"] is True
    assert seed_payload["pair_trade_counts"] == {"BTC/USDT": 10, "ETH/USDT": 10}
    assert seed_payload["strong_reduction_support"]["all_strong_criteria_met"] is True

    aggregate = aggregate_seed_evidence(paths)
    assert aggregate["ordered_seeds"] == [ANCHOR_SEED, *NEW_SEEDS]
    assert aggregate["new_seed_execution_count"] == 4
    assert aggregate["anchor_seed_rerun"] is False
    assert aggregate["baseline_rerun"] is False
    assert aggregate["decision"] == "supported"


def test_invalid_seed_is_inconclusive_and_not_replaced(tmp_path: Path) -> None:
    paths = [
        _evidence_file(tmp_path, seed, 10 if index == 0 else 20)
        for index, seed in enumerate(NEW_SEEDS)
    ]
    aggregate = aggregate_seed_evidence(paths)
    assert aggregate["decision"] == "inconclusive"
    assert aggregate["invalid_seeds"] == [NEW_SEEDS[0]]
    assert aggregate["invalid_seed_replacement_allowed"] is False


def test_aggregate_rejects_tampered_support(tmp_path: Path) -> None:
    paths = [_evidence_file(tmp_path, seed) for seed in NEW_SEEDS]
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    payload["strong_reduction_support"]["all_strong_criteria_met"] = False
    paths[0].write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RLV2SeedEvidenceError, match="strong support"):
        aggregate_seed_evidence(paths)


def test_workflow_is_inert_and_four_seed_only() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert REQUEST_REPO_PATH in workflow
    assert workflow.count("freqtrade backtesting") == 1
    assert all(str(seed) in workflow for seed in NEW_SEEDS)
    assert "seed: 42" not in workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in workflow
    assert not (ROOT / REQUEST_REPO_PATH).exists()
