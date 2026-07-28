---
task_id: FTAI-20260728-portal-bmw01-catalog-builder
status: active
branch: feat/portal-bmw01-catalog-builder-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
depends_on:
  - FTAI-20260728-portal-bm-default-catalog
owned_paths:
  - ai_platform/portal/bot_catalog/service.py
  - ai_platform/portal/bot_catalog/router.py
  - ai_platform/portal/web/app/api/bot-management/builder/route.ts
  - ai_platform/portal/web/app/bots/new/page.tsx
  - ai_platform/portal/web/components/bot-builder/create-bot-configuration-form.tsx
  - ai_platform/portal/web/lib/bot-management-api.ts
  - ai_platform/portal/web/lib/bot-management-contracts.ts
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
updated_at: 2026-07-28T13:34:00+02:00
branch: feat/portal-bmw01-catalog-builder-v1
pr: null
status: active
base_head: 418f9f22d07739288c7d6941624d548e2e9b52be
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
  - ai_platform/portal/web/e2e/specs/bots/create-bot.spec.ts
  - tests/ai_platform/portal/bot_catalog/test_snapshot_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw01-catalog-builder.md
proven:
  - The previous create form posted the legacy /api/bots contract and exposed browser-editable internal versions.
  - BM-01/BM-02 canonical services and routers are registered in the private control plane.
  - The approved starter catalog package is the exact base of this stacked branch.
  - Builder finalization creates immutable configuration evidence and does not submit runtime execution.
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
  - ai_platform/portal/web/e2e/specs/bots/create-bot.spec.ts
  - tests/ai_platform/portal/bot_catalog/test_snapshot_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw01-catalog-builder.md
validation:
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: PR will be opened after the prerequisite catalog merge.
blockers:
  - PR 608 must merge before BMW-01 can be reviewed against develop as a clean package.
next_action: Complete prerequisite merge, patch the exact OpenAPI path set, run exact-head CI and merge BMW-01.
```
