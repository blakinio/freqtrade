---
task_id: FTAI-20260728-portal-bmw02-command-intent
status: implementing
branch: feat/portal-bmw02-command-intent-v3
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
depends_on:
  - FTAI-20260728-portal-bmw01-catalog-builder
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
- transport retries use a stable business digest and return the original command outcome;
- conflicting reuse of an idempotency key records conflict evidence without persisting the attempted command.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T15:10:00+02:00
branch: feat/portal-bmw02-command-intent-v3
base_merge: 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5
status: implementing
proven:
  - BMW-01 merged as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BM-03 persists command intent and evidence without invoking a runtime adapter.
  - Existing desired-state BFF mutates the legacy bot resource and does not bind an authoritative runtime revision.
derived:
  - A separate lifecycle-intent facade can safely expose BM-03 without accepting browser runtime authority.
unknown:
  - Exact-head CI results.
conflicts: []
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Existing lifecycle controls posted to /api/bots/{botId}/desired-state rather than canonical BM-03.
validation:
  - command: exact-head standard CI
    result: NOT_RUN
blockers:
  - PI-08 remains required before any accepted command can be submitted to a private runtime and moved to pending reconciliation.
next_action: Apply shared composition and stable-digest patches, run exact-head CI, audit and merge.
```
