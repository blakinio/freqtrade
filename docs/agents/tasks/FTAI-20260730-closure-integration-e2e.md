---
task_id: FTAI-20260730-closure-integration-e2e
status: completed
branch: agent/closure-integration-e2e
base_branch: develop
created: 2026-07-30
updated: 2026-08-01
related_pr: "#874"
dependencies:
  - all repository REAL_GAP implementation PRs merged
  - PR #753, #758, #761 and #762 terminal or explicitly excluded from autonomous repository closure
  - bounded responsive-shell repair PR #880 merged
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
- AI routing/ranking PR #829 and terminal PR #868;
- responsive overflow repair PR #880;
- final Integration/E2E PR #874 merged as `4660b1eb19b2c09af21f46cab2916b64dec7bfaf`.

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
updated_at: 2026-08-01T00:15:00+02:00
head: 4660b1eb19b2c09af21f46cab2916b64dec7bfaf
branch: develop
pr: "#874"
status: complete
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - .github/workflows/ai-program-closure-e2e.yml
  - tests/ai_platform_integration/test_program_closure_e2e.py
  - ai_platform/portal/web/e2e/program-closure.spec.ts
  - docs/ai_platform/PROGRAM_CLOSURE_E2E_EVIDENCE.md
proven:
  - All repository REAL_GAP implementation dependencies and terminal checkpoints are merged.
  - PR 874 differed from develop by exactly the five declared Integration/E2E owned paths at merge time.
  - Focused backend integration passed 3 tests and canonical regressions passed 49 tests.
  - The dedicated exact-head closure workflow passed backend integration, canonical regressions, Ruff, desktop Chromium and the strict 390 px responsive assertion on head dbb9d47e973eb2a5f0634525cf4f7866b3d7e5e8.
  - Full Freqtrade CI passed on exact head dbb9d47e973eb2a5f0634525cf4f7866b3d7e5e8.
  - Portal Web CI, Portal Universal E2E, AI Platform CI and GitHub Actions Security Analysis passed on the exact head.
  - Persisted intent, transport acknowledgement and deterministic execution proof remain separate evidence states.
  - Browser request and source scans reject direct Freqtrade, exchange-private, Vault and secret references.
  - Cross-tenant navigation is verified against the canonical proxy redirect and global denied page, while the protected API returns HTTP 403.
  - Repository fixtures are labelled explicitly and external P11 acceptance remains false.
  - Coordinator-authorized repair PR 880 removed the intrinsic table sizing defect without hiding overflow or removing the table minimum width.
  - PR 874 had no inline review threads and merged normally as 4660b1eb19b2c09af21f46cab2916b64dec7bfaf.
derived:
  - Repository closure evidence is complete for paper, shadow and dry-run scope.
  - No autonomous repository implementation or Integration/E2E worker remains.
  - External Cloudflare, Authentik, Vault and Synology P11 acceptance remains explicitly outside this repository fixture proof.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All concrete implementation, responsive, formatting and expectation failures are resolved.
rejected_hypotheses:
  - Persisted command intent is authoritative execution proof.
  - Repository fixture evidence is real protected-ingress P11 acceptance.
  - Arbitrary sleeps are valid readiness evidence.
  - The 547-pixel overflow may be hidden by weakening the E2E assertion.
  - Freqtrade CI formatting failure is an unrelated repository failure.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - .github/workflows/ai-program-closure-e2e.yml
  - tests/ai_platform_integration/test_program_closure_e2e.py
  - ai_platform/portal/web/e2e/program-closure.spec.ts
  - docs/ai_platform/PROGRAM_CLOSURE_E2E_EVIDENCE.md
validation:
  - command: AI Program Closure E2E run 30668369899
    result: PASS
    evidence: Backend deterministic integration, Critical Chromium journeys and Exact-head closure gate completed successfully.
  - command: Freqtrade CI run 30668369907
    result: PASS
    evidence: Full repository CI completed successfully.
  - command: Portal Web CI run 30668369892
    result: PASS
    evidence: Typecheck, lint, production build and Chromium regression completed successfully.
  - command: Portal Universal E2E run 30668369884
    result: PASS
    evidence: Universal backend and browser journeys completed successfully.
  - command: AI Platform CI run 30668369963
    result: PASS
    evidence: AI Platform checks completed successfully.
  - command: GitHub Actions Security Analysis run 30668369883
    result: PASS
    evidence: Workflow security analysis completed successfully.
blockers: []
next_action: None for autonomous repository closure. External P11 remains owner-managed; live capital remains prohibited.
```
