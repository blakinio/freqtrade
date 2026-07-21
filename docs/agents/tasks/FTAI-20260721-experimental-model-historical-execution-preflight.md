---
task_id: FTAI-20260721-experimental-model-historical-execution-preflight
status: done
branch: develop
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
updated_at: 2026-07-21T12:10:49Z
head: 262cebef33c8e06d8c9379f1603be93552f445fe
branch: develop
pr: "#73 merged"
status: ready
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
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
  - Runtime-smoke-hardening checkpoint #70 established this historical-execution preflight as the required gate before any canonical PyTorch or RL historical backtest.
  - Closed PR #66 proved dependency installation, static execution contracts, and both custom resolvers but its 20260630 stop could not certify full June coverage.
  - Freqtrade TimeRange parses an eight-digit stop token at 00:00 UTC on that date, so technical execution stops are corrected to 20260701 while semantic windows still end 20260630.
  - Strict experimental OOS scoring remains 20260501-20260630 with end_exclusive 2026-07-01T00:00:00Z, and backtest_period_days=122 matches March 1 through June 30 inclusive.
  - PyTorch and RL manifests use 20260301-20260701 for execution and 20250801-20260701 for download; protected final holdout 20260801-20260930 remains unused and forbidden, frozen thresholds 0.006/-0.009 are unchanged, and Phase 6 isolation remains intact.
  - PR #73 parallelizes Kraken trade-history acquisition per pair and verifies 15m, 1h, and 4h coverage independently for BTC/USDT and ETH/USDT.
  - PR #75 was closed without merge as superseded by the stronger parallel preflight in PR #73.
  - A deterministic pre-commit Mypy failure was isolated to variable-name reuse in experimental_model_historical_execution_preflight.py and fixed without changing runtime semantics.
  - Workflow concurrency uses cancel-in-progress=false, pair-specific jobs have a 240-minute timeout, and exact boundary-correct v2 caches are accepted only with independent coverage verification.
  - BTC/USDT verified coverage spans 2025-08-01 through at least the required 2026-07-01 boundary for 15m, 1h, and 4h with 32021, 8010, and 2004 rows respectively.
  - ETH/USDT verified coverage spans 2025-08-01 through at least the required 2026-07-01 boundary for 15m, 1h, and 4h with 31985, 8011, and 2004 rows respectively.
  - Final preflight artifacts report status=ready, market_data_available=true, phase6_member=false, protected_final_holdout_used=false, retuning_allowed=false, promotion_allowed=false, and profitability_claim_allowed=false.
  - Validated implementation head a3572689a6e3a3b808d95d886ae7e58e017418e5 passed AI Platform CI 29823749276, zizmor 29823749275, Experimental Model Runtime Smoke 29823749273, Freqtrade CI 29823749339, and Historical Execution Preflight 29823749323.
  - Final PR merge-ref 823b300e08b4c1611298fe268c0feccc37b9de4b passed AI Platform CI 29827777608, zizmor 29827777589, Experimental Model Runtime Smoke 29827777615, Historical Execution Preflight 29827777584, and full Freqtrade CI 29827777612 against the then-current develop.
  - Direct develop-versus-branch comparison before merge contained only the twelve intended experimental-preflight paths; apparent extra Phase 6 paths came from GitHub synthetic merge refs while develop advanced independently.
  - PR #73 was squash-merged into develop as 262cebef33c8e06d8c9379f1603be93552f445fe, and immediate comparison confirmed develop identical to that SHA.
derived:
  - Results from PR #66's stale 20260630-stop download remain invalid as proof of full-June historical coverage.
  - Verified pair-specific caches may be consumed by a later bounded execution workflow without changing model, scoring, or holdout contracts.
  - Real PyTorch or RL historical backtesting now requires a separate bounded execution work package and cannot be inferred as authorized merely from this preflight merge.
unknown: []
conflicts: []
first_failure:
  marker: freqtrade-exclusive-stop-boundary
  evidence: Canonical manifests originally used stop token 20260630, but TimeRange parses that as 2026-06-30T00:00:00Z while strict OOS requires end_exclusive 2026-07-01T00:00:00Z.
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
  - command: AI Platform CI / zizmor / Experimental Model Runtime Smoke / Historical Execution Preflight / Freqtrade CI on final PR merge-ref
    result: PASS
    evidence: Runs 29827777608, 29827777589, 29827777615, 29827777584, and 29827777612 all completed successfully before squash merge.
  - command: PR #73 squash merge
    result: PASS
    evidence: PR #73 merged successfully as 262cebef33c8e06d8c9379f1603be93552f445fe.
  - command: compare 262cebef33c8e06d8c9379f1603be93552f445fe...develop
    result: PASS
    evidence: develop was identical immediately after merge with ahead_by=0 and behind_by=0.
blockers: []
next_action: This preflight work package is complete. Continue only through the separate bounded task docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md; do not run a real PyTorch or RL backtest outside that task and do not access protected final holdout 20260801-20260930.
```
