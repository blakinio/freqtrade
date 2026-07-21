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

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence with the existing extractor, and preserve immutable execution artifacts without retuning, promotion, profitability claims, Phase 6 modification, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T12:15:00Z
head: 01e52b43784186f012ded3840e59dee8951c1a4e
branch: develop
pr: none
status: investigating
context_routes:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
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
  - Boundary-correct experimental historical-execution preflight implementation PR #73 was squash-merged into develop as 262cebef33c8e06d8c9379f1603be93552f445fe after all required final-head gates passed.
  - Durable preflight checkpoint closure PR #82 was squash-merged into develop as 01e52b43784186f012ded3840e59dee8951c1a4e with status=done and blockers empty.
  - Canonical PyTorch track is pytorch-research-v1 using SeededPyTorchMLPRegressor with AiFrozenCandidateStrategy.
  - Canonical RL track is rl-research-v1 using LongOnlyReinforcementLearner with AiLongOnlyRLResearchStrategy.
  - Both canonical manifests use Freqtrade execution timerange 20260301-20260701 and download timerange 20250801-20260701, encoding semantic windows ending 20260630 with an exclusive July 1 stop.
  - Strict historical-OOS scoring remains 20260501-20260630 and must use ai_platform.scripts.experimental_model_oos_result_extractor rather than generic full-window summaries.
  - Kraken BTC/USDT and ETH/USDT data were independently verified for 15m, 1h, and 4h through the required June 30 boundary; the execution path must independently verify restored data before use and fail closed on drift.
  - Frozen entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009 must remain frozen in this task, and protected final holdout 20260801-20260930 remains unused and forbidden.
  - PyTorch and RL remain outside Phase 6 membership; open Phase 6 boundary-correction work such as PR #81 is independent and may not be consumed, altered, selected against, or used to change this experimental execution contract.
  - This work package is research-only and authorizes no promotion, live trading, profitability claim, cross-track winner selection, or superiority conclusion.
derived:
  - A dedicated one-shot request boundary is required so workflow infrastructure can merge without executing real model backtests.
  - Historical execution must fail closed if canonical manifest identity, model/strategy resolution, temporal boundaries, frozen thresholds, protected-holdout isolation, pair/timeframe coverage, or request identity drifts.
  - PyTorch and RL outputs are independent research evidence; this task must not retrospectively invent a cross-track winner-selection policy or compare them to Phase 6 for promotion.
  - Successful historical execution alone cannot promote either track and does not authorize final-holdout evaluation; model-performance conclusions require strict historical-OOS extraction first.
unknown:
  - Whether both canonical real backtests complete successfully within bounded GitHub Actions resources.
  - Whether each strict historical-OOS extraction is non-empty and structurally valid after real execution.
  - Whether additional execution-only provenance binding is required before durable repository evidence is accepted.
conflicts: []
first_failure:
  marker: none
  evidence: Real canonical experimental backtests have not yet been authorized or executed by this work package.
rejected_hypotheses:
  - Run PyTorch or RL directly from the completed preflight work package without a separate one-shot execution boundary.
  - Retune thresholds, model parameters, features, reward design, or selection rules using consumed historical OOS 20260501-20260630.
  - Access protected final holdout 20260801-20260930 during historical execution.
  - Treat a successful backtest or favorable historical metric as promotion, profitability, or superiority evidence.
  - Add PyTorch or RL to Phase 6 or use Phase 6 rerun/evidence work to alter this experimental execution task.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
validation:
  - command: Experimental historical-execution preflight final merge-ref gates
    result: PASS
    evidence: AI Platform CI 29827777608, zizmor 29827777589, Experimental Model Runtime Smoke 29827777615, Historical Execution Preflight 29827777584, and full Freqtrade CI 29827777612 succeeded before PR #73 merged.
  - command: durable preflight checkpoint closure PR #82
    result: PASS
    evidence: Freqtrade CI 29829065208 and zizmor 29829065049 succeeded before merge; checkpoint/contract validation in Historical Execution Preflight run 29829064910 also passed before the docs-only closure merge.
  - command: real PyTorch/RL historical execution
    result: NOT_RUN
    evidence: This task declaration intentionally precedes any real canonical backtest.
blockers: []
next_action: On dedicated branch research/experimental-model-historical-backtest-execution-v1, implement a fail-closed one-shot execution workflow and canonical request contract that can run exactly one PyTorch and one RL historical backtest from the frozen manifests, restore and independently verify only boundary-correct historical data, extract strict historical-OOS evidence, and reject protected-final-holdout access; merge the workflow-infrastructure PR before creating any trigger request that executes the real backtests.
```
