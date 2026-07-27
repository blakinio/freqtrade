from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_PATH = REPO_ROOT / "ai_platform/strategies/AiFrozenCandidateStrategyV2.py"


def _volume_change_function() -> Callable[[pd.Series], pd.Series]:
    tree = ast.parse(STRATEGY_PATH.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "bounded_symmetric_volume_change"
    )
    module = ast.Module(body=[function], type_ignores=[])
    namespace: dict[str, Any] = {"Series": pd.Series}
    exec(compile(module, STRATEGY_PATH.as_posix(), "exec"), namespace)
    return namespace["bounded_symmetric_volume_change"]


def test_volume_change_is_finite_and_bounded_across_zero_volume() -> None:
    volume = pd.Series([0.0, 0.0, 10.0, 0.0, 5.0, 5.0])
    result = _volume_change_function()(volume)

    assert np.isfinite(result.to_numpy(dtype=float)).all()
    assert result.tolist() == [0.0, 0.0, 2.0, -2.0, 2.0, 0.0]
    assert result.between(-2.0, 2.0).all()


def test_volume_change_preserves_direction_and_scale_symmetry() -> None:
    volume = pd.Series([10.0, 30.0, 10.0])
    result = _volume_change_function()(volume)

    assert result.iloc[1] == 1.0
    assert result.iloc[2] == -1.0


def test_strategy_uses_only_the_versioned_volume_change_override() -> None:
    tree = ast.parse(STRATEGY_PATH.read_text(encoding="utf-8"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

    assert len(classes) == 1
    assert classes[0].name == "AiFrozenCandidateStrategyV2"
    assert [method.name for method in classes[0].body if isinstance(method, ast.FunctionDef)] == [
        "feature_engineering_expand_basic"
    ]
