---
task_id: FTAI-20260730-closure-integration-e2e
status: blocked
branch: agent/closure-integration-e2e
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - all repository REAL_GAP implementation PRs merged
  - PR #753, #758, #761 and #762 terminal or explicitly excluded from autonomous closure
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - .github/workflows/ai-program-closure-e2e.yml
  - tests/ai_platform_integration/test_program_closure_e2e.py
  - ai_platform/portal/web/e2e/program-closure.spec.ts
  - docs/ai_platform/PROGRAM_CLOSURE_E2E_EVIDENCE.md
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

# Closure full-platform integration and E2E

## Goal

Prove the merged paper/shadow product as one deterministic, secure and observable full-platform path.

## Evidence at Gate 0

BM-09 and P10 already prove the existing product, but they cannot cover the new typed DSL, scheduler, support/resistance, simulator fidelity, research alignment, routing/ranking and completed frontend journeys until those PRs merge.

## Deliverables

- One versioned closure scenario matrix and deterministic fixtures.
- Backend integration from strategy draft through experiment, routing/ranking, risk, paper or shadow admission and reconciliation.
- Critical Chromium wizard, catalog and paper or shadow journeys.
- Security assertions for tenant isolation, denied states, no direct private paths and no secrets.
- Observability and first-failure evidence bundle.
- Dedicated Linux CI workflow and evidence document.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- All required backend, browser, security and deterministic checks pass on the exact head.
- No arbitrary readiness sleeps or external staging claims.
- The evidence distinguishes simulated, repository and external states.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-integration-e2e
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - .github/workflows/ai-program-closure-e2e.yml
  - tests/ai_platform_integration/test_program_closure_e2e.py
  - ai_platform/portal/web/e2e/program-closure.spec.ts
  - docs/ai_platform/PROGRAM_CLOSURE_E2E_EVIDENCE.md
proven:
  - BM-09 and P10 already prove the existing product, but they cannot cover the new typed DSL, scheduler, support/resistance, simulator fidelity, research alignment, routing/ranking and completed frontend journeys until those PRs merge.
derived:
  - The bounded implementation scope is restricted to 5 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: WAIT_FOR_IMPLEMENTATION_MERGES
  evidence: A final closure E2E assertion would be incomplete before every real-gap implementation and overlapping active PR reaches terminal state.
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
  - Repository implementation workstreams are not merged.
  - Open PRs still own adjacent deployment, evidence and liquidation paths.
next_action: After all required implementation PRs merge, create the branch from current develop and run the final cross-layer acceptance.
```
