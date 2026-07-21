---
task_id: FTAI-20260721-experimental-model-heavy-runtime-smoke
status: implementing
branch: feat/experimental-model-heavy-runtime-smoke-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
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
updated_at: 2026-07-21T07:20:00Z
head: 8be21011678da596ad20f0415c58698e7dacc92a
branch: feat/experimental-model-heavy-runtime-smoke-v1
pr: none
status: implementing
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
  - The prior strict experimental OOS extractor checkpoint declares the next action as a minimal heavy-runtime proof for both canonical PyTorch and RL classes.
  - SeededPyTorchMLPRegressor extends the repository PyTorchMLPRegressor and seeds Python, NumPy, PyTorch, CUDA, and cuDNN settings before fit.
  - LongOnlyReinforcementLearner binds the custom three-action LongOnlyEnvironment and inherits the repository ReinforcementLearner fit path.
  - The smoke uses only deterministic synthetic feature, target, and OHLC data and does not access any exchange or historical market dataset.
  - The dedicated workflow installs the freqai and freqai_rl optional dependency profiles and runs the smoke on Python 3.12.
  - Protected final holdout 20260801-20260930 remains unused; historical OOS scoring, Phase 6 membership, promotion, and profitability conclusions remain forbidden.
derived:
  - A successful smoke establishes runtime compatibility of the canonical experimental paths but is not evidence of trading quality.
unknown:
  - Whether the dedicated GitHub Actions heavy-runtime smoke passes with the current dependency graph.
  - Whether repository-wide CI exposes integration or formatting issues in the new smoke code/workflow.
conflicts: []
first_failure:
  marker: none
  evidence: none
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
  - command: GitHub Actions
    result: NOT_RUN
    evidence: Implementation pull request has not been opened yet.
blockers: []
next_action: Open the implementation pull request against develop and use the dedicated Experimental Model Runtime Smoke plus required repository CI to validate the synthetic PyTorch fit and PPO environment training path; fix any failures before merge.
```
