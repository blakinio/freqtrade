---
task_id: FTAI-20260728-portal-bmw01-catalog-builder
status: validating
branch: feat/portal-bmw01-catalog-builder-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 625
owned_paths:
  - ai_platform/portal/bot_catalog/service.py
  - ai_platform/portal/bot_catalog/router.py
  - ai_platform/portal/web/app/api/bot-management/builder/route.ts
  - ai_platform/portal/web/app/bots/new/page.tsx
  - ai_platform/portal/web/components/bot-builder/create-bot-configuration-form.tsx
  - ai_platform/portal/web/lib/bot-management-api.ts
  - ai_platform/portal/web/lib/bot-management-contracts.ts
  - ai_platform/portal/web/e2e/journeys/portal.journeys.ts
  - ai_platform/portal/web/e2e/specs/bots/create-bot.spec.ts
  - tests/ai_platform/portal/bot_catalog/test_snapshot_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw01-catalog-builder.md
---

# BMW-01 catalog-driven bot configuration builder

## Delivered

- authorized exact catalog snapshot read;
- browser selects only active server-owned template, strategy, model, profile, runtime and risk versions;
- CSRF/session-protected create-draft, preview and finalize orchestration;
- immutable dry-run configuration summary with `runtime_submission_performed=false`;
- fail-closed catalog unavailable behavior;
- API, OpenAPI, secret-boundary and Playwright coverage.

## Safety boundary

No credential resolution, exchange call, private runtime creation, Freqtrade submission, order placement, reconciliation claim or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T14:36:00+02:00
branch: feat/portal-bmw01-catalog-builder-v2
pr: 625
status: validating
base_head: d86e2a33a1ac155f794782da23bb27b2e401b2fe
proven:
  - Superseded head 54826561312a019732d85310a6c0db6a1ae8dcc3 passed Portal Web, Universal E2E, AI Platform, Freqtrade final gate and security.
  - PR 615 was closed without merge because squash ancestry duplicated the already merged catalog package.
  - PR 625 is reconstructed from current develop and contains BMW-01-only paths.
unknown:
  - Exact-head CI results for the clean branch.
conflicts: []
first_failure:
  marker: SQUASH_ANCESTRY_DUPLICATION
  evidence: Final audit of PR 615 showed previously merged catalog files in its diff; clean reconstruction was required.
validation:
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: This checkpoint creates the clean authoritative validation head.
blockers: []
next_action: Run exact-head CI, audit the clean diff and merge.
```
