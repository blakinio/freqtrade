---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: in_progress
dispatch_state: ACTIVE
branch: agent/closure-ui-signal-wizard-v2
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
context_repair_pr: 846
context_repair_merge: 367a51b610d2a34ee5841bc0b86622bd64fc6858
implementation_pr: 855
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-signal-wizard-context-repair merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858
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

## Current implementation

PR #855 implements approved-only Feature Registry selection, parameter and dependency constraints, closed-bar conditions, canonical preview, leakage/repaint warnings, experiment-candidate submit, same-origin session/CSRF boundaries and responsive Chromium coverage. Submit remains research-only and grants no deployment, execution, promotion or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:55:00+02:00
head: 4919100c04eb921b4eae0c2c67a76a2d289c75f5
branch: agent/closure-ui-signal-wizard-v2
pr: 855
status: in_progress
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
  - PR 825 provides canonical tenant-scoped preview and submit endpoints using frozen v2 contracts.
  - PR 846 makes the production identity-enabled HTTP path compatible with durable command idempotency.
  - PR 855 changes exactly the eight assigned Signal Wizard paths and is based on context-repair merge 367a51b610d2a34ee5841bc0b86622bd64fc6858.
  - Exact head cca2cddfb19f3242e9d9471f9b9551a86069d79f passed typecheck, Universal E2E, AI Platform CI, Freqtrade CI and security analysis.
  - The only failing gate on cca2cddfb19f3242e9d9471f9b9551a86069d79f was the React lint rule forbidding JSX construction inside try/catch.
  - Implementation head 4919100c04eb921b4eae0c2c67a76a2d289c75f5 separates data acquisition from JSX rendering.
derived:
  - The frontend converges directly on canonical endpoints without guessed trusted correlation or incompatible Strategy Lab mapping.
  - Fixture evidence is explicitly test-only; API mode forwards canonical commands through authenticated BFF routes.
unknown:
  - Exact-head Portal Web lint, build and Chromium evidence after the render-boundary repair.
conflicts: []
first_failure:
  marker: NONE
  evidence: The evidenced JSON typing and React render-boundary failures were repaired without changing authority semantics.
rejected_hypotheses:
  - Direct browser access to control-plane, Freqtrade, exchange or Vault endpoints.
  - Selection of features not returned as approved_for_ai.
  - Submit as deployment, promotion, execution or live-capital authority.
  - Suppress the React lint rule instead of separating fetch error handling from rendering.
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
  - command: Portal Web typecheck on cca2cddfb19f3242e9d9471f9b9551a86069d79f
    result: PASS
    evidence: TypeScript accepted canonical command, response and explicit JSON constraint serialization.
  - command: Portal Universal E2E run 30614167627
    result: PASS
    evidence: Backend scenarios and critical Chromium journey completed successfully.
  - command: AI Platform CI run 30614167658
    result: PASS
    evidence: AI platform tests and validation completed successfully.
  - command: Freqtrade CI run 30614167628
    result: PASS
    evidence: Repository validation completed successfully.
  - command: Security analysis run 30614167636
    result: PASS
    evidence: GitHub Actions security analysis completed successfully.
blockers: []
next_action: Inspect PR 855 exact-head CI and review state, fix only evidenced failures, and merge normally when all required gates are green.
```
