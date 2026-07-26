from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from ai_platform.scripts.residual_pytorch_research_contract import (
    CONFIG_PATH,
    CONTRACT_PATH,
    EXPERIMENT_PATH,
    validate_all,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_residual_pytorch_foundation_contract_passes() -> None:
    validate_all()


def test_foundation_is_inert_and_isolated() -> None:
    contract = _load(CONTRACT_PATH)
    experiment = _load(EXPERIMENT_PATH)

    assert contract["status"] == "implemented_not_executed"
    assert all(value is False for value in contract["authorization"].values())
    assert contract["isolation"]["phase6_selected_model"] is None
    assert contract["isolation"]["consumed_historical_oos"]["usage"] == "forbidden"
    assert contract["isolation"]["protected_final_holdout"]["usage"] == "forbidden"
    assert experiment["execution_timerange"] is None
    assert experiment["download_timerange"] is None
    assert experiment["run_request"] is None
    assert experiment["phase6_candidate"] is False
    assert experiment["automatic_promotion"] is False


def test_config_defaults_fail_safe() -> None:
    config = _load(CONFIG_PATH)
    assert config["dry_run"] is True
    assert config["initial_state"] == "stopped"
    assert config["trading_mode"] == "spot"
    assert config["freqai"]["continual_learning"] is False
    assert config["freqai"]["data_split_parameters"]["shuffle"] is False
    assert config["exchange"]["key"] == ""
    assert config["exchange"]["secret"] == ""


def test_residual_block_preserves_identity_when_branch_is_zeroed() -> None:
    torch = pytest.importorskip("torch")
    module = importlib.import_module("ai_platform.freqaimodels.residual_mlp_components")
    block = module.ResidualFeedForwardBlock(
        hidden_dim=8,
        expansion_factor=2,
        dropout_percent=0.0,
        residual_scale=1.0,
    )
    block.eval()
    with torch.no_grad():
        for parameter in block.branch.parameters():
            parameter.zero_()
        inputs = torch.randn(4, 8)
        outputs = block(inputs)
    assert torch.equal(outputs, inputs)


def test_residual_network_shape_and_finite_output() -> None:
    torch = pytest.importorskip("torch")
    module = importlib.import_module("ai_platform.freqaimodels.residual_mlp_components")
    model = module.ResidualMLPNetwork(
        input_dim=12,
        output_dim=1,
        hidden_dim=16,
        n_blocks=2,
        expansion_factor=2,
        dropout_percent=0.0,
    )
    model.eval()
    with torch.no_grad():
        outputs = model(torch.randn(5, 12))
    assert outputs.shape == (5, 1)
    assert torch.isfinite(outputs).all()
