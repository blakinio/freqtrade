---
task_id: FTAI-20260720-experimental-model-research-foundation
status: ready
branch: feat/experimental-model-research-foundation-v1
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: "52"
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
updated_at: 2026-07-20T22:13:54Z
head: a881a8020a7da2894558340071f3c3c7044f7217
branch: develop
pr: 52
status: ready
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
  - Implementation PR 52 was squash-merged to develop as a881a8020a7da2894558340071f3c3c7044f7217 after all required checks passed.
  - Phase 6 advanced independently through PRs 51 and 53 while this task was active; this foundation does not modify its candidates, selection policy, comparison result, or final result assembler.
  - Current FreqAI provides PyTorchMLPRegressor and custom FreqAI model loading through freqaimodel_path without upstream core changes.
  - Current FreqAI reinforcement learning uses Gymnasium plus stable_baselines3 or sb3_contrib and supports custom model and environment classes.
  - The repository declares torch, gymnasium, stable-baselines3, and sb3-contrib in the freqai_rl optional dependency profile.
  - The protected final holdout remains 20260801-20260930 and both research manifests stop at 20260630.
  - PyTorch research has a distinct manifest, config, FreqAI identifier, artifact root, seed 42, and frozen thresholds entry 0.006 and exit -0.009.
  - RL research has a distinct manifest, config, FreqAI identifier, artifact root, PPO backend, long-only three-action space, and pre-transition decision-tick reward timing.
  - Both new trading configs keep dry_run true, and no training, backtesting, protected-holdout access, model promotion, or profitability claim was performed.
derived:
  - One shared bounded foundation task is sufficient to establish two isolated subtracks without creating competing active governance tasks.
  - Single-training 90-day training plus 122-day prediction geometry prevents periodic retraining from learning from May-June consumed historical OOS before it is scored.
  - Generic March-June run-summary metrics are insufficient OOS evidence; strict fully-contained May-June trade extraction is required before model-performance conclusions.
unknown:
  - Heavy freqai_rl runtime import and minimal real training behavior were not smoke-tested in this foundation task.
  - No real PyTorch or RL OOS trading metrics have been collected.
conflicts: []
first_failure:
  marker: AI Platform CI Ruff
  evidence: Initial PR runs exposed Ruff import-order, formatting, complexity, and test-regex issues; all were corrected and final AI Platform CI run 29782155984 passed.
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
  - command: AI Platform CI run 29782155984
    result: PASS
    evidence: Compile, targeted AI Platform tests, Ruff, Ruff format, codespell, and JSON validation completed successfully on implementation head 2ca0b0acef9588f80f810e84cdfdd0f0cb5e733e.
  - command: Freqtrade CI run 29782156015
    result: PASS
    evidence: Pre-commit, documentation, core test matrix, coverage, smoke tests, Ruff, formatting, and mypy gates completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29782156365
    result: PASS
    evidence: Security analysis completed successfully on implementation head 2ca0b0acef9588f80f810e84cdfdd0f0cb5e733e.
  - command: PR 52 mergeability and review-thread check
    result: PASS
    evidence: PR was mergeable and had no inline review threads before squash merge.
blockers: []
next_action: Add a strict historical-OOS result extractor for experimental manifests that scores only fully contained trades in 20260501-20260630 before any PyTorch or RL model-performance execution or conclusion.
```
