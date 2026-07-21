---
task_id: FTAI-20260721-experimental-model-historical-backtest-execution
status: active
branch: research/experimental-model-historical-backtest-execution-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#86"
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
  - PR #86 exact-head gates and merged state
  - current develop after Phase 6 corrected evidence merge b6facf2ec47aadbd025dda31e482004bdac9f3ec
  - open PRs overlapping experimental model historical execution
---

# Experimental Model Historical Backtest Execution v1

## Goal

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence with the existing extractor, and persist immutable execution artifacts without retuning, promotion, profitability claims, Phase 6 modification, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T15:10:00Z
head: 035748caba4416d2e222ceef01c5d2f704a56840
branch: research/experimental-model-historical-backtest-execution-v1
pr: "#86"
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
  - Phase 6 boundary-corrected durable evidence PR #91 was squash-merged as b6facf2ec47aadbd025dda31e482004bdac9f3ec with authoritative selected_model null; PyTorch/RL remain outside Phase 6 and cannot alter that result.
  - Canonical tracks remain exactly pytorch-research-v1 with SeededPyTorchMLPRegressor/AiFrozenCandidateStrategy and rl-research-v1 with LongOnlyReinforcementLearner/AiLongOnlyRLResearchStrategy.
  - Both manifests remain frozen at execution timerange 20260301-20260701, download timerange 20250801-20260701, Kraken BTC/USDT and ETH/USDT, 15m/1h/4h, and fee 0.002.
  - Strict historical-OOS extraction remains fully-contained closed trades inside 20260501-20260630 using ai_platform.scripts.experimental_model_oos_result_extractor.
  - Frozen thresholds 0.006/-0.009, protected final holdout 20260801-20260930 isolation, and Phase 6 non-membership remain unchanged.
  - The infrastructure contract pins exactly two tracks, one execution per track, frozen temporal/data assumptions, strict extraction, no cross-track selection, and no promotion/live/profitability/superiority authorization.
  - The canonical request validator binds SHA-256 provenance for the execution contract and each track's manifest, config, strategy implementation, and FreqAI model implementation.
  - The workflow triggers only when a same-repository pull request is opened against develop with the canonical request path and validates that the PR adds exactly that one file before runtime or market-data access.
  - The infrastructure workflow itself has no workflow_dispatch trigger and therefore cannot execute a real backtest merely by being merged.
  - Market-data preparation is pair-specific and fail-closed: exact v2 cache reuse is preferred, allowed historical seeds may be completed only through 20260701, and each pair is verified before a verified cache is saved.
  - Each backtest matrix job restores both exact verified pair caches with cache-miss failure enabled, re-verifies combined coverage, runs one canonical backtesting command, performs strict OOS extraction, and uploads independent evidence without a selection stage.
  - Temporary diagnostic PR #90 was closed without merge after exact full pre-commit reproduction isolated the only failing hook to zizmor.
  - The zizmor findings were fixed by removing temporary diagnostic/autofix workflows and passing execute-step outputs through environment variables before shell use; the final PR #86 diff returned to exactly six intended infrastructure files.
  - On implementation head 035748caba4416d2e222ceef01c5d2f704a56840, AI Platform CI run 29842371726 and zizmor run 29842370845 completed successfully; Pre-commit Types update 29842370874 was skipped.
  - Freqtrade CI run 29842370848 pre-commit job 88674402762 and documentation job 88674510984 completed successfully, confirming the original pre-commit blocker is resolved; the remaining core matrix was still executing when this checkpoint metadata was written.
derived:
  - A separate exact-one-file trigger PR remains the safest reusable boundary because infrastructure review and real model execution cannot occur in the same merge event.
  - Separate PyTorch and RL matrix jobs preserve independent evidence and do not introduce winner-selection semantics.
  - If exact v2 caches are unavailable in the trigger PR cache scope, pair preparation must complete and verify the historical seed before any backtest job can start.
  - Schema-valid zero-trade strict OOS output remains evidence rather than an implicit rejection or winner rule.
unknown:
  - Whether exact verified pair caches are directly visible to the future trigger PR or must be rebuilt from allowed historical seeds in that PR scope.
  - Whether both real canonical backtests complete within the 360-minute per-track bound.
  - Whether strict OOS extractions contain included trades; zero included trades remains a valid observable outcome rather than a selection rule.
conflicts: []
first_failure:
  marker: resolved-precommit-zizmor-template-injection
  evidence: Diagnostic PR #90 established that schema, mypy, Ruff, Ruff format, standard hooks and codespell passed while zizmor alone failed. Direct shell interpolation of steps.execute outputs and a temporary autofix workflow were removed/fixed; current pre-commit job 88674402762 and zizmor run 29842370845 pass.
rejected_hypotheses:
  - Merge workflow infrastructure and execute real backtests in the same pull request.
  - Add a workflow_dispatch execution path that bypasses the exact-one-file trigger request boundary.
  - Retune thresholds, model parameters, features, reward design, or selection rules using consumed historical OOS.
  - Access the protected final holdout during historical execution.
  - Add PyTorch or RL retroactively to completed Phase 6 or introduce a cross-track winner-selection policy.
  - Keep temporary diagnostic or autofix workflows in the final infrastructure PR.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - tests/ai_platform/test_experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
validation:
  - command: AI Platform CI 29842371726 on 035748caba4416d2e222ceef01c5d2f704a56840
    result: PASS
    evidence: Focused AI Platform validation completed successfully.
  - command: zizmor 29842370845 on 035748caba4416d2e222ceef01c5d2f704a56840
    result: PASS
    evidence: Security analysis completed successfully after template-injection cleanup.
  - command: Freqtrade CI pre-commit job 88674402762
    result: PASS
    evidence: Full repository pre-commit hook execution completed successfully.
  - command: Freqtrade CI documentation job 88674510984
    result: PASS
    evidence: Documentation syntax and build completed successfully.
  - command: real PyTorch/RL historical execution
    result: NOT_RUN
    evidence: Canonical run-request file is intentionally absent from this infrastructure PR.
blockers: []
next_action: Wait for exact-head repository gates on the checkpoint metadata commit, squash-merge PR #86 after all required gates pass, then create a fresh separate pull request from current develop that adds exactly ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json with the canonical payload. Let that one-shot workflow execute each track once, close the trigger without merge after evidence collection, and preserve PyTorch and RL evidence independently without cross-track selection.
```
