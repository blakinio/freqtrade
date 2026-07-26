---
task_id: FTAI-20260726-portal-bot-operations-completion
status: review
branch: feat/portal-bot-operations-completion
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 320
owned_paths:
  - ai_platform/portal/web/lib/bot-operations.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-bot-operations-completion.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
---

# Portal Bot Operations Completion

## Goal

Make the bot fleet and bot detail routes the primary tenant-scoped operational workflow by composing existing canonical portal APIs and exposing the existing immutable-revision and desired-state mutations through same-origin BFF routes.

## Boundaries

- Browser code must not receive private Freqtrade, exchange, observability or secret-store endpoints or credentials.
- Lifecycle controls mutate desired runtime state only and do not submit orders.
- Revision changes create a new immutable revision and never edit an earlier revision.
- Evidence remains tenant- and bot-attributed; stale, partial, mismatched and unavailable states remain explicit.
- No PI-07, PI-08, P11, P13, P14, research-policy, protected-holdout or live-capital change.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:05:00+02:00
head: ee626af374dd27d25d01553037b93f1cc2e72786
branch: feat/portal-bot-operations-completion
pr: 320
status: review
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/web/lib/bot-operations.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-bot-operations-completion.md
proven:
  - develop HEAD at task declaration was b10ebefaace1e15d070dd2f4662775df5d974db8.
  - Open PR 313 owned only Synology preview deployment paths and open PR 109 owned only design-reference documentation paths at preflight.
  - Existing control-plane endpoints provide bot list/get, immutable revision creation and desired-state mutations.
  - Existing canonical runtime evidence, valuation, performance, audit and runtime-observability APIs are server-side and tenant-scoped.
  - PR 320 is mergeable against current develop.
  - TypeScript, lint and production build passed in Portal Web CI run 275 on implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3.
  - Chromium E2E passed in Portal Web CI run 275 and Portal Universal E2E run 280 on implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3.
  - AI Platform CI run 1314 and Freqtrade CI run 1587 passed on implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3.
derived:
  - Bot Operations is complete as a bounded web/BFF composition package without new execution authority or credential integration.
unknown:
  - Exact final-head CI outcome after status-document updates and removal of the temporary diagnostic workflow change.
conflicts: []
first_failure:
  head: fe036d2764039ddb0a23402b74eeeb618b9eb2a5
  cause:
    - Existing shell E2E used an unscoped exact text selector after the risk policy became visible in both immutable configuration and correlated risk evidence.
    - The first implementation changed the authoritative valuation fixture identity and broke the existing valuation E2E contract.
  repair:
    - Scoped the immutable configuration assertion by semantic definition role.
    - Restored the authoritative valuation fixture and asserted fail-closed bot attribution in the new fleet test.
rejected_hypotheses:
  - Implement order submission or credential brokering as part of lifecycle controls.
  - Treat unavailable operational evidence as a healthy empty result.
  - Rewrite the canonical valuation fixture merely to produce a numeric fleet preview.
changed_paths:
  - ai_platform/portal/web/lib/bot-operations.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-bot-operations-completion.md
validation:
  - implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3: Portal Web CI 275 success.
  - implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3: Portal Universal E2E 280 success.
  - implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3: AI Platform CI 1314 success.
  - implementation head cb6afe82b215cf9af4356ed12a11b63972242bb3: Freqtrade CI 1587 success.
  - final-head CI pending.
blockers: []
next_action: Run all required pull-request workflows on the exact final head, mark PR 320 ready, merge it, then record merge and exact CI evidence in a bounded closure update.
```
