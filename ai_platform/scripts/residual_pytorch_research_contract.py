#!/usr/bin/env python3
"""Validate the inert residual-PyTorch research foundation."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT / "ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json"
)
CONFIG_PATH = REPO_ROOT / "ai_platform/configs/freqai-residual-pytorch-research.example.json"
EXPERIMENT_PATH = REPO_ROOT / "ai_platform/experiments/residual-pytorch-research-v1.json"
MODEL_PATH = REPO_ROOT / "ai_platform/freqaimodels/ResidualPyTorchRegressor.py"
COMPONENTS_PATH = REPO_ROOT / "ai_platform/freqaimodels/residual_mlp_components.py"


class ResidualPyTorchContractError(RuntimeError):
    """Raised when the research foundation drifts from its frozen inert contract."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualPyTorchContractError(f"Unable to read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResidualPyTorchContractError(f"{label} must be a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResidualPyTorchContractError(message)


def validate_contract() -> dict[str, Any]:
    contract = _read_json(CONTRACT_PATH, "research contract")
    _require(contract.get("schema_version") == 1, "Contract schema drifted")
    _require(
        contract.get("contract_id") == "residual-pytorch-research-foundation-v1",
        "Contract id drifted",
    )
    _require(contract.get("status") == "implemented_not_executed", "Contract status drifted")

    candidate = contract.get("current_candidate", {})
    _require(candidate.get("model") == "ResidualPyTorchRegressor", "Candidate model drifted")
    _require(candidate.get("target_count") == 1, "Target-count boundary drifted")
    _require(candidate.get("loss") == "SmoothL1Loss", "Loss boundary drifted")
    _require(candidate.get("optimizer") == "AdamW", "Optimizer boundary drifted")
    _require(candidate.get("continual_learning") is False, "Continual learning must be disabled")

    isolation = contract.get("isolation", {})
    _require(isolation.get("phase5_entry_threshold") == 0.006, "Entry threshold drifted")
    _require(isolation.get("phase5_exit_threshold") == -0.009, "Exit threshold drifted")
    _require(isolation.get("phase6_selected_model") is None, "Phase 6 result drifted")
    _require(isolation.get("phase6_mutation_allowed") is False, "Phase 6 mutation enabled")
    _require(
        isolation.get("consumed_historical_oos", {}).get("usage") == "forbidden",
        "Consumed historical OOS became usable",
    )
    _require(
        isolation.get("protected_final_holdout", {}).get("usage") == "forbidden",
        "Protected final holdout became usable",
    )

    authorization = contract.get("authorization", {})
    _require(authorization, "Authorization section is missing")
    _require(
        all(value is False for value in authorization.values()),
        "The foundation must authorize no execution, tuning, deployment or promotion",
    )

    paths = contract.get("paths", {})
    for label, relative_path in paths.items():
        _require(isinstance(relative_path, str), f"Contract path {label} is invalid")
        _require(
            (REPO_ROOT / relative_path).is_file(),
            f"Contract path is missing: {relative_path}",
        )
    return contract


def validate_config() -> dict[str, Any]:
    config = _read_json(CONFIG_PATH, "research config")
    _require(config.get("dry_run") is True, "Research config must remain dry-run")
    _require(config.get("initial_state") == "stopped", "Research config must start stopped")
    _require(config.get("trading_mode") == "spot", "Research config must remain spot")
    _require(config.get("freqaimodel_path") == "ai_platform/freqaimodels", "Model path drifted")
    _require(
        config.get("exchange", {}).get("pair_whitelist") == ["BTC/USDT", "ETH/USDT"],
        "Pair universe drifted",
    )

    freqai = config.get("freqai", {})
    _require(
        freqai.get("identifier") == "ai-platform-residual-pytorch-research-v1",
        "Identifier drifted",
    )
    _require(freqai.get("continual_learning") is False, "Continual learning must remain disabled")
    _require(
        freqai.get("data_split_parameters")
        == {"test_size": 0.2, "random_state": 42, "shuffle": False},
        "Chronological split contract drifted",
    )
    training = freqai.get("model_training_parameters", {})
    _require(training.get("research_seed") == 42, "Research seed drifted")
    _require(training.get("learning_rate") == 0.0003, "Learning rate drifted")
    _require(training.get("weight_decay") == 0.0001, "Weight decay drifted")
    _require(training.get("loss_beta") == 0.01, "Huber beta drifted")
    _require(
        training.get("model_kwargs")
        == {
            "hidden_dim": 128,
            "n_blocks": 3,
            "expansion_factor": 2,
            "dropout_percent": 0.1,
            "residual_scale": 1.0,
        },
        "Residual architecture parameters drifted",
    )
    return config


def validate_experiment() -> dict[str, Any]:
    experiment = _read_json(EXPERIMENT_PATH, "experiment declaration")
    _require(experiment.get("status") == "declared_not_executed", "Experiment status drifted")
    _require(experiment.get("freqai_model") == "ResidualPyTorchRegressor", "Model binding drifted")
    _require(experiment.get("strategy") == "AiFrozenCandidateStrategy", "Strategy binding drifted")
    _require(experiment.get("target") == "&-future_return", "Target binding drifted")
    _require(experiment.get("execution_timerange") is None, "Execution window is unauthorized")
    _require(experiment.get("download_timerange") is None, "Download window is unauthorized")
    _require(experiment.get("run_request") is None, "Run request is unauthorized")
    _require(experiment.get("strict_oos") is False, "Strict-OOS claim is unauthorized")
    _require(
        experiment.get("protected_final_validation") is False,
        "Protected-final-validation claim is unauthorized",
    )
    _require(experiment.get("phase6_candidate") is False, "Phase 6 candidate mutation detected")
    _require(experiment.get("automatic_promotion") is False, "Automatic promotion enabled")
    return experiment


def validate_python_sources() -> None:
    for path in (MODEL_PATH, COMPONENTS_PATH):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ResidualPyTorchContractError(
                f"Unable to read Python source {path}: {exc}"
            ) from exc
        ast.parse(source, filename=str(path))

    model_source = MODEL_PATH.read_text(encoding="utf-8")
    component_source = COMPONENTS_PATH.read_text(encoding="utf-8")
    _require("class ResidualPyTorchRegressor" in model_source, "Regressor class is missing")
    _require("torch.optim.AdamW" in model_source, "AdamW binding is missing")
    _require("torch.nn.SmoothL1Loss" in model_source, "SmoothL1Loss binding is missing")
    _require("train_labels.shape[-1] != 1" in model_source, "Single-target guard is missing")
    _require("class ResidualFeedForwardBlock" in component_source, "Residual block is missing")
    _require(
        "return x + self.residual_scale * residual" in component_source,
        "Residual skip connection is missing",
    )


def validate_all() -> None:
    validate_contract()
    validate_config()
    validate_experiment()
    validate_python_sources()


def main() -> int:
    try:
        validate_all()
    except ResidualPyTorchContractError as exc:
        print(f"Residual PyTorch research contract failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
