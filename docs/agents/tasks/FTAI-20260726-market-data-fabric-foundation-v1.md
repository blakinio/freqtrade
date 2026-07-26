---
task_id: FTAI-20260726-market-data-fabric-foundation-v1
status: in_progress
branch: feat/market-data-fabric-foundation-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
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
updated_at: 2026-07-26T13:45:00+02:00
head: bef49bdf4d914c2aa363d99621cdb7b80fd16c9d
branch: feat/market-data-fabric-foundation-v1
pr: pending
status: in_progress
context_routes:
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
owned_paths:
  - ai_platform/market_data/
  - docs/ai_platform/market_data/
  - tests/ai_platform_integration/test_market_data_*.py
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
proven:
  - develop HEAD at task declaration is bef49bdf4d914c2aa363d99621cdb7b80fd16c9d.
  - No generic ai_platform/market_data package exists on develop.
  - PR 339 owns isolated OKX liquidation source paths, including the existing liquidation source catalog.
  - PR 350 owns liquidation candle-artifact infrastructure and pyproject.toml.
  - PR 360 owns provider-neutral historical liquidation contracts under ai_platform/research/liquidations/historical/.
  - The planned market-data paths are disjoint from all relevant open PR owned paths.
derived:
  - A new provider-neutral package can be added without moving, renaming or modifying Liquid20 code.
  - Historical provider capture time must remain distinct from first-party live collector receive time.
unknown:
  - Exact repository CI outcome for the future implementation head.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Modify the existing Liquid20 source catalog to host generic market-data declarations.
  - Copy or merge the open OKX shadow implementation into the generic package.
  - Add live exchange calls or a capture request in the foundation PR.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
validation:
  - command: live-state preflight
    result: PASS
    evidence: Required documents, relevant open PR ownership and current develop head were inspected before editing.
blockers: []
next_action: Implement and locally validate the bounded market-data contracts, schemas, source declarations, deterministic universe selector and architecture package on this branch.
```
