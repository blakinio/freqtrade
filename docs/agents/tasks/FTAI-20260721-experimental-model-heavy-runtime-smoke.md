---
task_id: FTAI-20260721-experimental-model-heavy-runtime-smoke
status: implementing
branch: test/experimental-model-heavy-runtime-smoke-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - .github/workflows/ai-platform-heavy-runtime.yml
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/foundation-v1.json
search_first:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
---

# Experimental model heavy runtime smoke

## Goal

Prove the canonical PyTorch and RL research model classes load and complete bounded integration work in a real heavy runtime using synthetic data entirely inside the declared pre-OOS training window, without historical-OOS scoring, protected-final-holdout access, retuning, Phase 6 participation, promotion, or performance conclusions.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T07:20:00Z
head: 6af5285a0f05a60574996a2b6c90b0f83475b13c
branch: test/experimental-model-heavy-runtime-smoke-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/ai-platform-heavy-runtime.yml
owned_paths:
  - .github/workflows/ai-platform-heavy-runtime.yml
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
proven:
  - develop was verified at 8be21011678da596ad20f0415c58698e7dacc92a and no open pull requests were present before branch creation.
  - The prior ready checkpoint requires a minimal heavy-runtime proof for the canonical PyTorch and RL classes using only synthetic or minimal pre-OOS data and forbids historical-OOS scoring or performance conclusions.
  - The repository freqai_rl extra supplies Torch, Gymnasium, Stable-Baselines3 and sb3-contrib, while inherited FreqAI modules import dependencies declared by the separate freqai extra.
  - The dependency-closed canonical research runtime declaration is therefore freqtrade[freqai,freqai_rl]; no upstream dependency definitions were changed.
  - The smoke script uses synthetic 15-minute timestamps starting 2026-01-01 and fails closed if they leave 20251201-20260228 or reach historical OOS/final holdout boundaries.
  - The smoke does not invoke the Freqtrade backtest path or the strict historical-OOS extractor.
derived:
  - A dedicated path-scoped heavy-runtime workflow is the smallest durable proof because normal AI Platform CI intentionally installs only lightweight validation dependencies.
  - Canonical research execution remains false because the smoke does not execute either canonical manifest or produce model-performance evidence.
unknown:
  - The new heavy-runtime workflow has not yet executed on GitHub Actions.
  - The canonical PyTorch fit and bounded PPO fit may expose runtime-only integration failures not visible to lightweight CI.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - freqtrade[freqai_rl] alone is dependency-closed for importing the canonical classes through the FreqAI inheritance stack.
  - A static import-only check is sufficient proof of PyTorch and RL runtime integration.
changed_paths:
  - .github/workflows/ai-platform-heavy-runtime.yml
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-heavy-runtime-smoke.md
validation:
  - command: GitHub Actions CI
    result: NOT_RUN
    evidence: Implementation pull request has not been opened yet.
blockers: []
next_action: Open the implementation pull request against develop and use the dedicated heavy-runtime workflow plus standard repository CI to validate the bounded PyTorch and RL integration smoke before merge.
```
