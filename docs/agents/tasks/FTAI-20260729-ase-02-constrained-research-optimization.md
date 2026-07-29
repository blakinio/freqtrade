---
task_id: FTAI-20260729-ase-02-constrained-research-optimization
status: validating
branch: agent/ase-02-constrained-research-optimization
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/ASE_02_CONSTRAINED_RESEARCH.md
search_first:
  - ai_strategy_engine/src/strategy_engine/research/
  - ai_strategy_engine/configs/dataset_manifest.v1.yaml
  - ai_strategy_engine/configs/optimization_plan.v1.yaml
  - ai_strategy_engine/tests/integration/test_ase02_constrained_research_contract.py
owned_paths:
  - ai_strategy_engine/src/strategy_engine/research/
  - ai_strategy_engine/configs/dataset_manifest.v1.yaml
  - ai_strategy_engine/configs/optimization_plan.v1.yaml
  - ai_strategy_engine/examples/ai_candidate_request.json
  - ai_strategy_engine/schemas/dataset-manifest.v1.schema.json
  - ai_strategy_engine/schemas/ai-candidate-request.v1.schema.json
  - ai_strategy_engine/schemas/optimization-plan.v1.schema.json
  - ai_strategy_engine/tests/unit/test_research_dataset.py
  - ai_strategy_engine/tests/unit/test_ai_candidate_generator.py
  - ai_strategy_engine/tests/unit/test_constrained_optimization.py
  - ai_strategy_engine/tests/integration/test_ase02_constrained_research_contract.py
  - ai_strategy_engine/docs/ASE_02_CONSTRAINED_RESEARCH.md
  - docs/ai_platform/ASE_02_CONSTRAINED_RESEARCH.md
  - ai_strategy_engine/pyproject.toml
  - ai_strategy_engine/TASKS.md
  - docs/agents/tasks/FTAI-20260729-ase-02-constrained-research-optimization.md
---

# ASE-02 constrained research and optimization

## Goal

Add an immutable dataset identity, a fail-closed lock around the prospective final holdout,
constrained Optuna studies with trial lineage and robustness scoring, and a schema-constrained
AI candidate generator that can emit only the existing Strategy DSL from canonical registry entries.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T21:14:00+02:00
checkpoint_carrier: self
branch: agent/ase-02-constrained-research-optimization
base_head: c4a4a1f22dfea1f0193f886686f6db8cb145e7a7
pr: 741
status: validating
exact_head_resolution: Resolve checkpoint_carrier from the current PR 741 head; required GitHub checks and the PR body attached to that commit are authoritative.
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/ASE_02_CONSTRAINED_RESEARCH.md
proven:
  - The existing FeatureRegistry, SearchSpaceRegistry, StrategyDefinition and StrategyValidator are reused rather than duplicated.
  - The immutable dataset manifest is hash-bound and matches the canonical protected final holdout declaration.
  - The protected timerange remains 20260801-20260930 with used false and retuning disallowed.
  - AI candidate generation accepts only validated and approved registry features, emits existing DSL and forces execution_authority and order_submission false.
  - Optuna studies use seeded TPE sampling, explicit search bindings, forbidden combinations, feasibility constraints, median pruning, canonical lineage hashes and stability-aware robustness scoring.
  - Local package validation passed 11 unit and integration tests; no final holdout data, exchange credentials or execution path was used.
  - Synchronization PR 742 merged current develop normally into the ASE-02 branch without force-push or branch-protection bypass.
derived:
  - ASE-02 supplies the bounded research evidence required before a separately reviewed ASE-03 paper/shadow integration package.
unknown:
  - Required exact-head GitHub workflow conclusions on the current PR 741 head.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Duplicate the existing experiment registry or Phase 4 discovery engine.
  - Permit arbitrary source-code generation, eval, exec or direct Freqtrade execution imports.
  - Use, unlock or retune from the prospective final holdout.
changed_paths:
  - ai_strategy_engine/src/strategy_engine/research/
  - ai_strategy_engine/configs/dataset_manifest.v1.yaml
  - ai_strategy_engine/configs/optimization_plan.v1.yaml
  - ai_strategy_engine/examples/ai_candidate_request.json
  - ai_strategy_engine/schemas/dataset-manifest.v1.schema.json
  - ai_strategy_engine/schemas/ai-candidate-request.v1.schema.json
  - ai_strategy_engine/schemas/optimization-plan.v1.schema.json
  - ai_strategy_engine/tests/unit/test_research_dataset.py
  - ai_strategy_engine/tests/unit/test_ai_candidate_generator.py
  - ai_strategy_engine/tests/unit/test_constrained_optimization.py
  - ai_strategy_engine/tests/integration/test_ase02_constrained_research_contract.py
  - ai_strategy_engine/docs/ASE_02_CONSTRAINED_RESEARCH.md
  - docs/ai_platform/ASE_02_CONSTRAINED_RESEARCH.md
  - ai_strategy_engine/pyproject.toml
  - ai_strategy_engine/TASKS.md
validation:
  - command: PYTHONPATH=. pytest -q tests/unit tests/integration
    result: PASS
    evidence: 11 tests passed; only Optuna constraints_func experimental-interface warnings were emitted.
  - command: Normal develop synchronization through PR 742
    result: PASS
    evidence: Branch was synchronized at behind_by 0 using merge commit 7e1678cbb158cc011fc038f0eb814f05c5a19da2.
  - command: Final exact-head workflow suite
    result: REQUIRED
    evidence: AI Strategy Engine, AI Platform CI, Freqtrade CI and GitHub Actions Security Analysis must succeed on the current PR head before normal merge.
known_limitations:
  - Research-only package; no market-data execution, deployment, promotion, order submission or capital authority.
  - Robustness scoring consumes evaluator metrics supplied by existing validation systems; it does not replace walk-forward or bias analysis.
blockers: []
next_action: Inspect the exact-head workflow suite for PR 741, fix only evidenced failures, resynchronize if develop moves, then update the PR body and merge normally after all required checks are green.
```
