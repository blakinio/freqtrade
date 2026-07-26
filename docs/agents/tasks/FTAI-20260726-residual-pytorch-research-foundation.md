---
task_id: FTAI-20260726-residual-pytorch-research-foundation
status: completed
branch: feat/residual-pytorch-research-foundation
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 338
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-research-foundation.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/freqaimodels/residual_mlp_components.py
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_research_contract.py
  - tests/ai_platform/test_residual_pytorch_research_contract.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
context_routes:
  - docs/agents/tasks/FTAI-20260720-experimental-model-research-foundation.md
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
---

# Residual PyTorch research foundation

## Goal

Introduce the smallest useful custom neural-model successor to the existing seeded MLP baseline: a deterministic, single-target residual MLP through supported FreqAI extension points, together with a safe config, inert experiment declaration, fail-closed contract, tests and a staged implementation/evaluation plan.

## Boundaries

This package performed no market-data access, training on historical exchange data, backtesting, hyperparameter search, feature search, strict-OOS scoring, protected-final-holdout access, deployment, model promotion or profitability claim.

It did not change Freqtrade core, the frozen strategy thresholds, completed Phase 6, the authoritative `selected_model = null`, RL models or liquidation-data contracts.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:16:00+02:00
implementation_head: a0aa39921e4136cd30b7d66eb0df71d44bd0fbab
merge_commit: 1ed82158374684aa9a01b3d98e172fcca84ee88d
branch: feat/residual-pytorch-research-foundation
pr: 338
status: completed
context_routes:
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-research-foundation.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/freqaimodels/residual_mlp_components.py
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_research_contract.py
  - tests/ai_platform/test_residual_pytorch_research_contract.py
proven:
  - PR 338 merged exact implementation_head as merge_commit with exactly the nine intended owned paths.
  - PR 338 was mergeable, non-draft, had no submitted reviews, no review threads and no unresolved review blocker at merge time.
  - No open pull request owned or changed any PR 338 path during the final pre-merge audit.
  - ResidualPyTorchRegressor uses the supported BasePyTorchRegressor extension point.
  - The M1 network has an explicit residual addition, one target, AdamW and SmoothL1Loss.
  - The config is spot, dry_run, initial_state stopped, empty-secret and continual-learning disabled.
  - The experiment has no execution or download timerange and no run request.
  - Phase 5 thresholds remain 0.006 and -0.009.
  - Authoritative Phase 6 evidence remains completed with selected_model null.
  - Consumed historical OOS 20260501-20260630 remains forbidden.
  - Protected final holdout 20260801-20260930 remains unused and unauthorized.
  - Exact-head AI Platform CI 30197544469 run 1435 succeeded.
  - Exact-head Freqtrade CI 30197544511 run 1739 succeeded, including pre-commit, documentation, Python 3.11 through 3.14, coverage, package build, Ruff, Ruff format and mypy where applicable.
  - Exact-head Experimental Model Runtime Smoke 30197544464 run 80 succeeded; this existing smoke does not prove residual-specific P1 lifecycle support.
  - Exact-head Zizmor 30197544539 run 1606 succeeded.
  - Pre-commit Types update 30197544519 run 1370 was skipped; Freqtrade CI pre-commit checks succeeded.
derived:
  - The bounded P0 foundation is accepted and merged.
  - Residual-specific runtime support still requires a separate synthetic-only P1 task, branch and PR.
unknown:
  - Residual-model resolver, fit, save, load and predict behavior under the dependency-closed Linux FreqAI profile.
  - CUDA behavior when CUDA is available.
  - Market-data, model-quality or trading performance of the residual model.
conflicts: []
first_failure:
  marker: RUFF_FORMAT_DRIFT
  evidence: Initial source formatting differed from Ruff 0.15.21 output.
  correction: Applied canonical Ruff formatting and required exact-head CI subsequently passed.
first_live_blocker:
  marker: DEVELOP_ADVANCED_DURING_CI
  evidence: Develop advanced repeatedly during exact-head validation and GitHub temporarily reported PR 338 as non-mergeable despite no owned-path overlap.
  correction: Reconstructed the exact bounded nine-file tree on current develop without semantic expansion, required fresh exact-head CI and merged only after the final atomic audit passed.
rejected_hypotheses:
  - Force-merge a non-mergeable PR.
  - Add residual-specific runtime smoke, market-data training or backtesting to PR 338.
  - Reuse consumed historical OOS or the protected final holdout.
  - Treat the model as a Phase 6 candidate or compare it retrospectively with RL for promotion.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-research-foundation.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/freqaimodels/residual_mlp_components.py
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_research_contract.py
  - tests/ai_platform/test_residual_pytorch_research_contract.py
validation:
  - AI Platform CI 30197544469 run 1435: success.
  - Freqtrade CI 30197544511 run 1739: success.
  - Experimental Model Runtime Smoke 30197544464 run 80: success; residual-specific runtime remains unknown.
  - Zizmor 30197544539 run 1606: success.
  - Review state: no reviews and no review threads.
blockers: []
next_action: Start bounded task FTAI-20260726-residual-pytorch-runtime-smoke from merge_commit on a separate branch and PR; use only deterministic synthetic data and report runtime_supported, runtime_not_supported or runtime_inconclusive.
```
