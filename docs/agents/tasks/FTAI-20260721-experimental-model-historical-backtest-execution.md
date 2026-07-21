---
task_id: FTAI-20260721-experimental-model-historical-backtest-execution
status: implementing
branch: research/experimental-model-historical-backtest-execution-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - tests/ai_platform/test_experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
search_first:
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - .github/workflows/ai-platform-phase6-model-comparison.yml
---

# Experimental Model Historical Backtest Execution v1

## Goal

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence with the existing extractor, and persist immutable execution artifacts without retuning, promotion, profitability claims, Phase 6 modification, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T12:30:00Z
head: 8b07721004addae4b5cf73d6a0c6d8ff429a796b
branch: research/experimental-model-historical-backtest-execution-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - tests/ai_platform/test_experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
proven:
  - Historical execution preflight PR #73 was squash-merged as 262cebef33c8e06d8c9379f1603be93552f445fe and its durable closure was subsequently merged by parallel PR #82.
  - Bounded execution task declaration PR #84 was squash-merged as 0ce4be07aad84e18feeb2740d544b63626aee6d8; develop was identical immediately afterward.
  - Canonical tracks remain exactly pytorch-research-v1 with SeededPyTorchMLPRegressor/AiFrozenCandidateStrategy and rl-research-v1 with LongOnlyReinforcementLearner/AiLongOnlyRLResearchStrategy.
  - Both manifests remain frozen at execution timerange 20260301-20260701, download timerange 20250801-20260701, Kraken BTC/USDT and ETH/USDT, 15m/1h/4h, and fee 0.002.
  - Strict historical-OOS extraction remains fully-contained closed trades inside 20260501-20260630 using ai_platform.scripts.experimental_model_oos_result_extractor.
  - Frozen thresholds 0.006/-0.009, protected final holdout isolation, and Phase 6 non-membership remain unchanged.
  - The originally declared required-read docs/ai_platform/EXPERIMENTAL_MODEL_STRICT_OOS_EXTRACTION.md does not exist on develop; immutable OOS semantics are instead present in EXPERIMENTAL_MODEL_RESEARCH.md, oos-extraction-contract-v1.json, and the extractor implementation.
  - The infrastructure contract pins exactly two tracks, one execution per track, frozen temporal/data assumptions, strict extraction, no cross-track selection, and no promotion/live/profitability/superiority authorization.
  - The canonical request validator binds SHA-256 provenance for the execution contract and each track's manifest, config, strategy implementation, and FreqAI model implementation.
  - The workflow triggers only when a same-repository pull request is opened against develop with the canonical request path and validates that the PR adds exactly that one file before runtime or market-data access.
  - The infrastructure workflow itself has no workflow_dispatch trigger and therefore cannot execute a real backtest merely by being merged.
  - Market-data preparation is pair-specific and fail-closed: exact v2 cache reuse is preferred, allowed historical seeds may be completed only through 20260701, and each pair is verified before a verified cache is saved.
  - Each backtest matrix job restores both exact verified pair caches with cache-miss failure enabled, re-verifies combined coverage, runs one canonical backtesting command, performs strict OOS extraction, and uploads independent evidence without a selection stage.
derived:
  - A separate exact-one-file trigger PR is the safest reusable boundary because infrastructure review and real model execution cannot occur in the same merge event.
  - Separate PyTorch and RL matrix jobs allow an isolated failed-track rerun without deliberately rerunning a successful other track; no winner-selection semantics are introduced.
  - If exact v2 caches are unavailable in the trigger PR cache scope, pair preparation must complete and verify the historical seed before any backtest job can start.
  - Schema-valid zero-trade strict OOS output should remain evidence rather than being converted into an implicit rejection or winner rule not prospectively declared.
unknown:
  - Whether the new workflow and request validator pass repository CI, pre-commit, and zizmor unchanged.
  - Whether exact verified pair caches are directly visible to a future trigger PR or must be rebuilt from allowed historical seeds in that PR scope.
  - Whether both real canonical backtests complete within the 360-minute per-track bound.
  - Whether strict OOS extractions contain included trades; zero included trades remain a valid observable outcome rather than a selection rule.
conflicts: []
first_failure:
  marker: stale-required-read-route
  evidence: The task declaration referenced EXPERIMENTAL_MODEL_STRICT_OOS_EXTRACTION.md, which is absent on develop; existing immutable OOS contract and extractor sources were used instead.
rejected_hypotheses:
  - Merge workflow infrastructure and execute real backtests in the same pull request.
  - Add a workflow_dispatch execution path that bypasses the exact-one-file trigger request boundary.
  - Retune thresholds, model parameters, features, reward design, or selection rules using consumed historical OOS.
  - Access the protected final holdout during historical execution.
  - Add PyTorch or RL retroactively to completed Phase 6 or introduce a cross-track winner-selection policy.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - tests/ai_platform/test_experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
validation:
  - command: infrastructure repository CI
    result: NOT_RUN
    evidence: Workflow infrastructure branch has not yet been opened as a pull request.
  - command: real PyTorch/RL historical execution
    result: NOT_RUN
    evidence: Canonical run-request file is intentionally absent from this infrastructure branch.
blockers: []
next_action: Open the workflow-infrastructure pull request, require AI Platform CI, Freqtrade CI, pre-commit/checkpoint validation, and zizmor to pass, fix only concrete failures, and squash-merge the infrastructure before creating any canonical one-shot trigger request.
```
