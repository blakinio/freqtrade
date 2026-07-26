---
task_id: FTAI-20260726-residual-pytorch-research-foundation
status: active
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

This package performs no market-data access, training on historical exchange data, backtesting, hyperparameter search, feature search, strict-OOS scoring, protected-final-holdout access, deployment, model promotion or profitability claim.

It does not change Freqtrade core, the frozen strategy thresholds, completed Phase 6, the authoritative `selected_model = null`, RL models or liquidation-data contracts.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T11:43:00+02:00
branch: feat/residual-pytorch-research-foundation
pr: 338
status: second_reconstruction_pending_exact_head_ci
base_develop_at_second_reconstruction: f49929bd151df878de8b83f83a909e68a70dcad8
validated_checkpoint_refresh_head: 038dcd06317d0af60f71256809d41c8e9779d795
previous_reconstructed_head: 14c6954aa92f1ad08a7e8c006d1533950ab092ab
initial_head: 9c05b88acecb9fe37d79c8b8282fbb1add3d674a
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
  - PR 338 contains exactly the nine intended owned paths.
  - No open pull request owns or changes any PR 338 path.
  - PR 338 has no submitted reviews, review threads or unresolved review blocker.
  - ResidualPyTorchRegressor uses the supported BasePyTorchRegressor extension point.
  - The M1 network has an explicit residual addition, one target, AdamW and SmoothL1Loss.
  - The config is spot, dry_run, initial_state stopped, empty-secret and continual-learning disabled.
  - The experiment has no execution/download timerange and no run request.
  - Phase 5 thresholds remain 0.006 and -0.009.
  - Authoritative Phase 6 evidence remains completed with selected_model null.
  - Consumed historical OOS 20260501-20260630 remains forbidden.
  - Protected final holdout 20260801-20260930 remains unused and unauthorized.
  - Initial exact-head AI Platform CI 30195444286 run 1411 succeeded on initial_head.
  - Initial exact-head Freqtrade CI 30195444278 run 1708 succeeded on initial_head.
  - Initial exact-head Experimental Model Runtime Smoke 30195444285 run 76 succeeded on initial_head.
  - Initial exact-head Zizmor 30195444300 run 1575 succeeded on initial_head.
  - Reconstructed exact-head AI Platform CI 30196151286 run 1418 succeeded on previous_reconstructed_head.
  - Reconstructed exact-head Freqtrade CI 30196151287 run 1717 succeeded on previous_reconstructed_head.
  - Reconstructed exact-head Experimental Model Runtime Smoke 30196151282 run 77 succeeded on previous_reconstructed_head.
  - Reconstructed exact-head Zizmor 30196151294 run 1584 succeeded on previous_reconstructed_head.
  - Checkpoint-refresh exact-head AI Platform CI 30196672519 run 1421 succeeded on validated_checkpoint_refresh_head.
  - Checkpoint-refresh exact-head Freqtrade CI 30196672535 run 1721 succeeded on validated_checkpoint_refresh_head.
  - Checkpoint-refresh exact-head Experimental Model Runtime Smoke 30196672521 run 78 succeeded on validated_checkpoint_refresh_head.
  - Checkpoint-refresh exact-head Zizmor 30196672552 run 1588 succeeded on validated_checkpoint_refresh_head.
  - Pre-commit Types update 30196672530 run 1355 was skipped; Freqtrade CI pre-commit checks succeeded.
  - All eight non-checkpoint files retained their prior blob SHA through both reconstructions.
  - Develop-only advances touched no PR 338 owned path, but repository mergeability required another current-base reconstruction.
derived:
  - P0 remains the only authorized scope of PR 338.
  - Residual-specific runtime support still requires a separate P1 synthetic-only package.
unknown:
  - Residual-model resolver, fit, save, load and predict behavior under the dependency-closed Linux FreqAI profile.
  - CUDA behavior when CUDA is available.
  - Market-data, model-quality or trading performance of the residual model.
conflicts: []
first_failure:
  marker: RUFF_FORMAT_DRIFT
  evidence: Initial source formatting differed from Ruff 0.15.21 output; canonical formatting was applied and required CI passed.
first_live_blocker:
  marker: DEVELOP_ADVANCED_DURING_CI
  evidence: Develop advanced during exact-head validation and GitHub repeatedly changed PR 338 to mergeable false despite no owned-path overlap.
  correction: Reconstructed the exact bounded nine-file diff on each current develop base, replaced the PR branch atomically, and required fresh exact-head CI rather than force-merging.
rejected_hypotheses:
  - Force-merge a non-mergeable PR.
  - Add runtime smoke, market-data training or backtesting to PR 338.
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
  - Latest completed AI Platform CI 30196672519 run 1421: success.
  - Latest completed Freqtrade CI 30196672535 run 1721: success.
  - Latest completed Experimental Model Runtime Smoke 30196672521 run 78: success; it does not prove residual P1 runtime.
  - Latest completed Zizmor 30196672552 run 1588: success.
  - Review state: no reviews and no review threads.
blockers:
  - Exact-head CI is required for the second reconstructed PR head.
next_action: Replace feat/residual-pytorch-research-foundation with this current-develop reconstruction, verify the exact nine-file diff and all exact-head workflows, then squash-merge PR 338 immediately if mergeable and blocker-free. Start a separate P1 runtime-smoke task only after merge.
```
