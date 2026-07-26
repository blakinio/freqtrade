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
updated_at: 2026-07-26T19:13:00+02:00
head: 688a70f3eca003310fc0e43119517e29105a040e
branch: feat/market-data-fabric-foundation-v1
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
  - PR 368 is open, non-draft, mergeable and its final diff contains exactly the declared 18 files.
  - The package defines provider-neutral event, instrument, universe, capture, segment, gap and manifest contracts with deterministic identities and fail-closed validation.
  - Deterministic all-active, Top 100 and Top 20 selectors operate only on supplied snapshots and perform no network calls.
  - All six initial Binance, Bybit and OKX source declarations remain not implemented, not validated and not accepted.
  - No live capture, raw market record, credential, order, model, replay, portal or deployment change is present.
  - PR 339 remains open on disjoint liquidation-specific OKX paths; PRs 350 and 360 merged without path overlap.
  - The implementation tree at a257278d5dc8be40055f75ff7ae3da228eb4443c passed AI Platform CI, full Freqtrade CI and security analysis.
derived:
  - The generic package can coexist with Liquid20 without moving or reinterpreting existing contracts or timestamps.
  - The next package should be a separate source and instrument-catalog live preflight after PR 368 is merged.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All implementation, lint, format, type, documentation, matrix and security checks are green; no unresolved failure remains.
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
  - command: live-state preflight and open-PR ownership inspection
    result: PASS
    evidence: Current develop, PR 339, merged PRs 350 and 360, required documents and path ownership were verified.
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_market_data_*.py
    result: PASS
    evidence: The focused synthetic foundation suite passed 24 tests and the published tests passed in AI Platform CI.
  - command: python -m compileall -q ai_platform/market_data tests/ai_platform_integration/test_market_data_*.py
    result: PASS
    evidence: Market-data modules and focused tests compiled locally and in AI Platform CI.
  - command: JSON parsing and Draft 2020-12 schema checks
    result: PASS
    evidence: Source catalog, architecture manifest and contract schema validation passed.
  - command: GitHub Actions AI Platform CI run 30211393132
    result: PASS
    evidence: Compile, focused tests, Ruff, Ruff format, codespell and JSON validation all succeeded on a257278d5dc8be40055f75ff7ae3da228eb4443c.
  - command: GitHub Actions Freqtrade CI run 30211393174
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11 through 3.14 matrix, Mypy, packaging and CI gate succeeded.
  - command: GitHub Actions security run 30211393145
    result: PASS
    evidence: Zizmor security analysis succeeded on the implementation tree.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md --require-checkpoint
    result: PASS
    evidence: The compact checkpoint validates against docs/agents/GOVERNANCE_CONTRACT.json.
blockers: []
next_action: Review and merge PR 368.
```
