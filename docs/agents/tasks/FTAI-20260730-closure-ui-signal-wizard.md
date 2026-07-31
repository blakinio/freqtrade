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
correlation_repair_task: FTAI-20260731-signal-wizard-correlation-repair
correlation_repair_pr: 844
correlation_repair_branch: agent/signal-wizard-correlation-repair-20260731
hardening_task: FTAI-20260731-closure-signal-wizard-context-hardening
hardening_branch: agent/closure-signal-wizard-semantic-hardening
hardening_prompt: docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - PR 844 must merge before semantic hardening starts
  - FTAI-20260731-closure-signal-wizard-context-hardening must merge before frontend restart
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

Build the complete research-only Signal Wizard against the frozen typed DSL and canonical backend only after both the active trusted-correlation repair and the disjoint semantic/persistence hardening are merged.

## Integration blocker discovered after backend merge

- PR #825 added canonical preview and submit services, but its HTTP coverage used a static request context and did not prove the product identity-enabled path.
- `IdentityService` creates trusted request/correlation UUIDs only after the upstream request reaches the control plane, so the BFF cannot know them while constructing the frozen command body.
- PR #844 now owns the bounded router/test correlation repair, but its current exact head still requires review fixes for a real portal session/CSRF test, deterministic conflict codes, bounded messages and secret-exclusion assertions.
- Final PR #825 service/persistence code also leaves semantic gaps around disabled feature identity, immutable draft versioning, fabricated risk compatibility, exact command persistence, full submit binding and fail-closed numeric constraints.
- Therefore fixture-only success or route-local frontend work would be false compatibility. No UI or BFF implementation may restart yet.

## Coordinator dispatch

- Active correlation task: `docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md`.
- Active correlation branch: `agent/signal-wizard-correlation-repair-20260731`.
- Active correlation PR: #844.
- Follow-up semantic task: `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`.
- Follow-up branch: `agent/closure-signal-wizard-semantic-hardening`.
- Follow-up prompt: `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md`.
- Frontend dispatch state: `WAIT_FOR_CONTEXT_REPAIR`.
- Agent 0 may mark this task `READY` only after PR #844 and the semantic-hardening PR both merge normally with green exact-head CI and zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:20:00+02:00
head: 20b4ca6e1341061a9ebe98a8415ff18501a11557
branch: agent/program-closure-signal-wizard-context-repair-dispatch
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md
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
  - PR 832 merged the production correlation blocker as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - Active PR 844 owns router.py, tests/ai_platform/portal/signal_wizard/test_signal_wizard.py and its task path.
  - PR 844 exact head 41133fcc9943fd8ae347409ceba6f6bfc6167c30 has green AI Platform and security workflows; Freqtrade CI remains in progress at this checkpoint.
  - Agent 0 review 4826262200 requires real portal session/CSRF coverage, stable conflict codes, bounded messages and secret-exclusion assertions before merge.
  - Final PR 825 service/persistence code still drops disabled selection identity, can reuse base_strategy_version as the new draft version, fabricates risk.max_leverage, omits canonical preview command persistence, incompletely binds submit context and allows nonnumeric bound fall-through.
derived:
  - PR 844 must finish the correlation/router lane before the disjoint semantic-hardening branch is created.
  - UI implementation must wait until both repair lanes are merged and exact-head validated.
unknown:
  - PR 844 final head, final workflow conclusions and merge SHA.
  - Semantic-hardening implementation PR number, exact head, workflow conclusions and merge SHA.
conflicts:
  - Router and existing Signal Wizard test paths are actively owned by PR 844 and excluded from the semantic task.
first_failure:
  marker: SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED
  evidence: Trusted UUIDs are generated after the client sends the command, while the merged service requires body equality.
rejected_hypotheses:
  - Use fixture-only fixed UUIDs and describe the flow as production compatible.
  - Start a duplicate correlation branch while PR 844 is active.
  - Guess trusted correlation identifiers in the BFF.
  - Generate transient experiment IDs or map to incompatible fixed Strategy Lab entries.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: PR 832 exact-head workflow and review audit
    result: PASS
    evidence: Exact head 556d1e9ff5714d77898c467b9d83e17832e5b840 passed Freqtrade CI and security with zero unresolved review threads before merge.
  - command: PR 844 live path and exact-head audit
    result: BLOCKED
    evidence: Correct bounded correlation direction exists, but required identity/error-shape review fixes and final green CI are not yet proven.
  - command: Final PR 825 semantic/persistence review
    result: BLOCKED
    evidence: The listed semantic requirements remain unresolved on develop.
blockers:
  - PR 844 must merge normally after addressing Agent 0 review and passing final exact-head CI.
  - FTAI-20260731-closure-signal-wizard-context-hardening must then merge normally with green exact-head CI and zero unresolved review threads.
next_action: Continue PR 844 to a reviewed exact-head green merge; then mark the disjoint semantic-hardening task READY.
```
