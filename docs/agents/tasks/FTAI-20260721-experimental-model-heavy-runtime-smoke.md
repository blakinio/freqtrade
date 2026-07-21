---
task_id: FTAI-20260721-experimental-model-heavy-runtime-smoke
status: done
branch: feat/experimental-model-heavy-runtime-smoke-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#61"
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
search_first: []
optional_reads:
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
---

# Experimental Model Heavy Runtime Smoke v1

## Goal

Run the smallest real heavy-runtime proof of integration for both canonical experimental model classes using synthetic-only data and the FreqAI/freqai_rl dependency profiles, without historical-OOS scoring or model-performance conclusions.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T08:30:00Z
head: 2ed90b8d74949117edacb634f286acf6e8fd034c
branch: develop
pr: "#61 merged"
status: done
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
proven:
  - PR #61 was squash-merged into develop as 2ed90b8d74949117edacb634f286acf6e8fd034c after the final head remained mergeable and had no review comments.
  - The dedicated workflow installs the repository freqai and freqai_rl optional dependency profiles on Python 3.12 and uses deterministic synthetic data only.
  - SeededPyTorchMLPRegressor completed its real inherited fit path for one synthetic epoch and produced finite predictions with the expected shape.
  - LongOnlyEnvironment completed construction, reset, the canonical three-action/observation contract checks, and the LongOnlyReinforcementLearner inherited PPO fit path on synthetic data.
  - The initial combined RL smoke failure was isolated to the runtime-result path before PPO; after normalizing Gymnasium-derived action/shape scalar values to built-in integers, construction, reset, contract, and PPO fit all passed.
  - Final Experimental Model Runtime Smoke run 29813916198 completed successfully and validated this checkpoint with tools/agents/checkpoint.py --require-checkpoint before rerunning all heavy-runtime stages.
  - Final AI Platform CI run 29813916158, Freqtrade CI run 29813916131, and zizmor run 29813916115 completed successfully; Pre-commit Types update run 29813916129 was skipped rather than failed.
  - Protected final holdout 20260801-20260930 remained unused; no historical OOS was scored and no Phase 6 membership, promotion, profitability, or model-performance conclusion was produced.
derived:
  - Both canonical experimental model paths are runtime-feasible under the declared heavy dependency profile, but this is integration evidence only and says nothing about trading quality.
  - The next research dependency can move from synthetic runtime proof to a bounded real historical execution package using only the already-declared pre-final-holdout geometry and the strict experimental OOS extractor.
unknown:
  - Whether the repository currently has all required historical market data and execution resources to produce real PyTorch and RL backtest archives under the declared single-training-window geometry.
  - Actual strict historical-OOS trading metrics for either experimental model remain unknown.
conflicts: []
first_failure:
  marker: experimental-runtime-smoke-rl-result-scalar
  evidence: The first dedicated runtime runs installed all heavy dependencies and passed PyTorch fit but failed in the combined RL environment result path before PPO; splitting the stages and normalizing action/shape values to built-in integers yielded successful construction, reset, contract, and PPO fit.
rejected_hypotheses:
  - Use May-June historical OOS to make the runtime smoke more realistic.
  - Access the protected final holdout for integration validation.
  - Treat synthetic runtime completion as a profitability or superiority result.
changed_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
validation:
  - command: GitHub Actions Experimental Model Runtime Smoke #9
    result: PASS
    evidence: Run 29813916198 passed checkpoint validation, dependency installation, canonical PyTorch fit, RL construction, RL reset, RL contract, and canonical RL PPO fit.
  - command: GitHub Actions AI Platform CI #261
    result: PASS
    evidence: Run 29813916158 completed successfully on the final implementation head.
  - command: GitHub Actions Freqtrade CI #276
    result: PASS
    evidence: Run 29813916131 completed successfully on the final implementation head.
  - command: GitHub Actions Security Analysis with zizmor #255
    result: PASS
    evidence: Run 29813916115 completed successfully on the final implementation head.
blockers: []
next_action: Create the next bounded experimental historical-execution task and first verify historical market-data availability, execution resources, and the existing FreqAI command path for the declared single-training-window geometry before producing any PyTorch or RL backtest archive for strict 20260501-20260630 OOS extraction.
```
