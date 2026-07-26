from __future__ import annotations

import json
from pathlib import Path

from ai_platform.scripts.residual_pytorch_runtime_smoke_contract import (
    CONTRACT_PATH,
    MODEL_PATH,
    SMOKE_PATH,
    WORKFLOW_PATH,
    validate_all,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_residual_runtime_smoke_contract_passes() -> None:
    validate_all()


def test_runtime_smoke_is_synthetic_only_and_non_promotional() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["stage"] == "P1"
    assert contract["outcomes"] == [
        "runtime_supported",
        "runtime_not_supported",
        "runtime_inconclusive",
    ]
    assert contract["synthetic_data"]["market_data"] is False
    assert contract["synthetic_data"]["exchange_download"] is False
    assert contract["authorization"]["synthetic_training"] is True
    assert all(
        value is False
        for key, value in contract["authorization"].items()
        if key != "synthetic_training"
    )


def test_model_runtime_guards_are_present() -> None:
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "if self.continual_learning:" in source
    assert "def _validate_training_data" in source
    assert '"parameter_count": parameter_count' in source
    assert "np.isfinite" in source


def test_dedicated_workflow_executes_and_uploads_report() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert '-e ".[freqai,freqai_rl,develop]"' in workflow
    assert "python -m ai_platform.scripts.residual_pytorch_runtime_smoke" in workflow
    assert "if: always()" in workflow
    assert "retention-days: 30" in workflow


def test_smoke_reports_only_allowed_outcomes() -> None:
    source = SMOKE_PATH.read_text(encoding="utf-8")
    for outcome in (
        "runtime_supported",
        "runtime_not_supported",
        "runtime_inconclusive",
    ):
        assert outcome in source
    assert '"market_data_used": False' in source
    assert '"backtest_performed": False' in source
    assert '"historical_oos_used": False' in source
    assert '"protected_holdout_used": False' in source
