---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: implementing
branch: feat/experimental-model-historical-execution-preflight-v2
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
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
updated_at: 2026-07-21T10:00:00Z
head: 57a19ca45d53cd3062d13870812a88463be7a14c
branch: feat/experimental-model-historical-execution-preflight-v2
pr: none
status: implementing
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
  - Closed PR #66 proved dependency installation, static execution contracts, and both custom resolvers but was not merged.
  - Freqtrade TimeRange parses an eight-digit stop token at 00:00 UTC on that date, making the stop boundary exclusive for the intended daily window.
  - Strict experimental OOS scoring explicitly ends at 2026-07-01T00:00:00Z, while the semantic OOS label remains 20260501-20260630.
  - backtest_period_days=122 matches March 1 through June 30 inclusive and therefore requires Freqtrade execution timerange 20260301-20260701.
  - Canonical semantic labels remain unchanged; explicit freqtrade_prediction_timerange and freqtrade_download_timerange now encode exclusive July 1 stops.
  - PyTorch and RL manifests now use 20260301-20260701 for execution and 20250801-20260701 for download without touching the protected final holdout.
  - The replacement preflight parallelizes Kraken trade-history acquisition per pair because Freqtrade downloads trade-history pairs sequentially inside one process.
derived:
  - Results from PR #66's stale 20260630-stop download cannot certify full June coverage and are rejected as evidence even if the old workflow eventually completes.
  - Pair-specific verified caches can later be restored into one execution runner without changing model or scoring contracts.
unknown:
  - Whether both pair-specific Kraken downloads complete within the 120-minute job limits and cover 15m, 1h, and 4h through the final June 30 candles.
  - Whether the boundary-correct replacement passes all standard repository CI and security gates.
conflicts: []
first_failure:
  marker: freqtrade-exclusive-stop-boundary
  evidence: Canonical manifests used stop token 20260630, but TimeRange parses that as 2026-06-30T00:00:00Z while strict OOS requires end_exclusive 2026-07-01T00:00:00Z.
rejected_hypotheses:
  - Treat PR #66's 20260630-stop download as valid full-June historical coverage.
  - Change the semantic historical OOS label or access the protected 20260801-20260930 final holdout.
  - Run a real PyTorch or RL backtest before the corrected preflight is green.
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
  - command: GitHub Actions CI
    result: NOT_RUN
    evidence: Boundary-correct replacement pull request has not been opened yet.
blockers: []
next_action: Add boundary-correct preflight documentation, open the replacement pull request against current develop, and require both pair-specific Kraken coverage jobs plus AI Platform CI, Freqtrade CI, and zizmor to pass before merge.
```
