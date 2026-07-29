---
task_id: FTAI-20260729-ase-02-constrained-research-optimization
status: complete
branch: develop
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 741
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
updated_at: 2026-07-29T21:48:00+02:00
head: e6ff45aa810b3982f79b7167450ec38a50b1b4f4
branch: develop
pr: 741
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/ASE_02_CONSTRAINED_RESEARCH.md
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
proven:
  - The existing FeatureRegistry, SearchSpaceRegistry, StrategyDefinition and StrategyValidator are reused rather than duplicated.
  - The immutable dataset manifest is SHA-256 bound, uses ordered train/tune/validation windows and matches the canonical protected final holdout declaration.
  - The prospective final holdout remains 20260801-20260930 with used false and retuning disallowed.
  - AI candidate generation accepts only validated AI-approved registry features, emits the existing Strategy DSL and forces execution_authority and order_submission false.
  - Seeded Optuna TPE studies use explicit search bindings, scalar categorical choices, forbidden combinations, feasibility constraints, median pruning, canonical lineage hashes and stability-aware robustness scoring.
  - Final synchronized implementation head dd4cd6018ea405d7325efd3ddd68273ffb41de9d was behind current develop by zero commits and had zero unresolved review threads.
  - AI Strategy Engine 30484642073 passed package and Portal tests, Ruff, mypy, compile, deterministic E2E, schemas, materialization and architecture-boundary scans on the final head.
  - AI Platform CI 30484641913, Freqtrade CI 30484642271 including Python 3.11-3.14, coverage, documentation, build distributions and CI Gate, and workflow-security run 30484642412 passed on the final head.
  - PR 741 merged normally with expected-head protection as e6ff45aa810b3982f79b7167450ec38a50b1b4f4.
derived:
  - ASE-02 supplies the bounded immutable research and optimization evidence required before a separately reviewed ASE-03 paper/shadow integration package.
  - No final-holdout unlock, execution authority, order path, deployment, promotion, exchange credential or live-capital capability was introduced.
unknown: []
conflicts: []
first_failure:
  marker: ASE02_VALIDATION_REPAIRS
  evidence: Initial exact-head validation exposed a canonical DSL validator import error, then Ruff timezone/pairwise/export-order findings, then two Optuna mypy findings; each was repaired without changing research scope, final-holdout policy or execution boundaries before the final synchronized workflow suite passed.
rejected_hypotheses:
  - Duplicate the existing experiment registry, Feature Registry, Search Space Registry or Phase 4 discovery engine.
  - Permit arbitrary source-code generation, eval, exec, direct Freqtrade execution imports or non-scalar Optuna categorical values.
  - Use, unlock or retune from the prospective final holdout.
  - Treat optimization output as deployment, promotion, order or live-capital authority.
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
  - docs/agents/tasks/FTAI-20260729-ase-02-constrained-research-optimization.md
validation:
  - command: Final synchronized AI Strategy Engine 30484642073 on dd4cd6018ea405d7325efd3ddd68273ffb41de9d
    result: PASS
    evidence: Package and Portal tests, Ruff, mypy, compile, deterministic E2E, schema/example validation, required paths and prohibited-boundary scan all succeeded.
  - command: Final synchronized AI Platform CI 30484641913
    result: PASS
    evidence: Exact-head platform integration validation succeeded.
  - command: Final synchronized Freqtrade CI 30484642271
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11-3.14, coverage, generated-file checks, smoke tests, Ruff, mypy, distributions and CI Gate succeeded.
  - command: Final synchronized GitHub Actions Security Analysis 30484642412
    result: PASS
    evidence: Exact-head workflow-security analysis succeeded.
  - command: Normal protected merge of PR 741
    result: PASS
    evidence: Merged expected exact head as e6ff45aa810b3982f79b7167450ec38a50b1b4f4 without force push or branch-protection bypass.
known_limitations:
  - Research-only package; no market-data execution, deployment, promotion, order submission or capital authority.
  - Robustness scoring consumes evaluator metrics supplied by existing validation systems; it does not replace walk-forward, simulator parity or bias analysis.
blockers: []
next_action: Create FTAI-20260729-ase-03-paper-shadow-integration from current develop and begin its bounded preflight for simulator parity, Risk Core approval, private paper/shadow adapter, audit trail and rollback without adding live-capital authority.
```
