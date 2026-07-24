---
task_id: FTAI-20260724-portal-pi01-runtime-read-reconciliation
status: active
branch: feat/portal-pi01-runtime-read-reconciliation-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: null
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
updated_at: 2026-07-24T07:38:00+02:00
head: 6296a4472d80e32d1f67dcfe258c70f1ce3f4f1e
branch: feat/portal-pi01-runtime-read-reconciliation-20260724
pr: null
status: active
context_routes:
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
proven:
  - develop is 6296a4472d80e32d1f67dcfe258c70f1ce3f4f1e and PR 233 is merged.
  - Open PR 109 is documentation/design-only and does not overlap PI-01.
  - No open PR owns execution or operational reconciliation paths.
  - ExecutionAdapter v1 read methods return tuples and cannot encode completeness, freshness or source availability.
  - FreqtradeExecutionAdapter read methods currently fail closed with query-not-implemented reason codes.
  - The operational mirror stores tenant, bot, runtime and source records but lacks observation/freshness/reconciliation metadata and a canonical trade mirror.
  - ReconciliationStatus already defines SYNCED, PENDING, SOURCE_UNAVAILABLE and MISMATCH.
  - PR 233 recorded passing AI Platform CI, Freqtrade CI and zizmor for the current develop content.
derived:
  - A versioned private collector/read-batch interface avoids an incompatible shared-contract change while preserving ExecutionAdapter v1.
  - Portal-facing reads must remain operational-mirror reads and must serialize status metadata without private transport details.
unknown:
  - Exact Freqtrade private transport payload variants must be normalized behind deterministic fake-covered parsing.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation or validation failure has occurred yet.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-portal-pi01-runtime-read-reconciliation.md
validation: []
blockers: []
next_action: Implement the versioned private runtime collector models and deterministic transport/error mapping in ai_platform/portal/execution/.
```
