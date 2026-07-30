---
task_id: FTAI-20260731-wickhunter-okx-market-evidence-v2
status: in_progress
branch: agent/wickhunter-okx-market-evidence-v2
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: null
depends_on:
  - FTAI-20260731-wickhunter-market-evidence-recovery-v1
  - merged production Market Evidence v1 implementation
  - merged public OKX Liquid20 source implementation
owned_paths:
  - ai_platform/wickhunter/production-market-evidence-contract-v2.json
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v2.json
  - ai_platform/portal/web/lib/market-evidence/reader-v2.ts
  - ai_platform/portal/web/lib/market-evidence/index.ts
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - ai_platform/portal/web/e2e/specs/market-evidence-okx-v2.spec.ts
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
---

# WickHunter OKX Market Evidence v2

## Goal

Add a versioned, backward-compatible three-source Market Evidence contract for `bybit-linear`, `binance-usdm` and `okx-swap` without mutating the immutable v1 request currently running in PR #816.

## Scope

- public credential-free OKX SWAP tickers, completed 5m candles and instrument metadata;
- exact `BASE-USDT-SWAP` to `BASEUSDT` mapping;
- source-separated deterministic normalization and dynamic verified record counts;
- completed-candle and response-receipt availability semantics;
- fail-closed credential, proxy, redirect, private endpoint, malformed mapping, stale, gap, tamper, traversal, symlink and overwrite behavior;
- a v2 publication adapter that can produce immutable rows for all three sources;
- Portal read-model support that derives OKX availability and eligibility from verified package rows rather than source-name exclusions;
- focused backend and Portal tests;
- no operational request in this mergeable package.

## Non-goals

- no mutation or reuse of `wickhunter-production-market-evidence-20260730-v1`;
- no production capture trigger;
- no archive binding or WH-01 materialization;
- no credentials, orders, replay, training, performance research, execution or live capital.

## Acceptance

- v1 behavior remains importable and unchanged;
- v2 rejects unsafe environments and uncompleted OKX candles;
- exact three-source geometry is validated dynamically;
- OKX source and instrument rows are emitted only from verified public payloads;
- Portal remains red for absent evidence and becomes eligible only for a verified v2 package;
- focused exact-head CI passes with zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T00:45:00+02:00
head: e19327315cd40d11bcaaa48b11dc53afa80d78e8
branch: agent/wickhunter-okx-market-evidence-v2
status: in_progress
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
owned_paths:
  - ai_platform/wickhunter/production-market-evidence-contract-v2.json
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v2.json
  - ai_platform/portal/web/lib/market-evidence/reader-v2.ts
  - ai_platform/portal/web/lib/market-evidence/index.ts
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - ai_platform/portal/web/e2e/specs/market-evidence-okx-v2.spec.ts
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
proven:
  - The immutable v1 request and implementation cover only Bybit and Binance.
  - The public OKX Liquid20 collector already validates live USDT linear SWAP instrument contracts.
  - Official OKX public market responses identify completed candles with confirm equal to 1 and expose public tickers and instruments.
derived:
  - A separate v2 module avoids changing the semantics of the active v1 run.
unknown:
  - Exact prospective v2 request window, which belongs to a later request-only package.
conflicts: []
first_failure:
  marker: OKX_CANDLE_EVIDENCE_NOT_CONFIGURED
  evidence: Current Portal reader explicitly excludes okx-swap from verified Market Evidence availability.
rejected_hypotheses:
  - Modify the active v1 request or collector constants in place.
  - Accept confirm equal to 0 candles.
  - Derive OKX eligibility from liquidation connectivity alone.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
validation:
  - command: task ownership and current source-contract audit
    result: PASS
    evidence: Owned paths are disjoint from current effective open-PR diffs.
blockers: []
next_action: Implement the versioned public OKX normalization and safety contract with focused tests before wiring the v2 publication and Portal reader.
```
