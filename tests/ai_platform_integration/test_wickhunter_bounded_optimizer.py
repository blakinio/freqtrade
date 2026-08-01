from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from ai_platform.wickhunter.bounded_optimizer import (
    BoundedOptimizationResult,
    BoundedOptimizerError,
    BoundedOptimizerPolicy,
    TrialSelectionKind,
    optimize_bounded_parameters,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    INITIAL_COMPATIBILITY_PRIOR,
    WickHunterParameters,
)


@dataclass(frozen=True)
class _FakeCase:
    split_name: str
    case_sha256: str


@dataclass(frozen=True)
class _FakeSummary:
    decision_count: int
    selected_count: int
    net_return_mean: Decimal


@dataclass(frozen=True)
class _FakeSlice:
    dimension: str
    net_return_mean: Decimal


@dataclass(frozen=True)
class _FakeReport:
    report_id: str
    overall: _FakeSummary
    slices: tuple[_FakeSlice, ...]


def _cases(*, include_holdout: bool = False) -> tuple[_FakeCase, ...]:
    values = [
        _FakeCase("train", canonical_sha256({"split": "train"})),
        _FakeCase("validation", canonical_sha256({"split": "validation"})),
        _FakeCase("test", canonical_sha256({"split": "test"})),
    ]
    if include_holdout:
        values.append(_FakeCase("holdout", canonical_sha256({"split": "holdout"})))
    return tuple(values)


def _candidate(version: str) -> WickHunterParameters:
    return replace(INITIAL_COMPATIBILITY_PRIOR, parameter_version=version)


def _score(version: str, split_name: str) -> Decimal:
    validation = {
        "candidate-a": Decimal("0.08"),
        "candidate-b": Decimal("0.06"),
        "candidate-c": Decimal("0.04"),
        "candidate-d": Decimal("0.02"),
    }
    test = {
        "candidate-a": Decimal("-0.03"),
        "candidate-b": Decimal("0.05"),
        "candidate-c": Decimal("0.04"),
        "candidate-d": Decimal("0.10"),
    }
    if split_name == "validation":
        return validation[version]
    if split_name == "test":
        return test[version]
    return validation[version] - Decimal("0.01")


def _evaluator(**kwargs: Any) -> _FakeReport:
    cases = kwargs["cases"]
    parameters = kwargs["parameters"]
    split_name = cases[0].split_name
    value = _score(parameters.parameter_version, split_name)
    return _FakeReport(
        report_id=canonical_sha256(
            {
                "split_name": split_name,
                "parameter_hash": parameters.parameter_hash,
                "value": value,
            }
        ),
        overall=_FakeSummary(
            decision_count=10,
            selected_count=8,
            net_return_mean=value,
        ),
        slices=(
            _FakeSlice("symbol", value - Decimal("0.01")),
            _FakeSlice("symbol", value + Decimal("0.01")),
            _FakeSlice("regime", value),
        ),
    )


def _run(candidates: tuple[WickHunterParameters, ...]) -> BoundedOptimizationResult:
    return optimize_bounded_parameters(
        cases=_cases(),  # type: ignore[arg-type]
        candidates=candidates,
        parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
        policy=BoundedOptimizerPolicy(
            initial_trials=2,
            maximum_trials=4,
            top_k=2,
            exploration_ratio=Decimal("0.20"),
        ),
        evaluator=_evaluator,  # type: ignore[arg-type]
    )


def test_search_is_seeded_bounded_and_input_order_independent() -> None:
    candidates = tuple(
        _candidate(version)
        for version in (
            "candidate-a",
            "candidate-b",
            "candidate-c",
            "candidate-d",
        )
    )

    forward = _run(candidates)
    reverse = _run(tuple(reversed(candidates)))

    assert forward == reverse
    assert forward.result_id == reverse.result_id
    assert forward.search_space_size == 4
    assert forward.evaluated_trial_count == 4
    assert sum(trial.selection_kind is TrialSelectionKind.INITIAL for trial in forward.trials) == 2
    assert (
        sum(trial.selection_kind is TrialSelectionKind.SURROGATE for trial in forward.trials) == 2
    )


def test_selection_uses_validation_and_test_is_descriptive_only() -> None:
    result = _run(
        tuple(
            _candidate(version)
            for version in (
                "candidate-a",
                "candidate-b",
                "candidate-c",
                "candidate-d",
            )
        )
    )
    by_version = {trial.parameter_version: trial for trial in result.trials}

    assert result.selection_source == "validation_only"
    assert result.test_used_for_selection is False
    assert result.top_parameter_sha256s == (
        by_version["candidate-a"].parameter_sha256,
        by_version["candidate-b"].parameter_sha256,
    )
    assert by_version["candidate-a"].selected_top_k is True
    assert by_version["candidate-b"].selected_top_k is True
    assert by_version["candidate-d"].selected_top_k is False
    assert by_version["candidate-d"].test_report_id is None
    assert result.stability[0].validation_objective > result.stability[1].validation_objective
    assert result.stability[0].test_objective < result.stability[1].test_objective


def test_result_retains_fail_closed_authority_boundary() -> None:
    result = _run(
        tuple(
            _candidate(version)
            for version in (
                "candidate-a",
                "candidate-b",
                "candidate-c",
                "candidate-d",
            )
        )
    )

    assert result.protected_holdout_accessed is False
    assert result.model_promoted is False
    assert result.profitability_claimed is False
    assert result.execution_enabled is False
    assert result.live_capital_authorized is False
    assert result.orders_submitted == 0
    assert all(trial.test_evidence is not None for trial in result.trials if trial.selected_top_k)
    assert all(trial.test_evidence is None for trial in result.trials if not trial.selected_top_k)


def test_protected_holdout_duplicate_space_and_budget_fail_closed() -> None:
    candidates = (
        _candidate("candidate-a"),
        _candidate("candidate-b"),
        _candidate("candidate-c"),
        _candidate("candidate-d"),
    )
    with pytest.raises(BoundedOptimizerError, match="protected holdout"):
        optimize_bounded_parameters(
            cases=_cases(include_holdout=True),  # type: ignore[arg-type]
            candidates=candidates,
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
            policy=BoundedOptimizerPolicy(
                initial_trials=2,
                maximum_trials=4,
                top_k=2,
            ),
            evaluator=_evaluator,  # type: ignore[arg-type]
        )

    with pytest.raises(BoundedOptimizerError, match="unique"):
        optimize_bounded_parameters(
            cases=_cases(),  # type: ignore[arg-type]
            candidates=(candidates[0], candidates[0]),
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
            policy=BoundedOptimizerPolicy(
                initial_trials=1,
                maximum_trials=2,
                top_k=1,
            ),
            evaluator=_evaluator,  # type: ignore[arg-type]
        )

    with pytest.raises(BoundedOptimizerError, match="initial_trials exceed"):
        optimize_bounded_parameters(
            cases=_cases(),  # type: ignore[arg-type]
            candidates=candidates[:2],
            parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
            policy=BoundedOptimizerPolicy(
                initial_trials=3,
                maximum_trials=4,
                top_k=1,
            ),
            evaluator=_evaluator,  # type: ignore[arg-type]
        )
