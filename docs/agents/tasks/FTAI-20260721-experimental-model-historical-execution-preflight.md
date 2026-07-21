---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: validating
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
updated_at: 2026-07-21T11:00:00Z
head: 0e6414f4489713181b9083e9847244fbe2d0f536
branch: feat/experimental-model-historical-execution-preflight-v2
pr: "#73"
status: validating
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
  - Freqtrade CI pre-commit checks pass after the Mypy fix.
  - Workflow concurrency now uses cancel-in-progress=false so validation commits do not cancel long pair downloads.
  - Final pair-specific preflight jobs have a 240-minute timeout; existing earlier 120-minute jobs may finish first and seed verified pair caches.
  - AI Platform CI run 29823122085, zizmor run 29823122066, and Experimental Model Runtime Smoke run 29823122115 completed successfully on implementation head 0e6414f4489713181b9083e9847244fbe2d0f536.
  - Protected final holdout 20260801-20260930 remains unused and forbidden; frozen thresholds 0.006/-0.009 and Phase 6 isolation remain unchanged.
derived:
  - Results from PR #66's stale 20260630-stop download cannot certify full June coverage and remain rejected as evidence.
  - Pair-specific verified caches can later be restored into one execution runner without changing model or scoring contracts.
unknown:
  - Whether both boundary-correct pair-specific Kraken downloads cover all required timeframes through the final June 30 candles.
  - Whether the full Freqtrade CI matrix completes successfully after the already-green pre-commit job.
conflicts: []
first_failure:
  marker: freqtrade-exclusive-stop-boundary
  evidence: Canonical manifests used stop token 20260630, but TimeRange parses that as 2026-06-30T00:00:00Z while strict OOS requires end_exclusive 2026-07-01T00:00:00Z.
rejected_hypotheses:
  - Treat PR #66's 20260630-stop download as valid full-June historical coverage.
  - Change the semantic historical OOS label or access the protected 20260801-20260930 final holdout.
  - Run a real PyTorch or RL backtest before the corrected preflight is green.
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
  - command: AI Platform CI run 29823122085
    result: PASS
    evidence: Boundary contract tests and AI Platform quality gates completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29823122066
    result: PASS
    evidence: Workflow security analysis completed successfully.
  - command: Experimental Model Runtime Smoke run 29823122115
    result: PASS
    evidence: Canonical PyTorch reproducibility and RL environment/PPO runtime paths remained green with corrected manifests.
  - command: Freqtrade CI run 29823122048
    result: NOT_RUN
    evidence: Pre-commit checks passed after the Mypy fix; the remaining repository matrix is still running.
  - command: Experimental Model Historical Execution Preflight run 29821500846
    result: NOT_RUN
    evidence: Guarded contract/resolver job passed; BTC/USDT and ETH/USDT boundary-correct Kraken downloads are still running before coverage verification and cache save.
blockers: []
next_action: Let the active pair-specific Kraken jobs finish and verify corrected coverage, require the full Freqtrade CI matrix to pass, then replay PR #73 onto the latest develop using the verified pair caches for one final cached preflight before merge.
```
