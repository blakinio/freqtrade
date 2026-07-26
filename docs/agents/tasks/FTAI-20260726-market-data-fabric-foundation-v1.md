---
task_id: FTAI-20260726-market-data-fabric-foundation-v1
status: ready
branch: feat/market-data-fabric-foundation-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#368"
owned_paths:
  - ai_platform/market_data/
  - docs/ai_platform/market_data/
  - tests/ai_platform_integration/test_market_data_*.py
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - ai_platform/research/liquidations/contracts.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/scripts/liquidation_multi_source_runner.py
search_first:
  - current develop HEAD and all open market-data, liquidation, source-catalog, dataset, replay and collector PRs
  - existing generic market-data package names and path ownership
optional_reads: []
---

# Provider-neutral Market Data Fabric foundation v1

## Goal

Create the first bounded provider-neutral contract and deterministic-universe foundation for Binance, Bybit and OKX spot, perpetual and dated-futures market data. This task adds no live connector, REST discovery, broad capture, historical bulk download, replay, model, strategy, portal, deployment or execution behavior.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T20:20:00+02:00
head: 0693c9f7bad2c5f68000c256e11a60603827bd9c
branch: develop
pr: "#368"
status: ready
context_routes:
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/architecture-v1.json
  - ai_platform/market_data/market-data-foundation-v1.schema.json
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
owned_paths:
  - ai_platform/market_data/
  - docs/ai_platform/market_data/
  - tests/ai_platform_integration/test_market_data_*.py
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
proven:
  - PR 368 was squash-merged into develop as 0693c9f7bad2c5f68000c256e11a60603827bd9c.
  - The merged PR contains exactly the declared 18 files under the task-owned paths.
  - The package defines provider-neutral event, instrument, universe, capture, segment, gap and manifest contracts with deterministic identities and fail-closed validation.
  - Deterministic all-active, Top 100 and Top 20 selectors operate only on supplied snapshots and perform no network calls.
  - All six initial Binance, Bybit and OKX source declarations remain not implemented, not validated and not accepted.
  - No live capture, raw market record, credential, order, model, replay, portal or deployment change was merged.
  - Exact PR head 93a036a35f26a37f1dcfc6b4020c9d9a22f5ec85 passed AI Platform CI, full Freqtrade CI and security analysis.
  - Open PRs 339 and 376 remained path-disjoint from the Market Data Fabric package at merge time.
derived:
  - The generic package can coexist with Liquid20 without moving or reinterpreting existing contracts or timestamps.
  - The next package is a separate source and instrument-catalog live preflight and must not include broad capture.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: Review, exact-head CI, security analysis and the guarded squash merge completed without an unresolved failure.
rejected_hypotheses:
  - Modify the existing Liquid20 source catalog to host generic market-data declarations.
  - Copy or merge the open OKX shadow implementation into the generic package.
  - Treat historical provider capture time as first-party live collector receive time.
  - Add live exchange calls, broad capture or a runtime request in the foundation PR.
changed_paths:
  - ai_platform/market_data/
  - docs/ai_platform/market_data/
  - tests/ai_platform_integration/test_market_data_contracts.py
  - tests/ai_platform_integration/test_market_data_source_catalog.py
  - tests/ai_platform_integration/test_market_data_universe.py
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
validation:
  - command: required reads, live-state preflight and open-PR ownership inspection
    result: PASS
    evidence: Current develop, all required documents, PR 339, PR 376 and path ownership were inspected before merge.
  - command: review PR 368 final 18-file diff and review state
    result: PASS
    evidence: Contract, schema, source catalog, universe, capture and test files were reviewed; all review threads were resolved and outdated.
  - command: GitHub Actions on exact PR head 93a036a35f26a37f1dcfc6b4020c9d9a22f5ec85
    result: PASS
    evidence: AI Platform CI run 30212190466, Freqtrade CI run 30212190442 and security run 30212190459 succeeded.
  - command: focused synthetic Market Data Fabric suite
    result: PASS
    evidence: The exact PR head published 24 passing focused tests through AI Platform CI.
  - command: JSON parsing and Draft 2020-12 schema checks
    result: PASS
    evidence: Source catalog, architecture manifest and contract schema validation succeeded on the exact PR head.
  - command: guarded squash merge of PR 368
    result: PASS
    evidence: GitHub accepted expected head 93a036a35f26a37f1dcfc6b4020c9d9a22f5ec85 and created develop commit 0693c9f7bad2c5f68000c256e11a60603827bd9c.
blockers: []
next_action: Start a separate source and instrument-catalog live preflight task from current develop without implementing broad capture.
```
