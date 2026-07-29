from __future__ import annotations

import json
from pathlib import Path

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
)

ENGINE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ENGINE_ROOT.parent


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


def test_locked_dataset_to_constrained_candidate_lineage() -> None:
    manifest = load_dataset_manifest(
        ENGINE_ROOT / "configs" / "dataset_manifest.v1.yaml",
        protected_declaration_path=(
            REPO_ROOT / "ai_platform" / "validation" / "final-holdout-v2-declaration.json"
        ),
    )
    request = CandidateRequest.model_validate_json(
        (ENGINE_ROOT / "examples" / "ai_candidate_request.json").read_text(encoding="utf-8")
    )
    plan = OptimizationPlan.model_validate(
        yaml.safe_load(
            (ENGINE_ROOT / "configs" / "optimization_plan.v1.yaml").read_text(
                encoding="utf-8"
            )
        )
    )
    registry = FeatureRegistry.load(ENGINE_ROOT / "configs" / "feature_registry.v1.yaml")
    spaces = SearchSpaceRegistry.load(ENGINE_ROOT / "configs" / "search_spaces.v1.yaml")

    result = ConstrainedOptimizer(
        generator=CandidateGenerator(registry, spaces),
        search_spaces=spaces,
        dataset_manifest=manifest,
    ).optimize(request=request, plan=plan, evaluator=_evaluate)

    assert result.best_candidate is not None
    assert result.best_candidate.execution["execution_authority"] is False
    assert result.best_candidate.execution["order_submission"] is False
    assert result.final_holdout_used is False
    assert result.execution_authority is False
    assert manifest.final_holdout.used is False
    assert all(trial.dataset_manifest_hash == manifest.manifest_hash for trial in result.trials)
    assert all(
        trial.metrics is None or trial.metrics.final_holdout_used is False
        for trial in result.trials
    )
    assert json.loads(result.best_candidate.model_dump_json())["provenance"]["details"][
        "final_holdout_used"
    ] is False
