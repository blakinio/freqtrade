---
task_id: FTAI-20260728-portal-bmw02-command-intent
status: validating
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
- transport retries use a stable business digest and return the original command outcome;
- conflicting reuse of an idempotency key records conflict evidence without persisting the attempted command.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T15:18:00+02:00
branch: feat/portal-bmw02-command-intent-v3
pr: 632
base_merge: 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5
status: validating
proven:
  - BMW-01 merged as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BM-03 persists command intent and evidence without invoking a runtime adapter.
  - Shared composition, stable business digest, config-revision binding and OpenAPI registration were applied and formatted.
  - The integration workflow removed itself before this connector-authored validation head.
derived:
  - A separate lifecycle-intent facade safely exposes BM-03 without accepting browser runtime authority.
unknown:
  - Exact-head Portal Web, Universal E2E, AI Platform, Freqtrade and security CI results.
conflicts: []
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Existing lifecycle controls posted to /api/bots/{botId}/desired-state rather than canonical BM-03.
validation:
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: This connector-authored commit creates the authoritative validation head.
blockers:
  - PI-08 remains required before any accepted command can be submitted to a private runtime and moved to pending reconciliation.
next_action: Run exact-head CI, repair only BMW-02 findings, audit and merge.
```
