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
updated_at: 2026-07-26T22:24:00+02:00
head: 7d76e7bd27132edb95645d8dccbefb6f79eb22ba
branch: feat/market-data-instrument-snapshot-adapters-v1
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
  - Source and instrument-catalog preflight v1 merged with five ready source families and Binance USD-M fail-closed.
  - PR 392 is open, non-draft, mergeable and contains exactly the five task-owned files.
  - Current develop 7dcf26e1376c9ceae9f2e83bbfd49f1abc208758 is three path-disjoint commits ahead of the original branch base.
  - Open PRs 394 and 395 own liquidation publication and residual PyTorch execution paths; neither overlaps this generic package.
  - The adapter package has no default HTTP client and requires a caller-injected public JSON transport.
  - The implementation produces deterministic source-bound InstrumentSnapshot records and a self-hashed InstrumentCatalogSnapshot.
  - Binance USD-M remains explicitly blocked and recognized trading credentials are refused before transport invocation.
  - Bybit Linear pagination is bounded to ten pages and rejects repeated cursors; non-unit OKX ctMult fails closed.
  - Exact implementation head 7d76e7bd27132edb95645d8dccbefb6f79eb22ba passed AI Platform CI, full Freqtrade CI and security analysis.
derived:
  - The package is ready for review and merge without exchange requests or source acceptance.
  - A later bounded one-source smoke can execute these adapters without combining WebSocket capture or broad source acceptance.
unknown:
  - Exact current production payload inventory because no live request is authorized in this package.
  - Future operational timeout, retry and host storage policy, which belongs to a separate bounded execution package.
conflicts: []
first_failure:
  marker: RUFF_STYLE_AND_FORMAT
  evidence: Initial exact-head validation passed all adapter tests but failed Ruff style and later Ruff format. The module was simplified, validator complexity was locally scoped, and a temporary one-shot formatter workflow produced canonical formatting before being deleted. Final PR scope returned to exactly five files and all exact-head gates passed.
rejected_hypotheses:
  - Add a default HTTP client or execute official endpoints during this adapter package.
  - Enable Binance USD-M by inferring contract value from lot size or quantity precision.
  - Modify the frozen foundation source catalog to imply source acceptance.
  - Add WebSocket subscriptions, broad capture or raw market records.
  - Keep the temporary formatter workflow in the final PR.
changed_paths:
  - ai_platform/market_data/instrument_adapters.py
  - ai_platform/market_data/__init__.py
  - tests/ai_platform_integration/test_market_data_instrument_adapters.py
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - docs/agents/tasks/FTAI-20260726-market-data-instrument-snapshot-adapters-v1.md
validation:
  - command: live-state and open-PR ownership preflight
    result: PASS
    evidence: Current develop and open PR paths were inspected; no generic market-data ownership conflict was found.
  - command: focused synthetic adapter tests
    result: PASS
    evidence: Tests cover all five ready sources, deterministic provenance, Bybit pagination, credential refusal, Binance USD-M blocking and non-unit OKX ctMult rejection.
  - command: GitHub Actions AI Platform CI run 30218301350
    result: PASS
    evidence: Compilation, all AI Platform tests, Ruff, Ruff format, codespell and JSON validation succeeded on 7d76e7bd27132edb95645d8dccbefb6f79eb22ba.
  - command: GitHub Actions Freqtrade CI run 30218301345
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11 through 3.14, generated-file checks, smoke tests, Ruff, Ruff format, Mypy, packaging and final CI gate succeeded.
  - command: GitHub Actions security run 30218301362
    result: PASS
    evidence: Zizmor security analysis succeeded on the exact implementation head.
  - command: PR 392 changed-file, mergeability and review inspection
    result: PASS
    evidence: The PR is mergeable, changes exactly the five declared task files and has no unresolved current review thread; the only thread is resolved and outdated with the deleted temporary workflow.
blockers: []
next_action: Review and merge PR 392.
```
