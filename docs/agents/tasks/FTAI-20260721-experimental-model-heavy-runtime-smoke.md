---
task_id: FTAI-20260721-experimental-model-heavy-runtime-smoke
status: ready
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
updated_at: 2026-07-21T08:20:00Z
head: 9ecd7bc37bb5b8113ac148255d0c3e29bbaeb7a7
branch: feat/experimental-model-heavy-runtime-smoke-v1
pr: "#61"
status: ready
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
proven:
  - develop was verified at 8be21011678da596ad20f0415c58698e7dacc92a before branch creation and no open pull requests were present.
  - The prior strict experimental OOS extractor checkpoint declared the next action as a minimal heavy-runtime proof for both canonical PyTorch and RL classes.
  - The dedicated workflow installs the repository freqai and freqai_rl optional dependency profiles on Python 3.12 and uses deterministic synthetic data only.
  - SeededPyTorchMLPRegressor completed its real inherited fit path for one synthetic epoch and produced finite predictions with the expected shape.
  - LongOnlyEnvironment completed construction, reset, the canonical three-action/observation contract checks, and the LongOnlyReinforcementLearner inherited PPO fit path on synthetic data.
  - The initial combined RL smoke failure was isolated to the runtime-result path before PPO; after normalizing Gymnasium-derived action/shape scalar values to built-in integers, construction, reset, contract, and PPO fit all passed.
  - Experimental Model Runtime Smoke run 29813554543 completed successfully on head 9ecd7bc37bb5b8113ac148255d0c3e29bbaeb7a7.
  - AI Platform CI run 29813554620, Freqtrade CI run 29813554818, and zizmor run 29813554635 completed successfully on the same head; Pre-commit Types update run 29813554657 was skipped rather than failed.
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
  evidence: The first dedicated runtime runs installed all heavy dependencies and passed PyTorch fit but failed in the combined RL environment result path before PPO; splitting the stages and normalizing action/shape values to built-in integers yielded successful construction, reset, contract, and PPO fit on run 29813554543.
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
  - command: GitHub Actions Experimental Model Runtime Smoke #7
    result: PASS
    evidence: Run 29813554543 passed dependency installation, canonical PyTorch fit, RL construction, RL reset, RL contract, and canonical RL PPO fit.
  - command: GitHub Actions AI Platform CI #259
    result: PASS
    evidence: Run 29813554620 completed successfully.
  - command: GitHub Actions Freqtrade CI #274
    result: PASS
    evidence: Run 29813554818 completed successfully.
  - command: GitHub Actions Security Analysis with zizmor #253
    result: PASS
    evidence: Run 29813554635 completed successfully.
blockers: []
next_action: Merge PR #61 into develop after confirming its head is unchanged, it remains mergeable, required checks remain green, and no unresolved review thread exists.
```
