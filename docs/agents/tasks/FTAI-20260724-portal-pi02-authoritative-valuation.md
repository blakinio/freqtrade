---
task_id: FTAI-20260724-portal-pi02-authoritative-valuation
status: ready
branch: feat/portal-pi02-authoritative-valuation-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: 267
owned_paths:
  - ai_platform/portal/valuation/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/lib/valuation.ts
  - ai_platform/portal/web/e2e/valuation.spec.ts
  - tests/ai_platform/portal/valuation/**
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

Provide attributable current position valuation and unrealized PNL from reconciled private runtime positions and a timestamped mark emitted by the exact same pinned Freqtrade runtime, without public market-data access, fabricated conversion or execution authority.

## Selected authoritative source and policy

- The canonical price evidence is the authenticated private Freqtrade open-trade status for the exact `source_runtime_id`.
- A dedicated server-side valuation source boundary accepts a versioned normalized envelope derived from that exact runtime. It does not mutate PI-01 operational records or expose the runtime endpoint or authorization material to the browser.
- Source evidence preserves the source position, pair and side, base and quote currency, entry rate corresponding to Freqtrade `open_rate`, current mark corresponding to `current_rate`, leverage, source-price identity and source observation timestamp.
- PI-02 v1 supports unleveraged positions whose quote currency exactly matches the bot capital currency.
- Cross-currency conversion, non-unit leverage, funding, derivatives-specific settlement and missing or conflicting price provenance produce `UNPRICED`; no fallback rate is used.
- Unrealized PNL is gross mark-to-entry PNL before hypothetical exit fees. Realized PNL and fees remain sourced from closed-trade evidence and are not recomputed.
- A mark older than the versioned freshness bound produces `STALE`; source failure produces `SOURCE_UNAVAILABLE`.

## Deliverables

- versioned immutable valuation snapshot contract with position, runtime, price-source and timestamp attribution;
- bounded private runtime valuation source adapter with URL, timeout, response-size, sensitive-key and scope validation;
- deterministic valuation service with `CURRENT`, `STALE`, `SOURCE_UNAVAILABLE` and `UNPRICED` states;
- tenant-scoped `GET /v1/valuations` API requiring `bot.read`;
- PNL & Performance UI integration that keeps realized and unrealized evidence separate;
- deterministic handling of side, unsupported currency conversion, non-unit leverage, stale or missing prices and reconciliation gaps;
- focused contract, tenant-isolation, provenance, freshness, transport, API and UI tests;
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
- public browser or exchange market-data access;
- automatic currency conversion without an attributable source;
- derivatives funding or liquidation valuation in v1;
- order submission, credential brokering, live capital or P14;
- modifying frozen thresholds, Phase 6 evidence or protected final-holdout policy.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T23:19:04+02:00
head: bae1bc9e0ab1d43601abb1984c9baa26e4c40175
branch: feat/portal-pi02-authoritative-valuation-20260724
pr: 267
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - ai_platform/portal/valuation/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/lib/valuation.ts
  - ai_platform/portal/web/e2e/valuation.spec.ts
  - tests/ai_platform/portal/valuation/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi02-authoritative-valuation.md
proven:
  - develop head 5afb797f389bd4eb90cf189804cba26d8249ba07 durably closes PI-04 and provided the clean base for PI-02.
  - PR 267 adds versioned runtime mark, source-result and immutable valuation snapshot contracts without changing PI-01 reconciliation records.
  - The dedicated private source adapter validates HTTP or HTTPS endpoints, rejects embedded credentials and sensitive payload keys, bounds timeout to five seconds by default and bounds responses to one MiB by default.
  - Source envelopes fail closed on protocol, authentication, timeout, availability or tenant, bot and runtime scope mismatch.
  - Valuation requires a current reconciled position, an exact source-position and pair or side match, a fresh positive mark, unit leverage and quote currency equal to the bot capital currency.
  - Unsupported or insufficient evidence produces STALE, SOURCE_UNAVAILABLE or UNPRICED with no numeric current valuation and no fixture or public-price fallback in API mode.
  - mark-to-entry-v1 computes deterministic gross unrealized PNL for long and short positions while realized PNL remains separate closed-trade evidence.
  - GET /v1/valuations requires BOT_READ, is tenant-scoped server-side and returns no private endpoint, authorization header or credential.
  - PNL and Performance displays realized performance and open-position valuation as independent evidence tables with source identity and availability state.
  - Focused math, provenance, tenant-isolation, transport-boundary, sensitive-data, API and browser tests pass.
  - Temporary patch, diagnostic, autofix and documentation-sync workflows and scripts were removed from the final candidate.
  - AI Platform CI 1142, Portal Web CI 206, Portal Universal E2E 211, zizmor 1259 and Freqtrade CI 1329 passed on head bae1bc9e0ab1d43601abb1984c9baa26e4c40175; Freqtrade CI 1328 was cancelled only because the later checkpoint commit superseded it.
  - All PR review threads are resolved and outdated.
derived:
  - PI-02 satisfies its bounded repository-side acceptance without selecting a public price provider or adding currency conversion, execution or live-capital authority.
  - Exact-runtime mark provenance is the narrowest source consistent with PI-01 runtime attribution and fail-closed portal architecture.
unknown: []
conflicts: []
first_failure:
  marker: RESOLVED
  evidence: Full pytest initially found duplicate test module basenames. Temporary package names then conflicted with production modules under mypy. Unique valuation test filenames resolved collection and typing; Ruff import, format and C901 findings were fixed without changing valuation semantics.
rejected_hypotheses:
  - Select an unaffiliated public price API without an owner decision.
  - Reuse fixture prices in API mode.
  - Treat stale, cross-currency or leveraged evidence as a numeric current valuation.
  - Recompute realized PNL from open-position marks.
  - Mutate PI-01 operational records to carry PI-02-only price semantics.
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
  - tests/ai_platform/portal/valuation/test_valuation_runtime.py
  - tests/ai_platform/portal/valuation/test_valuation_runtime_api.py
validation:
  - command: AI Platform CI 30126369470 / run 1142
    result: PASS
    evidence: Tests, compile, Ruff, Ruff format, codespell and contract validation passed on head bae1bc9e0ab1d43601abb1984c9baa26e4c40175.
  - command: Portal Web CI 30126369498 / run 206
    result: PASS
    evidence: Typecheck, lint, production build and Chromium browser E2E passed on the current head.
  - command: Portal Universal E2E 30126369510 / run 211
    result: PASS
    evidence: Backend universal scenario and critical Chromium path passed on the current head.
  - command: GitHub Actions Security Analysis with zizmor 30126369503 / run 1259
    result: PASS
    evidence: Required workflow security analysis passed on the current head.
  - command: Freqtrade CI 30126369494 / run 1329
    result: PASS
    evidence: Pre-commit, documentation, full multi-platform core matrix, coverage, smoke checks, Ruff, formatter, mypy and CI gate passed on the current head.
blockers: []
next_action: After durable merge evidence exists on develop, select the next authorized package from current repository and open-PR state.
```
