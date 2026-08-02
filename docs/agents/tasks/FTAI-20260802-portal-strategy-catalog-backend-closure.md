---
task_id: FTAI-20260802-portal-strategy-catalog-backend-closure
status: ready
branch: unassigned
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260802-portal-end-to-end-completeness-audit
owned_paths:
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/app/api/strategy-catalog/
  - ai_platform/portal/control_plane/
  - ai_platform/portal/strategy_catalog/
  - tests/ai_platform/portal/strategy_catalog/
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
  - docs/agents/tasks/FTAI-20260802-portal-strategy-catalog-backend-closure.md
---

# Portal Strategy Catalog backend closure

## Proven gap

The browser page and same-origin BFF are present, but API mode calls:

- `GET /v1/strategy-catalog`;
- `GET /v1/strategy-catalog/{strategy_version}`;
- `POST /v1/strategy-catalog/{strategy_version}/rollback`.

No matching FastAPI producer route exists on the audited product head `0e7825bf860cd8011e1bd9207fcb0765baf8d52a`. Existing browser tests can pass in explicit fixture mode, so they do not prove the production API vertical slice. The canonical delivery document currently labels the surface `integrated`; that claim is not supported for API mode.

## Objective

Complete the Strategy Catalog vertical slice from persisted immutable server state through authorization, API contracts, same-origin BFF and real API-mode browser behavior.

## Required scope

- define or reuse one canonical Python contract matching the existing public TypeScript v2 contract;
- provide tenant-scoped list and detail routes;
- provide an idempotent, authorization-gated dry-run rollback command with append-only audit evidence;
- persist strategy versions, approvals, deployments, rollback targets and provenance, or bind them to an existing authoritative repository without fixture substitution;
- keep deployment and rollback authority limited to the currently authorized non-live modes;
- return truthful empty, denied, conflict, stale and unavailable states;
- update `UI_DELIVERY_STATUS.md` only after API-mode evidence exists;
- remove contract drift between Python and TypeScript through a deterministic test.

## Acceptance inventory

- persistence and migration or an explicitly proven existing source;
- backend domain and authorization tests;
- exact list/detail/rollback FastAPI routes;
- BFF read and mutation forwarding with CSRF/session enforcement;
- fixture, empty, stale, denied, not-found, conflict and success browser states;
- API-mode integration test using the real backend producer;
- real Chromium critical journey without request interception for the successful catalog read;
- rollback evidence proves acceptance separately from execution;
- no direct browser access to Freqtrade or private services;
- no credentials, withdrawals, live trading or live-capital authorization.

## Handover

```yaml
checkpoint_version: 3
status: ready
proven:
  - frontend and BFF consumer paths exist
  - API mode references /v1/strategy-catalog contracts
  - no matching backend route was found in 92 statically detected FastAPI routes
  - fixture-mode E2E exists and cannot prove the missing producer
next_action: claim the task, create a dedicated branch and implement the backend-first vertical slice with API-mode E2E
blockers: []
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
