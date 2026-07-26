---
task_id: FTAI-20260726-liquidation-okx-shadow-source-v1
status: validating
branch: feat/liquidation-okx-shadow-source-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#339"
owned_paths:
  - ai_platform/research/liquidations/okx.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_okx_collector.py
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-source-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
search_first:
  - current develop HEAD, open liquidation PRs and CI
  - current official OKX liquidation, instrument and time contracts
  - current Liquid20 Synology status without modifying Oteryn-Platform
optional_reads: []
---

# OKX Liquidation Shadow Source v1

## Goal

Add a bounded public OKX USDT-swap liquidation source foundation while preserving the existing Bybit-plus-Binance
`liquid20-v1`, frozen acceptance policy, portal contract, model evidence and trading boundary.

## Acceptance criteria

- [x] OKX has a distinct canonical source identity.
- [x] Public instrument metadata is required before contract quantities are normalized.
- [x] Only live, linear, USDT-settled swaps with base-currency `ctVal` and `ctMult=1` are accepted.
- [x] `sz` is converted from contracts to base quantity before USD notional is calculated.
- [x] Side and position-side combinations are normalized to the liquidated position.
- [x] The collector uses public endpoints and refuses recognized trading credentials.
- [x] Instrument metadata is persisted and SHA-256 bound in the source summary.
- [x] Unrelated instruments from the global channel are filtered locally.
- [x] Focused synthetic tests cover metadata, quantities, sides, filtering, duplicates, clock and catalog semantics.
- [ ] Repository CI passes on the exact PR head.
- [ ] A separate public smoke is executed in a later operational task.
- [ ] A prospective OKX shadow acceptance policy is declared before any long run is judged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T10:40:00Z
head: 1e66cc7f1237c00c2b9eca2ad62b59216b3a3c31
branch: feat/liquidation-okx-shadow-source-v1
pr: "#339"
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/okx.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_okx_collector.py
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-source-v1.md
proven:
  - Current develop Liquid20 v1 contains only Bybit linear and Binance USD-M sources.
  - OKX provides a public WebSocket liquidation-orders channel for SWAP observations.
  - Public OKX WebSocket channels do not require login.
  - OKX removed its public REST liquidation-history endpoint in 2023.
  - OKX swap sz is contract count and requires instrument ctVal metadata for normalization.
  - The implementation keeps OKX outside liquid20-v1, its runner, acceptance policy, portal and Synology runtime.
  - Eleven focused synthetic OKX tests pass.
  - AI Platform CI compile and all tests passed on every inspected head.
  - Ruff complexity was resolved by decomposing parser and collector behavior into focused deterministic helpers.
  - Ruff lint passed after removing the final unused import.
  - Ruff 0.15.11 formatting was captured by diagnostic run 30194767964 and applied exactly; artifact digest is sha256:b70e35e76c5226caa95c8399f359a89c3c81c83a2161d8df806ebe43e21fb25a.
  - The consumed diagnostic workflow was removed from the branch before final validation.
derived:
  - OKX is the safest third source only as an isolated shadow source first.
  - A frozen public instrument snapshot is part of event provenance, not optional reference data.
  - BitMEX is the next source preflight candidate after OKX operational evidence.
unknown:
  - Final exact-head repository CI outcome for PR #339.
  - Exact public endpoint behavior and payload variations from the intended staging host.
  - Event volume, latency distribution, reconnect behavior and symbol coverage during a representative run.
  - Whether every liquid20-v1 symbol has stable live OKX USDT-swap metadata at execution time.
  - Exact OKX-specific prospective smoke and 24-hour acceptance thresholds.
conflicts: []
first_failure:
  marker: ruff-complexity-and-format
  evidence: Initial AI Platform CI found only Ruff complexity, an unused import and formatting drift; compile and all tests passed, and each issue was corrected without changing source semantics.
rejected_hypotheses:
  - Add OKX directly to the frozen liquid20-v1 runner and acceptance package.
  - Calculate OKX notional as bankruptcy price multiplied directly by contract count.
  - Accept missing or incompatible instrument metadata by guessing contract value.
  - Modify the portal or Synology runtime in the source-foundation PR.
  - Add BitMEX, Gate.io and other venues in the same implementation package.
changed_paths:
  - ai_platform/research/liquidations/okx.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_okx_collector.py
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-source-v1.md
validation:
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_liquidation_okx_source.py
    result: PASS
    evidence: Eleven synthetic parser, metadata, normalization, filtering, duplicate, clock and catalog tests passed.
  - command: Python compile in AI Platform CI
    result: PASS
    evidence: Parser, collector and focused tests compile on repository CI.
  - command: AI Platform tests
    result: PASS
    evidence: The complete AI Platform test step passed on every inspected PR head.
  - command: Ruff lint
    result: PASS
    evidence: Ruff lint passed after the focused complexity refactor and unused-import removal.
  - command: Diagnostic OKX Ruff format run 30194767964
    result: PASS
    evidence: Ruff 0.15.11 generated the exact final formatting artifact, which was applied before removing the diagnostic workflow.
  - command: GitHub Actions Security Analysis runs 30193978273, 30194482710, 30194602215, 30194767975
    result: PASS
    evidence: Zizmor passed on each inspected implementation head.
blockers: []
next_action: After PR #339 merges, declare a separate OKX shadow staging/smoke and prospective acceptance task without adding OKX to liquid20-v1.
```
