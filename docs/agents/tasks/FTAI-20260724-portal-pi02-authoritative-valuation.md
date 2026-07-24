---
task_id: FTAI-20260724-portal-pi02-authoritative-valuation
status: active
branch: feat/portal-pi02-authoritative-valuation-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: 267
owned_paths:
  - ai_platform/portal/valuation/**
  - ai_platform/portal/execution/private_read.py
  - ai_platform/portal/operations/schema.py
  - ai_platform/portal/operations/service.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/fixtures.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - tests/ai_platform/portal/valuation/**
  - tests/ai_platform/portal/operations/test_private_runtime_reconciliation.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi02-authoritative-valuation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# PI-02 — Authoritative Valuation and Unrealized PNL

## Goal

Provide attributable current position valuation and unrealized PNL from reconciled private runtime positions and a timestamped mark price emitted by the exact same pinned Freqtrade runtime, without public market-data access, fabricated conversion or execution authority.

## Selected authoritative source and policy

- The canonical mark source is the authenticated private Freqtrade open-trade status for the exact `source_runtime_id`, normalized by the existing PI-01 private collector.
- Source fields are `open_rate`, `current_rate`, base/quote currency, source trade/position identity and collector observation timestamp. `current_rate` is the mark price; `open_rate` is the entry basis.
- Repository code never exposes the private runtime endpoint or authorization material to the browser.
- PI-02 v1 supports unleveraged positions whose quote currency exactly matches the bot capital currency.
- Cross-currency conversion, non-unit leverage, funding, derivatives-specific settlement and missing price provenance produce `UNPRICED`; no fallback rate is used.
- Unrealized PNL is gross mark-to-entry PNL before hypothetical exit fees. Realized PNL and fees remain sourced from closed trade evidence and are not recomputed.
- A mark older than the versioned freshness bound produces `STALE`; source failure produces `SOURCE_UNAVAILABLE`.

## Deliverables

- versioned immutable valuation snapshot contract with position, runtime, price-source and timestamp attribution;
- optional PI-02 source fields on normalized private positions, preserving PI-01 compatibility;
- deterministic valuation service with `CURRENT`, `STALE`, `SOURCE_UNAVAILABLE` and `UNPRICED` states;
- tenant-scoped `GET /v1/valuations` API requiring `bot.read`;
- PNL & Performance UI integration that keeps realized and unrealized evidence separate;
- deterministic handling of side, unsupported currency conversion, non-unit leverage, stale/missing prices and reconciliation gaps;
- focused contract, tenant-isolation, provenance, freshness and API/UI tests;
- backlog, program, architecture and UI status updates.

## Acceptance criteria

1. Every numeric valuation links to one reconciled position, one pinned runtime, one source price identity and one source timestamp.
2. Stale, missing, cross-currency, leveraged or unreconciled evidence never produces a current numeric valuation.
3. Tenant isolation is enforced server-side and browser responses contain no runtime endpoint, authorization header or credential.
4. Long and short gross mark-to-entry PNL use a versioned deterministic method; unsupported settlement semantics fail closed as `UNPRICED`.
5. Realized PNL remains sourced from closed trade evidence and is displayed separately from unrealized PNL.
6. API mode never falls back to fixture or public price data.
7. Required targeted and repository CI pass before merge.

## Non-goals

- forecasting prices or future PNL;
- public browser/exchange market-data access;
- automatic currency conversion without an attributable source;
- derivatives funding/liquidation valuation in v1;
- order submission, credential brokering, live capital or P14;
- modifying frozen thresholds, Phase 6 evidence or protected final-holdout policy.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T22:25:00+02:00
head: e14a200514431010901f866a1277cd08917bdce9
branch: feat/portal-pi02-authoritative-valuation-20260724
pr: 267
status: validating
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - ai_platform/portal/valuation/**
  - ai_platform/portal/execution/private_read.py
  - ai_platform/portal/operations/schema.py
  - ai_platform/portal/operations/service.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/fixtures.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - tests/ai_platform/portal/valuation/**
  - tests/ai_platform/portal/operations/test_private_runtime_reconciliation.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi02-authoritative-valuation.md
proven:
  - develop head 5afb797f389bd4eb90cf189804cba26d8249ba07 durably closes PI-04 and records no active software PI package.
  - Open PR 265 is a one-shot RL-v2 execution trigger and does not own PI-02 paths; PR 109 is an inert design reference.
  - PI-01 provides tenant/runtime-scoped reconciled positions and explicit CURRENT, STALE, PARTIAL and SOURCE_UNAVAILABLE evidence.
  - Freqtrade OpenTradeSchema exposes base_currency, quote_currency, open_rate and current_rate for private open-trade status responses.
  - Existing performance summaries are realized-only and do not fabricate unrealized PNL.
derived:
  - The same pinned private runtime is the narrowest attributable mark source and avoids a new public market-data dependency.
  - V1 can safely support exact-quote, unit-leverage mark-to-entry valuation while failing closed for conversion and derivatives semantics.
unknown:
  - Final required repository CI result on the documentation-synchronized candidate.
conflicts: []
first_failure:
  marker: RESOLVED
  evidence: Full pytest initially found a duplicate test_runtime module basename; a valuation test-package marker resolved collection. Ruff then identified import/format findings and one C901 decision method, all fixed without changing valuation semantics.
rejected_hypotheses:
  - Select an unaffiliated public price API without an owner decision.
  - Reuse fixture prices in API mode.
  - Treat stale or cross-currency evidence as a numeric current valuation.
  - Recompute realized PNL from open-position marks.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/valuation/__init__.py
  - ai_platform/portal/valuation/runtime.py
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/e2e/valuation.spec.ts
  - ai_platform/portal/web/lib/valuation.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi02-authoritative-valuation.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/valuation/__init__.py
  - tests/ai_platform/portal/valuation/test_runtime.py
  - tests/ai_platform/portal/valuation/test_runtime_api.py
validation:
  - command: AI Platform CI 30123794369 / run 1129
    result: PASS
    evidence: Tests, compile, Ruff, formatter, codespell and contract validation passed on clean implementation head e14a200514431010901f866a1277cd08917bdce9.
blockers: []
next_action: Complete final required CI on the documentation-synchronized candidate, then mark PR 267 ready and merge only if the head remains unchanged and all required workflows pass.
```
