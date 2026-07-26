---
task_id: FTAI-20260726-market-data-source-instrument-preflight-v1
status: validating
branch: feat/market-data-source-instrument-preflight-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#384"
owned_paths:
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json
  - ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json
  - tests/ai_platform_integration/test_market_data_source_preflight.py
  - docs/agents/tasks/FTAI-20260726-market-data-source-instrument-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/architecture-v1.json
  - ai_platform/market_data/source-catalog-v1.json
  - ai_platform/market_data/market-data-foundation-v1.schema.json
  - docs/agents/tasks/FTAI-20260726-market-data-fabric-foundation-v1.md
search_first:
  - current develop HEAD and all open market-data, liquidation, source-catalog, dataset, replay and collector PRs
  - official Binance, Bybit and OKX instrument, rate-limit and public WebSocket documentation
optional_reads: []
---

# Market Data source and instrument-catalog preflight v1

## Goal

Verify current official source and instrument-catalog semantics for the six Market Data Fabric declarations,
without implementing adapters, making live endpoint requests, starting capture or granting source acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T20:45:00+02:00
head: 6099178fa90ed6f0e17e87023d6b11f6a3ba9de4
branch: feat/market-data-source-instrument-preflight-v1
pr: "#384"
status: validating
context_routes:
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json
  - ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json
owned_paths:
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json
  - ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json
  - tests/ai_platform_integration/test_market_data_source_preflight.py
  - docs/agents/tasks/FTAI-20260726-market-data-source-instrument-preflight-v1.md
proven:
  - Market Data Fabric foundation v1 is merged and routes next to a separate source and instrument-catalog preflight without broad capture.
  - Current PR base develop is 11ad81870c0b199b0739af9dcfa239cb32d455cc.
  - PR 339 merged on liquidation-specific OKX paths and open PR 376 owns residual PyTorch audit paths; neither overlaps this task.
  - PR 384 is open, non-draft, mergeable and contains exactly the five task-owned files.
  - The foundation catalog contains exactly six declarations and keeps every source not implemented, not validated and not accepted.
  - Current official documentation exposes sufficient bounded instrument metadata for Binance Spot, Bybit Spot, Bybit Linear, OKX Spot and OKX SWAP/FUTURES adapter design.
  - Binance USD-M official exchange information does not expose explicit contract value and contract-value unit evidence required by the foundation contract.
derived:
  - The preflight can complete with a source-specific partial pass while preserving Binance USD-M as fail-closed.
  - The next adapter package can implement only the five ready source families without authorizing WebSocket capture.
unknown:
  - Exact current production inventory and endpoint reachability because this package performs no live endpoint requests.
  - Explicit Binance USD-M contract value and contract-value unit semantics.
  - Representation policy for non-unit OKX ctMult values outside the validated unit-multiplier boundary.
conflicts: []
first_failure:
  marker: NONE
  evidence: No implementation failure has occurred; exact-head repository CI is pending.
rejected_hypotheses:
  - Modify the declarations-only foundation source catalog to claim source acceptance.
  - Infer Binance USD-M contract value from quantity precision or lot-size step.
  - Treat official example payloads as proof of current production inventory.
  - Add a WebSocket collector, broad capture or raw market records to the preflight.
changed_paths:
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json
  - ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json
  - tests/ai_platform_integration/test_market_data_source_preflight.py
  - docs/agents/tasks/FTAI-20260726-market-data-source-instrument-preflight-v1.md
validation:
  - command: live-state and open-PR ownership preflight
    result: PASS
    evidence: Current develop and relevant PR paths were inspected; no generic market-data ownership conflict was found.
  - command: official documentation verification
    result: PASS
    evidence: Current Binance, Bybit and OKX catalog, payload, rate and public WebSocket documentation was inspected.
  - command: local JSON generation and Draft 2020-12 schema validation
    result: PASS
    evidence: The machine-readable preflight validates and its canonical self-hash reproduces.
  - command: PR 384 changed-file and mergeability inspection
    result: PASS
    evidence: The PR is non-draft, mergeable and changes exactly the five declared task files.
  - command: exact-head repository CI
    result: NOT_RUN
    evidence: GitHub Actions is pending on the checkpoint update commit.
blockers: []
next_action: Complete exact-head GitHub Actions for PR 384, repair the first failing required job if any, then update the checkpoint to ready.
```
