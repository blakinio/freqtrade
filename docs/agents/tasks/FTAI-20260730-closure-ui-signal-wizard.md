---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: blocked
branch: agent/closure-ui-signal-wizard
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - FTAI-20260730-closure-contracts merged
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
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure Signal Wizard UI

## Goal

Build the complete strategy-research Signal Wizard against the frozen typed DSL and existing Strategy Lab APIs.

## Evidence at Gate 0

The existing component is a manual advisory signal recorder only. It has no feature selection, parameter constraints, leakage warnings, strategy preview or experiment submission.

## Deliverables

- Registry-backed feature selection and parameter constraints.
- Leakage and repaint warnings derived from canonical metadata.
- Deterministic strategy preview and validation errors.
- Idempotent experiment submit through same-origin BFF.
- Loading, empty, denied, invalid and server-failure states.
- Responsive Chromium coverage.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Browser code has no direct Freqtrade, exchange or Vault path.
- Submitted work remains research-only and cannot promote or execute.
- All client payloads conform to the frozen contract.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-ui-signal-wizard
pr: null
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
  - The existing component is a manual advisory signal recorder only. It has no feature selection, parameter constraints, leakage warnings, strategy preview or experiment submission.
derived:
  - The bounded implementation scope is restricted to 8 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: WAIT_FOR_SHARED_CONTRACT
  evidence: The current manual advisory Signal Wizard cannot safely be expanded before one canonical typed strategy contract is merged.
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
  - Signal Wizard preview and submit contracts and the typed AST are not frozen.
next_action: Wait for the contract PR to merge, then create the branch and implement only the route-local wizard and BFF paths.
```
