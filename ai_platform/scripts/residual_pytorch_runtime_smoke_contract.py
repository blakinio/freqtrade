"""Validate the bounded ResidualPyTorchRegressor P1 runtime-smoke package."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "ai_platform/experimental_model_research/residual-pytorch-runtime-smoke-contract-v1.json"
)
MODEL_PATH = REPO_ROOT / "ai_platform/freqaimodels/ResidualPyTorchRegressor.py"
SMOKE_PATH = REPO_ROOT / "ai_platform/scripts/residual_pytorch_runtime_smoke.py"
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/residual-pytorch-runtime-smoke.yml"
DOC_PATH = REPO_ROOT / "docs/ai_platform/RESIDUAL_PYTORCH_RUNTIME_SMOKE.md"
TASK_PATH = REPO_ROOT / "docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md"
TEST_PATH = REPO_ROOT / "tests/ai_platform/test_residual_pytorch_runtime_smoke_contract.py"


class ResidualRuntimeSmokeContractError(RuntimeError):
    """Raised when the P1 package drifts from its bounded runtime contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResidualRuntimeSmokeContractError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualRuntimeSmokeContractError(f"Unable to read {path}: {exc}") from exc
    _require(isinstance(payload, dict), f"{path} must contain a JSON object")
    return payload


def validate_contract() -> dict[str, Any]:
    contract = _read_json(CONTRACT_PATH)
    _require(contract.get("schema_version") == 1, "Contract schema drifted")
    _require(contract.get("stage") == "P1", "Runtime stage drifted")
    _require(contract.get("model") == "ResidualPyTorchRegressor", "Model binding drifted")
    _require(
        contract.get("resolver") == "FreqaiModelResolver.load_freqaimodel",
        "Resolver binding drifted",
    )
    _require(
        contract.get("outcomes")
        == ["runtime_supported", "runtime_not_supported", "runtime_inconclusive"],
        "Runtime outcomes drifted",
    )

    paths = contract.get("paths", {})
    _require(isinstance(paths, dict), "Contract paths are missing")
    for relative_path in paths.values():
        _require(isinstance(relative_path, str), "Contract path is invalid")
        _require((REPO_ROOT / relative_path).is_file(), f"Missing contract path: {relative_path}")

    synthetic = contract.get("synthetic_data", {})
    _require(synthetic.get("deterministic") is True, "Synthetic determinism drifted")
    _require(synthetic.get("exchange_download") is False, "Exchange download was enabled")
    _require(synthetic.get("market_data") is False, "Market data was enabled")

    required_checks = contract.get("required_checks", {})
    _require(bool(required_checks), "Required runtime checks are missing")
    _require(
        all(value is True for value in required_checks.values()), "A runtime check was disabled"
    )

    authorization = contract.get("authorization", {})
    _require(
        authorization.get("synthetic_training") is True, "Synthetic training is not authorized"
    )
    forbidden = {key: value for key, value in authorization.items() if key != "synthetic_training"}
    _require(bool(forbidden), "Forbidden authorization set is missing")
    _require(all(value is False for value in forbidden.values()), "A forbidden action was enabled")

    isolation = contract.get("isolation", {})
    _require(isolation.get("phase5_entry_threshold") == 0.006, "Entry threshold drifted")
    _require(isolation.get("phase5_exit_threshold") == -0.009, "Exit threshold drifted")
    _require(isolation.get("phase6_selected_model") is None, "Phase 6 result drifted")
    _require(
        isolation.get("consumed_historical_oos") == "20260501-20260630",
        "Historical OOS boundary drifted",
    )
    _require(
        isolation.get("protected_final_holdout") == "20260801-20260930",
        "Protected holdout boundary drifted",
    )
    return contract


def validate_sources() -> None:
    for path in (MODEL_PATH, SMOKE_PATH):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise ResidualRuntimeSmokeContractError(f"Invalid Python source {path}: {exc}") from exc

    model_source = MODEL_PATH.read_text(encoding="utf-8")
    smoke_source = SMOKE_PATH.read_text(encoding="utf-8")
    workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")

    for marker in (
        "if self.continual_learning:",
        "def _validate_training_data",
        '"parameter_count": parameter_count',
        "np.isfinite",
    ):
        _require(marker in model_source, f"Model runtime guard is missing: {marker}")

    for marker in (
        "FreqaiModelResolver.load_freqaimodel",
        "torch.cuda.is_available()",
        "trainer.save(checkpoint_path)",
        "torch.load(path, weights_only=False)",
        '"runtime_supported"',
        '"runtime_not_supported"',
        '"runtime_inconclusive"',
        '"market_data_used": False',
        '"backtest_performed": False',
        '"historical_oos_used": False',
        '"protected_holdout_used": False',
    ):
        _require(marker in smoke_source, f"Runtime smoke marker is missing: {marker}")

    _require(
        '-e ".[freqai,freqai_rl,develop]"' in workflow_source,
        "Complete residual runtime dependency install drifted",
    )
    _require(
        "python -m ai_platform.scripts.residual_pytorch_runtime_smoke" in workflow_source,
        "Dedicated runtime command is missing",
    )
    _require(
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow_source,
        "Artifact upload action is not pinned to the accepted SHA",
    )


def validate_all() -> None:
    validate_contract()
    validate_sources()


def main() -> int:
    try:
        validate_all()
    except ResidualRuntimeSmokeContractError as exc:
        print(f"Residual runtime-smoke contract failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
