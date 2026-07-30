---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
branch: agent/closure-ui-signal-wizard
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 818
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

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T21:45:10+02:00
head: 63ce29b69c22e4e643a2a525ffe272fa136a3df4
branch: agent/closure-ui-signal-wizard
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
  - The worker branch was created from current develop at 9bb8edad795e122a2e513b354cd4aafa16d5917b.
  - Shared contracts PR 781 merged as 6e489f7e10199120424cbcd01b3e125711630243 and defines typed Signal Wizard preview and submit commands/results.
  - The canonical control-plane app registers Feature Registry and Strategy Lab routers but no Signal Wizard preview or submit router/service.
  - Strategy Lab accepts only catalog identities loaded from tv_supertrend_v1 and tv_squeeze_momentum_v1.
  - Those catalog strategies depend on supertrend_direction.v1 and squeeze_ratio.v1, which are approved_for_ai false in the current Feature Registry.
  - Open PRs 816 and 758 do not touch any Signal Wizard owned path.
  - Focused blocker checkpoint PR 818 is open against develop and changes only this child task record.
derived:
  - A production Signal Wizard cannot persist a preview-derived experiment or candidate through the existing Strategy Lab API without discarding the selected approved features or falsely claiming compatibility.
  - A route-local synthetic candidate identifier would not provide durable canonical experiment storage and cannot be merged as production convergence.
unknown:
  - The coordinator-assigned owner and exact paths for the missing canonical Signal Wizard application service and control-plane endpoints.
conflicts:
  - Complete preview and submit require a canonical backend capability outside this child task's owned paths.
first_failure:
  marker: MISSING_CANONICAL_SIGNAL_WIZARD_SERVICE
  evidence: The frozen SignalWizardPreviewCommand and SignalWizardSubmitCommand contracts have no registered control-plane endpoint or service, while the only existing experiment create endpoint accepts two fixed catalog strategies that are not approved_for_ai.
rejected_hypotheses:
  - Generate a transient experiment or candidate ID inside the BFF and describe it as a persisted submission.
  - Map approved feature selections onto either fixed Strategy Lab strategy while ignoring incompatible feature identity.
  - Add a new backend router, service or shared API implementation outside the eight assigned paths.
  - Redefine the frozen contracts in browser code or add a direct browser path to Freqtrade, exchange or Vault.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: Open PR changed-path comparison against Signal Wizard ownership
    result: PASS
    evidence: PR 816 changes one WickHunter run request and PR 758 changes external preflight paths; neither overlaps the eight declared paths.
  - command: Canonical Signal Wizard endpoint and service inventory
    result: BLOCKED
    evidence: Repository and PR search found the frozen contract definitions only; create_app registers Feature Registry and Strategy Lab but no /v1/signal-wizard preview or submit endpoint.
  - command: Existing Strategy Lab compatibility review
    result: BLOCKED
    evidence: The catalog loads only tv_supertrend_v1 and tv_squeeze_momentum_v1, whose registry features are not approved_for_ai and cannot represent arbitrary approved wizard selections.
  - command: Focused blocker checkpoint PR creation
    result: PASS
    evidence: PR 818 targets develop from agent/closure-ui-signal-wizard and initially contained one changed task path.
blockers:
  - A coordinator-owned backend/API slice must implement durable canonical Signal Wizard preview and submit semantics, or transfer exact backend ownership to this task.
next_action: Agent 0 must assign and merge one bounded canonical Signal Wizard preview/submit backend task, then mark this UI child READY.
```
