---
task_id: FTAI-20260729-ase-02-constrained-research-optimization
status: implementing
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
updated_at: 2026-07-29T20:55:00+02:00
checkpoint_carrier: self
branch: agent/ase-02-constrained-research-optimization
base_head: 3d3c5d2c5806e2d23c86d2fc53cb01322d85a147
pr: null
status: implementing
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
derived:
  - ASE-02 supplies the bounded research evidence required before a separately reviewed ASE-03 paper/shadow integration package.
unknown:
  - Required exact-head GitHub workflow conclusions after PR creation and synchronization with current develop.
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
validation:
  - command: PYTHONPATH=. pytest -q tests/unit tests/integration
    result: PASS
    evidence: 11 tests passed; only Optuna constraints_func experimental-interface warnings were emitted.
known_limitations:
  - Research-only package; no market-data execution, deployment, promotion, order submission or capital authority.
  - Robustness scoring consumes evaluator metrics supplied by existing validation systems; it does not replace walk-forward or bias analysis.
blockers: []
next_action: Update the backlog, open the ASE-02 PR, synchronize it with current develop through a normal merge, then validate every required exact-head workflow and fix only evidenced failures.
```
