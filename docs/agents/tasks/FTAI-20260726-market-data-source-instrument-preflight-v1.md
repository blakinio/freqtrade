---
task_id: FTAI-20260726-market-data-source-instrument-preflight-v1
status: ready
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
updated_at: 2026-07-26T21:06:00+02:00
head: 2d0d5e739762b30906939cfc4e0b7731b55eb43d
branch: feat/market-data-source-instrument-preflight-v1
pr: "#384"
status: ready
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
  - Exact implementation head 2d0d5e739762b30906939cfc4e0b7731b55eb43d passed AI Platform CI, full Freqtrade CI and security analysis.
derived:
  - The preflight completes with a source-specific partial pass while preserving Binance USD-M as fail-closed.
  - The next adapter package can implement only the five ready source families without authorizing WebSocket capture.
unknown:
  - Exact current production inventory and endpoint reachability because this package performs no live endpoint requests.
  - Explicit Binance USD-M contract value and contract-value unit semantics.
  - Representation policy for non-unit OKX ctMult values outside the validated unit-multiplier boundary.
conflicts: []
first_failure:
  marker: PRE_COMMIT_TYPING
  evidence: Predecessor head b582d4267cdc2337d8d7fea86a90d5b49bc2e53d failed pre-commit because the JSON test fixture was typed as object; commit 2d0d5e739762b30906939cfc4e0b7731b55eb43d changed it to Any and subsequent pre-commit and Mypy passed.
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
  - command: focused preflight schema, self-hash and boundary tests
    result: PASS
    evidence: Five focused tests passed and bind the manifest to the exact foundation catalog with fail-closed source decisions.
  - command: GitHub Actions AI Platform CI run 30215543319
    result: PASS
    evidence: Focused tests, Ruff, Ruff format, codespell, JSON validation and checkpoint validation succeeded on 2d0d5e739762b30906939cfc4e0b7731b55eb43d.
  - command: GitHub Actions Freqtrade CI run 30215543340
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11 through 3.14, Mypy, packaging and final CI gate succeeded.
  - command: GitHub Actions security run 30215543316
    result: PASS
    evidence: Zizmor security analysis succeeded on the exact implementation head.
  - command: PR 384 changed-file, mergeability and review inspection
    result: PASS
    evidence: The PR is non-draft, mergeable, changes exactly the five declared task files and has no unresolved review thread.
blockers: []
next_action: Review and merge PR 384.
```
