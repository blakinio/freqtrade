---
task_id: FTAI-20260728-portal-bmw02-command-intent
status: active
branch: feat/portal-bmw02-command-intent-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
depends_on:
  - FTAI-20260728-portal-bmw01-catalog-builder
owned_paths:
  - ai_platform/portal/bot_operations/intent_service.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/api/bot-management/commands/lifecycle/route.ts
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/lib/bot-command-contracts.ts
  - ai_platform/portal/web/e2e/pages/portal.pages.ts
  - ai_platform/portal/web/e2e/specs/bots/operations.spec.ts
  - tests/ai_platform/portal/bot_operations/test_intent_service.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw02-command-intent.md
---

# BMW-02 audited lifecycle command intent

## Goal

Replace the legacy desired-state browser mutation with a same-origin route that submits a canonical BM-03 lifecycle command intent while keeping runtime identity, runtime revision and environment under trusted server control.

## Delivered

- authoritative runtime-state provider boundary;
- fail-closed default provider returning `RUNTIME_UNAVAILABLE` without persisting a command;
- exact fresh runtime path that persists BM-03 command/audit/event history;
- stale config-revision rejection evidence;
- browser request restricted to bot, action, expected config revision and idempotency key;
- strict rejection of browser-supplied runtime, actor, tenant or environment authority;
- explicit `execution_submission_performed=false` result;
- lifecycle UI that reports intent status without mutating observed state;
- unit and Playwright coverage.

## Safety boundary

BMW-02 never calls an execution adapter and never marks a command pending reconciliation. `ACCEPTED` means only that command intent was accepted and persisted. PI-08 remains required for private dry-run submission, acknowledgement and reconciliation.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T14:12:00+02:00
branch: feat/portal-bmw02-command-intent-v1
pr: null
status: active
stacked_on: feat/portal-bmw01-catalog-builder-v1
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/bot_operations/intent_service.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/api/bot-management/commands/lifecycle/route.ts
  - ai_platform/portal/web/app/bots/detail/[botId]/page.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/lib/bot-command-contracts.ts
  - ai_platform/portal/web/e2e/pages/portal.pages.ts
  - ai_platform/portal/web/e2e/specs/bots/operations.spec.ts
  - tests/ai_platform/portal/bot_operations/test_intent_service.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw02-command-intent.md
proven:
  - BM-03 persists command intent, audit and event evidence without execution submission.
  - PI-08 is not available and must not be bypassed.
  - The legacy browser mutation changed desired state directly and was not composed through the BM-03 command vocabulary.
  - The new facade returns BLOCKED/RUNTIME_UNAVAILABLE when no authoritative runtime state provider is injected.
derived:
  - BMW-02 can safely complete command-intent persistence while leaving execution and reconciliation blocked.
unknown:
  - Exact-head standard CI after BMW-01 merge and clean branch reconstruction.
conflicts: []
first_failure:
  marker: BROWSER_DESIRED_STATE_MUTATION
  evidence: Existing lifecycle component posted directly to /api/bots/{botId}/desired-state.
rejected_hypotheses:
  - Accept runtime_id, runtime_revision, environment or actor identity from the browser.
  - Treat ACCEPTED command intent as runtime success.
  - Mark pending reconciliation without an actual PI-08 execution attempt.
changed_paths:
  - ai_platform/portal/bot_operations/intent_service.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/web/app/api/bot-management/commands/lifecycle/route.ts
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/lib/bot-command-contracts.ts
  - ai_platform/portal/web/e2e/pages/portal.pages.ts
  - ai_platform/portal/web/e2e/specs/bots/operations.spec.ts
  - tests/ai_platform/portal/bot_operations/test_intent_service.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw02-command-intent.md
validation:
  - command: exact-head standard CI
    result: NOT_RUN
    evidence: BMW-01 must merge before BMW-02 can be reconstructed as a clean PR.
blockers:
  - BMW-01 PR 615 must merge.
next_action: Finish shared composition patches, reconstruct from current develop after BMW-01 merge, run exact-head CI and merge.
```
