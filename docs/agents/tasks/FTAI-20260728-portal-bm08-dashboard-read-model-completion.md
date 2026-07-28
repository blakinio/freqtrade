---
task_id: FTAI-20260728-portal-bm08-dashboard-read-model-completion
status: completed
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
  - ai_platform/portal/web/lib/dashboard-api.ts
  - ai_platform/portal/web/app/page.tsx
  - ai_platform/portal/web/e2e/specs/dashboard/dashboard-read-model.spec.ts
  - tests/ai_platform/portal/dashboard/test_dashboard_service.py
  - tests/ai_platform/portal/dashboard/test_router.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm08-dashboard-read-model-completion.md
---

# BM-08 dashboard read-model completion

## Goal

Replace the browser-composed dashboard snapshot with one tenant-scoped, server-owned read model that reports bot-management evidence, bounded filters and truthful source freshness without claiming unavailable runtime, valuation, model or risk evidence.

## Delivered

- versioned `/v1/bot-management/dashboard/search` public read model;
- tenant-scoped and permission-gated bot summaries;
- bounded deterministic filters and cursor pagination;
- explicit `CURRENT`, `ATTENTION`, `DEGRADED`, `STALE`, `PARTIAL`, `UNAVAILABLE` and `NOT_APPLICABLE` evidence states;
- authoritative runtime, valuation, model and risk aggregation without browser-side health inference;
- dashboard UI consuming only the server-owned read model;
- service, router, OpenAPI, tenant-isolation, secret-exclusion and Playwright coverage;
- no persistence migration, credential resolution, runtime submission or live-capital activation.

## Safety boundary

BM-08 is read-only. BM-07 remains blocked until PI-08 is complete. Missing evidence is represented as unavailable or partial and is never inferred as healthy.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T21:45:00+02:00
branch: feat/portal-bm08-dashboard-read-model
pr: 651
status: completed
base_head: 66e119db9a009cef6a51303a0f054012362fc98b
validated_head: d9c395e0e871c3c1cf711a857ac9ba84265b7a20
merge_commit: 8cabed2dd116da3e5ac2156650d0b69803667fa6
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
proven:
  - BMW-03 is merged and checkpointed through PR 649.
  - BM-08 merged through PR 651 as 8cabed2dd116da3e5ac2156650d0b69803667fa6.
  - The browser dashboard no longer derives runtime health from bot state or hard-codes model and risk health.
  - Runtime, valuation, model and risk evidence expose explicit source states and observation times.
  - Empty source collections remain unavailable or not applicable rather than healthy.
  - Dashboard cursors are bound to tenant, filters, page size and sort direction.
  - Public payloads and OpenAPI exclude credential and private-runtime fields.
  - The merged diff contains no temporary diagnostic workflows.
derived:
  - BM-09 cannot provide the final dry-run execution journey until PI-07, PI-08 and BM-07 are complete.
  - A bounded pre-execution E2E closure may prove all currently available read-only/configuration paths, but must not be labeled final BM-09 completion.
unknown:
  - Target secret backend and credential-provider decision required for PI-07.
  - PI-08 private dry-run submission acceptance environment and runtime binding.
conflicts: []
first_failure:
  marker: CLIENT_COMPOSED_DASHBOARD_TRUTH
  evidence: The prior browser dashboard labeled a bot-list-derived view as a live control-plane snapshot and could not distinguish absent authoritative sources.
rejected_hypotheses:
  - Treat RUNNING bot state as proof that runtime evidence is current.
  - Treat an empty risk decision list as normal risk health.
  - Treat absent model telemetry as healthy.
  - Add browser calls to private Freqtrade or valuation endpoints.
changed_paths:
  - ai_platform/portal/dashboard/__init__.py
  - ai_platform/portal/dashboard/schema.py
  - ai_platform/portal/dashboard/service.py
  - ai_platform/portal/dashboard/router.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/lib/dashboard-api.ts
  - ai_platform/portal/web/app/page.tsx
  - ai_platform/portal/web/e2e/specs/dashboard/dashboard-read-model.spec.ts
  - tests/ai_platform/portal/dashboard/test_dashboard_service.py
  - tests/ai_platform/portal/dashboard/test_router.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm08-dashboard-read-model-completion.md
validation:
  - command: AI Platform CI run 30391613818
    result: PASS
  - command: Portal Web CI run 30391613571
    result: PASS
  - command: Portal Universal E2E run 30391613808
    result: PASS
  - command: Freqtrade CI run 30391613525
    result: PASS
  - command: GitHub Actions Security Analysis run 30391613710
    result: PASS
blockers: []
next_action: Start PI-07 only after freezing the secret backend/provider decision; do not activate BM-07 or claim final BM-09 completion before PI-08.
```
