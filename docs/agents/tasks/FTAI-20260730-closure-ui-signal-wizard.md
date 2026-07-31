---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: completed
dispatch_state: COMPLETE
branch: agent/closure-ui-signal-wizard-terminal-v2
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
context_repair_pr: 846
context_repair_merge: 367a51b610d2a34ee5841bc0b86622bd64fc6858
semantic_hardening_pr: 858
semantic_hardening_merge: da86b55310a3c3575ad3168743cd1062f1387d6d
implementation_pr: 855
implementation_merge: 521c8ef6bd3f9281e0f2e429a7e32c70273b5e0e
completion_pr: 863
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-signal-wizard-context-repair merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858
  - Signal Wizard semantic hardening merged as da86b55310a3c3575ad3168743cd1062f1387d6d
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

Build the complete research-only Signal Wizard against the frozen typed DSL and canonical identity-enabled Signal Wizard backend/API.

## Delivered implementation

PR #855 is merged as `521c8ef6bd3f9281e0f2e429a7e32c70273b5e0e`. It delivers approved-only Feature Registry selection, dependency and parameter constraints, closed-bar conditions, canonical preview, blocking leakage/repaint evidence, experiment-candidate submission, same-origin session and CSRF boundaries, structured backend reason codes, responsive states and Chromium coverage. Submission remains research-only and grants no deployment, execution, promotion or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T12:52:20+02:00
head: 521c8ef6bd3f9281e0f2e429a7e32c70273b5e0e
branch: agent/closure-ui-signal-wizard-terminal-v2
pr: 855
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md
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
  - PR 825 provides canonical tenant-scoped Signal Wizard preview and submit endpoints using frozen v2 contracts.
  - PR 846 provides authenticated deterministic command correlation and merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858.
  - PR 858 hardens semantic identity, persistence and bounded reason codes and merged as da86b55310a3c3575ad3168743cd1062f1387d6d.
  - PR 855 changes exactly the eight assigned Signal Wizard paths and merged as 521c8ef6bd3f9281e0f2e429a7e32c70273b5e0e.
  - Exact implementation head 67168f0169803c36304750ccb8a983afb2700960 passed Portal Web, Universal E2E, AI Platform, Freqtrade and security workflows.
  - Production BFF preview and submit preserve canonical backend status and structured detail including actionable reason codes.
  - Chromium evidence covers approved selection, preview, accepted candidate, stale, empty, denied, leakage, CSRF and conflict states.
derived:
  - Browser traffic remains same-origin and cannot address Freqtrade, exchange or Vault endpoints directly.
  - The implemented workflow converges on the hardened canonical backend without a Strategy Lab compatibility shim.
  - The child task is complete and ready for coordinator archival.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All evidenced contract, correlation, semantic, TypeScript, React lint and merge-base failures were repaired and exact-head gates passed.
rejected_hypotheses:
  - Direct browser access to control-plane, Freqtrade, exchange or Vault endpoints.
  - Selection of features not returned as approved_for_ai.
  - Submit as deployment, promotion, execution or live-capital authority.
  - Flatten canonical backend reason codes into generic BFF text.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/web/app/ai/signal-wizard/page.tsx
  - ai_platform/portal/web/app/ai/signal-wizard/signal-wizard-client.tsx
  - ai_platform/portal/web/app/api/ai/signal-wizard/preview/route.ts
  - ai_platform/portal/web/app/api/ai/signal-wizard/submit/route.ts
  - ai_platform/portal/web/lib/signal-wizard-api.ts
  - ai_platform/portal/web/lib/signal-wizard-contracts.ts
  - ai_platform/portal/web/e2e/signal-wizard-closure.spec.ts
validation:
  - command: Portal Web CI run 30624832191 on 67168f0169803c36304750ccb8a983afb2700960
    result: PASS
    evidence: Typecheck, lint, production build and Chromium regression completed successfully.
  - command: Portal Universal E2E run 30624832210 on 67168f0169803c36304750ccb8a983afb2700960
    result: PASS
    evidence: Backend scenarios and the critical Chromium journey completed successfully.
  - command: AI Platform CI run 30624832190 on 67168f0169803c36304750ccb8a983afb2700960
    result: PASS
    evidence: AI platform tests, Ruff, formatting, codespell and schema validation completed successfully.
  - command: Freqtrade CI run 30624832227 on 67168f0169803c36304750ccb8a983afb2700960
    result: PASS
    evidence: Scope, pre-commit, documentation and CI gate completed successfully.
  - command: Security analysis run 30624832215 on 67168f0169803c36304750ccb8a983afb2700960
    result: PASS
    evidence: GitHub Actions security analysis completed successfully.
  - command: PR 855 changed-file and review inspection
    result: PASS
    evidence: Exactly eight owned paths changed, the PR was mergeable and no unresolved review threads existed.
blockers: []
next_action: Agent 0 should archive FTAI-20260730-closure-ui-signal-wizard and mark its closure row complete after this terminal checkpoint PR merges.
```
