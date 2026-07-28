---
task_id: FTAI-20260728-portal-bmw02-command-intent
status: repairing
branch: feat/portal-bmw02-command-intent-v3
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
depends_on:
  - FTAI-20260728-portal-bmw01-catalog-builder
related_pr: 632
owned_paths:
  - ai_platform/portal/bot_operations/intent_service.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/bot_operations/service.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/api/bot-management/commands/lifecycle-intents/route.ts
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/lib/bot-command-contracts.ts
  - ai_platform/portal/web/e2e/specs/bots/lifecycle-intent.spec.ts
  - tests/ai_platform/portal/bot_operations/test_intent_service.py
  - tests/ai_platform/portal/bot_operations/test_intent_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw02-command-intent.md
---

# BMW-02 lifecycle command intent

## Goal

Replace the legacy browser desired-state mutation with a same-origin lifecycle command-intent flow over canonical BM-03.

## Delivered boundary

- browser request contains only bot ID, lifecycle action, expected configuration revision and idempotency key;
- tenant, actor and correlation come from trusted session context;
- environment, runtime ID and runtime revision come only from an authoritative provider;
- the default provider is unavailable and fails closed before command persistence;
- an exact current runtime may persist `ACCEPTED`, `REJECTED` or `BLOCKED` BM-03 evidence;
- no execution adapter, Freqtrade call, exchange call, order submission or reconciliation transition is invoked;
- every public result fixes `execution_submission_performed=false`;
- transport retries are resolved by the BMW-02 facade without weakening BM-03 command identity;
- conflicting reuse of an idempotency key records conflict evidence when authoritative runtime context is available and never persists the attempted command.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T15:40:00+02:00
branch: feat/portal-bmw02-command-intent-v3
pr: 632
base_merge: 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5
status: repairing
proven:
  - BMW-01 merged as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BM-03 persists command intent and evidence without invoking a runtime adapter.
  - Shared composition, config-revision binding and OpenAPI registration were applied and formatted.
  - Focused BMW-02 tests passed 7 of 7 after breaking the composition import cycle and aligning the versioned API assertion.
  - Full tests/ai_platform isolated one regression: a global normalized digest weakened existing BM-03 conflict semantics.
derived:
  - Transport replay must be handled in the BMW-02 facade by inspecting existing command business identity while BM-03 retains its strict canonical command digest.
unknown:
  - Exact-head Portal Web, Universal E2E, AI Platform, Freqtrade and security CI results after the scoped repair.
conflicts:
  - marker: BM03_IDEMPOTENCY_SEMANTICS
    resolution: Restore the canonical full-command digest and add a trusted facade lookup for browser transport replay.
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Existing lifecycle controls posted to /api/bots/{botId}/desired-state rather than canonical BM-03.
validation:
  - command: pytest -q tests/ai_platform
    result: 928 passed, 50 skipped, 1 failed before repair
    evidence: Only test_conflicting_idempotency_key_is_rejected_and_recorded failed because the global digest treated a distinct command as replay.
blockers:
  - PI-08 remains required before any accepted command can be submitted to a private runtime and moved to pending reconciliation.
next_action: Apply the scoped repair, remove temporary workflow, run exact-head CI, audit and merge.
```
