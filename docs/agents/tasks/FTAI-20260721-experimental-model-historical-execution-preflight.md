---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: done
branch: feat/experimental-model-historical-execution-preflight-v2
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#73 merged"
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
updated_at: 2026-07-21T12:10:00Z
head: 262cebef33c8e06d8c9379f1603be93552f445fe
branch: develop
pr: "#73 merged"
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
  - Runtime-smoke-hardening checkpoint #70 established this historical-execution preflight as the canonical prerequisite before any real experimental PyTorch or RL backtest.
  - Closed PR #66 proved dependency installation, static execution contracts, and both custom resolvers, but its 20260630 stop was rejected because it could not certify all of June 30.
  - Freqtrade TimeRange treats an eight-digit stop token as midnight at the start of that date, so semantic windows still end 20260630 while executable prediction and download timeranges end exclusively at 20260701.
  - Strict experimental historical-OOS scoring remains 20260501-20260630 with end_exclusive 2026-07-01T00:00:00Z; this preflight does not consume or score that OOS window.
  - PyTorch and RL manifests use execution timerange 20260301-20260701 and download timerange 20250801-20260701; backtest_period_days remains 122, frozen thresholds remain 0.006/-0.009, Phase 6 isolation remains intact, and protected final holdout 20260801-20260930 remains unused and forbidden.
  - PR #73 added a fail-closed historical-execution preflight that validates contracts and resolvers, parallelizes Kraken trade-history acquisition per pair, and verifies BTC/USDT and ETH/USDT independently at 15m, 1h, and 4h without executing a backtest.
  - Corrected preflight run 29821500846 completed full boundary-correct Kraken download, coverage verification, pair-specific cache save, and evidence upload successfully for both BTC/USDT and ETH/USDT.
  - Final preflight run 29827777584 restored the exact boundary-correct caches, skipped download on exact cache hits, independently re-ran coverage verification for both pairs, and completed successfully on final validated head 823b300e08b4c1611298fe268c0feccc37b9de4b.
  - BTC/USDT verified coverage rows are 32021 at 15m, 8010 at 1h, and 2004 at 4h from 2025-08-01 through the required exclusive 2026-07-01 boundary.
  - ETH/USDT verified coverage rows are 31985 at 15m, 8011 at 1h, and 2004 at 4h from 2025-08-01 through the required exclusive 2026-07-01 boundary.
  - Final preflight artifacts report status=ready, market_data_available=true, phase6_member=false, protected_final_holdout_used=false, retuning_allowed=false, promotion_allowed=false, and profitability_claim_allowed=false.
  - Before merge, final head 823b300e08b4c1611298fe268c0feccc37b9de4b had behind_by=0 against develop and a net diff limited to the twelve intended experimental-preflight files; no Phase 6 file was part of that net diff.
  - Final validation passed AI Platform CI run 29827777608, zizmor run 29827777589, Experimental Model Runtime Smoke run 29827777615, Experimental Model Historical Execution Preflight run 29827777584, and full Freqtrade CI run 29827777612; Pre-commit Types update was skipped rather than failed.
  - No real PyTorch or RL historical backtest archive was produced, no historical-OOS extractor was run on model results, and no model-performance, profitability, superiority, promotion, retuning, or live-trading conclusion was made.
  - PR #73 was merged into develop as 262cebef33c8e06d8c9379f1603be93552f445fe after all required final-head gates completed successfully.
  - With the preflight merged, any real canonical PyTorch or RL historical backtest now requires a new separately bounded execution task and must remain isolated from the protected final holdout and from performance conclusions until strict historical-OOS extraction.
derived:
  - Results from PR #66's stale 20260630-stop download remain invalid as evidence for full-June historical coverage.
  - Verified pair-specific caches may be restored by a later bounded execution runner without changing model, temporal, scoring, threshold, Phase 6, or holdout contracts.
  - This completed preflight authorizes no automatic backtest, OOS scoring, retuning, promotion, profitability claim, or live-trading change.
unknown: []
conflicts: []
first_failure:
  marker: freqtrade-exclusive-stop-boundary
  evidence: Canonical manifests originally used stop token 20260630, but TimeRange parses that as 2026-06-30T00:00:00Z while the strict historical-OOS contract requires end_exclusive 2026-07-01T00:00:00Z.
rejected_hypotheses:
  - Treat PR #66's 20260630-stop download as valid full-June historical coverage.
  - Change the semantic historical-OOS label or access the protected 20260801-20260930 final holdout.
  - Run a real PyTorch or RL backtest before the corrected preflight was green and merged.
  - Use this experimental preflight or its future results to alter frozen Phase 6 candidates, thresholds, comparison policy, or live trading.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-execution-preflight.md
validation:
  - command: AI Platform CI run 29827777608
    result: PASS
    evidence: Final-head AI Platform tests, lint, formatting, codespell, and JSON validations completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29827777589
    result: PASS
    evidence: Final-head workflow security analysis completed successfully.
  - command: Experimental Model Runtime Smoke run 29827777615
    result: PASS
    evidence: Canonical PyTorch reproducibility and RL environment/PPO runtime paths remained green on the final validated head.
  - command: Experimental Model Historical Execution Preflight run 29827777584
    result: PASS
    evidence: Guarded contract/resolver validation and cached independent BTC/USDT and ETH/USDT coverage verification completed successfully without a real model backtest.
  - command: Freqtrade CI run 29827777612
    result: PASS
    evidence: Full repository CI matrix, including Ubuntu coverage, Windows, macOS, smoke, Ruff, formatting, and Mypy gates, completed successfully on the final validated head.
blockers: []
next_action: Create a separate bounded execution task for canonical PyTorch and RL historical backtests using only verified pre-OOS/prediction data and the merged boundary-correct manifests, producing backtest archives for later strict historical-OOS extraction without accessing the protected final holdout or making model-performance conclusions before strict extraction.
```
