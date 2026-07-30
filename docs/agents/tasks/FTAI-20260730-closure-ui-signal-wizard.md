---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
dispatch_state: WAIT_FOR_BACKEND
branch: agent/closure-ui-signal-wizard-terminal
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 818
terminal_pr: 820
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend must merge before restart
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

Build the complete research-only Signal Wizard against the frozen typed DSL and the canonical Signal Wizard backend/API after `FTAI-20260730-closure-signal-wizard-backend` merges. Do not restart frontend implementation while dispatch state is `WAIT_FOR_BACKEND`.

## Blocker result

- PR #818 merged normally into `develop` as `94e15dde23e0a2402b580ef263d51af689e989b6`.
- The frozen Signal Wizard command/result contracts have no canonical application service or registered control-plane preview/submit endpoints on current `develop`.
- Existing Strategy Lab submission supports only two fixed catalog strategies whose registry features are not `approved_for_ai`.
- Route-local UI/BFF work cannot truthfully persist arbitrary approved feature selections without a backend slice outside this task's owned paths.
- No frontend product implementation was added; the task remains blocked rather than merging a mock-only or false-compatible workflow.

## Coordinator dispatch

- Backend task: `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md`.
- Backend branch: `agent/closure-signal-wizard-backend`.
- Backend implementation PR: #825.
- Backend prompt: `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-BACKEND-AGENT-PROMPT.md`.
- Frontend dispatch state: `WAIT_FOR_BACKEND`.
- Agent 0 may mark this task `READY` only after PR #825 merges normally with green exact-head CI and zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T22:41:00+02:00
head: 087456dc23c9c198744b8cae7822c88a97d5abff
branch: agent/program-closure-signal-wizard-backend-dispatch-v2
pr: null
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
  - PR 818 merged normally into develop as 94e15dde23e0a2402b580ef263d51af689e989b6.
  - Exact blocker head 4a539fd84729c468fd5bee12f92381f795b10a22 passed Freqtrade CI run 30576227336 and security analysis run 30576227338.
  - Shared contracts PR 781 defines typed Signal Wizard preview and submit commands/results but current develop has no registered application service.
  - The canonical control-plane app on develop registers Feature Registry and Strategy Lab routers but no Signal Wizard preview or submit router.
  - Strategy Lab loads only tv_supertrend_v1 and tv_squeeze_momentum_v1; their features are approved_for_ai false in the current registry.
  - Backend task FTAI-20260730-closure-signal-wizard-backend is active in draft PR 825 on agent/closure-signal-wizard-backend.
  - PR 825 owns twelve backend/API/test paths and does not touch any of this frontend task's route-local implementation paths.
derived:
  - A complete production UI requires the canonical durable preview/submit backend slice before route-local implementation can converge.
  - A BFF-generated transient identifier or incompatible fixed-strategy mapping would misrepresent persistence and feature identity.
unknown:
  - Exact final PR 825 head, workflow conclusions, merge commit and unresolved review-thread count.
conflicts:
  - Frontend implementation cannot restart until PR 825 merges and Agent 0 records the exact merge evidence.
first_failure:
  marker: MISSING_CANONICAL_SIGNAL_WIZARD_SERVICE
  evidence: Current develop has no control-plane endpoint consuming the frozen SignalWizardPreviewCommand or SignalWizardSubmitCommand; PR 825 is the single assigned remediation.
rejected_hypotheses:
  - Generate a transient experiment or candidate ID in the BFF and call it durable submission.
  - Ignore selected feature identity by mapping the request to a fixed Strategy Lab catalog item.
  - Add backend router/service files inside frontend ownership.
  - Redefine shared contracts or expose Freqtrade, exchange or Vault to the browser.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: PR 818 exact-head and review evidence
    result: PASS
    evidence: Blocker head passed Freqtrade CI and security analysis; the PR changed one owned task path with zero unresolved threads.
  - command: PR 825 owned-path comparison
    result: PASS
    evidence: The active backend PR changes its task, control-plane registration, new signal_wizard package and backend tests only; no frontend route-local path overlaps.
  - command: Current develop service inventory
    result: BLOCKED
    evidence: Preview and submit remain absent from develop until PR 825 merges.
blockers:
  - PR 825 must merge normally with green exact-head CI and zero unresolved review threads.
next_action: Continue PR 825 to a normal green merge; then Agent 0 changes this task and the closure matrix from WAIT_FOR_BACKEND to READY.
```
