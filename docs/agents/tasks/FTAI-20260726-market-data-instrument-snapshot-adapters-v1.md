---
task_id: FTAI-20260726-market-data-instrument-snapshot-adapters-v1
status: ready
branch: feat/market-data-instrument-snapshot-adapters-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#392"
owned_paths:
  - ai_platform/market_data/instrument_adapters.py
  - ai_platform/market_data/__init__.py
  - tests/ai_platform_integration/test_market_data_instrument_adapters.py
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - docs/agents/tasks/FTAI-20260726-market-data-instrument-snapshot-adapters-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json
  - ai_platform/market_data/source-catalog-v1.json
  - ai_platform/market_data/common.py
  - ai_platform/market_data/events.py
  - docs/agents/tasks/FTAI-20260726-market-data-source-instrument-preflight-v1.md
search_first:
  - current develop HEAD and open market-data, liquidation, source-catalog, dataset, replay and collector PRs
  - existing generic instrument snapshot adapters and package ownership
optional_reads: []
---

# Bounded Market Data instrument snapshot adapters v1

## Goal

Implement five deterministic, public-only instrument metadata adapters using an injected JSON transport. Keep Binance USD-M fail-closed, perform no live request in this package and add no WebSocket, broad capture, raw market record, source acceptance, replay, model, portal, deployment or execution behavior.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T23:20:00+02:00
head: 453a5f64cd7023f891841ae92ec4f0737cd7355a
branch: develop
pr: "#392"
status: ready
context_routes:
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/SOURCE_AND_INSTRUMENT_CATALOG_PREFLIGHT.md
  - ai_platform/market_data/instrument_adapters.py
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
owned_paths:
  - ai_platform/market_data/instrument_adapters.py
  - ai_platform/market_data/__init__.py
  - tests/ai_platform_integration/test_market_data_instrument_adapters.py
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - docs/agents/tasks/FTAI-20260726-market-data-instrument-snapshot-adapters-v1.md
proven:
  - PR 392 was squash-merged into develop as 453a5f64cd7023f891841ae92ec4f0737cd7355a.
  - The merged package contains exactly the five declared task files.
  - The package exposes deterministic public-only adapters for Binance Spot, Bybit Spot, Bybit Linear, OKX Spot and OKX SWAP/FUTURES.
  - The adapters require caller-injected transport and perform no network request by default.
  - Binance USD-M remains explicitly fail-closed and recognized trading credentials are refused before transport invocation.
  - Bybit Linear pagination remains bounded to ten pages and non-unit OKX ctMult remains rejected.
  - Exact final PR head 8dc28b14706691a74d9128609a5957af96dc6da1 passed AI Platform CI, full Freqtrade CI and security analysis after a clean rebase onto current develop.
  - No WebSocket, broad capture, raw market record, source acceptance, replay, model, portal, deployment or trading behavior was merged.
derived:
  - A separate exact-one-source public smoke may now exercise the Binance Spot adapter and retain immutable artifact evidence.
  - One successful smoke cannot grant broad source acceptance.
unknown:
  - Exact current production payload inventory and reachability because the adapter package itself made no live request.
  - Continuous availability, capacity and WebSocket semantics.
conflicts: []
first_failure:
  marker: RUFF_STYLE_AND_FORMAT
  evidence: Initial validation passed adapter tests but failed Ruff style and format. The module was simplified, validator complexity locally scoped and canonical Ruff formatting applied through a temporary workflow that was deleted before merge. A later clean Git-data rebase preserved the exact five final blobs on current develop.
rejected_hypotheses:
  - Add a default HTTP client or execute official endpoints during the adapter package.
  - Enable Binance USD-M by inferring contract value from lot size or quantity precision.
  - Modify the frozen foundation source catalog to imply source acceptance.
  - Add WebSocket subscriptions, broad capture or raw market records.
  - Keep temporary diagnostic workflows in the final package.
changed_paths:
  - ai_platform/market_data/instrument_adapters.py
  - ai_platform/market_data/__init__.py
  - tests/ai_platform_integration/test_market_data_instrument_adapters.py
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - docs/agents/tasks/FTAI-20260726-market-data-instrument-snapshot-adapters-v1.md
validation:
  - command: focused synthetic adapter tests
    result: PASS
    evidence: Tests cover five ready sources, deterministic provenance, Bybit pagination, credential refusal, Binance USD-M blocking and non-unit OKX ctMult rejection.
  - command: GitHub Actions AI Platform CI run 30219993534
    result: PASS
    evidence: Compilation, AI Platform tests, Ruff, Ruff format, codespell and JSON validation succeeded on exact rebased head 8dc28b14706691a74d9128609a5957af96dc6da1.
  - command: GitHub Actions Freqtrade CI run 30219993512
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11 through 3.14, Mypy, packaging and final CI gate succeeded.
  - command: GitHub Actions security run 30219993543
    result: PASS
    evidence: Zizmor security analysis succeeded on the exact rebased head.
  - command: guarded squash merge of PR 392
    result: PASS
    evidence: GitHub accepted expected head 8dc28b14706691a74d9128609a5957af96dc6da1 and created develop commit 453a5f64cd7023f891841ae92ec4f0737cd7355a.
blockers: []
next_action: Start the separate bounded Binance Spot instrument-catalog smoke infrastructure task with one public REST request, zero retries and source acceptance disabled.
```
