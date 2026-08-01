from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

import numpy as np

from ai_platform.wickhunter.baseline_strategy import (
    DEFAULT_SLICE_POLICY,
    BaselineEvaluationReport,
    BaselineSlicePolicy,
    EvaluationCase,
    evaluate_deterministic_baselines,
)
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.parameters import (
    WickHunterParameterBounds,
    WickHunterParameters,
    validate_parameters,
)


OPTIMIZER_POLICY_SCHEMA_VERSION = "wickhunter-bounded-optimizer-policy-v1"
TRIAL_SCHEMA_VERSION = "wickhunter-bounded-optimizer-trial-v1"
RESULT_SCHEMA_VERSION = "wickhunter-bounded-optimizer-result-v1"
OBJECTIVE_VERSION = "wickhunter-validation-stability-objective-v1"
DESCRIPTIVE_CONCLUSION = "bounded_validation_selection_no_profitability_or_promotion_claim"


class BoundedOptimizerError(RuntimeError):
    """Raised when a bounded optimization run is unsafe or inconsistent."""


class TrialSelectionKind(StrEnum):
    INITIAL = "initial"
    SURROGATE = "surrogate"


@dataclass(frozen=True, slots=True)
class BoundedOptimizerPolicy:
    schema_version: str = OPTIMIZER_POLICY_SCHEMA_VERSION
    policy_version: str = "wickhunter-bounded-optimizer-v1"
    training_splits: tuple[str, ...] = ("train",)
    validation_splits: tuple[str, ...] = ("validation",)
    test_splits: tuple[str, ...] = ("test",)
    forbidden_splits: tuple[str, ...] = ("holdout", "protected_holdout")
    seed: int = 20260801
    initial_trials: int = 3
    maximum_trials: int = 12
    top_k: int = 3
    exploration_ratio: Decimal = Decimal("0.25")
    stability_penalty: Decimal = Decimal("0.20")
    inactivity_penalty: Decimal = Decimal("0.05")
    surrogate_length_scale: Decimal = Decimal("0.75")
    surrogate_jitter: Decimal = Decimal("0.000001")

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != OPTIMIZER_POLICY_SCHEMA_VERSION:
            raise BoundedOptimizerError(
                f"optimizer policy schema must be {OPTIMIZER_POLICY_SCHEMA_VERSION}"
            )
        if not self.policy_version.strip():
            raise BoundedOptimizerError("policy_version must be non-empty")
        split_groups = (
            self.training_splits,
            self.validation_splits,
            self.test_splits,
            self.forbidden_splits,
        )
        for group in split_groups:
            if not group or group != tuple(sorted(set(group))):
                raise BoundedOptimizerError("split groups must be non-empty, unique and sorted")
            if any(not item.strip() for item in group):
                raise BoundedOptimizerError("split names must be non-empty")
        research_splits = (
            set(self.training_splits) | set(self.validation_splits) | set(self.test_splits)
        )
        if len(research_splits) != (
            len(self.training_splits) + len(self.validation_splits) + len(self.test_splits)
        ):
            raise BoundedOptimizerError("training, validation and test splits must be disjoint")
        if research_splits & set(self.forbidden_splits):
            raise BoundedOptimizerError("protected splits cannot be assigned to optimization")
        if self.seed < 0:
            raise BoundedOptimizerError("seed must be non-negative")
        if min(self.initial_trials, self.maximum_trials, self.top_k) < 1:
            raise BoundedOptimizerError("trial and top-k counts must be positive")
        if self.initial_trials > self.maximum_trials:
            raise BoundedOptimizerError("initial_trials cannot exceed maximum_trials")
        if self.top_k > self.maximum_trials:
            raise BoundedOptimizerError("top_k cannot exceed maximum_trials")
        for value, field_name, allow_zero in (
            (self.exploration_ratio, "exploration_ratio", True),
            (self.stability_penalty, "stability_penalty", True),
            (self.inactivity_penalty, "inactivity_penalty", True),
            (self.surrogate_length_scale, "surrogate_length_scale", False),
            (self.surrogate_jitter, "surrogate_jitter", False),
        ):
            if not value.is_finite() or value < 0 or (not allow_zero and value == 0):
                raise BoundedOptimizerError(f"{field_name} has an invalid value")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ObjectiveEvidence:
    schema_version: str
    objective_version: str
    report_id: str
    net_return_mean: Decimal
    selected_ratio: Decimal
    slice_dispersion: Decimal
    stability_penalty: Decimal
    inactivity_penalty: Decimal
    objective_value: Decimal

    def __post_init__(self) -> None:
        if self.schema_version != "wickhunter-optimizer-objective-evidence-v1":
            raise BoundedOptimizerError("objective evidence schema mismatch")
        if self.objective_version != OBJECTIVE_VERSION:
            raise BoundedOptimizerError("objective version mismatch")
        _require_sha256(self.report_id, field_name="report_id")
        for value, field_name in (
            (self.net_return_mean, "net_return_mean"),
            (self.selected_ratio, "selected_ratio"),
            (self.slice_dispersion, "slice_dispersion"),
            (self.stability_penalty, "stability_penalty"),
            (self.inactivity_penalty, "inactivity_penalty"),
            (self.objective_value, "objective_value"),
        ):
            if not value.is_finite():
                raise BoundedOptimizerError(f"{field_name} must be finite")
        if not Decimal("0") <= self.selected_ratio <= Decimal("1"):
            raise BoundedOptimizerError("selected_ratio must be in [0, 1]")
        if self.slice_dispersion < 0:
            raise BoundedOptimizerError("slice_dispersion must be non-negative")


@dataclass(frozen=True, slots=True)
class OptimizationTrial:
    schema_version: str
    trial_number: int
    selection_kind: TrialSelectionKind
    parameter_version: str
    parameter_sha256: str
    training_report_id: str
    validation_report_id: str
    validation_evidence: ObjectiveEvidence
    surrogate_mean_before_observation: Decimal | None
    surrogate_std_before_observation: Decimal | None
    acquisition_value: Decimal | None
    test_report_id: str | None
    test_evidence: ObjectiveEvidence | None
    selected_top_k: bool

    def __post_init__(self) -> None:
        if self.schema_version != TRIAL_SCHEMA_VERSION:
            raise BoundedOptimizerError(f"trial schema must be {TRIAL_SCHEMA_VERSION}")
        if self.trial_number < 0:
            raise BoundedOptimizerError("trial_number must be non-negative")
        if not self.parameter_version.strip():
            raise BoundedOptimizerError("parameter_version must be non-empty")
        for digest, field_name in (
            (self.parameter_sha256, "parameter_sha256"),
            (self.training_report_id, "training_report_id"),
            (self.validation_report_id, "validation_report_id"),
        ):
            _require_sha256(digest, field_name=field_name)
        surrogate_values = (
            self.surrogate_mean_before_observation,
            self.surrogate_std_before_observation,
            self.acquisition_value,
        )
        if self.selection_kind is TrialSelectionKind.INITIAL:
            if any(value is not None for value in surrogate_values):
                raise BoundedOptimizerError("initial trial cannot contain surrogate evidence")
        elif any(value is None for value in surrogate_values):
            raise BoundedOptimizerError(
                "surrogate-selected trial requires complete acquisition evidence"
            )
        if self.selected_top_k:
            if self.test_report_id is None or self.test_evidence is None:
                raise BoundedOptimizerError("top-k trial requires descriptive test evidence")
            _require_sha256(self.test_report_id, field_name="test_report_id")
        elif self.test_report_id is not None or self.test_evidence is not None:
            raise BoundedOptimizerError("non-top-k trial cannot contain test evidence")


@dataclass(frozen=True, slots=True)
class StabilityEvidence:
    rank: int
    parameter_sha256: str
    validation_objective: Decimal
    test_objective: Decimal
    validation_test_delta: Decimal
    validation_slice_dispersion: Decimal
    test_slice_dispersion: Decimal

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise BoundedOptimizerError("stability rank must be positive")
        _require_sha256(self.parameter_sha256, field_name="parameter_sha256")
        for value in (
            self.validation_objective,
            self.test_objective,
            self.validation_test_delta,
            self.validation_slice_dispersion,
            self.test_slice_dispersion,
        ):
            if not value.is_finite():
                raise BoundedOptimizerError("stability values must be finite")


@dataclass(frozen=True, slots=True)
class BoundedOptimizationResult:
    schema_version: str
    result_id: str
    policy: BoundedOptimizerPolicy
    search_space_sha256: str
    search_space_size: int
    evaluated_trial_count: int
    objective_version: str
    selection_source: str
    top_parameter_sha256s: tuple[str, ...]
    trials: tuple[OptimizationTrial, ...]
    stability: tuple[StabilityEvidence, ...]
    conclusion: str
    protected_holdout_accessed: bool
    test_used_for_selection: bool
    model_promoted: bool
    profitability_claimed: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise BoundedOptimizerError(f"result schema must be {RESULT_SCHEMA_VERSION}")
        _require_sha256(self.result_id, field_name="result_id")
        _require_sha256(self.search_space_sha256, field_name="search_space_sha256")
        if self.search_space_size < 1 or self.evaluated_trial_count < 1:
            raise BoundedOptimizerError("search space and evaluated trial counts must be positive")
        if self.evaluated_trial_count > self.search_space_size:
            raise BoundedOptimizerError("evaluated trials cannot exceed search space")
        if self.objective_version != OBJECTIVE_VERSION:
            raise BoundedOptimizerError("result objective version mismatch")
        if self.selection_source != "validation_only":
            raise BoundedOptimizerError("selection_source must be validation_only")
        if self.top_parameter_sha256s != tuple(item.parameter_sha256 for item in self.stability):
            raise BoundedOptimizerError("top parameter and stability order mismatch")
        if self.conclusion != DESCRIPTIVE_CONCLUSION:
            raise BoundedOptimizerError("result conclusion is not descriptive-only")
        if (
            self.protected_holdout_accessed
            or self.test_used_for_selection
            or self.model_promoted
            or self.profitability_claimed
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise BoundedOptimizerError("optimization result contains unsafe authority")


EvaluationFunction = Callable[..., BaselineEvaluationReport]


def _require_sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise BoundedOptimizerError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


def _split_cases(
    cases: Sequence[EvaluationCase],
    split_names: tuple[str, ...],
) -> tuple[EvaluationCase, ...]:
    return tuple(
        sorted(
            (case for case in cases if case.split_name in split_names),
            key=lambda item: item.case_sha256,
        )
    )


def _audit_cases(
    cases: Sequence[EvaluationCase],
    policy: BoundedOptimizerPolicy,
) -> None:
    if not cases:
        raise BoundedOptimizerError("optimization requires evaluation cases")
    if any(case.split_name in policy.forbidden_splits for case in cases):
        raise BoundedOptimizerError("protected holdout access is forbidden")
    for split_names, field_name in (
        (policy.training_splits, "training"),
        (policy.validation_splits, "validation"),
        (policy.test_splits, "test"),
    ):
        if not _split_cases(cases, split_names):
            raise BoundedOptimizerError(f"{field_name} split is empty")


def _objective(
    report: OptimizationReport,
    *,
    policy: BoundedOptimizerPolicy,
) -> ObjectiveEvidence:
    selected_ratio = Decimal(report.overall.selected_count) / Decimal(report.overall.decision_count)
    net_return_mean = report.overall.net_return_mean or Decimal("0")
    slice_means = [
        item.net_return_mean
        for item in report.slices
        if item.dimension in {"symbol", "regime", "side"} and item.net_return_mean is not None
    ]
    if len(slice_means) > 1:
        numeric = [value for value in slice_means if value is not None]
        center = sum(numeric, Decimal(0)) / Decimal(len(numeric))
        variance = sum((value - center) ** 2 for value in numeric) / Decimal(len(numeric))
        slice_dispersion = variance.sqrt()
    else:
        slice_dispersion = Decimal("0")
    stability_penalty = policy.stability_penalty * slice_dispersion
    inactivity_penalty = policy.inactivity_penalty * (Decimal("1") - selected_ratio)
    objective_value = net_return_mean - stability_penalty - inactivity_penalty
    return ObjectiveEvidence(
        schema_version="wickhunter-optimizer-objective-evidence-v1",
        objective_version=OBJECTIVE_VERSION,
        report_id=report.report_id,
        net_return_mean=net_return_mean,
        selected_ratio=selected_ratio,
        slice_dispersion=slice_dispersion,
        stability_penalty=stability_penalty,
        inactivity_penalty=inactivity_penalty,
        objective_value=objective_value,
    )


def _numeric_parameter_vector(parameters: WickHunterParameters) -> tuple[Decimal, ...]:
    values: list[Decimal] = []
    for item in fields(parameters):
        if item.name == "parameter_version":
            continue
        value = getattr(parameters, item.name)
        if isinstance(value, bool):
            values.append(Decimal(int(value)))
        elif isinstance(value, (int, Decimal)):
            values.append(Decimal(value))
    if not values:
        raise BoundedOptimizerError("parameter candidate has no numeric dimensions")
    return tuple(values)


def _normalized_vectors(
    candidates: Sequence[WickHunterParameters],
) -> Mapping[str, np.ndarray]:
    rows = [_numeric_parameter_vector(candidate) for candidate in candidates]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise BoundedOptimizerError("parameter vectors have inconsistent dimensions")
    matrix = np.asarray([[float(value) for value in row] for row in rows], dtype=np.float64)
    minimum = matrix.min(axis=0)
    maximum = matrix.max(axis=0)
    span = maximum - minimum
    span[span == 0.0] = 1.0
    normalized = (matrix - minimum) / span
    return {
        candidate.parameter_hash: normalized[index] for index, candidate in enumerate(candidates)
    }


def _surrogate_predictions(
    *,
    observed_vectors: np.ndarray,
    observed_values: np.ndarray,
    candidate_vectors: np.ndarray,
    policy: BoundedOptimizerPolicy,
) -> tuple[np.ndarray, np.ndarray]:
    length_scale = float(policy.surrogate_length_scale)
    jitter = float(policy.surrogate_jitter)

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        distances = np.sum((left[:, None, :] - right[None, :, :]) ** 2, axis=2)
        return np.exp(-distances / (2.0 * length_scale**2))

    covariance = kernel(observed_vectors, observed_vectors)
    covariance += np.eye(len(observed_vectors), dtype=np.float64) * jitter
    cross_covariance = kernel(candidate_vectors, observed_vectors)
    solved_values = np.linalg.solve(covariance, observed_values)
    mean = cross_covariance @ solved_values
    solved_cross = np.linalg.solve(covariance, cross_covariance.T)
    variance = 1.0 - np.sum(cross_covariance * solved_cross.T, axis=1)
    variance = np.maximum(variance, 0.0)
    return mean, np.sqrt(variance)


def _run_report(
    *,
    evaluator: EvaluationFunction,
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
    parameter_bounds: WickHunterParameterBounds,
    slice_policy: BaselineSlicePolicy,
) -> BaselineEvaluationReport:
    try:
        return evaluator(
            cases=cases,
            parameters=parameters,
            parameter_bounds=parameter_bounds,
            slice_policy=slice_policy,
        )
    except Exception as exc:
        raise BoundedOptimizerError(
            f"parameter candidate {parameters.parameter_hash} failed evaluation"
        ) from exc


def optimize_bounded_parameters(
    *,
    cases: Sequence[EvaluationCase],
    candidates: Sequence[WickHunterParameters],
    parameter_bounds: WickHunterParameterBounds,
    policy: BoundedOptimizerPolicy | None = None,
    slice_policy: BaselineSlicePolicy = DEFAULT_SLICE_POLICY,
    evaluator: EvaluationFunction = evaluate_deterministic_baselines,
) -> BoundedOptimizationResult:
    policy = policy or BoundedOptimizerPolicy()
    _audit_cases(cases, policy)
    if not candidates:
        raise BoundedOptimizerError("explicit finite parameter candidates are required")
    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.parameter_hash))
    if len({candidate.parameter_hash for candidate in ordered_candidates}) != len(
        ordered_candidates
    ):
        raise BoundedOptimizerError("parameter candidates must be unique")
    for candidate in ordered_candidates:
        validate_parameters(candidate, parameter_bounds)
    maximum_trials = min(policy.maximum_trials, len(ordered_candidates))
    if policy.initial_trials > maximum_trials:
        raise BoundedOptimizerError("initial_trials exceed the bounded search space")
    if policy.top_k > maximum_trials:
        raise BoundedOptimizerError("top_k exceeds evaluated trial budget")

    training_cases = _split_cases(cases, policy.training_splits)
    validation_cases = _split_cases(cases, policy.validation_splits)
    test_cases = _split_cases(cases, policy.test_splits)
    vectors = _normalized_vectors(ordered_candidates)
    by_hash = {candidate.parameter_hash: candidate for candidate in ordered_candidates}
    rng = np.random.default_rng(policy.seed)
    initial_indices = tuple(
        sorted(
            rng.choice(len(ordered_candidates), size=policy.initial_trials, replace=False).tolist()
        )
    )
    pending = {candidate.parameter_hash for candidate in ordered_candidates}
    observations: dict[str, Decimal] = {}
    provisional: list[
        tuple[
            WickHunterParameters,
            TrialSelectionKind,
            BaselineEvaluationReport,
            BaselineEvaluationReport,
            ObjectiveEvidence,
            Decimal | None,
            Decimal | None,
            Decimal | None,
        ]
    ] = []

    def observe(
        candidate: WickHunterParameters,
        selection_kind: TrialSelectionKind,
        surrogate_mean: Decimal | None,
        surrogate_std: Decimal | None,
        acquisition: Decimal | None,
    ) -> None:
        training_report = _run_report(
            evaluator=evaluator,
            cases=training_cases,
            parameters=candidate,
            parameter_bounds=parameter_bounds,
            slice_policy=slice_policy,
        )
        validation_report = _run_report(
            evaluator=evaluator,
            cases=validation_cases,
            parameters=candidate,
            parameter_bounds=parameter_bounds,
            slice_policy=slice_policy,
        )
        evidence = _objective(validation_report, policy=policy)
        observations[candidate.parameter_hash] = evidence.objective_value
        pending.remove(candidate.parameter_hash)
        provisional.append(
            (
                candidate,
                selection_kind,
                training_report,
                validation_report,
                evidence,
                surrogate_mean,
                surrogate_std,
                acquisition,
            )
        )

    for index in initial_indices:
        observe(
            ordered_candidates[index],
            TrialSelectionKind.INITIAL,
            None,
            None,
            None,
        )

    while len(observations) < maximum_trials:
        observed_hashes = tuple(sorted(observations))
        pending_hashes = tuple(sorted(pending))
        observed_vectors = np.asarray(
            [vectors[parameter_hash] for parameter_hash in observed_hashes],
            dtype=np.float64,
        )
        observed_values = np.asarray(
            [float(observations[parameter_hash]) for parameter_hash in observed_hashes],
            dtype=np.float64,
        )
        candidate_vectors = np.asarray(
            [vectors[parameter_hash] for parameter_hash in pending_hashes],
            dtype=np.float64,
        )
        means, standard_deviations = _surrogate_predictions(
            observed_vectors=observed_vectors,
            observed_values=observed_values,
            candidate_vectors=candidate_vectors,
            policy=policy,
        )
        acquisitions = means + float(policy.exploration_ratio) * standard_deviations
        best_index = min(
            range(len(pending_hashes)),
            key=lambda index: (-acquisitions[index], pending_hashes[index]),
        )
        selected_hash = pending_hashes[best_index]
        observe(
            by_hash[selected_hash],
            TrialSelectionKind.SURROGATE,
            Decimal(str(means[best_index])),
            Decimal(str(standard_deviations[best_index])),
            Decimal(str(acquisitions[best_index])),
        )

    ranked_hashes = tuple(
        sorted(
            observations,
            key=lambda parameter_hash: (
                -observations[parameter_hash],
                parameter_hash,
            ),
        )
    )
    top_hashes = ranked_hashes[: policy.top_k]
    test_reports: dict[str, BaselineEvaluationReport] = {}
    test_evidence: dict[str, ObjectiveEvidence] = {}
    for parameter_hash in top_hashes:
        report = _run_report(
            evaluator=evaluator,
            cases=test_cases,
            parameters=by_hash[parameter_hash],
            parameter_bounds=parameter_bounds,
            slice_policy=slice_policy,
        )
        test_reports[parameter_hash] = report
        test_evidence[parameter_hash] = _objective(report, policy=policy)

    trials = tuple(
        OptimizationTrial(
            schema_version=TRIAL_SCHEMA_VERSION,
            trial_number=index,
            selection_kind=selection_kind,
            parameter_version=candidate.parameter_version,
            parameter_sha256=candidate.parameter_hash,
            training_report_id=training_report.report_id,
            validation_report_id=validation_report.report_id,
            validation_evidence=validation_evidence,
            surrogate_mean_before_observation=surrogate_mean,
            surrogate_std_before_observation=surrogate_std,
            acquisition_value=acquisition,
            test_report_id=(
                None
                if candidate.parameter_hash not in top_hashes
                else test_reports[candidate.parameter_hash].report_id
            ),
            test_evidence=(
                None
                if candidate.parameter_hash not in top_hashes
                else test_evidence[candidate.parameter_hash]
            ),
            selected_top_k=candidate.parameter_hash in top_hashes,
        )
        for index, (
            candidate,
            selection_kind,
            training_report,
            validation_report,
            validation_evidence,
            surrogate_mean,
            surrogate_std,
            acquisition,
        ) in enumerate(provisional)
    )
    evidence_by_hash = {trial.parameter_sha256: trial.validation_evidence for trial in trials}
    stability = tuple(
        StabilityEvidence(
            rank=rank,
            parameter_sha256=parameter_hash,
            validation_objective=evidence_by_hash[parameter_hash].objective_value,
            test_objective=test_evidence[parameter_hash].objective_value,
            validation_test_delta=(
                test_evidence[parameter_hash].objective_value
                - evidence_by_hash[parameter_hash].objective_value
            ),
            validation_slice_dispersion=evidence_by_hash[parameter_hash].slice_dispersion,
            test_slice_dispersion=test_evidence[parameter_hash].slice_dispersion,
        )
        for rank, parameter_hash in enumerate(top_hashes, start=1)
    )
    search_space_sha256 = canonical_sha256(
        {
            "parameter_sha256s": tuple(
                candidate.parameter_hash for candidate in ordered_candidates
            ),
            "parameter_bounds": parameter_bounds,
        }
    )
    result_seed = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "policy_sha256": policy.policy_sha256,
        "search_space_sha256": search_space_sha256,
        "objective_version": OBJECTIVE_VERSION,
        "trial_parameter_sha256s": tuple(trial.parameter_sha256 for trial in trials),
        "validation_objectives": tuple(
            trial.validation_evidence.objective_value for trial in trials
        ),
        "top_parameter_sha256s": top_hashes,
        "stability": stability,
        "selection_source": "validation_only",
        "conclusion": DESCRIPTIVE_CONCLUSION,
    }
    return BoundedOptimizationResult(
        schema_version=RESULT_SCHEMA_VERSION,
        result_id=canonical_sha256(result_seed),
        policy=policy,
        search_space_sha256=search_space_sha256,
        search_space_size=len(ordered_candidates),
        evaluated_trial_count=len(trials),
        objective_version=OBJECTIVE_VERSION,
        selection_source="validation_only",
        top_parameter_sha256s=top_hashes,
        trials=trials,
        stability=stability,
        conclusion=DESCRIPTIVE_CONCLUSION,
        protected_holdout_accessed=False,
        test_used_for_selection=False,
        model_promoted=False,
        profitability_claimed=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )


# --- WH05 model-aware walk-forward extension ---

WALK_FORWARD_SCHEMA_VERSION = "wickhunter-walk-forward-optimizer-v1"
CANDIDATE_PACKAGE_SCHEMA_VERSION = "wickhunter-parameter-candidate-package-v1"
PERTURBATION_SCHEMA_VERSION = "wickhunter-local-perturbation-v1"


class OptimizationSummary(Protocol):
    @property
    def decision_count(self) -> int: ...

    @property
    def selected_count(self) -> int: ...

    @property
    def net_return_mean(self) -> Decimal | None: ...


class OptimizationSlice(Protocol):
    @property
    def dimension(self) -> str: ...

    @property
    def net_return_mean(self) -> Decimal | None: ...


class OptimizationReport(Protocol):
    @property
    def report_id(self) -> str: ...

    @property
    def overall(self) -> OptimizationSummary: ...

    @property
    def slices(self) -> Sequence[OptimizationSlice]: ...


class ParameterScope(StrEnum):
    GLOBAL = "global"
    REGIME = "regime"
    SYMBOL_CLUSTER = "symbol_cluster"


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold_id: str
    training_splits: tuple[str, ...]
    calibration_splits: tuple[str, ...]
    validation_splits: tuple[str, ...]
    test_splits: tuple[str, ...]
    purge_ms: int
    embargo_ms: int

    def __post_init__(self) -> None:
        if not self.fold_id.strip():
            raise BoundedOptimizerError("fold_id must be non-empty")
        groups = (
            self.training_splits,
            self.calibration_splits,
            self.validation_splits,
            self.test_splits,
        )
        for group in groups:
            if not group or group != tuple(sorted(set(group))):
                raise BoundedOptimizerError(
                    "walk-forward split groups must be non-empty and sorted"
                )
        all_splits = tuple(item for group in groups for item in group)
        if len(all_splits) != len(set(all_splits)):
            raise BoundedOptimizerError("walk-forward split groups must be disjoint")
        if self.purge_ms < 0 or self.embargo_ms < 0:
            raise BoundedOptimizerError("purge and embargo must be non-negative")

    @property
    def fold_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ScopeSpec:
    scope: ParameterScope
    value: str
    minimum_case_count: int = 1
    inherited_from: str | None = None

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise BoundedOptimizerError("scope value must be non-empty")
        if self.minimum_case_count < 1:
            raise BoundedOptimizerError("minimum_case_count must be positive")
        if self.scope is ParameterScope.GLOBAL and self.value != "global":
            raise BoundedOptimizerError("global scope value must be global")
        if self.scope is ParameterScope.GLOBAL and self.inherited_from is not None:
            raise BoundedOptimizerError("global scope cannot inherit")


@dataclass(frozen=True, slots=True)
class ModelAwareReport:
    report_id: str
    overall: OptimizationSummary
    slices: tuple[OptimizationSlice, ...]
    model_hash: str

    def __post_init__(self) -> None:
        _require_sha256(self.report_id, field_name="report_id")
        _require_sha256(self.model_hash, field_name="model_hash")


@dataclass(frozen=True, slots=True)
class FoldCandidateEvidence:
    fold_id: str
    parameter_sha256: str
    baseline_result_id: str
    baseline_validation_objective: Decimal
    model_validation_report_id: str
    model_validation_objective: Decimal
    model_hash: str
    model_test_report_id: str | None
    model_test_objective: Decimal | None

    def __post_init__(self) -> None:
        if not self.fold_id.strip():
            raise BoundedOptimizerError("fold evidence requires fold_id")
        for digest, field_name in (
            (self.parameter_sha256, "parameter_sha256"),
            (self.baseline_result_id, "baseline_result_id"),
            (self.model_validation_report_id, "model_validation_report_id"),
            (self.model_hash, "model_hash"),
        ):
            _require_sha256(digest, field_name=field_name)
        if (self.model_test_report_id is None) != (self.model_test_objective is None):
            raise BoundedOptimizerError("test report identity and objective must align")
        if self.model_test_report_id is not None:
            _require_sha256(self.model_test_report_id, field_name="model_test_report_id")


@dataclass(frozen=True, slots=True)
class PerturbationEvidence:
    schema_version: str
    parameter_sha256: str
    neighbor_parameter_sha256: str
    normalized_distance: Decimal
    objective_delta: Decimal
    stable: bool

    def __post_init__(self) -> None:
        if self.schema_version != PERTURBATION_SCHEMA_VERSION:
            raise BoundedOptimizerError("perturbation schema mismatch")
        _require_sha256(self.parameter_sha256, field_name="parameter_sha256")
        _require_sha256(
            self.neighbor_parameter_sha256,
            field_name="neighbor_parameter_sha256",
        )
        if not self.normalized_distance.is_finite() or self.normalized_distance < 0:
            raise BoundedOptimizerError("normalized_distance must be finite and non-negative")
        if not self.objective_delta.is_finite():
            raise BoundedOptimizerError("objective_delta must be finite")


@dataclass(frozen=True, slots=True)
class ParameterCandidatePackage:
    schema_version: str
    package_id: str
    scope: ParameterScope
    scope_value: str
    inherited_from: str | None
    parameter_version: str
    parameter_sha256: str
    bounds_sha256: str
    dataset_sha256: str
    code_sha: str
    model_hashes: tuple[str, ...]
    fold_sha256s: tuple[str, ...]
    seed: int
    validation_objective: Decimal
    test_objective: Decimal | None
    promotion_state: str
    protected_holdout_accessed: bool
    automatically_promoted: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != CANDIDATE_PACKAGE_SCHEMA_VERSION:
            raise BoundedOptimizerError("candidate package schema mismatch")
        for digest, field_name in (
            (self.package_id, "package_id"),
            (self.parameter_sha256, "parameter_sha256"),
            (self.bounds_sha256, "bounds_sha256"),
            (self.dataset_sha256, "dataset_sha256"),
        ):
            _require_sha256(digest, field_name=field_name)
        if len(self.code_sha) not in {40, 64} or any(
            char not in "0123456789abcdef" for char in self.code_sha
        ):
            raise BoundedOptimizerError("code_sha must be a lowercase git digest")
        if not self.scope_value.strip() or not self.parameter_version.strip():
            raise BoundedOptimizerError("scope and parameter identities must be non-empty")
        if self.model_hashes != tuple(sorted(set(self.model_hashes))) or not self.model_hashes:
            raise BoundedOptimizerError("model hashes must be non-empty, unique and sorted")
        if self.fold_sha256s != tuple(sorted(set(self.fold_sha256s))) or not self.fold_sha256s:
            raise BoundedOptimizerError("fold hashes must be non-empty, unique and sorted")
        for digest in self.model_hashes:
            _require_sha256(digest, field_name="model_hash")
        for digest in self.fold_sha256s:
            _require_sha256(digest, field_name="fold_sha256")
        if self.seed < 0:
            raise BoundedOptimizerError("seed must be non-negative")
        if self.promotion_state != "candidate":
            raise BoundedOptimizerError("parameter package must remain candidate-only")
        if (
            self.protected_holdout_accessed
            or self.automatically_promoted
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise BoundedOptimizerError("candidate package contains unsafe authority")


@dataclass(frozen=True, slots=True)
class ScopedWalkForwardResult:
    schema_version: str
    result_id: str
    scope: ParameterScope
    scope_value: str
    inherited_from: str | None
    selected_package: ParameterCandidatePackage
    fold_evidence: tuple[FoldCandidateEvidence, ...]
    perturbations: tuple[PerturbationEvidence, ...]
    conclusion: str
    protected_holdout_accessed: bool
    test_used_for_selection: bool
    automatically_promoted: bool
    execution_enabled: bool
    live_capital_authorized: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != WALK_FORWARD_SCHEMA_VERSION:
            raise BoundedOptimizerError("walk-forward result schema mismatch")
        _require_sha256(self.result_id, field_name="result_id")
        if not self.fold_evidence:
            raise BoundedOptimizerError("walk-forward result requires fold evidence")
        if self.conclusion != DESCRIPTIVE_CONCLUSION:
            raise BoundedOptimizerError("walk-forward result must remain descriptive")
        if (
            self.protected_holdout_accessed
            or self.test_used_for_selection
            or self.automatically_promoted
            or self.execution_enabled
            or self.live_capital_authorized
            or self.orders_submitted != 0
        ):
            raise BoundedOptimizerError("walk-forward result contains unsafe authority")


ModelAwareEvaluator = Callable[..., ModelAwareReport]


def _label_end_ms(case: EvaluationCase) -> int:
    return max(label.label_end_ms for label in case.labels)


def _audit_walk_forward_fold(
    cases: Sequence[EvaluationCase],
    fold: WalkForwardFold,
    *,
    forbidden_splits: tuple[str, ...],
) -> tuple[EvaluationCase, ...]:
    selected_names = (
        set(fold.training_splits)
        | set(fold.calibration_splits)
        | set(fold.validation_splits)
        | set(fold.test_splits)
    )
    if selected_names & set(forbidden_splits):
        raise BoundedOptimizerError("protected holdout access is forbidden")
    selected = tuple(
        sorted(
            (case for case in cases if case.split_name in selected_names),
            key=lambda item: item.case_sha256,
        )
    )
    groups = {
        "training": _split_cases(selected, fold.training_splits),
        "calibration": _split_cases(selected, fold.calibration_splits),
        "validation": _split_cases(selected, fold.validation_splits),
        "test": _split_cases(selected, fold.test_splits),
    }
    if any(not group for group in groups.values()):
        raise BoundedOptimizerError("every walk-forward split group must be populated")
    validation_start = min(case.feature.decision_timestamp_ms for case in groups["validation"])
    test_start = min(case.feature.decision_timestamp_ms for case in groups["test"])
    train_end = max(_label_end_ms(case) for case in (*groups["training"], *groups["calibration"]))
    validation_end = max(_label_end_ms(case) for case in groups["validation"])
    if train_end + fold.purge_ms > validation_start:
        raise BoundedOptimizerError("walk-forward purge boundary is violated")
    if validation_end + fold.embargo_ms > test_start:
        raise BoundedOptimizerError("walk-forward embargo boundary is violated")
    return selected


def _scope_cases(
    cases: Sequence[EvaluationCase],
    spec: ScopeSpec,
    *,
    symbol_clusters: Mapping[str, str],
    slice_policy: BaselineSlicePolicy,
) -> tuple[EvaluationCase, ...]:
    if spec.scope is ParameterScope.GLOBAL:
        return tuple(cases)
    if spec.scope is ParameterScope.SYMBOL_CLUSTER:
        return tuple(
            case for case in cases if symbol_clusters.get(case.feature.symbol) == spec.value
        )
    result: list[EvaluationCase] = []
    for case in cases:
        trend = case.feature.metric("trend_return_ratio")
        if trend > slice_policy.trend_threshold_ratio:
            regime = "uptrend"
        elif trend < -slice_policy.trend_threshold_ratio:
            regime = "downtrend"
        else:
            regime = "range"
        if regime == spec.value:
            result.append(case)
    return tuple(result)


def _scope_has_fold_coverage(
    cases: Sequence[EvaluationCase],
    folds: Sequence[WalkForwardFold],
) -> bool:
    return all(
        _split_cases(cases, split_names)
        for fold in folds
        for split_names in (
            fold.training_splits,
            fold.calibration_splits,
            fold.validation_splits,
            fold.test_splits,
        )
    )


def _default_model_aware_evaluator(
    *,
    cases: Sequence[EvaluationCase],
    parameters: WickHunterParameters,
    parameter_bounds: WickHunterParameterBounds,
    training_splits: tuple[str, ...],
    calibration_splits: tuple[str, ...],
    target_splits: tuple[str, ...],
    forbidden_splits: tuple[str, ...],
    seed: int,
    slice_policy: BaselineSlicePolicy,
) -> ModelAwareReport:
    from ai_platform.wickhunter.lightgbm_scorer import (
        LightGBMTrainingPolicy,
        evaluate_lightgbm_against_baseline,
        train_lightgbm_scorer,
    )

    model_policy = LightGBMTrainingPolicy(
        training_splits=training_splits,
        calibration_splits=calibration_splits,
        validation_splits=target_splits,
        forbidden_splits=forbidden_splits,
        seed=seed,
    )
    artifact = train_lightgbm_scorer(
        cases=cases,
        parameters=parameters,
        parameter_bounds=parameter_bounds,
        policy=model_policy,
    )
    comparison = evaluate_lightgbm_against_baseline(
        artifact=artifact,
        cases=cases,
        parameters=parameters,
        parameter_bounds=parameter_bounds,
        slice_policy=slice_policy,
    )
    return ModelAwareReport(
        report_id=comparison.report_id,
        overall=comparison.model_overall,
        slices=tuple(comparison.model_slices),
        model_hash=artifact.model_hash,
    )


def _report_objective(
    report: ModelAwareReport,
    *,
    policy: BoundedOptimizerPolicy,
) -> ObjectiveEvidence:
    return _objective(report, policy=policy)


def _mean(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise BoundedOptimizerError("cannot average empty evidence")
    return sum(values, Decimal(0)) / Decimal(len(values))


def _perturbations(
    candidates: Sequence[WickHunterParameters],
    objectives: Mapping[str, Decimal],
    *,
    selected_hash: str,
    maximum_delta: Decimal,
) -> tuple[PerturbationEvidence, ...]:
    vectors = _normalized_vectors(candidates)
    selected = vectors[selected_hash]
    neighbors: list[tuple[float, str]] = []
    for parameter_hash, vector in vectors.items():
        if parameter_hash == selected_hash or parameter_hash not in objectives:
            continue
        distance = float(np.linalg.norm(selected - vector))
        neighbors.append((distance, parameter_hash))
    if not neighbors:
        return ()
    distance, neighbor_hash = min(neighbors, key=lambda item: (item[0], item[1]))
    delta = objectives[selected_hash] - objectives[neighbor_hash]
    return (
        PerturbationEvidence(
            schema_version=PERTURBATION_SCHEMA_VERSION,
            parameter_sha256=selected_hash,
            neighbor_parameter_sha256=neighbor_hash,
            normalized_distance=Decimal(str(distance)),
            objective_delta=delta,
            stable=abs(delta) <= maximum_delta,
        ),
    )


def optimize_model_aware_walk_forward(  # noqa: C901
    *,
    cases: Sequence[EvaluationCase],
    candidates: Sequence[WickHunterParameters],
    parameter_bounds: WickHunterParameterBounds,
    folds: Sequence[WalkForwardFold],
    scopes: Sequence[ScopeSpec],
    dataset_sha256: str,
    code_sha: str,
    symbol_clusters: Mapping[str, str],
    policy: BoundedOptimizerPolicy | None = None,
    slice_policy: BaselineSlicePolicy = DEFAULT_SLICE_POLICY,
    model_evaluator: ModelAwareEvaluator = _default_model_aware_evaluator,
    baseline_evaluator: EvaluationFunction = evaluate_deterministic_baselines,
    maximum_perturbation_delta: Decimal = Decimal("0.02"),
) -> tuple[ScopedWalkForwardResult, ...]:
    policy = policy or BoundedOptimizerPolicy()
    _require_sha256(dataset_sha256, field_name="dataset_sha256")
    if len(code_sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in code_sha):
        raise BoundedOptimizerError("code_sha must be a lowercase git digest")
    if not folds or not scopes:
        raise BoundedOptimizerError("walk-forward folds and scopes are required")
    if any(case.split_name in policy.forbidden_splits for case in cases):
        raise BoundedOptimizerError("protected holdout access is forbidden")
    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.parameter_hash))
    if not ordered_candidates:
        raise BoundedOptimizerError("finite parameter candidates are required")
    for candidate in ordered_candidates:
        validate_parameters(candidate, parameter_bounds)
    if len({candidate.parameter_hash for candidate in ordered_candidates}) != len(
        ordered_candidates
    ):
        raise BoundedOptimizerError("parameter candidates must be unique")
    fold_cases = {
        fold.fold_id: _audit_walk_forward_fold(
            cases,
            fold,
            forbidden_splits=policy.forbidden_splits,
        )
        for fold in folds
    }
    spec_by_key = {(spec.scope.value, spec.value): spec for spec in scopes}
    global_key = (ParameterScope.GLOBAL.value, "global")
    if global_key not in spec_by_key:
        raise BoundedOptimizerError("global scope is required")
    if len(spec_by_key) != len(scopes):
        raise BoundedOptimizerError("scope specifications must be unique")
    ordered_scopes = tuple(
        sorted(
            scopes,
            key=lambda spec: (
                0 if spec.scope is ParameterScope.GLOBAL else 1,
                spec.scope.value,
                spec.value,
            ),
        )
    )
    results: dict[tuple[str, str], ScopedWalkForwardResult] = {}

    for spec in ordered_scopes:
        key = (spec.scope.value, spec.value)
        scoped = _scope_cases(
            cases,
            spec,
            symbol_clusters=symbol_clusters,
            slice_policy=slice_policy,
        )
        if len(scoped) < spec.minimum_case_count or not _scope_has_fold_coverage(scoped, folds):
            if spec.inherited_from is None:
                raise BoundedOptimizerError("sparse scope requires explicit inheritance")
            parent_key = (
                ParameterScope.GLOBAL.value,
                spec.inherited_from,
            )
            if parent_key not in results:
                raise BoundedOptimizerError("scope inheritance parent is unavailable")
            parent = results[parent_key]
            inherited_package = replace(
                parent.selected_package,
                package_id=canonical_sha256(
                    {
                        "parent_package_id": parent.selected_package.package_id,
                        "scope": spec.scope.value,
                        "scope_value": spec.value,
                    }
                ),
                scope=spec.scope,
                scope_value=spec.value,
                inherited_from=spec.inherited_from,
            )
            results[key] = ScopedWalkForwardResult(
                schema_version=WALK_FORWARD_SCHEMA_VERSION,
                result_id=canonical_sha256(
                    {
                        "scope": spec.scope.value,
                        "value": spec.value,
                        "parent": parent.result_id,
                    }
                ),
                scope=spec.scope,
                scope_value=spec.value,
                inherited_from=spec.inherited_from,
                selected_package=inherited_package,
                fold_evidence=parent.fold_evidence,
                perturbations=parent.perturbations,
                conclusion=DESCRIPTIVE_CONCLUSION,
                protected_holdout_accessed=False,
                test_used_for_selection=False,
                automatically_promoted=False,
                execution_enabled=False,
                live_capital_authorized=False,
                orders_submitted=0,
            )
            continue

        scoped_hashes = {case.case_sha256 for case in scoped}
        fold_selected_cases: dict[str, tuple[EvaluationCase, ...]] = {}
        fold_baselines: dict[str, BoundedOptimizationResult] = {}
        model_candidate_hashes: set[str] = set()

        for fold in folds:
            selected = tuple(
                case for case in fold_cases[fold.fold_id] if case.case_sha256 in scoped_hashes
            )
            if not selected:
                raise BoundedOptimizerError("scope removed every case from a walk-forward fold")
            fold_selected_cases[fold.fold_id] = selected
            fold_policy = BoundedOptimizerPolicy(
                training_splits=tuple(sorted((*fold.training_splits, *fold.calibration_splits))),
                validation_splits=fold.validation_splits,
                test_splits=fold.test_splits,
                forbidden_splits=policy.forbidden_splits,
                seed=policy.seed,
                initial_trials=min(policy.initial_trials, len(ordered_candidates)),
                maximum_trials=len(ordered_candidates),
                top_k=min(policy.top_k, len(ordered_candidates)),
                exploration_ratio=policy.exploration_ratio,
                stability_penalty=policy.stability_penalty,
                inactivity_penalty=policy.inactivity_penalty,
                surrogate_length_scale=policy.surrogate_length_scale,
                surrogate_jitter=policy.surrogate_jitter,
            )
            baseline = optimize_bounded_parameters(
                cases=selected,
                candidates=ordered_candidates,
                parameter_bounds=parameter_bounds,
                policy=fold_policy,
                slice_policy=slice_policy,
                evaluator=baseline_evaluator,
            )
            fold_baselines[fold.fold_id] = baseline
            model_candidate_hashes.update(baseline.top_parameter_sha256s)

        validation_by_hash: dict[str, list[Decimal]] = {
            parameter_hash: [] for parameter_hash in model_candidate_hashes
        }
        fold_validation: dict[
            tuple[str, str],
            tuple[str, Decimal, str, str, Decimal],
        ] = {}
        for parameter_hash in sorted(model_candidate_hashes):
            candidate = next(
                item for item in ordered_candidates if item.parameter_hash == parameter_hash
            )
            for fold in folds:
                selected = fold_selected_cases[fold.fold_id]
                baseline = fold_baselines[fold.fold_id]
                validation_report = model_evaluator(
                    cases=selected,
                    parameters=candidate,
                    parameter_bounds=parameter_bounds,
                    training_splits=fold.training_splits,
                    calibration_splits=fold.calibration_splits,
                    target_splits=fold.validation_splits,
                    forbidden_splits=policy.forbidden_splits,
                    seed=policy.seed,
                    slice_policy=slice_policy,
                )
                validation_evidence = _report_objective(
                    validation_report,
                    policy=policy,
                )
                validation_by_hash[parameter_hash].append(validation_evidence.objective_value)
                fold_validation[(fold.fold_id, parameter_hash)] = (
                    validation_report.report_id,
                    validation_evidence.objective_value,
                    validation_report.model_hash,
                    baseline.result_id,
                    next(
                        trial.validation_evidence.objective_value
                        for trial in baseline.trials
                        if trial.parameter_sha256 == parameter_hash
                    ),
                )

        eligible = {
            parameter_hash: _mean(values)
            for parameter_hash, values in validation_by_hash.items()
            if len(values) == len(folds)
        }
        if not eligible:
            raise BoundedOptimizerError("no candidate was evaluated in every walk-forward fold")
        selected_hash = min(
            eligible,
            key=lambda parameter_hash: (-eligible[parameter_hash], parameter_hash),
        )
        selected_parameter = next(
            item for item in ordered_candidates if item.parameter_hash == selected_hash
        )
        fold_evidence: list[FoldCandidateEvidence] = []
        test_values: list[Decimal] = []
        model_hashes: set[str] = set()
        for fold in folds:
            selected = fold_selected_cases[fold.fold_id]
            test_report = model_evaluator(
                cases=selected,
                parameters=selected_parameter,
                parameter_bounds=parameter_bounds,
                training_splits=fold.training_splits,
                calibration_splits=fold.calibration_splits,
                target_splits=fold.test_splits,
                forbidden_splits=policy.forbidden_splits,
                seed=policy.seed,
                slice_policy=slice_policy,
            )
            test_evidence = _report_objective(test_report, policy=policy)
            test_values.append(test_evidence.objective_value)
            (
                validation_report_id,
                validation_objective,
                validation_model_hash,
                baseline_id,
                baseline_objective,
            ) = fold_validation[(fold.fold_id, selected_hash)]
            if test_report.model_hash != validation_model_hash:
                raise BoundedOptimizerError("validation and test model hashes differ for one fold")
            model_hashes.add(test_report.model_hash)
            fold_evidence.append(
                FoldCandidateEvidence(
                    fold_id=fold.fold_id,
                    parameter_sha256=selected_hash,
                    baseline_result_id=baseline_id,
                    baseline_validation_objective=baseline_objective,
                    model_validation_report_id=validation_report_id,
                    model_validation_objective=validation_objective,
                    model_hash=test_report.model_hash,
                    model_test_report_id=test_report.report_id,
                    model_test_objective=test_evidence.objective_value,
                )
            )
        perturbations = _perturbations(
            ordered_candidates,
            eligible,
            selected_hash=selected_hash,
            maximum_delta=maximum_perturbation_delta,
        )
        bounds_sha256 = canonical_sha256(parameter_bounds)
        fold_sha256s = tuple(sorted(fold.fold_sha256 for fold in folds))
        package_seed = {
            "schema_version": CANDIDATE_PACKAGE_SCHEMA_VERSION,
            "scope": spec.scope.value,
            "scope_value": spec.value,
            "parameter_sha256": selected_hash,
            "bounds_sha256": bounds_sha256,
            "dataset_sha256": dataset_sha256,
            "code_sha": code_sha,
            "model_hashes": tuple(sorted(model_hashes)),
            "fold_sha256s": fold_sha256s,
            "seed": policy.seed,
            "validation_objective": eligible[selected_hash],
            "test_objective": _mean(test_values),
            "promotion_state": "candidate",
        }
        package = ParameterCandidatePackage(
            schema_version=CANDIDATE_PACKAGE_SCHEMA_VERSION,
            package_id=canonical_sha256(package_seed),
            scope=spec.scope,
            scope_value=spec.value,
            inherited_from=None,
            parameter_version=selected_parameter.parameter_version,
            parameter_sha256=selected_hash,
            bounds_sha256=bounds_sha256,
            dataset_sha256=dataset_sha256,
            code_sha=code_sha,
            model_hashes=tuple(sorted(model_hashes)),
            fold_sha256s=fold_sha256s,
            seed=policy.seed,
            validation_objective=eligible[selected_hash],
            test_objective=_mean(test_values),
            promotion_state="candidate",
            protected_holdout_accessed=False,
            automatically_promoted=False,
            execution_enabled=False,
            live_capital_authorized=False,
            orders_submitted=0,
        )
        result_seed = {
            "schema_version": WALK_FORWARD_SCHEMA_VERSION,
            "scope": spec.scope.value,
            "scope_value": spec.value,
            "package_id": package.package_id,
            "fold_evidence": tuple(fold_evidence),
            "perturbations": perturbations,
            "conclusion": DESCRIPTIVE_CONCLUSION,
        }
        results[key] = ScopedWalkForwardResult(
            schema_version=WALK_FORWARD_SCHEMA_VERSION,
            result_id=canonical_sha256(result_seed),
            scope=spec.scope,
            scope_value=spec.value,
            inherited_from=None,
            selected_package=package,
            fold_evidence=tuple(fold_evidence),
            perturbations=perturbations,
            conclusion=DESCRIPTIVE_CONCLUSION,
            protected_holdout_accessed=False,
            test_used_for_selection=False,
            automatically_promoted=False,
            execution_enabled=False,
            live_capital_authorized=False,
            orders_submitted=0,
        )

    return tuple(results[(spec.scope.value, spec.value)] for spec in scopes)
