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
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/api/bot-management/commands/lifecycle-intents/route.ts
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/lib/bot-command-contracts.ts
  - ai_platform/portal/web/e2e/specs/bots/lifecycle-intent.spec.ts
  - ai_platform/portal/web/e2e/specs/bots/operations.spec.ts
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
- transport retries are resolved by a facade-scoped lookup over append-only BM-03 history without changing BM-03 command identity;
- conflicting reuse of an idempotency key never persists the attempted command.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T16:05:00+02:00
branch: feat/portal-bmw02-command-intent-v3
pr: 632
base_merge: 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5
validation_parent: 30a9ae1d05e62852c330ae4c9e008980e0313ad3
status: validating
proven:
  - BMW-01 merged as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BM-03 retains its strict canonical full-command digest and append-only conflict evidence.
  - BMW-02 transport replay uses a separate read-only lookup and returns the original command outcome only for the same actor, capability, tenant, bot, configuration revision and lifecycle action.
  - The browser cannot supply tenant, actor, environment, runtime ID or runtime revision.
  - Focused BMW-02 domain and API tests passed 7 of 7.
  - On validation parent 30a9ae1d05e62852c330ae4c9e008980e0313ad3, AI Platform CI, Portal Web CI, Portal Universal E2E and security analysis succeeded.
  - Python 3.11, 3.13 and 3.14 Freqtrade jobs succeeded on the validation parent; Python 3.12 coverage was still running when this terminal checkpoint head was created.
derived:
  - The terminal connector-authored head contains no functional change after the successful web, E2E, AI and security runs.
unknown:
  - Exact-head terminal workflow results for this checkpoint commit.
conflicts:
  - marker: BM03_IDEMPOTENCY_SEMANTICS
    resolution: Restore BM-03 unchanged and scope transport replay to the BMW-02 facade.
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Existing lifecycle controls posted to /api/bots/{botId}/desired-state rather than canonical BM-03.
validation:
  - command: focused BMW-02 tests
    result: 7 passed
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: This connector-authored commit creates the terminal validation head.
blockers:
  - PI-08 remains required before any accepted command can be submitted to a private runtime and moved to pending reconciliation.
next_action: Run exact-head CI, audit PR #632 and squash merge if all required workflows succeed.
```
