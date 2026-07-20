import copy
import json
from pathlib import Path

import pytest

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_oos_result_extractor import (
    CANONICAL_MATERIALIZATION_ROOT,
    DEFAULT_COMPARISON_CONTRACT,
    _validate_manifest_against_comparison,
)


def test_extractor_manifest_validation_rejects_protected_final_holdout(tmp_path: Path) -> None:
    materialization = build_materialization(
        DEFAULT_COMPARISON_CONTRACT,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    manifest = copy.deepcopy(materialization["models"][0]["manifest"])
    manifest["timerange"] = "20260801-20260930"
    manifest_path = tmp_path / "protected-final-holdout-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    comparison = load_model_comparison_contract(DEFAULT_COMPARISON_CONTRACT)

    with pytest.raises(RuntimeError, match="overlaps protected final holdout"):
        _validate_manifest_against_comparison(manifest_path, comparison)
