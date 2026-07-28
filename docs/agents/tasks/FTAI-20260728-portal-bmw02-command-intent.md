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
required_reads:
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
search_first:
  - ai_platform/portal/bot_operations
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
optional_reads:
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
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

Replace the legacy browser desired-state mutation with a same-origin lifecycle command-intent flow over canonical BM-03 without adding runtime execution authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T16:20:00+02:00
head: d5063cdc3a5307de8d35df24f4cb2a33f3fa89d0
branch: feat/portal-bmw02-command-intent-v3
pr: 632
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/agents/tasks/FTAI-20260728-portal-bmw02-command-intent.md
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
proven:
  - BMW-01 merged as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BM-03 strict command digest and append-only conflict evidence remain unchanged.
  - Browser payload excludes tenant, actor, environment, runtime ID and runtime revision.
  - Default runtime provider fails closed before command persistence.
  - Transport replay is scoped to a read-only BMW-02 lookup over BM-03 history.
  - Focused BMW-02 domain and API tests passed 7 of 7.
  - Exact-head AI Platform CI 30366588200 succeeded.
  - Exact-head Universal E2E 30366588479 succeeded.
  - Exact-head security analysis 30366588292 succeeded.
  - Exact-head Portal Web typecheck, lint and production build succeeded before Chromium regression.
  - Exact-head Freqtrade pre-commit, documentation and Python 3.11, 3.13 and 3.14 jobs succeeded.
derived:
  - Remaining validation is runner completion, not a known code defect.
  - Accepted command intent still performs no runtime submission or reconciliation transition.
unknown:
  - Terminal conclusion of Portal Web CI 30366592438.
  - Terminal conclusion of Freqtrade CI 30366590083 including Python 3.12 coverage and CI Gate.
conflicts:
  - BM03_IDEMPOTENCY_SEMANTICS resolved by keeping BM-03 unchanged and handling browser retry in the BMW-02 facade.
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Legacy lifecycle controls posted desired state instead of recording canonical BM-03 command intent.
rejected_hypotheses:
  - Normalize the global BM-03 digest to treat transport retries as identical commands.
  - Accept browser-supplied runtime identity or environment.
  - Report desired or observed runtime state changes before PI-08 execution and reconciliation.
changed_paths:
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
validation:
  - command: focused BMW-02 domain and API tests
    result: PASS
    evidence: 7 tests passed after restoring BM-03 semantics.
  - command: AI Platform CI 30366588200
    result: PASS
    evidence: Full AI Platform suite succeeded on exact head d5063cdc3a5307de8d35df24f4cb2a33f3fa89d0.
  - command: Portal Universal E2E 30366588479
    result: PASS
    evidence: Canonical lifecycle intent journeys and authority rejection succeeded.
  - command: GitHub Actions Security Analysis 30366588292
    result: PASS
    evidence: Security workflow succeeded on exact head.
  - command: Portal Web CI 30366592438
    result: NOT_RUN
    evidence: Typecheck, lint and production build passed; Chromium regression was still running at handoff.
  - command: Freqtrade CI 30366590083
    result: NOT_RUN
    evidence: Python 3.11, 3.13 and 3.14 passed; Python 3.12 coverage and final gate were still running at handoff.
blockers:
  - PI-08 is required before accepted intent may be submitted to private Freqtrade and reconciled.
next_action: Verify only terminal Portal Web CI 30366592438 and Freqtrade CI 30366590083; if both succeed, audit PR 632 and squash merge expected head d5063cdc3a5307de8d35df24f4cb2a33f3fa89d0, otherwise repair the first integration-owned failure.
```
