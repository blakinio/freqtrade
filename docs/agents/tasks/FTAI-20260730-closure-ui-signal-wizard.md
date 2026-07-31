---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
dispatch_state: WAIT_FOR_BACKEND
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
correlation_repair_task: FTAI-20260731-signal-wizard-context-repair
correlation_repair_pr: 846
correlation_repair_merge: 367a51b610d2a34ee5841bc0b86622bd64fc6858
superseded_correlation_pr: 844
hardening_task: FTAI-20260731-closure-signal-wizard-context-hardening
hardening_branch: agent/closure-signal-wizard-semantic-hardening
hardening_prompt: docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-signal-wizard-context-repair merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858
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

Build the complete research-only Signal Wizard against the frozen typed DSL and canonical backend only after the remaining semantic/persistence hardening merges.

## Current dependency state

- PR #825 added canonical preview and submit services.
- PR #846 removed the production correlation blocker using authenticated server-side command correlation and real IdentityService login/session/CSRF coverage.
- PR #846 merged normally as `367a51b610d2a34ee5841bc0b86622bd64fc6858`; exact head `647ea9fb79134e90af87f165ea1529482f2c1f5c` passed AI Platform CI `30612077198`, Freqtrade CI `30612077288` and security `30612077128`, with zero review threads.
- Competing PR #844 was closed as superseded.
- The merged backend still leaves bounded semantic gaps around disabled feature identity, immutable draft versioning, fabricated risk compatibility, exact command persistence, full submit binding, deterministic reason codes, bounded public messages and fail-closed numeric constraints.
- Therefore no UI or BFF implementation may restart yet.

## Coordinator dispatch

- Backend semantic task: `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`.
- Backend branch: `agent/closure-signal-wizard-semantic-hardening`.
- Backend prompt: `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md`.
- Backend dispatch state: `READY`.
- Frontend dispatch state: `WAIT_FOR_BACKEND`.
- Agent 0 may mark this task `READY` only after the semantic-hardening PR merges normally with green exact-head CI and zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:45:00+02:00
head: 367a51b610d2a34ee5841bc0b86622bd64fc6858
branch: agent/program-closure-signal-wizard-context-repair-dispatch
pr: 851
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
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
  - PR 846 merged authenticated server-side correlation as 367a51b610d2a34ee5841bc0b86622bd64fc6858.
  - PR 846 exact head 647ea9fb79134e90af87f165ea1529482f2c1f5c passed AI Platform, Freqtrade and security workflows and had zero review threads.
  - PR 846 uses a real IdentityService, persisted principal/membership/session, login callback and CSRF cookie/header in its identity-enabled regression test.
  - PR 844 is closed and cannot conflict with the new semantic branch.
  - Live Signal Wizard open-PR inventory showed no implementation PR after #844 closed; Agent 0 created the semantic branch from current develop.
  - Final backend code still drops disabled selection identity, can reuse base_strategy_version as the new draft version, fabricates risk.max_leverage, omits canonical preview command persistence, incompletely binds submit context, returns generic/raw conflicts and allows nonnumeric bound fall-through.
derived:
  - Correlation compatibility is complete.
  - One bounded backend semantic/persistence task remains before frontend implementation can safely start.
  - UI implementation must remain WAIT_FOR_BACKEND until that PR merges and exact-head gates pass.
unknown:
  - Semantic-hardening implementation PR number, exact head, workflow conclusions and merge SHA.
conflicts: []
first_failure:
  marker: SIGNAL_WIZARD_SEMANTIC_IDENTITY_INCOMPLETE
  evidence: Production context construction now works, but canonical feature/draft/persistence/submit/error identity is still incomplete.
rejected_hypotheses:
  - Revive or merge superseded PR 844.
  - Use fixture-only compatibility or guess trusted correlation in the BFF.
  - Start frontend before semantic hardening merges.
  - Generate transient experiment IDs or map to incompatible fixed Strategy Lab entries.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: PR 846 exact-head workflow and review audit
    result: PASS
    evidence: Runs 30612077198, 30612077288 and 30612077128 succeeded; zero review threads.
  - command: live Signal Wizard implementation overlap
    result: PASS
    evidence: PR 844 closed; no open implementation PR owns the semantic task paths.
  - command: Final backend semantic/persistence review
    result: BLOCKED
    evidence: The listed semantic requirements remain unresolved on develop.
blockers:
  - FTAI-20260731-closure-signal-wizard-context-hardening must merge normally with green exact-head CI and zero unresolved review threads.
next_action: Run docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md on agent/closure-signal-wizard-semantic-hardening.
```
