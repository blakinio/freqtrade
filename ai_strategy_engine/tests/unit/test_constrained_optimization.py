from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from strategy_engine.domain.models import StrategyDefinition
from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
from strategy_engine.research import (
    CandidateGenerator,
    CandidateRequest,
    ConstrainedOptimizer,
    EvaluationMetrics,
    OptimizationPlan,
    load_dataset_manifest,
    robustness_score,
)

ENGINE_ROOT = Path(__file__).resolve().parents[2]


def _load_request() -> CandidateRequest:
    return CandidateRequest.model_validate_json(
        (ENGINE_ROOT / "examples" / "ai_candidate_request.json").read_text(encoding="utf-8")
    )


def _load_plan() -> OptimizationPlan:
    raw = yaml.safe_load(
        (ENGINE_ROOT / "configs" / "optimization_plan.v1.yaml").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ENGINE_ROOT / "schemas" / "optimization-plan.v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(raw, schema)
    return OptimizationPlan.model_validate(raw)


def _evaluate(candidate: StrategyDefinition) -> EvaluationMetrics:
    roc = next(feature for feature in candidate.features if feature.id == "roc.v1")
    period = float(roc.params["period"])
    edge = max(0.001, 0.08 - abs(period - 12.0) * 0.002)
    return EvaluationMetrics(
        fold_profits=(edge, edge * 0.9, edge * 0.85),
        fold_drawdowns=(0.08, 0.10, 0.09),
        trade_count=50,
        lookahead_passed=True,
        recursive_passed=True,
        falsification_passed=True,
    )


def test_constrained_optuna_records_lineage_and_never_uses_final_holdout() -> None:
    registry = FeatureRegistry.load(ENGINE_ROOT / "configs" / "feature_registry.v1.yaml")
    spaces = SearchSpaceRegistry.load(ENGINE_ROOT / "configs" / "search_spaces.v1.yaml")
    manifest = load_dataset_manifest(ENGINE_ROOT / "configs" / "dataset_manifest.v1.yaml")
    result = ConstrainedOptimizer(
        generator=CandidateGenerator(registry, spaces),
        search_spaces=spaces,
        dataset_manifest=manifest,
    ).optimize(request=_load_request(), plan=_load_plan(), evaluator=_evaluate)

    assert len(result.trials) == 8
    assert result.best_trial_number is not None
    assert result.best_candidate is not None
    assert result.execution_authority is False
    assert result.final_holdout_used is False
    assert all(trial.dataset_manifest_hash == manifest.manifest_hash for trial in result.trials)
    assert all(
        trial.lineage_hash == trial.canonical_sha256(exclude={"lineage_hash"})
        for trial in result.trials
    )
    assert result.best_candidate.execution["execution_authority"] is False


def test_robustness_score_penalizes_instability_and_drawdown() -> None:
    stable = EvaluationMetrics(
        fold_profits=(0.05, 0.052, 0.048),
        fold_drawdowns=(0.08, 0.09, 0.08),
        trade_count=60,
        lookahead_passed=True,
        recursive_passed=True,
        falsification_passed=True,
    )
    unstable = EvaluationMetrics(
        fold_profits=(0.12, -0.03, 0.01),
        fold_drawdowns=(0.10, 0.24, 0.18),
        trade_count=60,
        lookahead_passed=True,
        recursive_passed=True,
        falsification_passed=True,
    )

    assert robustness_score(stable) > robustness_score(unstable)
