from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from ai_platform.wickhunter.bounded_optimizer import (
    BoundedOptimizationResult,
    BoundedOptimizerError,
    BoundedOptimizerPolicy,
    ModelAwareReport,
    ParameterScope,
    ScopeSpec,
    TrialSelectionKind,
    WalkForwardFold,
    optimize_bounded_parameters,
    optimize_model_aware_walk_forward,
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


@dataclass(frozen=True)
class _WalkForwardLabel:
    label_end_ms: int


@dataclass(frozen=True)
class _WalkForwardFeature:
    symbol: str
    decision_timestamp_ms: int
    trend_return_ratio: Decimal

    def metric(self, name: str) -> Decimal:
        if name != "trend_return_ratio":
            raise KeyError(name)
        return self.trend_return_ratio


@dataclass(frozen=True)
class _WalkForwardCase:
    split_name: str
    case_sha256: str
    feature: _WalkForwardFeature
    labels: tuple[_WalkForwardLabel, ...]


def _walk_forward_cases(*, include_holdout: bool = False) -> tuple[_WalkForwardCase, ...]:
    rows = (
        ("train-1", 100, 120, "BTC", Decimal("0.01")),
        ("calibration-1", 140, 150, "ETH", Decimal("0.00")),
        ("validation-1", 200, 220, "BTC", Decimal("-0.01")),
        ("test-1", 300, 320, "ETH", Decimal("0.01")),
        ("train-2", 400, 420, "BTC", Decimal("0.01")),
        ("calibration-2", 440, 450, "ETH", Decimal("0.00")),
        ("validation-2", 500, 520, "BTC", Decimal("-0.01")),
        ("test-2", 600, 620, "ETH", Decimal("0.01")),
    )
    cases = [
        _WalkForwardCase(
            split_name=split_name,
            case_sha256=canonical_sha256(
                {"split_name": split_name, "decision_timestamp_ms": timestamp}
            ),
            feature=_WalkForwardFeature(
                symbol=symbol,
                decision_timestamp_ms=timestamp,
                trend_return_ratio=trend,
            ),
            labels=(_WalkForwardLabel(label_end_ms=label_end_ms),),
        )
        for split_name, timestamp, label_end_ms, symbol, trend in rows
    ]
    if include_holdout:
        cases.append(
            _WalkForwardCase(
                split_name="holdout",
                case_sha256=canonical_sha256({"split_name": "holdout"}),
                feature=_WalkForwardFeature(
                    symbol="BTC",
                    decision_timestamp_ms=700,
                    trend_return_ratio=Decimal("0"),
                ),
                labels=(_WalkForwardLabel(label_end_ms=720),),
            )
        )
    return tuple(cases)


def _walk_forward_folds() -> tuple[WalkForwardFold, ...]:
    return (
        WalkForwardFold(
            fold_id="fold-1",
            training_splits=("train-1",),
            calibration_splits=("calibration-1",),
            validation_splits=("validation-1",),
            test_splits=("test-1",),
            purge_ms=40,
            embargo_ms=50,
        ),
        WalkForwardFold(
            fold_id="fold-2",
            training_splits=("train-2",),
            calibration_splits=("calibration-2",),
            validation_splits=("validation-2",),
            test_splits=("test-2",),
            purge_ms=40,
            embargo_ms=50,
        ),
    )


def _walk_forward_candidate(version: str, zscore: str) -> WickHunterParameters:
    return replace(
        INITIAL_COMPATIBILITY_PRIOR,
        parameter_version=version,
        liquidation_zscore=Decimal(zscore),
    )


def _walk_forward_candidates() -> tuple[WickHunterParameters, ...]:
    return (
        _walk_forward_candidate("candidate-a", "1.0"),
        _walk_forward_candidate("candidate-b", "1.5"),
        _walk_forward_candidate("candidate-c", "2.0"),
        _walk_forward_candidate("candidate-d", "2.5"),
    )


def _walk_forward_baseline_evaluator(**kwargs: Any) -> _FakeReport:
    cases = kwargs["cases"]
    parameters = kwargs["parameters"]
    split_name = cases[0].split_name
    validation_values = {
        "candidate-a": Decimal("0.08"),
        "candidate-b": Decimal("0.06"),
        "candidate-c": Decimal("0.04"),
        "candidate-d": Decimal("0.02"),
    }
    test_values = {
        "candidate-a": Decimal("-0.05"),
        "candidate-b": Decimal("0.05"),
        "candidate-c": Decimal("0.04"),
        "candidate-d": Decimal("0.10"),
    }
    values = test_values if split_name.startswith("test") else validation_values
    value = values[parameters.parameter_version]
    return _FakeReport(
        report_id=canonical_sha256(
            {
                "kind": "baseline",
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


def _walk_forward_model_evaluator(**kwargs: Any) -> ModelAwareReport:
    parameters = kwargs["parameters"]
    target_splits = kwargs["target_splits"]
    target = target_splits[0]
    validation_values = {
        "candidate-a": Decimal("0.12"),
        "candidate-b": Decimal("0.09"),
        "candidate-c": Decimal("0.05"),
        "candidate-d": Decimal("0.01"),
    }
    test_values = {
        "candidate-a": Decimal("-0.02"),
        "candidate-b": Decimal("0.07"),
        "candidate-c": Decimal("0.06"),
        "candidate-d": Decimal("0.20"),
    }
    values = test_values if target.startswith("test") else validation_values
    value = values[parameters.parameter_version]
    model_hash = canonical_sha256(
        {
            "kind": "model",
            "parameter_hash": parameters.parameter_hash,
            "training_splits": kwargs["training_splits"],
            "calibration_splits": kwargs["calibration_splits"],
            "seed": kwargs["seed"],
        }
    )
    return ModelAwareReport(
        report_id=canonical_sha256(
            {
                "kind": "model-report",
                "target": target,
                "parameter_hash": parameters.parameter_hash,
                "value": value,
            }
        ),
        overall=_FakeSummary(
            decision_count=10,
            selected_count=7,
            net_return_mean=value,
        ),
        slices=(
            _FakeSlice("symbol", value - Decimal("0.01")),
            _FakeSlice("symbol", value + Decimal("0.01")),
            _FakeSlice("side", value),
        ),
        model_hash=model_hash,
    )


def test_model_aware_walk_forward_is_validation_only_and_deterministic() -> None:
    candidates = _walk_forward_candidates()
    scopes = (
        ScopeSpec(ParameterScope.GLOBAL, "global", minimum_case_count=4),
        ScopeSpec(ParameterScope.SYMBOL_CLUSTER, "majors", minimum_case_count=4),
        ScopeSpec(
            ParameterScope.SYMBOL_CLUSTER,
            "sparse",
            minimum_case_count=4,
            inherited_from="global",
        ),
    )
    kwargs: dict[str, Any] = {
        "cases": _walk_forward_cases(),
        "parameter_bounds": DEFAULT_RESEARCH_BOUNDS,
        "folds": _walk_forward_folds(),
        "scopes": scopes,
        "dataset_sha256": canonical_sha256({"dataset": "wickhunter"}),
        "code_sha": "a" * 40,
        "symbol_clusters": {"BTC": "majors", "ETH": "majors"},
        "policy": BoundedOptimizerPolicy(
            initial_trials=2,
            maximum_trials=4,
            top_k=2,
        ),
        "model_evaluator": _walk_forward_model_evaluator,
        "baseline_evaluator": _walk_forward_baseline_evaluator,
    }

    forward = optimize_model_aware_walk_forward(
        candidates=candidates,
        **kwargs,  # type: ignore[arg-type]
    )
    reverse = optimize_model_aware_walk_forward(
        candidates=tuple(reversed(candidates)),
        **kwargs,  # type: ignore[arg-type]
    )

    assert forward == reverse
    global_result, cluster_result, sparse_result = forward
    assert global_result.selected_package.parameter_version == "candidate-a"
    assert cluster_result.selected_package.parameter_version == "candidate-a"
    assert sparse_result.selected_package.parameter_sha256 == (
        global_result.selected_package.parameter_sha256
    )
    assert sparse_result.inherited_from == "global"
    assert global_result.test_used_for_selection is False
    assert global_result.selected_package.test_objective is not None
    assert global_result.selected_package.test_objective < Decimal("0")
    assert all(item.model_test_report_id is not None for item in global_result.fold_evidence)
    assert global_result.perturbations
    assert global_result.selected_package.promotion_state == "candidate"
    assert global_result.selected_package.automatically_promoted is False
    assert global_result.execution_enabled is False
    assert global_result.orders_submitted == 0


def test_walk_forward_purge_embargo_and_holdout_fail_closed() -> None:
    candidates = _walk_forward_candidates()
    common: dict[str, Any] = {
        "candidates": candidates,
        "parameter_bounds": DEFAULT_RESEARCH_BOUNDS,
        "scopes": (ScopeSpec(ParameterScope.GLOBAL, "global"),),
        "dataset_sha256": canonical_sha256({"dataset": "wickhunter"}),
        "code_sha": "b" * 40,
        "symbol_clusters": {"BTC": "majors", "ETH": "majors"},
        "policy": BoundedOptimizerPolicy(
            initial_trials=2,
            maximum_trials=4,
            top_k=2,
        ),
        "model_evaluator": _walk_forward_model_evaluator,
        "baseline_evaluator": _walk_forward_baseline_evaluator,
    }
    bad_fold = replace(_walk_forward_folds()[0], purge_ms=100)

    with pytest.raises(BoundedOptimizerError, match="purge boundary"):
        optimize_model_aware_walk_forward(
            cases=_walk_forward_cases(),
            folds=(bad_fold,),
            **common,  # type: ignore[arg-type]
        )

    with pytest.raises(BoundedOptimizerError, match="protected holdout"):
        optimize_model_aware_walk_forward(
            cases=_walk_forward_cases(include_holdout=True),
            folds=_walk_forward_folds(),
            **common,  # type: ignore[arg-type]
        )
