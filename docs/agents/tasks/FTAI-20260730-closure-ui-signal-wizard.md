---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: ready
dispatch_state: READY
branch: agent/closure-ui-signal-wizard
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 818
terminal_pr: 820
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

Build the complete research-only Signal Wizard against the frozen typed DSL and the merged canonical Signal Wizard backend/API.

## Resolved blocker

- Blocker PR #818 and terminal PR #820 correctly found that the frozen commands had no canonical application service.
- Agent 0 assigned the bounded backend task `FTAI-20260730-closure-signal-wizard-backend` with disjoint backend/API/test ownership.
- Implementation PR #825 merged normally as `0bc35521debd33312820dfad9f010e22aa651610` after green exact-head AI Platform, AI Strategy Engine, Freqtrade and security gates.
- The backend now provides durable tenant-scoped preview and submit semantics for arbitrary explicitly selected Feature Registry entries approved for AI.
- Transient BFF candidate identifiers and incompatible mapping to fixed Strategy Lab catalog entries remain prohibited.
- The frontend may now implement only its eight route-local paths and consume the canonical control-plane endpoints through the same-origin Portal boundary.

## Dispatch

- Frontend dispatch state: `READY`.
- Prompt: `docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md`.
- Branch: `agent/closure-ui-signal-wizard`.
- Start from current `develop` and re-run live ownership comparison before editing.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T23:24:00+02:00
head: 0bc35521debd33312820dfad9f010e22aa651610
branch: agent/closure-signal-wizard-unblock
pr: null
status: ready
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
  - Shared contracts PR 781 merged as 6e489f7e10199120424cbcd01b3e125711630243.
  - Signal Wizard backend PR 825 exact head 47c042846094f43a8dc06494b177d3d69c64878d passed AI Platform CI run 30582265385.
  - The same exact head passed AI Strategy Engine run 30582265713, Freqtrade CI run 30582265405 and security run 30582265752.
  - PR 825 changed exactly thirteen assigned backend/API/test paths, had zero unresolved review threads and merged as 0bc35521debd33312820dfad9f010e22aa651610.
  - The canonical control plane registers /v1/signal-wizard/preview and /v1/signal-wizard/submit.
  - Preview validates approved registry features, parameters, dependencies, typed condition AST, tenant/actor/correlation and research-only environment.
  - Submit requires a persisted preview and expected strategy version and durably stores the canonical command and research experiment intent.
  - Backend execution_authority, promotion_authority and live-capital authority remain false.
derived:
  - All repository dependencies required to restart the route-local frontend task are satisfied.
  - The UI can preserve exact feature identity and durable preview-derived submission without redefining backend authority.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: The previously missing canonical backend is merged and exact-head validated.
rejected_hypotheses:
  - Generate a transient experiment or candidate ID in the BFF and call it durable submission.
  - Ignore selected feature identity by mapping the request to a fixed Strategy Lab catalog item.
  - Add backend router/service files inside frontend ownership.
  - Redefine shared contracts or expose Freqtrade, exchange or Vault to the browser.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: PR 825 exact-head workflow audit
    result: PASS
    evidence: AI Platform, AI Strategy Engine, full Freqtrade CI and security workflows succeeded.
  - command: PR 825 changed-path and review audit
    result: PASS
    evidence: Thirteen backend-owned paths and zero unresolved review threads.
  - command: Current develop canonical service inventory
    result: PASS
    evidence: Preview and submit routers, services, persistence and tests are merged as 0bc35521debd33312820dfad9f010e22aa651610.
blockers: []
next_action: Start docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md in a new chat from current develop.
```
