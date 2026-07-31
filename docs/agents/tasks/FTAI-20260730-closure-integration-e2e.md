---
task_id: FTAI-20260730-closure-integration-e2e
status: ready
branch: agent/closure-integration-e2e
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
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
- responsive overflow repair PR #880.

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
updated_at: 2026-07-31T23:36:00+02:00
head: b29b4055f4748b57b5820f0b2e0d70a543a7a5dd
branch: agent/closure-integration-e2e
pr: "#874"
status: ready
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
  - PR 874 differs from develop by exactly the five declared Integration/E2E owned paths and is behind develop by zero commits.
  - Focused backend integration passed 3 tests and canonical regressions passed 49 tests.
  - The dedicated exact-head closure workflow passed backend integration, canonical regressions, Ruff, desktop Chromium and the strict 390 px responsive assertion on the validated implementation head.
  - Full Freqtrade CI passed pre-commit, documentation, Python 3.11, 3.12, 3.13 and 3.14 jobs, including coverage, Ruff, Ruff format and mypy where applicable.
  - Portal Web CI passed typecheck, lint, production build and Chromium regression.
  - Portal Universal E2E, AI Platform CI and GitHub Actions Security Analysis passed.
  - Persisted intent, transport acknowledgement and deterministic execution proof remain separate evidence states.
  - Browser request and source scans reject direct Freqtrade, exchange-private, Vault and secret references.
  - Cross-tenant navigation is verified against the canonical proxy redirect and global denied page, while the protected API returns HTTP 403.
  - Repository fixtures are labelled explicitly and external P11 acceptance remains false.
  - Coordinator-authorized repair PR 880 removed the intrinsic table sizing defect without hiding overflow or removing the table minimum width.
  - PR 880 merged normally as 6c43481187d8e74c2e80aeebc178aabff1bbb75c after all required workflows passed twice, including terminal exact-head CI.
  - PR 874 has no inline review threads and is mergeable.
derived:
  - Repository closure evidence is complete for paper, shadow and dry-run scope.
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
  - command: AI Program Closure E2E run 30659016272
    result: PASS
    evidence: Backend deterministic integration, Critical Chromium journeys and Exact-head closure gate completed successfully.
  - command: Freqtrade CI run 30659016107
    result: PASS
    evidence: All required pre-commit, documentation and Python matrix jobs completed successfully.
  - command: Portal Web CI run 30659016126
    result: PASS
    evidence: Typecheck, lint, production build and Chromium regression completed successfully.
  - command: Portal Universal E2E run 30659016158
    result: PASS
    evidence: Universal backend and browser journeys completed successfully.
  - command: AI Platform CI run 30659016172
    result: PASS
    evidence: AI Platform checks completed successfully.
  - command: GitHub Actions Security Analysis run 30659016221
    result: PASS
    evidence: Workflow security analysis completed successfully.
blockers: []
next_action: Merge PR 874 normally into develop after this terminal checkpoint commit passes the same required exact-head workflows.
```
