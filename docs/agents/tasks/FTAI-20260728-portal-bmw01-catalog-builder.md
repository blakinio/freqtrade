---
task_id: FTAI-20260728-portal-bmw01-catalog-builder
status: validating
branch: feat/portal-bmw01-catalog-builder-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
depends_on:
  - FTAI-20260728-portal-bm-default-catalog
related_pr: 615
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

## Goal

Replace browser-entered strategy, model, risk and runtime identifiers with server-owned catalog selections and finalize one immutable BM-02 dry-run configuration through the same-origin BFF.

## Delivered

- capability-gated exact catalog snapshot endpoint;
- server-only catalog loader with explicit fixture/API modes;
- catalog-driven browser selects instead of arbitrary version text fields;
- bounded spot-long, market-entry and fixed-quote policy composition;
- same-origin CSRF/session protected create-draft, preview and finalize sequence;
- explicit `runtime_submission_performed=false` result;
- fail-closed unavailable catalog state;
- API, capability, secret-exclusion and Playwright coverage.

## Safety boundary

BMW-01 finalizes configuration evidence only. It does not create a private runtime, resolve credentials, call an exchange, submit to Freqtrade, place an order or authorize live capital. The opaque `simulated-dry-run` connection reference contains no credential material.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T13:46:00+02:00
branch: feat/portal-bmw01-catalog-builder-v1
pr: 615
status: validating
base_merge: 97b74d210123f2d4d45883822de7e40f545d2c16
head_parent: 21036279898d57df25e0dc0101ed8e35458ae848
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
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
proven:
  - The previous create form posted the legacy /api/bots contract and exposed browser-editable internal versions.
  - BM-01/BM-02 canonical services and routers are registered in the private control plane.
  - The approved starter catalog merged as 97b74d210123f2d4d45883822de7e40f545d2c16.
  - Builder finalization creates immutable configuration evidence and does not submit runtime execution.
  - OpenAPI registration workflow completed and removed itself before this exact-head validation commit.
derived:
  - A catalog snapshot read plus BFF orchestration is sufficient to complete BMW-01 without PI-07 or PI-08.
unknown:
  - Exact-head Portal Web, E2E, AI Platform, Freqtrade and security CI results.
conflicts: []
first_failure:
  marker: BROWSER_TYPED_INTERNAL_VERSIONS
  evidence: Existing create-bot-form rendered strategy_version, model_version, risk_policy_version and runtime_version as editable text inputs.
rejected_hypotheses:
  - Continue posting the legacy /api/bots resource and label it BM-02 finalization.
  - Claim finalized configuration started or reconciled a runtime.
  - Expose exchange credentials or credential references to the browser.
changed_paths:
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
validation:
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: This connector-authored commit creates the authoritative validation head.
blockers: []
next_action: Run exact-head CI, repair only BMW-01 findings, audit and merge.
```
