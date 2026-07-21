---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: implementing
branch: feat/experimental-model-historical-execution-preflight-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#66"
owned_paths:
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
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
---

# Experimental Model Historical Execution Preflight v1

## Goal

Verify historical market-data availability, execution resources, custom model/strategy resolution, and the existing FreqAI command path for both canonical experimental tracks before producing any PyTorch or RL backtest archive.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T09:35:00Z
head: 71e8ad122cefa9dfb23a7d7f53a512fc57b5f528
branch: feat/experimental-model-historical-execution-preflight-v1
pr: "#66"
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
owned_paths:
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
proven:
  - The original PR #66 implementation head 625d8c14f1bacdd573d2a22bb42bbb2ddd5d2f2e passed AI Platform CI, Freqtrade CI, and zizmor before develop advanced.
  - The original dedicated preflight run 29815837243 passed checkpoint validation, dependency installation, frozen contract validation, and custom model/strategy resolution before entering the Kraken historical-data download step.
  - Canonical PyTorch and RL manifests share Kraken, BTC/USDT and ETH/USDT, 15m/1h/4h, download range 20250801-20260630, and prediction range 20260301-20260630.
  - Existing ai_platform.scripts.run_experiment builds guarded download-data and backtesting command paths and validates protected-final-holdout isolation before execution.
  - The preflight workflow downloads or restores only Kraken history ending 20260630, verifies pair/timeframe coverage, and does not execute a backtest or OOS extractor.
  - Develop advanced to ccf98eab3fa90d867558cf2511111415e0bd3e51 through independent Phase 6 and experimental runtime-hardening work without modifying any PR #66 owned path.
  - PR #66 was six commits behind develop, so its exact five-file implementation is being replayed onto current develop before final validation.
  - The workflow concurrency contract uses cancel-in-progress false, allowing the original data download to finish and populate the dedicated cache before the replayed final run starts.
derived:
  - One shared experimental Kraken data cache is sufficient for both canonical research tracks because their data geometry is identical.
  - Replaying onto current develop should preserve the preflight semantics while ensuring final CI validates against the latest Phase 6 and experimental runtime foundation.
unknown:
  - Whether Kraken history for every required pair/timeframe fully covers the declared 20250801-20260630 boundary in the GitHub Actions runtime.
  - Whether the original long-running download completes and saves the dedicated cache before the replayed final run reaches cache restore.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation failure has been observed; the only unresolved runtime step is the still-running bounded Kraken historical-data download in run 29815837243.
rejected_hypotheses:
  - Produce a PyTorch or RL backtest archive before proving data availability and execution prerequisites.
  - Use the protected 20260801-20260930 final holdout for preflight or cache validation.
  - Cancel the original download while a replayed current-develop validation can safely queue behind it and reuse its cache.
changed_paths:
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
validation:
  - command: AI Platform CI on original PR #66 head
    result: PASS
    evidence: Run 29815837486 completed successfully.
  - command: Freqtrade CI on original PR #66 head
    result: PASS
    evidence: Run 29815837196 completed successfully.
  - command: zizmor on original PR #66 head
    result: PASS
    evidence: Run 29815837570 completed successfully.
  - command: Experimental Model Historical Execution Preflight run 29815837243
    result: NOT_RUN
    evidence: Contract and resolver gates passed; Kraken historical-data download remains in progress and final coverage verification has not run yet.
blockers: []
next_action: Force-update PR #66 head to the replayed implementation based on develop ccf98eab3fa90d867558cf2511111415e0bd3e51, let the original non-cancelled preflight finish and save its cache, then require the replayed final preflight plus AI Platform CI, Freqtrade CI, and zizmor to pass before merge.
```
