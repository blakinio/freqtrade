---
task_id: FTAI-20260730-closure-integration-e2e
status: ready
branch: agent/closure-integration-e2e
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: null
dependencies:
  - all repository REAL_GAP implementation PRs merged
  - PR #753, #758, #761 and #762 terminal or explicitly excluded from autonomous repository closure
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

## Dispatch state

All repository implementation dependencies are merged and terminal:

- Shared Contracts PR #781;
- Time/Leakage PR #777;
- Feature Engine PR #780;
- Simulator PR #787;
- Research Data PR #821 and terminal PR #823;
- Strategy Catalog PR #819 and terminal PR #822;
- Signal Wizard backend/context/hardening/frontend chain through PRs #825, #846, #858, #855 and terminal PR #863;
- AI routing/ranking PR #829 and terminal PR #868.

Open PRs #816 and #848 are immutable operational request lanes that must never merge into `develop`. PR #833 is a disjoint WickHunter recovery coordination package. External acceptance remains separately owner-managed and cannot be claimed by repository fixtures. None overlaps the five Integration/E2E owned paths.

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
- Do not treat repository fixtures as real P11 external acceptance.
- Do not modify, merge, replace or backdate immutable WickHunter operational request lanes.

## Acceptance criteria

- All required backend, browser, security and deterministic checks pass on the exact head.
- No arbitrary readiness sleeps or external staging claims.
- The evidence distinguishes simulated, repository and external states.
- The final scenario consumes the merged Signal Wizard, Strategy Catalog, Research Data and routing/ranking implementations rather than redefining their contracts.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T17:56:00+02:00
head: 286eb3a0d8a6e7a6eafe6da6ea5228e4c1a38595
branch: agent/closure-integration-e2e
pr: null
status: ready
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
  - Signal Wizard implementation and terminal checkpoints are merged through PRs 825, 846, 858, 855 and 863.
  - Strategy Catalog implementation and terminal checkpoint are merged through PRs 819 and 822.
  - Research Data implementation and terminal checkpoint are merged through PRs 821 and 823.
  - AI routing/ranking implementation PR 829 merged as 11f5924a2c8bed093fa1486c8df05df081121443 and terminal PR 868 merged as 286eb3a0d8a6e7a6eafe6da6ea5228e4c1a38595.
  - PR 829 exact final head passed AI Strategy Engine run 30633414223, Freqtrade CI run 30633414236 and security run 30633414280.
  - Open PRs 816, 848 and 833 do not touch any Integration/E2E owned path.
  - External P11 acceptance remains a separate owner-managed lane and is not a repository implementation dependency.
derived:
  - Every autonomous repository implementation dependency is terminal.
  - The final Integration/E2E worker is unblocked and may start from current develop.
unknown:
  - Exact implementation head, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: NONE
  evidence: The prior WAIT_FOR_IMPLEMENTATION_MERGES condition is satisfied and current active PR ownership is disjoint.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
  - Operational WickHunter request PRs are mergeable program dependencies.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
validation:
  - command: terminal implementation merge audit
    result: PASS
    evidence: All repository REAL_GAP child implementations and terminal checkpoints are merged through develop 286eb3a0d8a6e7a6eafe6da6ea5228e4c1a38595.
  - command: open PR changed-path comparison
    result: PASS
    evidence: PRs 816, 848 and 833 are disjoint from the five declared Integration/E2E paths.
blockers: []
next_action: Start docs/agents/prompts/ai-program-closure/INTEGRATION-E2E-AGENT-PROMPT.md in a new chat from current develop.
```
