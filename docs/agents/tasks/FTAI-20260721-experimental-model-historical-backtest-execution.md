---
task_id: FTAI-20260721-experimental-model-historical-backtest-execution
status: active
branch: docs/experimental-model-checkpoint-compactness-fix
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "pending checkpoint fix PR"
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
  - checkpoint compactness fix PR merged state
  - failed one-shot trigger PR #92 and fresh replacement trigger
  - open PRs overlapping experimental model historical execution
---

# Experimental Model Historical Backtest Execution v1

## Goal

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence with the existing extractor, and persist immutable execution artifacts without retuning, promotion, profitability claims, Phase 6 modification, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T15:30:00Z
head: 891ee62aa134b98bec9449155db9bd0b245e547b
branch: docs/experimental-model-checkpoint-compactness-fix
pr: pending checkpoint fix PR
status: ready
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
  - Historical execution preflight PR #73 was squash-merged as 262cebef33c8e06d8c9379f1603be93552f445fe and its durable closure was subsequently merged by PR #82.
  - Bounded execution task declaration PR #84 was squash-merged as 0ce4be07aad84e18feeb2740d544b63626aee6d8.
  - Phase 6 corrected evidence PR #91 was squash-merged as b6facf2ec47aadbd025dda31e482004bdac9f3ec with authoritative selected_model null; PyTorch/RL remain outside Phase 6 and cannot alter that result.
  - Canonical tracks remain exactly pytorch-research-v1 with SeededPyTorchMLPRegressor/AiFrozenCandidateStrategy and rl-research-v1 with LongOnlyReinforcementLearner/AiLongOnlyRLResearchStrategy.
  - Both manifests remain frozen at execution timerange 20260301-20260701, download timerange 20250801-20260701, Kraken BTC/USDT and ETH/USDT, 15m/1h/4h, and fee 0.002.
  - Strict historical-OOS extraction remains fully-contained closed trades inside 20260501-20260630 using ai_platform.scripts.experimental_model_oos_result_extractor.
  - Frozen thresholds 0.006/-0.009, protected final holdout 20260801-20260930 isolation, and Phase 6 non-membership remain unchanged.
  - The execution contract pins exactly two tracks, one execution per track, frozen temporal/data assumptions, strict extraction, no cross-track selection, and no promotion/live/profitability/superiority authorization.
  - The canonical request validator binds SHA-256 provenance for the execution contract and each track's manifest, config, strategy implementation, and FreqAI model implementation.
  - The workflow accepts only a same-repository pull request opened against develop whose diff adds exactly the canonical request file before runtime or market-data access.
  - The infrastructure workflow has no workflow_dispatch trigger and therefore cannot execute a real backtest merely by being merged.
  - Market-data preparation is pair-specific and fail-closed: exact v2 cache reuse is preferred, allowed historical seeds may be completed only through 20260701, and each pair is verified before a verified cache is saved.
  - Each backtest matrix job restores both exact verified pair caches with cache-miss failure enabled, re-verifies combined coverage, runs one canonical backtesting command, performs strict OOS extraction, and uploads independent evidence without a selection stage.
  - Infrastructure PR #86 was squash-merged as 891ee62aa134b98bec9449155db9bd0b245e547b after AI Platform CI, zizmor, full Freqtrade CI, pre-commit, documentation and core matrix gates passed; temporary diagnostic PR #90 and diagnostic/autofix workflows were removed without merge.
  - First trigger PR #92 passed exact-one-file scope validation but stopped at checkpoint validation before Python setup, market-data access, or model execution because the merged checkpoint had 17 proven facts while the governance limit is 16; PR #92 was closed without merge.
derived:
  - A fresh exact-one-file trigger PR is required after this compactness-only checkpoint fix merges because the execution workflow intentionally listens only to pull_request opened.
  - Separate PyTorch and RL matrix jobs preserve independent evidence and do not introduce winner-selection semantics.
  - If exact v2 caches are unavailable in the fresh trigger PR cache scope, pair preparation must complete and verify the historical seed before any backtest job can start.
  - Schema-valid zero-trade strict OOS output remains evidence rather than an implicit rejection or winner rule.
unknown:
  - Whether exact verified pair caches are directly visible to the fresh trigger PR or must be rebuilt from allowed historical seeds in that PR scope.
  - Whether both real canonical backtests complete within the 360-minute per-track bound.
  - Whether strict OOS extractions contain included trades; zero included trades remains a valid observable outcome rather than a selection rule.
conflicts: []
first_failure:
  marker: checkpoint-compactness-overflow
  evidence: Trigger PR #92 failed only at tools/agents/checkpoint.py --require-checkpoint because the checkpoint contained 17 proven facts while GOVERNANCE_CONTRACT.json limits proven to 16; all runtime and data-access steps were skipped.
rejected_hypotheses:
  - Merge workflow infrastructure and execute real backtests in the same pull request.
  - Reopen or rerun PR #92 after changing develop; the one-shot workflow is intentionally bound to the opened event and exact trigger head.
  - Add a workflow_dispatch execution path that bypasses the exact-one-file trigger request boundary.
  - Retune thresholds, model parameters, features, reward design, or selection rules using consumed historical OOS.
  - Access the protected final holdout during historical execution.
  - Add PyTorch or RL retroactively to completed Phase 6 or introduce a cross-track winner-selection policy.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
validation:
  - command: PR #86 exact-head repository gates before merge
    result: PASS
    evidence: AI Platform CI 29842774617, zizmor 29842773974, and Freqtrade CI 29842775156 completed successfully; full pre-commit, documentation and core matrix jobs passed.
  - command: PR #92 exact trigger scope validation
    result: PASS
    evidence: Validate trigger PR scope before runtime or data access completed successfully on one-file trigger head 5f755687d43ae046346726e93063c12d60e8ec53.
  - command: PR #92 checkpoint validation
    result: FAIL
    evidence: Checkpoint compactness overflow stopped execution before runtime or market-data access; no PyTorch or RL backtest ran.
  - command: real PyTorch/RL historical execution
    result: NOT_RUN
    evidence: PR #92 failed closed before setup/runtime and was closed without merge.
blockers: []
next_action: Merge this compactness-only checkpoint fix after repository gates pass, then create a fresh branch from current develop, generate the canonical request from merged hashes, open a new exact-one-file trigger PR, let the one-shot workflow execute each track once, close the trigger without merge, and preserve PyTorch and RL evidence independently without cross-track selection.
```
