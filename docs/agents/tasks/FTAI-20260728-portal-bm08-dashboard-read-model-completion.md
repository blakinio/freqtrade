---
task_id: FTAI-20260728-portal-bm08-dashboard-read-model-completion
status: active
branch: feat/portal-bm08-dashboard-read-model
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - ai_platform/portal/dashboard/__init__.py
  - ai_platform/portal/dashboard/schema.py
  - ai_platform/portal/dashboard/service.py
  - ai_platform/portal/dashboard/router.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - ai_platform/portal/web/app/page.tsx
  - ai_platform/portal/web/e2e/specs/dashboard/dashboard-read-model.spec.ts
  - tests/ai_platform/portal/dashboard/test_service.py
  - tests/ai_platform/portal/dashboard/test_router.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm08-dashboard-read-model-completion.md
---

# BM-08 dashboard read-model completion

## Goal

Replace the browser-composed dashboard snapshot with one tenant-scoped, server-owned read model that reports bot-management evidence, bounded filters and truthful source freshness without claiming unavailable runtime, valuation, model or risk evidence.

## Dependencies

- BM-00 contracts;
- BM-01 through BM-06 product surfaces;
- BMW-01 through BMW-03 web convergence;
- existing operational mirror, valuation and inference-telemetry read services.

## Non-goals

- no credential resolution or secret exposure;
- no direct browser-to-Freqtrade communication;
- no runtime submission, order placement or live-capital action;
- no BM-07 position/order command activation before PI-08;
- no claim that unavailable authoritative providers are healthy;
- no new persistence or migration head.

## Acceptance criteria

1. A dedicated bot-management dashboard router returns a versioned public schema.
2. Results are tenant-scoped and require server-side bot read permission.
3. Existing bounded pagination and deterministic filters are reused.
4. Runtime, valuation, model and risk evidence expose explicit current, stale, partial or unavailable states.
5. Bot summaries include authoritative observed/desired state, counts and reconciled analytics only.
6. Browser dashboard consumes the server response and does not reconstruct health from `/v1/bots`.
7. Empty, unavailable and stale states are covered by service, API and browser tests.
8. Public payloads and OpenAPI contain no secret fields or private runtime endpoints.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T20:32:00+02:00
branch: feat/portal-bm08-dashboard-read-model
status: active
base_head: f2431821f29878f3308469e035cba0f70d933b05
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
proven:
  - BMW-03 is merged and checkpointed through PR 649.
  - The current web dashboard derives runtime health from bot state and hard-codes model and risk health as unknown.
  - Operational mirror records already carry freshness and reconciliation states.
  - Valuation snapshots already distinguish current, stale, source-unavailable and unpriced evidence.
  - Model health records already carry drift and telemetry-source availability.
  - The frozen bot-management pagination and filter contracts are available.
derived:
  - BM-08 can be implemented as a read-only aggregation layer without new persistence.
  - Unknown or missing evidence must remain unavailable rather than being inferred as healthy.
unknown:
  - Exact final source-state mapping until focused tests freeze the public dashboard contract.
conflicts: []
first_failure:
  marker: CLIENT_COMPOSED_DASHBOARD_TRUTH
  evidence: The browser currently labels a bot-list-derived view as a live control-plane snapshot and cannot distinguish absent authoritative model, risk, runtime or valuation sources.
rejected_hypotheses:
  - Treat RUNNING bot state as proof that runtime evidence is current.
  - Treat an empty risk decision list as normal risk health.
  - Treat absent model telemetry as healthy.
  - Add browser calls to private Freqtrade or valuation endpoints.
validation: []
blockers: []
next_action: Freeze the public dashboard schema and implement the tenant-scoped aggregation service and router.
```
