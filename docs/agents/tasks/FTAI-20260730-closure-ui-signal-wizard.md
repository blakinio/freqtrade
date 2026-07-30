---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
branch: agent/closure-ui-signal-wizard-terminal
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 818
terminal_pr: null
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
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

Build the complete research-only Signal Wizard against the frozen typed DSL and existing Strategy Lab APIs.

## Blocker result

- PR #818 merged normally into `develop` as `94e15dde23e0a2402b580ef263d51af689e989b6`.
- The frozen Signal Wizard command/result contracts have no canonical application service or registered control-plane preview/submit endpoints.
- Existing Strategy Lab submission supports only two fixed catalog strategies whose registry features are not `approved_for_ai`.
- Route-local UI/BFF work cannot truthfully persist arbitrary approved feature selections without a backend slice outside this task's owned paths.
- No product implementation was added; the task remains blocked rather than merging a mock-only or false-compatible workflow.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T21:48:11+02:00
head: 94e15dde23e0a2402b580ef263d51af689e989b6
branch: agent/closure-ui-signal-wizard-terminal
pr: 818
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
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
  - PR 818 changed only the child task checkpoint and had zero unresolved review threads before merge.
  - Shared contracts PR 781 defines typed Signal Wizard preview and submit commands/results but no registered application service.
  - The canonical control-plane app registers Feature Registry and Strategy Lab routers but no Signal Wizard preview or submit router.
  - Strategy Lab loads only tv_supertrend_v1 and tv_squeeze_momentum_v1; their features are approved_for_ai false in the current registry.
derived:
  - A complete production UI requires a canonical durable preview/submit backend slice before route-local implementation can converge.
  - A BFF-generated transient identifier or incompatible fixed-strategy mapping would misrepresent persistence and feature identity.
unknown:
  - The coordinator-assigned backend owner, exact paths and endpoint implementation task.
conflicts:
  - Required backend work is outside this child task's eight owned paths.
first_failure:
  marker: MISSING_CANONICAL_SIGNAL_WIZARD_SERVICE
  evidence: No control-plane endpoint consumes the frozen SignalWizardPreviewCommand or SignalWizardSubmitCommand, and the existing experiment endpoint cannot represent approved registry selections.
rejected_hypotheses:
  - Generate a transient experiment or candidate ID in the BFF and call it durable submission.
  - Ignore selected feature identity by mapping the request to a fixed Strategy Lab catalog item.
  - Add backend router/service files outside assigned ownership.
  - Redefine shared contracts or expose Freqtrade, exchange or Vault to the browser.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: Freqtrade CI run 30576227336
    result: PASS
    evidence: Exact blocker head passed pre-commit, CI scope and documentation build; non-applicable core jobs were skipped normally.
  - command: GitHub Actions Security Analysis run 30576227338
    result: PASS
    evidence: Exact blocker head passed zizmor security analysis.
  - command: PR 818 changed-file and review-thread inspection
    result: PASS
    evidence: The PR contained exactly one owned task path and zero unresolved review threads before normal squash merge.
  - command: Portable checkpoint governance contract validation
    result: PASS
    evidence: Required fields, allowed blocked status, validation values, compactness limits, disjoint evidence states and concrete next_action all validated.
  - command: Canonical Signal Wizard service and Strategy Lab compatibility inventory
    result: BLOCKED
    evidence: No preview/submit service exists and fixed Strategy Lab definitions depend on registry features that are not approved_for_ai.
blockers:
  - A coordinator-owned backend/API slice must implement durable canonical Signal Wizard preview and submit semantics, or transfer exact backend ownership to this task.
next_action: Agent 0 must assign and merge one bounded canonical Signal Wizard preview/submit backend task, then mark this UI child READY.
```
