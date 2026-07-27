---
task_id: FTAI-20260727-wickhunter-wh00-contracts-vertical-slice
status: validating
branch: feat/wickhunter-wh00-contracts-vertical-slice-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: 488
depends_on:
  - FTAI-20260727-wickhunter-liquidation-ai-bot
owned_paths:
  - ai_platform/wickhunter/**
  - tests/ai_platform_integration/test_wickhunter_vertical_slice.py
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh00-contracts-vertical-slice.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
search_first:
  - current develop HEAD, open PRs, active tasks and overlapping WickHunter, Liquid20, Market Data Fabric, FreqAI, RL-v2, risk and BM ownership
  - all existing WickHunter strategy and configuration references
optional_reads: []
---

# WickHunter WH-00 contracts and synthetic vertical slice

## Goal

Create the dependency-neutral executable first slice without consuming real historical data or claiming strategy performance:

```text
synthetic source-labelled liquidation events
  -> deterministic availability-time features
  -> reversal or continuation candidate
  -> deterministic baseline or externally supplied model score
  -> versioned WickHunterTradeIntent
  -> deterministic fail-closed risk decision
  -> simulated shadow evidence
```

## Scope

WH-00 consumes existing Liquid20 and Market Data Fabric contracts but does not modify them. It does not modify portal, BM, FreqAI, RL-v2, execution, workflow or Synology paths.

## Delivered contracts

- deterministic canonical JSON/SHA-256 identities;
- hard-bounded research parameters and a non-live compatibility prior;
- dynamic universe decisions from instrument and decision-time quality snapshots;
- source-labelled liquidation aggregation and availability-time market features;
- independently testable reversal and continuation candidate rules;
- deterministic baseline score and supervised-model score envelope;
- versioned DCA plan, freshness evidence and WickHunter TradeIntent;
- pure deterministic risk limits/context/decision;
- deterministic shadow decision evidence.

## Safety boundary

- no exchange API, trading credential or order/execution adapter access;
- no real dataset selection, replay, training, FreqAI execution or model artifact;
- no automatic parameter/model promotion;
- no live-capital or live-mode authority;
- no final-holdout access;
- no change to Phase 6 `selected_model = null`;
- no profitability claim.

## Acceptance criteria

- dynamic universe selects multiple eligible symbols and removes inactive/stale/risk-blocked symbols;
- liquidation aggregates retain source identity, direction, event count, maximum event and ingest latency;
- future events and future/unclosed candle metrics are rejected;
- deterministic features, candidates, scores, intents, risk decisions and shadow evidence reproduce exactly;
- reversal and continuation hypotheses generate independently testable long/short candidates;
- duplicate, cooldown and hard parameter-bound gates work;
- stale data, source health, model promotion, drift, DCA, exposure, loss and circuit-breaker gates fail closed;
- live mode is rejected and no direct order-submission surface exists;
- focused tests and compile pass;
- Ruff/format and repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T18:55:00+02:00
head: a8b331d682e6bb8050a1c36b9e36b50f165bfc1f
branch: feat/wickhunter-wh00-contracts-vertical-slice-v1
pr: 488
status: validating
context_routes:
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
owned_paths:
  - ai_platform/wickhunter/**
  - tests/ai_platform_integration/test_wickhunter_vertical_slice.py
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh00-contracts-vertical-slice.md
proven:
  - Existing Liquid20 evidence and frozen liquid20-v1 collection profile remain immutable and separate from the dynamic WickHunter trading universe.
  - Market Data Fabric exposes provider-neutral instrument snapshots and deterministic universe inputs.
  - Existing WickHunter research code defines VWAP distances as ratios and requires liquidation evidence.
  - Existing portal risk authority is deterministic and fail-closed, but its manual DB-backed interface does not yet expose all WickHunter risk inputs.
  - BM-00 is merged; active BM feature PR paths are untouched by WH-00.
  - Phase 6 remains selected_model=null and RL-v2 remains a separate non-promoted research track.
  - Protected final holdout 20260801-20260930 is not accessed by WH-00.
  - Local focused synthetic validation passes 26 tests and Python compile.
derived:
  - A separate ai_platform/wickhunter boundary is path-disjoint and can consume existing contracts without changing active portal, BM, market-data or RL-v2 ownership.
  - The first executable slice can be proven synthetically while real replay/training remains gated by accepted dataset selection.
  - Compatibility VWAP references 0.3 and 0.5 are represented as ratios 0.003 and 0.005.
unknown:
  - Real accepted historical dataset identity and hash until WH-01.
  - Replay labels, costs and performance until WH-02.
  - LightGBM, XGBoost, PyTorch and RL comparative evidence until their declared packages.
  - Portal Risk Engine adapter contract until WH-06 ownership and shared-schema preflight.
  - Exact GitHub CI and review result until PR 488 completes.
conflicts: []
first_failure:
  marker: LOCAL_RUFF_UNAVAILABLE
  evidence: Ruff is not installed or cached in the sandbox; focused pytest and compile pass, and GitHub CI remains authoritative for Ruff and format.
rejected_hypotheses:
  - Use the frozen Liquid20 symbol list as the permanent WickHunter universe.
  - Modify active portal/BM risk contracts inside WH-00.
  - Start real training or replay before accepted dataset selection.
  - Promote RL-v2 merely because an adapter exists.
  - Treat a model score as order authority.
  - Permit live mode or direct order submission.
changed_paths:
  - ai_platform/wickhunter/__init__.py
  - ai_platform/wickhunter/canonical.py
  - ai_platform/wickhunter/contracts.py
  - ai_platform/wickhunter/features.py
  - ai_platform/wickhunter/parameters.py
  - ai_platform/wickhunter/risk.py
  - ai_platform/wickhunter/scoring.py
  - ai_platform/wickhunter/shadow.py
  - ai_platform/wickhunter/strategy.py
  - ai_platform/wickhunter/universe.py
  - tests/ai_platform_integration/test_wickhunter_vertical_slice.py
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh00-contracts-vertical-slice.md
validation:
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_wickhunter_vertical_slice.py
    result: PASS
    evidence: 26 passed.
  - command: python -m compileall -q ai_platform/wickhunter tests/ai_platform_integration/test_wickhunter_vertical_slice.py
    result: PASS
    evidence: All WH-00 Python files compile.
  - command: ruff check and ruff format --check
    result: NOT_RUN
    evidence: Ruff is unavailable in the sandbox and not present in the offline uv cache; GitHub CI is authoritative.
blockers: []
next_action: Resolve exact-head CI and review findings on PR 488, merge only after all required checks pass, then create WH-01 from current develop for the first accepted source-aware dataset.
```
