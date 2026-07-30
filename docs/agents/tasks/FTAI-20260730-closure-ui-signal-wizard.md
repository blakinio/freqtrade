---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: ready
branch: agent/closure-ui-signal-wizard
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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
updated_at: 2026-07-30T17:35:00+02:00
head: 3e0fe8e9310584aae3cd59750cbe013f54aaf698
branch: agent/closure-ui-signal-wizard
pr: null
status: ready
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
  - Shared contracts PR 781 merged as 6e489f7e10199120424cbcd01b3e125711630243.
  - Contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6 provides the canonical typed AST and versioned Signal Wizard preview and submit contracts.
  - Open PRs 780, 762 and 758 do not touch any Signal Wizard owned path.
derived:
  - The contract dependency is satisfied and no active duplicate or ownership conflict exists.
unknown:
  - Exact implementation head, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: NONE
  evidence: The prior shared-contract blocker is resolved and live ownership is disjoint.
rejected_hypotheses:
  - Redefine the frozen contracts in browser code.
  - Add a direct browser path to Freqtrade, exchange or Vault.
  - Grant execution or promotion authority to submitted research work.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: Open PR changed-path comparison against Signal Wizard ownership
    result: PASS
    evidence: PR 780, PR 762 and PR 758 have no overlap with the eight declared paths.
  - command: Contract dependency verification
    result: PASS
    evidence: PR 781 and terminal checkpoint PR 790 are merged on develop.
blockers: []
next_action: Start docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md in a new chat from current develop.
```
