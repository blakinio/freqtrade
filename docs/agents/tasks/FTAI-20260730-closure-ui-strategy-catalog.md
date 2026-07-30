---
task_id: FTAI-20260730-closure-ui-strategy-catalog
status: blocked
branch: agent/closure-ui-strategy-catalog
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - FTAI-20260730-closure-contracts merged
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
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure Strategy Catalog UI

## Goal

Replace the static summary table with a tenant-scoped catalog experience using canonical lifecycle, approval, deployment, rollback and provenance evidence.

## Evidence at Gate 0

The existing catalog is a two-row in-memory tuple and table containing only version, kind, modes, runtime status and immutability. Required history, approvals, deployments, rollback and provenance are absent.

## Deliverables

- Version history and immutable provenance detail.
- Approval and deployment state with capability-based denied states.
- Rollback target selection through an audited same-origin path restricted to paper, shadow or dry-run.
- Loading, empty, stale, denied and failure states.
- Responsive Chromium coverage.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Catalog actions cannot directly reach Freqtrade or grant live capital.
- Rollback uses an existing audited control-plane boundary and exact revisions.
- The route consumes the frozen catalog contract without redefining it.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-ui-strategy-catalog
pr: null
status: blocked
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
  - The existing catalog is a two-row in-memory tuple and table containing only version, kind, modes, runtime status and immutability. Required history, approvals, deployments, rollback and provenance are absent.
derived:
  - The bounded implementation scope is restricted to 9 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: WAIT_FOR_SHARED_CONTRACT
  evidence: The current static catalog does not expose the versioned lifecycle data required by the closure definition.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers:
  - Catalog history, approval, deployment, rollback and provenance contracts are not frozen.
next_action: Wait for the contract PR to merge, then create the branch and implement only the declared catalog and BFF paths.
```
