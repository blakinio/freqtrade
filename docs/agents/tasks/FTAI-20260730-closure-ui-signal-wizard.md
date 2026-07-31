---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
dispatch_state: WAIT_FOR_CONTEXT_REPAIR
branch: agent/closure-ui-signal-wizard-correlation-blocker
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
hardening_task: FTAI-20260731-closure-signal-wizard-context-hardening
hardening_branch: agent/closure-signal-wizard-context-hardening
hardening_prompt: docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-closure-signal-wizard-context-hardening must merge before restart
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

Build the complete research-only Signal Wizard against the frozen typed DSL and the canonical Signal Wizard backend/API only after the trusted-context and semantic-hardening dependency is merged.

## Integration blocker discovered after backend merge

- PR #825 added canonical preview and submit services, but its HTTP test uses a static `RequestContext` provider with fixed correlation identifiers.
- The product identity-enabled control plane resolves every request through `IdentityService.resolve_request` and creates new random `request_id` and `correlation_id` values inside the upstream request.
- The merged Signal Wizard service requires the command body correlation values to equal those newly generated trusted values.
- The same-origin Portal BFF can read tenant and principal session fields, but cannot know the upstream request correlation values before the request is authenticated.
- The final merged backend also leaves semantic gaps around disabled feature identity, immutable draft versioning, persisted canonical command identity, complete target binding, deterministic reason codes, bounded error messages and fail-closed numeric constraints.
- Therefore fixture-only success or route-local work would be false compatibility. No UI or BFF implementation may restart yet.

## Coordinator dispatch

- Repair task: `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`.
- Repair branch: `agent/closure-signal-wizard-context-hardening`.
- Repair prompt: `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md`.
- Frontend dispatch state: `WAIT_FOR_CONTEXT_REPAIR`.
- Agent 0 may mark this task `READY` only after the repair PR merges normally with green exact-head CI and zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T08:53:00+02:00
head: 28fb301db2c575d610c73143e44bd68c40b46ec7
branch: agent/program-closure-signal-wizard-context-repair-dispatch
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
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
  - PR 832 merged the identity-enabled correlation blocker as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - IdentityService creates trusted request and correlation UUIDs only after the upstream request reaches the identity-enabled control plane.
  - The same-origin BFF cannot know those trusted values while constructing the frozen command body.
  - Final PR 825 code still validates only enabled selections, can reuse base_strategy_version as the new draft version, fabricates risk.max_leverage, omits canonical preview command persistence, incompletely binds submit context and exposes generic/raw conflicts.
derived:
  - Production preview and submit cannot converge through the current same-origin boundary without a server-side trusted command-construction repair.
  - UI implementation must wait until the canonical backend preserves full feature and target identity and passes identity-enabled HTTP coverage.
unknown:
  - Repair implementation PR number, exact head, workflow conclusions and merge SHA.
conflicts:
  - Required repair is outside the eight frontend-owned paths.
first_failure:
  marker: SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED
  evidence: Trusted UUIDs are generated after the client sends the command, while the merged service requires body equality.
rejected_hypotheses:
  - Use fixture-only fixed UUIDs and describe the flow as production compatible.
  - Guess or independently generate trusted correlation identifiers in the BFF.
  - Relax tenant, actor or correlation validation in route-local TypeScript.
  - Generate transient experiment or candidate IDs in the BFF.
  - Map selected features to incompatible fixed Strategy Lab catalog entries.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: PR 832 exact-head workflow and review audit
    result: PASS
    evidence: Exact head 556d1e9ff5714d77898c467b9d83e17832e5b840 passed Freqtrade CI and security with zero unresolved review threads before merge.
  - command: Final PR 825 implementation review
    result: BLOCKED
    evidence: Trusted-context compatibility and the listed semantic requirements remain unresolved on develop.
blockers:
  - FTAI-20260731-closure-signal-wizard-context-hardening must merge normally with green exact-head CI and zero unresolved review threads.
next_action: Run docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md on agent/closure-signal-wizard-context-hardening from current develop.
```
