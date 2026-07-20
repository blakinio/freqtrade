---
task_id: FTAI-20260720-experimental-model-research-foundation
status: implementing
branch: feat/experimental-model-research-foundation-v1
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: ""
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/configs/freqai-pytorch-research.example.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260720-experimental-model-research-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/foundation-v1.json
search_first:
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/scripts/protected_final_holdout.py
  - ai_platform/scripts/run_experiment.py
---

# Experimental model research foundation

## Goal

Create one bounded, isolated research foundation for PyTorch and reinforcement learning without changing Phase 6, retuning the frozen Phase 5.2 candidate, accessing the protected final holdout, or executing uncontrolled model research.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T21:45:35Z
head: 7c6b61ed20032f7064438be7e02652062fa423d7
branch: feat/experimental-model-research-foundation-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/configs/freqai-pytorch-research.example.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260720-experimental-model-research-foundation.md
proven:
  - develop was verified at 0a798cba4628b5fbe9d15cf26e5aaa514daf2fe4 before branch creation and no open pull requests were present.
  - Phase 6 remains a LightGBMRegressor versus XGBoostRegressor comparison with its existing predeclared selection policy.
  - Current FreqAI provides PyTorchMLPRegressor and custom FreqAI model loading through freqaimodel_path without core changes.
  - Current FreqAI reinforcement learning uses Gymnasium plus stable_baselines3 or sb3_contrib and supports custom model/environment classes.
  - The repository declares torch, gymnasium, stable-baselines3, and sb3-contrib in the freqai_rl optional dependency profile.
  - The central generic manifest loader rejects timerange or download_timerange overlap with protected final holdout 20260801-20260930.
  - Both research manifests stop at 20260630 and use distinct configs, FreqAI identifiers, and artifact roots.
  - PyTorch research uses a seeded small MLP and the frozen candidate thresholds entry 0.006 and exit -0.009 as constants.
  - RL research uses a custom long-only three-action environment and a reward contract based only on current environment state.
  - No training, backtesting, protected-final-holdout access, Phase 6 result mutation, promotion, or profitability claim has been performed.
derived:
  - One shared bounded foundation task is sufficient to establish two isolated subtracks without creating competing active governance tasks.
  - Single-training 90-day training plus 122-day prediction geometry prevents periodic retraining from learning from May-June consumed historical OOS before it is scored.
  - Generic March-June run-summary metrics are insufficient OOS evidence; a strict May-June experimental result extractor is required before model-performance conclusions.
unknown:
  - Runtime import and minimal training behavior with the heavy freqai_rl dependency profile have not been smoke-tested in this work package.
  - No real PyTorch or RL OOS trading metrics have been collected.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Upstream core changes are required for custom PyTorch or RL integration.
  - PyTorch or RL must be added as a candidate to the current Phase 6 comparison.
changed_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/configs/freqai-pytorch-research.example.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260720-experimental-model-research-foundation.md
validation:
  - command: GitHub Actions CI
    result: NOT_RUN
    evidence: Pull request has not been opened yet.
blockers: []
next_action: Open the implementation pull request against develop and use required GitHub Actions checks to validate compile, targeted tests, Ruff, formatting, codespell, and repository CI before merge.
```
