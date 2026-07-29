from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import mean, pstdev
from typing import Any, Literal, Protocol, Self, cast

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from optuna.trial import FrozenTrial, Trial, TrialState
from pydantic import Field, JsonValue, model_validator

from strategy_engine.domain.models import CanonicalModel, StrategyDefinition
from strategy_engine.registry import RegistryError, SearchParameter, SearchSpaceRegistry

from .candidate import CandidateGenerationError, CandidateGenerator, CandidateRequest
from .dataset import DatasetManifest

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_PENALTY_SCORE = -1_000_000.0


class EvaluationMetrics(CanonicalModel):
    fold_profits: tuple[float, ...] = Field(min_length=1)
    fold_drawdowns: tuple[float, ...] = Field(min_length=1)
    trade_count: int = Field(ge=0)
    lookahead_passed: bool
    recursive_passed: bool
    falsification_passed: bool
    final_holdout_used: Literal[False] = False

    @model_validator(mode="after")
    def validate_metrics(self) -> Self:
        if len(self.fold_profits) != len(self.fold_drawdowns):
            raise ValueError("fold profit and drawdown counts must match")
        if any(value < 0.0 or value > 1.0 for value in self.fold_drawdowns):
            raise ValueError("fold drawdowns must be ratios in [0, 1]")
        return self


class ForbiddenCombination(CanonicalModel):
    reason: str = Field(min_length=1)
    values: dict[str, JsonValue]

    def matches(self, parameters: Mapping[str, object]) -> bool:
        return bool(self.values) and all(
            parameters.get(key) == value for key, value in self.values.items()
        )


class FeatureSearchBinding(CanonicalModel):
    space: str = Field(min_length=1)
    parameters: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_parameters(self) -> Self:
        if len(self.parameters) != len(set(self.parameters)):
            raise ValueError("search binding parameters must be unique")
        return self


class OptimizationPlan(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    study_id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    n_trials: int = Field(ge=1, le=128)
    startup_trials: int = Field(default=5, ge=1, le=32)
    feature_search_spaces: dict[str, FeatureSearchBinding]
    forbidden_combinations: tuple[ForbiddenCombination, ...] = ()
    minimum_trades: int = Field(default=20, ge=1)
    maximum_drawdown: float = Field(default=0.25, gt=0.0, le=1.0)
    max_conditions: int = Field(default=8, ge=1, le=8)
    direction: Literal["maximize"] = "maximize"
    execution_authority: Literal[False] = False
    final_holdout_used: Literal[False] = False


class TrialLineage(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    study_id: str = Field(min_length=1)
    trial_number: int = Field(ge=0)
    state: Literal["complete", "pruned", "fail", "running", "waiting"]
    dataset_manifest_hash: str = Field(pattern=_SHA256_PATTERN)
    base_request_hash: str = Field(pattern=_SHA256_PATTERN)
    candidate_hash: str = Field(pattern=_SHA256_PATTERN)
    parameters: dict[str, JsonValue]
    constraints: tuple[float, ...]
    metrics: EvaluationMetrics | None = None
    score: float | None = None
    failure_reason: str | None = None
    lineage_hash: str = Field(pattern=_SHA256_PATTERN)

    @model_validator(mode="after")
    def verify_hash(self) -> Self:
        expected = self.canonical_sha256(exclude={"lineage_hash"})
        if self.lineage_hash != expected:
            raise ValueError("lineage_hash does not match canonical trial lineage")
        return self

    @classmethod
    def create(cls, **values: Any) -> Self:
        payload = dict(values)
        payload.pop("lineage_hash", None)
        provisional = cls.model_construct(**payload, lineage_hash="0" * 64)
        digest = provisional.canonical_sha256(exclude={"lineage_hash"})
        return cls(**payload, lineage_hash=digest)


class OptimizationResult(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    study_id: str = Field(min_length=1)
    dataset_manifest_hash: str = Field(pattern=_SHA256_PATTERN)
    base_request_hash: str = Field(pattern=_SHA256_PATTERN)
    best_trial_number: int | None
    best_score: float | None
    best_candidate: StrategyDefinition | None
    trials: tuple[TrialLineage, ...]
    execution_authority: Literal[False] = False
    final_holdout_used: Literal[False] = False


class CandidateEvaluator(Protocol):
    def __call__(self, candidate: StrategyDefinition) -> EvaluationMetrics: ...


def robustness_score(metrics: EvaluationMetrics) -> float:
    mean_profit = mean(metrics.fold_profits)
    worst_profit = min(metrics.fold_profits)
    worst_drawdown = max(metrics.fold_drawdowns)
    stability_penalty = pstdev(metrics.fold_profits) if len(metrics.fold_profits) > 1 else 0.0
    trade_credit = min(metrics.trade_count / 100.0, 1.0)
    score = (
        0.45 * mean_profit
        + 0.25 * worst_profit
        - 0.20 * worst_drawdown
        - 0.10 * stability_penalty
        + 0.05 * trade_credit
    )
    return round(score, 12)


def _constraints_from_trial(trial: FrozenTrial) -> tuple[float, ...]:
    raw = trial.user_attrs.get("constraint_values", ())
    if not isinstance(raw, (list, tuple)):
        return (1.0,)
    try:
        return tuple(float(value) for value in raw)
    except (TypeError, ValueError):
        return (1.0,)


def _sample_parameter(trial: Trial, key: str, parameter: SearchParameter) -> JsonValue:
    if parameter.fixed is not None:
        return cast(JsonValue, parameter.fixed)
    if parameter.kind == "int":
        if parameter.low is None or parameter.high is None:
            raise RegistryError(f"integer search parameter {key} requires low and high")
        return trial.suggest_int(key, int(parameter.low), int(parameter.high))
    if parameter.kind == "float":
        if parameter.low is None or parameter.high is None:
            raise RegistryError(f"float search parameter {key} requires low and high")
        return trial.suggest_float(key, float(parameter.low), float(parameter.high))
    if parameter.kind == "categorical":
        if not parameter.choices:
            raise RegistryError(f"categorical search parameter {key} requires choices")
        return cast(JsonValue, trial.suggest_categorical(key, list(parameter.choices)))
    raise RegistryError(f"unsupported search parameter kind for {key}: {parameter.kind}")


class ConstrainedOptimizer:
    def __init__(
        self,
        *,
        generator: CandidateGenerator,
        search_spaces: SearchSpaceRegistry,
        dataset_manifest: DatasetManifest,
    ) -> None:
        self.generator = generator
        self.search_spaces = search_spaces
        self.dataset_manifest = dataset_manifest

    def _sample_request(
        self,
        trial: Trial,
        request: CandidateRequest,
        plan: OptimizationPlan,
    ) -> tuple[CandidateRequest, dict[str, JsonValue]]:
        flat_parameters: dict[str, JsonValue] = {}
        feature_payloads: list[dict[str, Any]] = []
        for feature in request.features:
            overrides: dict[str, JsonValue] = dict(feature.parameter_overrides)
            binding = plan.feature_search_spaces.get(feature.feature_id)
            if binding is not None:
                space = self.search_spaces.get(binding.space)
                unknown = set(binding.parameters) - set(space.parameters)
                if unknown:
                    raise RegistryError(
                        f"unknown bound parameters for {feature.feature_id}: {sorted(unknown)}"
                    )
                for parameter_name in binding.parameters:
                    parameter = space.parameters[parameter_name]
                    key = f"{feature.feature_id}.{parameter_name}"
                    sampled = _sample_parameter(trial, key, parameter)
                    flat_parameters[key] = sampled
                    overrides[parameter_name] = sampled
            feature_payloads.append(
                {
                    "feature_id": feature.feature_id,
                    "timeframe": feature.timeframe,
                    "parameter_overrides": overrides,
                }
            )
        payload = request.model_dump(mode="json")
        payload["features"] = feature_payloads
        return CandidateRequest.model_validate(payload), flat_parameters

    @staticmethod
    def _forbidden_reason(
        parameters: Mapping[str, object],
        plan: OptimizationPlan,
    ) -> str | None:
        for combination in plan.forbidden_combinations:
            if combination.matches(parameters):
                return combination.reason
        return None

    def optimize(
        self,
        *,
        request: CandidateRequest,
        plan: OptimizationPlan,
        evaluator: CandidateEvaluator,
    ) -> OptimizationResult:
        if request.max_conditions > plan.max_conditions:
            raise ValueError("candidate request max_conditions exceeds optimization plan")
        base_request_hash = request.canonical_sha256()
        sampler = TPESampler(
            seed=plan.seed,
            n_startup_trials=plan.startup_trials,
            constraints_func=_constraints_from_trial,
        )
        pruner = MedianPruner(
            n_startup_trials=plan.startup_trials,
            n_warmup_steps=1,
        )
        study = optuna.create_study(
            study_name=plan.study_id,
            direction=plan.direction,
            sampler=sampler,
            pruner=pruner,
        )

        def objective(trial: Trial) -> float:
            try:
                sampled_request, flat_parameters = self._sample_request(trial, request, plan)
                forbidden_reason = self._forbidden_reason(flat_parameters, plan)
                if forbidden_reason is not None:
                    trial.set_user_attr("failure_reason", forbidden_reason)
                    trial.set_user_attr("candidate_hash", "0" * 64)
                    trial.set_user_attr("constraint_values", (1.0, 1.0, 1.0, 1.0))
                    return _PENALTY_SCORE
                candidate = self.generator.generate(sampled_request)
                metrics = evaluator(candidate)
                constraints = (
                    float(plan.minimum_trades - metrics.trade_count),
                    float(max(metrics.fold_drawdowns) - plan.maximum_drawdown),
                    0.0 if metrics.lookahead_passed and metrics.recursive_passed else 1.0,
                    0.0 if metrics.falsification_passed else 1.0,
                )
                score = robustness_score(metrics)
                trial.set_user_attr("candidate_hash", candidate.canonical_sha256())
                trial.set_user_attr("candidate", candidate.model_dump(mode="json"))
                trial.set_user_attr("metrics", metrics.model_dump(mode="json"))
                trial.set_user_attr("constraint_values", constraints)
                trial.set_user_attr("dataset_manifest_hash", self.dataset_manifest.manifest_hash)
                trial.set_user_attr("base_request_hash", base_request_hash)
                running: list[float] = []
                for step, fold_profit in enumerate(metrics.fold_profits):
                    running.append(fold_profit)
                    trial.report(mean(running), step)
                    if trial.should_prune():
                        raise optuna.TrialPruned()
                return score
            except (CandidateGenerationError, RegistryError, ValueError) as exc:
                trial.set_user_attr("failure_reason", str(exc))
                trial.set_user_attr("candidate_hash", "0" * 64)
                trial.set_user_attr("constraint_values", (1.0, 1.0, 1.0, 1.0))
                return _PENALTY_SCORE

        study.optimize(objective, n_trials=plan.n_trials, gc_after_trial=True)
        lineages = tuple(
            self._lineage_from_trial(
                trial,
                study_id=plan.study_id,
                base_request_hash=base_request_hash,
            )
            for trial in study.trials
        )
        feasible = [
            trial
            for trial in study.trials
            if trial.state is TrialState.COMPLETE
            and trial.value is not None
            and all(value <= 0.0 for value in _constraints_from_trial(trial))
        ]
        if feasible:
            best = max(feasible, key=lambda item: cast(float, item.value))
            candidate_raw = best.user_attrs.get("candidate")
            best_candidate = (
                StrategyDefinition.model_validate(candidate_raw)
                if isinstance(candidate_raw, Mapping)
                else None
            )
            best_trial_number: int | None = best.number
            best_score: float | None = cast(float, best.value)
        else:
            best_candidate = None
            best_trial_number = None
            best_score = None
        return OptimizationResult(
            study_id=plan.study_id,
            dataset_manifest_hash=self.dataset_manifest.manifest_hash,
            base_request_hash=base_request_hash,
            best_trial_number=best_trial_number,
            best_score=best_score,
            best_candidate=best_candidate,
            trials=lineages,
        )

    def _lineage_from_trial(
        self,
        trial: FrozenTrial,
        *,
        study_id: str,
        base_request_hash: str,
    ) -> TrialLineage:
        metrics_raw = trial.user_attrs.get("metrics")
        metrics = (
            EvaluationMetrics.model_validate(metrics_raw)
            if isinstance(metrics_raw, Mapping)
            else None
        )
        failure_reason_raw = trial.user_attrs.get("failure_reason")
        failure_reason = failure_reason_raw if isinstance(failure_reason_raw, str) else None
        candidate_hash_raw = trial.user_attrs.get("candidate_hash", "0" * 64)
        candidate_hash = candidate_hash_raw if isinstance(candidate_hash_raw, str) else "0" * 64
        parameters = {
            key: cast(JsonValue, value)
            for key, value in sorted(cast(Mapping[str, object], trial.params).items())
        }
        state = cast(
            Literal["complete", "pruned", "fail", "running", "waiting"],
            trial.state.name.lower(),
        )
        return TrialLineage.create(
            study_id=study_id,
            trial_number=trial.number,
            state=state,
            dataset_manifest_hash=self.dataset_manifest.manifest_hash,
            base_request_hash=base_request_hash,
            candidate_hash=candidate_hash,
            parameters=parameters,
            constraints=_constraints_from_trial(trial),
            metrics=metrics,
            score=cast(float | None, trial.value),
            failure_reason=failure_reason,
        )
