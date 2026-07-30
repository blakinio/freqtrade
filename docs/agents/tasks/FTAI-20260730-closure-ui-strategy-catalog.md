---
task_id: FTAI-20260730-closure-ui-strategy-catalog
status: ready
branch: agent/closure-ui-strategy-catalog
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - ai_platform/portal/web/app/bots/strategies/page.tsx
  - ai_platform/portal/web/app/api/strategy-catalog/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/rollback/route.ts
  - ai_platform/portal/web/components/strategy-catalog-client.tsx
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/lib/strategy-catalog-contracts.ts
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
---

# Closure Strategy Catalog UI

## Goal

Replace the static summary table with the tenant-scoped, research-only catalog lifecycle defined by the frozen contracts.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T17:35:00+02:00
head: 09bc139a766034840ac01898f8b68cd5c76fb7a2
branch: agent/closure-ui-strategy-catalog
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - ai_platform/portal/web/app/bots/strategies/page.tsx
  - ai_platform/portal/web/app/api/strategy-catalog/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/rollback/route.ts
  - ai_platform/portal/web/components/strategy-catalog-client.tsx
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/lib/strategy-catalog-contracts.ts
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
proven:
  - Shared contracts PR 781 merged as 6e489f7e10199120424cbcd01b3e125711630243.
  - Contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6 provides canonical history, approval, dry-run or shadow deployment, rollback and provenance contracts.
  - Open PRs 801 and 758 do not touch any Strategy Catalog owned path.
derived:
  - The contract dependency is satisfied and no active duplicate or ownership conflict exists.
unknown:
  - Exact implementation head, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: NONE
  evidence: The prior shared-contract blocker is resolved and live ownership is disjoint.
rejected_hypotheses:
  - Redefine lifecycle or rollback contracts in route-local code.
  - Add a direct browser path to Freqtrade, exchange or Vault.
  - Permit live-capital deployment or promotion.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
validation:
  - command: Open PR changed-path comparison against Strategy Catalog ownership
    result: PASS
    evidence: PR 801 and PR 758 have no overlap with the nine declared paths.
  - command: Contract dependency verification
    result: PASS
    evidence: PR 781 and terminal checkpoint PR 790 are merged on develop.
blockers: []
next_action: Start docs/agents/prompts/ai-program-closure/UI-STRATEGY-CATALOG-AGENT-PROMPT.md in a new chat from current develop.
```
