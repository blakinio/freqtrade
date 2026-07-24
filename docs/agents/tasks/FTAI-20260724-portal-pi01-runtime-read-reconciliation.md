---
task_id: FTAI-20260724-portal-pi01-runtime-read-reconciliation
status: active
branch: feat/portal-pi01-runtime-read-reconciliation-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: 234
owned_paths:
  - ai_platform/portal/execution/**
  - ai_platform/portal/operations/**
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/execution/**
  - tests/ai_platform/portal/operations/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260724-portal-pi01-runtime-read-reconciliation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# PI-01 — Private Runtime Read and Reconciliation

## Goal

Implement authoritative, read-only private runtime ingestion for open positions, orders and trades, preserving tenant, bot, runtime, source identity, timestamps, freshness and reconciliation state through the existing portal operational mirror.

## Deliverables

- versioned private runtime collector/read-batch interface with bounded timeout, retry and pagination semantics;
- `FreqtradeExecutionAdapter` read implementation that fails closed outside complete authoritative reads;
- idempotent operational mirror ingestion and reconciliation for positions, orders and trades;
- explicit `SYNCED`, `PENDING`, `SOURCE_UNAVAILABLE` and `MISMATCH` plus current/stale/partial representation;
- tenant/runtime isolation, duplicate, timeout, authentication, pagination, partial-page, stale-source, redaction and API tests;
- truthful portal documentation without PI-02 valuation claims.

## Non-negotiable boundaries

- Read-only: no `submit_approved_intent`, order submission, live trading or P14 activation.
- No public/browser Freqtrade path, private endpoint serialization or credential exposure.
- No exchange credential retrieval, secret brokering, withdrawal permission or raw secret-bearing config.
- No fabricated source data or prices in API mode.
- No Phase 6, frozen-threshold, protected-holdout, P11, P13 or P14 changes.
- Shared `ExecutionAdapter` v1 remains unchanged; PI-01 uses a separately versioned private collector because v1 cannot represent batch completeness/freshness/reconciliation metadata.

## Acceptance criteria

1. Complete private reads populate the canonical operational mirror idempotently for one tenant/bot/runtime.
2. Missing runtime, authentication failure, timeout, partial pagination and stale source never produce false `SYNCED` or current evidence.
3. Cross-tenant and cross-runtime reads fail closed.
4. Source identities and source/observed/reconciled timestamps are preserved.
5. Browser/BFF responses contain no runtime address, credentials or secret fields.
6. Existing operational mirror remains the only portal-facing boundary.
7. Required targeted and repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T09:05:00+02:00
head: 117387233d66dba018fc3d8500be37ccb14cd109
branch: feat/portal-pi01-runtime-read-reconciliation-20260724
pr: 234
status: validating
context_routes:
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - ai_platform/portal/execution/**
  - ai_platform/portal/operations/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/positions/page.tsx
  - ai_platform/portal/web/app/orders/page.tsx
  - ai_platform/portal/web/app/trades/page.tsx
  - ai_platform/portal/web/lib/runtime-evidence.ts
  - tests/ai_platform/portal/execution/**
  - tests/ai_platform/portal/operations/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260724-portal-pi01-runtime-read-reconciliation.md
proven:
  - develop preflight head was 6296a4472d80e32d1f67dcfe258c70f1ce3f4f1e and PR 233 was merged.
  - Open PR 109 was documentation-only and did not overlap PI-01 ownership.
  - Shared ExecutionAdapter v1 remains unchanged; PI-01 uses a separately versioned private collector/read-batch interface.
  - Private runtime reads preserve tenant, bot, runtime, source identity and source/observed/reconciled timestamps.
  - Collector behavior is bounded for timeout, retry, pagination, body size, duplicate handling, partial pages and stale source.
  - Reconciliation is idempotent and represents SYNCED, PENDING, SOURCE_UNAVAILABLE and MISMATCH explicitly.
  - The operational mirror remains the only portal-facing read boundary through GET /v1/runtime-evidence.
  - Browser serialization excludes private runtime endpoints, authorization headers and credentials.
  - submit_approved_intent remains fail-closed with ORDER_SUBMISSION_NOT_IMPLEMENTED.
  - Targeted AI Platform tests reached 487 passed and 1 skipped before final documentation refresh.
  - Portal Web CI and Portal Universal E2E passed after the runtime-evidence UI integration fix.
derived:
  - Complete current synced batches may pass through ExecutionAdapter v1; stale, partial, unavailable or mismatched batches fail closed there.
  - Degraded evidence may remain visible only with explicit freshness and reconciliation metadata in the operational mirror.
unknown: []
conflicts: []
first_failure:
  marker: resolved
  evidence: Initial OpenAPI expectation, response-envelope and Ruff formatting failures were fixed; no unresolved implementation failure is known.
rejected_hypotheses:
  - Browser clients require direct Freqtrade access; rejected because the operational mirror is the sole portal-facing boundary.
  - ExecutionAdapter v1 must be incompatibly changed; rejected because a versioned private collector carries batch metadata.
changed_paths:
  - ai_platform/portal/execution/adapter.py
  - ai_platform/portal/execution/errors.py
  - ai_platform/portal/execution/private_read.py
  - ai_platform/portal/operations/models.py
  - ai_platform/portal/operations/repository.py
  - ai_platform/portal/operations/schema.py
  - ai_platform/portal/operations/service.py
  - ai_platform/portal/operations/migrations/0002_private_runtime_reconciliation.sql
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/lib/runtime-evidence.ts
  - ai_platform/portal/web/app/positions/page.tsx
  - ai_platform/portal/web/app/orders/page.tsx
  - ai_platform/portal/web/app/trades/page.tsx
  - tests/ai_platform/portal/execution/test_private_read.py
  - tests/ai_platform/portal/operations/test_private_runtime_reconciliation.py
  - tests/ai_platform/portal/operations/test_private_runtime_migration.py
  - tests/ai_platform/portal/execution/test_adapter.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/tasks/FTAI-20260724-portal-pi01-runtime-read-reconciliation.md
validation:
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
    result: PASS
    evidence: 487 passed and 1 skipped on PR 234 before final documentation refresh.
  - command: ruff check ai_platform tests/ai_platform
    result: PASS
    evidence: Ruff lint passed after the private collector refactor.
  - command: ruff format --check ai_platform tests/ai_platform
    result: PASS
    evidence: Exact Ruff formatter output was applied to all reported files.
  - command: Portal Web CI
    result: PASS
    evidence: Typecheck, lint, build and browser tests passed after runtime-evidence page integration.
  - command: Portal Universal E2E
    result: PASS
    evidence: Universal E2E passed after the strict-locator correction.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260724-portal-pi01-runtime-read-reconciliation.md --require-checkpoint
    result: PASS
    evidence: Executed by the current branch-scoped validation job before commit.
blockers: []
next_action: Restore the standard AI Platform workflow, complete required repository CI, resolve review findings and merge PR 234.
```
