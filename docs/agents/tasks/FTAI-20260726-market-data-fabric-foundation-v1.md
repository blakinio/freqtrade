---
task_id: FTAI-20260726-market-data-fabric-foundation-v1
status: validating
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
updated_at: 2026-07-26T14:27:00+02:00
head: d4406e4b4e2761dbab99a2911be8eb73a7a3ebd7
branch: feat/market-data-fabric-foundation-v1
pr: "#368"
status: validating
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
  - Task declaration started from develop bef49bdf4d914c2aa363d99621cdb7b80fd16c9d and the branch was rebuilt on current develop be7b387fa1090ee72b9ba4200f6e71098ed1d2ac.
  - No generic ai_platform/market_data package existed before this task.
  - PR 339 remains open and owns only existing liquidation-specific OKX paths.
  - PR 350 and PR 360 merged while this task was active; their paths remain disjoint from this package.
  - PR 368 is open, non-draft, mergeable and contains only the declared 18 new-path files.
  - The package defines real event, instrument, universe, capture, segment, gap and manifest contracts with deterministic identities and fail-closed validation.
  - The deterministic selector supports all-active, Top 100 and Top 20 profiles using supplied synthetic snapshots only and performs no network calls.
  - All six initial source declarations remain not implemented, not validated and not accepted.
  - No live capture request, raw market record, credential, order, model, replay, portal or deployment change is present.
derived:
  - The generic package can coexist with Liquid20 without moving or reinterpreting existing contracts or timestamps.
  - The next package can be a separate source and instrument-catalog live preflight after this foundation is reviewed.
unknown:
  - Exact-current-head GitHub Actions outcome for PR 368.
conflicts: []
first_failure:
  marker: NONE
  evidence: No implementation failure is unresolved; local Ruff was unavailable in the network-isolated sandbox, so repository CI is authoritative.
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
    evidence: Current develop, PR 339, merged PRs 350 and 360, required documents and path ownership were verified before and after implementation.
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_market_data_*.py
    result: PASS
    evidence: The pre-publication synthetic foundation suite passed 24 tests; exact published test files remain subject to repository CI.
  - command: python -m compileall -q ai_platform/market_data tests/ai_platform_integration/test_market_data_*.py
    result: PASS
    evidence: The pre-publication market-data modules and focused tests compiled successfully.
  - command: JSON parsing and Draft 2020-12 schema checks
    result: PASS
    evidence: The source catalog, architecture manifest and contract schema parsed and the schema passed Draft202012Validator.check_schema.
  - command: exact-current-head repository CI on PR 368
    result: NOT_RUN
    evidence: GitHub Actions is queued for the checkpoint predecessor d4406e4b4e2761dbab99a2911be8eb73a7a3ebd7 and must rerun on this checkpoint commit.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: Run against this governance-valid checkpoint before handoff.
blockers: []
next_action: Complete exact-current-head GitHub Actions for PR 368, repair the first non-green required job if any, then update this checkpoint to ready.
```
