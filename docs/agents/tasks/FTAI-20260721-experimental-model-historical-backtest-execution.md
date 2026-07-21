---
task_id: FTAI-20260721-experimental-model-historical-backtest-execution
status: investigating
branch: research/experimental-model-historical-backtest-execution-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - .github/workflows/experimental-model-historical-backtest-execution.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_STRICT_OOS_EXTRACTION.md
search_first:
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
---

# Experimental Model Historical Backtest Execution v1

## Goal

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence with the existing extractor, and persist immutable execution artifacts without retuning, promotion, profitability claims, Phase 6 modification, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T12:10:49Z
head: 262cebef33c8e06d8c9379f1603be93552f445fe
branch: develop
pr: none
status: investigating
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - .github/workflows/experimental-model-historical-backtest-execution.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
proven:
  - Historical execution preflight PR #73 was squash-merged into develop as 262cebef33c8e06d8c9379f1603be93552f445fe after all final merge-ref gates passed.
  - Canonical PyTorch track is pytorch-research-v1 using SeededPyTorchMLPRegressor with AiFrozenCandidateStrategy.
  - Canonical RL track is rl-research-v1 using LongOnlyReinforcementLearner with AiLongOnlyRLResearchStrategy.
  - Both canonical manifests use Freqtrade execution timerange 20260301-20260701 and download timerange 20250801-20260701, encoding semantic windows ending 20260630 with an exclusive July 1 stop.
  - Strict historical-OOS scoring remains 20260501-20260630 and must use ai_platform.scripts.experimental_model_oos_result_extractor rather than generic full-window summaries.
  - Kraken BTC/USDT and ETH/USDT data are independently verified for 15m, 1h, and 4h through the required June 30 boundary and stored in exact boundary-correct v2 pair caches.
  - Frozen entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009 must remain frozen in this task.
  - Protected final holdout 20260801-20260930 remains unused and forbidden.
  - PyTorch and RL remain outside Phase 6 membership and may not change completed Phase 6 candidates, policy, evidence, or result.
  - This work package is research-only and authorizes no promotion, live trading, profitability claim, or superiority conclusion.
derived:
  - A dedicated one-shot request boundary is preferable to executing real backtests merely by merging workflow infrastructure.
  - Exact v2 pair caches may seed the execution runner, but execution must fail closed if required pair/timeframe coverage or canonical manifest identity drifts.
  - PyTorch and RL outputs are independent research evidence; this task must not retrospectively invent a cross-track winner-selection policy.
  - Successful historical execution alone cannot promote either track and does not authorize final-holdout evaluation.
unknown:
  - Whether both canonical real backtests complete successfully within bounded GitHub Actions resources.
  - Whether each strict historical-OOS extraction is non-empty and structurally valid after real execution.
  - Whether additional execution-only provenance binding is required before durable repository evidence is accepted.
conflicts: []
first_failure:
  marker: none
  evidence: Real canonical experimental backtests have not yet been authorized or executed by this work package.
rejected_hypotheses:
  - Run PyTorch or RL directly from the completed preflight work package.
  - Retune thresholds, model parameters, features, reward design, or selection rules using consumed historical OOS 20260501-20260630.
  - Access protected final holdout 20260801-20260930 during historical execution.
  - Treat a successful backtest or favorable historical metric as promotion, profitability, or superiority evidence.
  - Add PyTorch or RL retroactively to the completed Phase 6 LightGBM-versus-XGBoost comparison.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
validation:
  - command: Historical execution preflight PR #73 final merge-ref gates
    result: PASS
    evidence: AI Platform CI 29827777608, zizmor 29827777589, Experimental Model Runtime Smoke 29827777615, Historical Execution Preflight 29827777584, and Freqtrade CI 29827777612 all succeeded before merge.
  - command: real PyTorch/RL historical execution
    result: NOT_RUN
    evidence: This task declaration intentionally precedes any real canonical backtest.
blockers: []
next_action: On dedicated branch research/experimental-model-historical-backtest-execution-v1, implement a fail-closed one-shot execution workflow and canonical request contract that can run exactly one PyTorch and one RL historical backtest from the frozen manifests, restore only verified boundary-correct data, extract strict OOS evidence, and reject final-holdout access; open and merge the workflow-infrastructure PR before creating any trigger request that executes the real backtests.
```
