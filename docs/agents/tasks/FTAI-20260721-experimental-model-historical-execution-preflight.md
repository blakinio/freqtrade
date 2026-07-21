---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: ready
branch: feat/experimental-model-historical-execution-preflight-v2
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#73"
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
search_first:
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - freqtrade/configuration/timerange.py
---

# Experimental Model Historical Execution Preflight v2

## Goal

Verify boundary-correct historical market-data availability, execution resources, custom model/strategy resolution, and the existing FreqAI command path for both canonical experimental tracks before producing any PyTorch or RL backtest archive.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T11:40:00Z
head: a3572689a6e3a3b808d95d886ae7e58e017418e5
branch: feat/experimental-model-historical-execution-preflight-v2
pr: "#73"
status: ready
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
proven:
  - Runtime-smoke-hardening checkpoint #70 keeps this historical-execution preflight as the canonical next action.
  - Closed PR #66 proved dependency installation, static execution contracts, and both custom resolvers but its 20260630 stop cannot certify full June coverage.
  - Freqtrade TimeRange parses an eight-digit stop token at 00:00 UTC on that date, so the corrected technical stop is 20260701 while semantic windows still end 20260630.
  - Strict experimental OOS scoring remains 20260501-20260630 with end_exclusive 2026-07-01T00:00:00Z.
  - backtest_period_days=122 matches March 1 through June 30 inclusive and therefore requires Freqtrade execution timerange 20260301-20260701.
  - PyTorch and RL manifests use 20260301-20260701 for execution and 20250801-20260701 for download without touching the protected final holdout.
  - PR #73 parallelizes Kraken trade-history acquisition per pair and verifies 15m, 1h, and 4h coverage independently for BTC/USDT and ETH/USDT.
  - PR #75 was closed without merge as superseded by the stronger parallel preflight in PR #73.
  - A deterministic pre-commit Mypy failure was isolated to variable-name reuse in experimental_model_historical_execution_preflight.py and fixed without changing runtime semantics.
  - Workflow concurrency uses cancel-in-progress=false and pair-specific jobs have a 240-minute timeout.
  - Exact boundary-correct v2 cache was restored on final preflight run 29823749323; the download step was skipped only because the exact v2 cache key hit, and independent coverage verification still executed for each pair.
  - BTC/USDT coverage evidence is ready for 15m, 1h, and 4h from 2025-08-01 through at least the required 2026-07-01 boundary; rows are 32021, 8010, and 2004 respectively.
  - ETH/USDT coverage evidence is ready for 15m, 1h, and 4h from 2025-08-01 through at least the required 2026-07-01 boundary; rows are 31985, 8011, and 2004 respectively.
  - Final preflight artifacts for BTC/USDT and ETH/USDT report status=ready, market_data_available=true, phase6_member=false, protected_final_holdout_used=false, retuning_allowed=false, promotion_allowed=false, and profitability_claim_allowed=false.
  - AI Platform CI run 29823749276, zizmor run 29823749275, Experimental Model Runtime Smoke run 29823749273, Freqtrade CI run 29823749339, and Experimental Model Historical Execution Preflight run 29823749323 all completed successfully on validated implementation head a3572689a6e3a3b808d95d886ae7e58e017418e5.
  - develop is merge-base 550766fc5e1fce065a0ddc7d8c3866f965e17393 and the branch is ahead with behind_by=0, so no replay/rebase is required before merge unless develop moves again.
  - Protected final holdout 20260801-20260930 remains unused and forbidden; frozen thresholds 0.006/-0.009 and Phase 6 isolation remain unchanged.
derived:
  - Results from PR #66's stale 20260630-stop download cannot certify full June historical coverage and remain rejected as evidence.
  - Verified pair-specific caches can be restored into a later bounded execution runner without changing model or scoring contracts.
  - The next bounded task may authorize canonical experimental backtest execution only after this preflight PR is merged; this PR itself authorizes no backtest.
unknown: []
conflicts: []
first_failure:
  marker: freqtrade-exclusive-stop-boundary
  evidence: Canonical manifests used stop token 20260630, but TimeRange parses that as 2026-06-30T00:00:00Z while strict OOS requires end_exclusive 2026-07-01T00:00:00Z.
rejected_hypotheses:
  - Treat PR #66's 20260630-stop download as valid full-June historical coverage.
  - Change the semantic historical OOS label or access the protected 20260801-20260930 final holdout.
  - Run a real PyTorch or RL backtest before the corrected preflight is green and merged.
  - Merge duplicate PR #75 instead of consolidating on the stronger parallel PR #73.
changed_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
validation:
  - command: AI Platform CI run 29823749276
    result: PASS
    evidence: Boundary contract tests and AI Platform quality gates completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29823749275
    result: PASS
    evidence: Workflow security analysis completed successfully.
  - command: Experimental Model Runtime Smoke run 29823749273
    result: PASS
    evidence: Canonical PyTorch reproducibility and RL environment/PPO runtime paths remained green with corrected manifests.
  - command: Freqtrade CI run 29823749339
    result: PASS
    evidence: Full repository CI completed successfully on the validated implementation head.
  - command: Experimental Model Historical Execution Preflight run 29823749323
    result: PASS
    evidence: Guarded contract/resolver validation and both BTC/USDT and ETH/USDT pair-specific coverage jobs completed successfully and uploaded durable evidence artifacts.
blockers: []
next_action: Require the metadata-only checkpoint head to pass standard gates and cached boundary-correct preflight, then squash-merge PR #73. After merge, close this task durably and open a separate bounded execution task before any real PyTorch or RL backtest.
```
