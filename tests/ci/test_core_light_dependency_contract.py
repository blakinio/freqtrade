from pathlib import Path

import pytest

from tools.ci.change_classifier import classify
from tools.ci.run_core_light import (
    MAX_TESTS,
    MIN_TESTS,
    load_targets,
    parse_collection_count,
)


OPTIONAL_PACKAGES = (
    "pyyaml==",
    "plotly==",
    "optuna==",
    "datasieve==",
    "pip-audit==",
    "lightgbm==",
    "xgboost==",
)
CRITICAL_TEST_PREFIXES = (
    "tests/data",
    "tests/exchange",
    "tests/freqai",
    "tests/optimize",
    "tests/persistence",
    "tests/rpc",
    "tests/strategy",
)


def _workflow() -> str:
    return Path(".github/workflows/ci.yml").read_text(encoding="utf-8")


def _core_light_block() -> str:
    workflow = _workflow()
    start = workflow.index("  core-light:\n")
    end = workflow.index("\n  pre-commit:\n", start)
    return workflow[start:end]


def test_core_light_uses_bounded_runner_and_ordinary_dependencies() -> None:
    block = _core_light_block()
    assert "pytest-xdist==3.8.0" in block
    assert "python tools/ci/run_core_light.py" in block
    assert "if: needs.classify.outputs.core_light == 'true'" in block
    assert "core_matrix != 'true'" not in block
    assert "pytest -q --durations 20 -n auto" not in block
    for package in OPTIONAL_PACKAGES:
        assert package not in block


def test_core_light_manifest_is_explicit_safe_and_noncritical() -> None:
    targets = load_targets()
    assert 10 <= len(targets) <= 25
    for target in targets:
        assert not target.startswith(CRITICAL_TEST_PREFIXES)
    assert MIN_TESTS == 200
    assert MAX_TESTS == 800


def test_collection_summary_parser_is_fail_closed() -> None:
    assert parse_collection_count("321 tests collected in 1.23s\n") == 321
    with pytest.raises(ValueError, match="summary"):
        parse_collection_count("collection completed")


def test_full_routes_execute_bounded_smoke_and_complete_matrix() -> None:
    outputs = classify([".github/workflows/ci.yml"])["outputs"]
    assert outputs["full"]
    assert outputs["core_light"]
    assert outputs["core_matrix"]


def test_complete_core_suite_and_gate_remain_enforced() -> None:
    workflow = _workflow()
    assert "run: pytest --random-order --durations 20 -n auto" in workflow
    assert (
        "run: pytest --random-order --cov=freqtrade --cov=freqtrade_client --cov-config=.coveragerc"
    ) in workflow
    assert (
        'require_success "$CORE_LIGHT_SCOPE" "$CORE_LIGHT_RESULT" "Bounded core validation"'
    ) in workflow
