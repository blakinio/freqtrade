---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
dispatch_state: WAIT_FOR_CONTEXT_REPAIR
branch: agent/closure-ui-signal-wizard-correlation-blocker
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/web/app/ai/signal-wizard/page.tsx
  - ai_platform/portal/web/app/ai/signal-wizard/signal-wizard-client.tsx
  - ai_platform/portal/web/app/api/ai/signal-wizard/preview/route.ts
  - ai_platform/portal/web/app/api/ai/signal-wizard/submit/route.ts
  - ai_platform/portal/web/lib/signal-wizard-api.ts
  - ai_platform/portal/web/lib/signal-wizard-contracts.ts
  - ai_platform/portal/web/e2e/signal-wizard-closure.spec.ts
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
---

# Closure Signal Wizard UI

## Goal

Build the complete research-only Signal Wizard against the frozen typed DSL and the canonical Signal Wizard backend/API.

## Integration blocker discovered after backend merge

- PR #825 added canonical preview and submit services, but its HTTP test uses a static `RequestContext` provider with fixed correlation identifiers.
- The product identity-enabled control plane resolves every request through `IdentityService.resolve_request` and creates new random `request_id` and `correlation_id` values inside the upstream request.
- `SignalWizardService._validate_context` requires the command body correlation values to equal those newly generated trusted values.
- The same-origin Portal BFF can read tenant and principal session fields, but no API exposes the upstream request correlation values and the existing mutation forwarder cannot know them before the upstream request is authenticated.
- Therefore a production BFF command cannot satisfy the canonical context equality check; fixture-only success would be false compatibility.
- No UI, BFF or fixture implementation was added after this first incompatible requirement was proven.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T00:02:00+02:00
head: 6b380d2af08e95f5faaff3c40828fe29c7d957f3
branch: agent/closure-ui-signal-wizard-correlation-blocker
pr: 832
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/web/app/ai/signal-wizard/page.tsx
  - ai_platform/portal/web/app/ai/signal-wizard/signal-wizard-client.tsx
  - ai_platform/portal/web/app/api/ai/signal-wizard/preview/route.ts
  - ai_platform/portal/web/app/api/ai/signal-wizard/submit/route.ts
  - ai_platform/portal/web/lib/signal-wizard-api.ts
  - ai_platform/portal/web/lib/signal-wizard-contracts.ts
  - ai_platform/portal/web/e2e/signal-wizard-closure.spec.ts
proven:
  - PR 825 merged canonical /v1/signal-wizard/preview and /submit endpoints as 0bc35521debd33312820dfad9f010e22aa651610.
  - SignalWizardService rejects a command when its tenant, actor, actor type or correlation context differs from trusted RequestContext.
  - IdentityService creates request_id=uuid4() and correlation_id=uuid4() while authenticating each identity-enabled control-plane request.
  - PortalSessionView exposes principal and tenant session data but not the new trusted request or correlation identifiers.
  - Existing web mutation forwarding sends cookie, CSRF and JSON body only; it receives no trusted context before sending the command.
  - PR 825 HTTP coverage uses a static lambda RequestContext provider and does not exercise create_identity_enabled_app.
derived:
  - Production preview and submit cannot pass context validation through the current same-origin BFF boundary.
  - Building only fixture payloads or claiming the current API path converges would conceal a deterministic production failure.
unknown: []
conflicts:
  - The first required repair is outside the eight frontend-owned paths and affects identity/control-plane context propagation or Signal Wizard command construction semantics.
first_failure:
  marker: SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED
  evidence: Identity-enabled requests generate trusted UUIDs after the BFF has already constructed the required command body, while SignalWizardService requires exact equality.
rejected_hypotheses:
  - Use fixture-only fixed UUIDs and describe the flow as production compatible.
  - Guess or independently generate request and correlation identifiers in the BFF.
  - Relax or bypass tenant, actor or correlation validation in route-local TypeScript.
  - Add identity or backend changes outside assigned ownership without coordinator transfer.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: Identity-enabled context construction review
    result: BLOCKED
    evidence: IdentityService creates fresh request and correlation UUIDs inside each authenticated upstream request.
  - command: Signal Wizard context validator review
    result: BLOCKED
    evidence: Command correlation must equal the trusted RequestContext generated by that same upstream request.
  - command: Same-origin BFF forwarding review
    result: BLOCKED
    evidence: The BFF has session, cookie and CSRF data but no pre-request trusted correlation values.
  - command: Existing backend HTTP test review
    result: PASS
    evidence: Static-provider tests prove service behavior but do not prove identity-enabled Portal integration.
blockers:
  - A coordinator-owned repair must establish one canonical trusted correlation propagation/construction mechanism and cover Signal Wizard through create_identity_enabled_app.
next_action: Agent 0 must assign and merge one bounded identity/control-plane correlation repair with an identity-enabled Signal Wizard HTTP test, then mark this frontend child READY.
```
