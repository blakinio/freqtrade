---
task_id: FTAI-20260726-portal-bot-operations-completion
status: active
branch: feat/portal-bot-operations-completion
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - ai_platform/portal/web/lib/bot-operations.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
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
updated_at: 2026-07-26T08:00:00+02:00
head: b10ebefaace1e15d070dd2f4662775df5d974db8
branch: feat/portal-bot-operations-completion
pr: null
status: active
context_routes:
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - ai_platform/portal/web/lib/bot-operations.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-bot-operations-completion.md
proven:
  - develop HEAD at task declaration is b10ebefaace1e15d070dd2f4662775df5d974db8.
  - Open PR 313 owns only Synology preview deployment paths; open PR 109 owns only design-reference documentation paths.
  - Existing control-plane endpoints provide bot list/get, immutable revision creation and desired-state mutations.
  - Existing canonical runtime evidence, valuation, performance, audit and runtime-observability APIs are server-side and tenant-scoped.
derived:
  - Bot Operations can be completed as a bounded web/BFF composition package without new execution authority or credential integration.
unknown:
  - Exact CI failures, if any, after implementation.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Implement order submission or credential brokering as part of lifecycle controls.
  - Treat unavailable operational evidence as a healthy empty result.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-portal-bot-operations-completion.md
validation: []
blockers: []
next_action: Implement the server-only bot operations composition and same-origin mutation routes, then update the bot fleet and detail surfaces with explicit degraded and permission states.
```
