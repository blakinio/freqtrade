from __future__ import annotations

import ast
import math
from itertools import pairwise
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_PATH = REPO_ROOT / "ai_platform/strategies/AiFrozenCandidateStrategyV2.py"


def _reference_volume_change(volume: list[float]) -> list[float]:
    result = [0.0]
    for previous, current in pairwise(volume):
        denominator = abs(current) + abs(previous)
        change = 0.0 if denominator == 0 else 2.0 * (current - previous) / denominator
        result.append(change if math.isfinite(change) else 0.0)
    return result


def _strategy_tree() -> ast.Module:
    return ast.parse(STRATEGY_PATH.read_text(encoding="utf-8"))


def test_volume_change_is_finite_and_bounded_across_zero_volume() -> None:
    result = _reference_volume_change([0.0, 0.0, 10.0, 0.0, 5.0, 5.0])

    assert all(math.isfinite(value) for value in result)
    assert result == [0.0, 0.0, 2.0, -2.0, 2.0, 0.0]
    assert all(-2.0 <= value <= 2.0 for value in result)


def test_volume_change_preserves_direction_and_scale_symmetry() -> None:
    result = _reference_volume_change([10.0, 30.0, 10.0])

    assert result[1] == 1.0
    assert result[2] == -1.0


def test_strategy_contains_the_exact_finite_formula_and_single_override() -> None:
    tree = _strategy_tree()
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

    assert [function.name for function in functions] == ["bounded_symmetric_volume_change"]
    function_source = ast.unparse(functions[0])
    assert "2.0 * (volume - previous)" in function_source
    assert "denominator.where(denominator != 0)" in function_source
    assert "replace([float('inf'), float('-inf')], 0.0).fillna(0.0)" in function_source

    assert len(classes) == 1
    assert classes[0].name == "AiFrozenCandidateStrategyV2"
    methods = [method.name for method in classes[0].body if isinstance(method, ast.FunctionDef)]
    assert methods == ["feature_engineering_expand_basic"]
