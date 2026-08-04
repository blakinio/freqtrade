# FTAI-20260804 — CI architecture audit and optimizer

```yaml
task_id: FTAI-20260804-ci-architecture-optimizer
project_lane: freqtrade-core
status: completed
phase: closeout
base_branch: develop
base_head_at_start: c236117f2efe6326d24f6cb58c0dabfd96469370
base_head_at_validation: aa4007d48fdcead11ba6c6cae447c73b2f0e3151
branch: audit/ci-architecture-optimizer-20260804
pull_request: 1191
validated_head: 9d8baa6081d478eccd742fa3c08804b3b76e486f
policy_version: 2
task_kind: implementation
implementation_authorized: true
execution_mode: github
run_scope: single_task
completion_claim: internal_only
completed_at: 2026-08-04T22:20:00+02:00
ownership_released: true
blockers: []
```

## Objective

Audit every workflow in `blakinio/freqtrade` and replace overlapping path-filtered pull-request execution with one tested, fail-closed changed-path and risk classifier, a lightweight required gate, component-specific validation, and justified heavy tiers without weakening security, migration, identity/OIDC, deployment, trading, live-capital or exact-head acceptance requirements.

## Delivered

- Added the dependency-free classifier `tools/ci/change_classifier.py` and machine-readable routing contract `tools/ci/change-routing.json`.
- Added `.github/actions/classify-changes` as the shared workflow adapter.
- Reworked `.github/workflows/ci.yml` into a stable lightweight gate plus conditional Core compatibility, online and distribution tiers.
- Added `.github/workflows/ci-components.yml` as the aggregate specialist DAG.
- Converted specialist AI Platform, Strategy Engine, Portal web, schema/database, OIDC, exact-image, closure E2E and completeness audit workflows to reusable calls.
- Prevented reusable-workflow concurrency collisions through guarded central sequencing and unique Portal Web concurrency.
- Added documentation-only routing that skips Docker, PostgreSQL and browser E2E.
- Added exact-image selection only for image contents, dependencies, startup, migrations, runtime composition or identity-impacting paths.
- Added fail-closed full validation for CI architecture, explicit `ci:full` and `ci:merge-ready`, ready-for-review, protected-branch pushes, schedules, releases and manual runs.
- Added 21 positive, negative and cross-cutting routing contract tests, including Portal E2E source and test paths.
- Added deterministic workflow syntax, GitHub expression, local reusable-reference and action-pin validation.
- Generated final workflow inventory, routing matrix, before/after cost evidence, retained coverage, residual-risk and rollback documentation.

## Acceptance inventory

```yaml
acceptance_inventory:
  - id: CI-001
    status: passed
    evidence: final inventory covers 83 target workflows with triggers, matrices, Docker, Playwright, PostgreSQL, schedule and reusable-call metadata
  - id: CI-002
    status: passed
    evidence: central classifier and JSON routing contract are committed and exercised by both aggregate workflows
  - id: CI-003
    status: passed
    evidence: Lightweight required PR gate passed compile, Mypy, Ruff, 21 routing tests and workflow validation
  - id: CI-004
    status: passed
    evidence: exact-head component routing selected and passed Core, AI Platform, Portal web, schema/database, OIDC, Strategy Engine and security-sensitive tiers
  - id: CI-005
    status: passed
    evidence: contract tests prove docs-only changes retain documentation/governance validation and skip Docker, PostgreSQL and browser E2E
  - id: CI-006
    status: passed
    evidence: exact-head full-risk run passed compatibility matrices, online tests, exact-image, recovery, closure E2E, completeness audit and distribution build
  - id: CI-007
    status: passed
    evidence: 21 representative routing cases passed, including unknown-path fail-closed and Portal E2E closure coverage
  - id: CI-008
    status: passed
    evidence: all pull-request workflow runs for validated head 9d8baa6081d478eccd742fa3c08804b3b76e486f completed successfully or were intentionally skipped
  - id: CI-009
    status: passed
    evidence: CI_ARCHITECTURE_AUDIT.md, workflow-inventory.json and routing-matrix.json document selection, retained coverage, cost, residual risks and rollback
```

## Exact-head validation

Validated head: `9d8baa6081d478eccd742fa3c08804b3b76e486f`

- `Freqtrade CI` run `30945789374`: success.
  - lightweight gate, pre-commit and documentation: success;
  - Core Python 3.11, 3.12 coverage, 3.13 quality and 3.14: success;
  - compatibility sweep on Ubuntu 22.04, Ubuntu 26.04 and ARM: success;
  - online/live compatibility: success;
  - distribution build: success;
  - aggregate `CI Gate`: success.
- `Risk-aware component CI` run `30945790076`: success.
  - AI Platform, Strategy Engine and Portal Web: success;
  - exact Portal image, PostgreSQL rollback/restore and OIDC probes: success;
  - full Chromium, universal Portal E2E and program closure E2E: success;
  - Portal completeness audit: success;
  - aggregate `Component CI Gate`: success.
- Zizmor run `30945789338`: success.
- Pre-commit Types update: intentionally skipped for this pull-request event.

## Before and after

A representative Portal schema change previously selected 11 overlapping top-level workflows. One unrelated Core Python 3.13 job alone consumed approximately 335.5 seconds while installing the full development and ML stack. The optimized model exposes four stable top-level pull-request workflows and expands specialist work only through tested classification outputs.

## Retained safety coverage

Security analysis, identity/OIDC concurrency, schema migration, PostgreSQL backup/restore, exact-image startup and readiness, trading/live-capital-sensitive paths, Core compatibility, online exchange compatibility, browser closure, reproducibility and exact-head aggregate gates remain reachable and fail closed.

## Residual risks

- Branch protection must require the stable aggregate gate names after merge.
- Unknown paths deliberately fall back to Core validation until explicitly classified.
- OIDC exact-image validation remains separate because it proves a distinct concurrent callback contract.
- Historical flakiness was not assigned a statistical rate because the bounded execution sample was insufficient.

## Rollback

Revert the implementation merge commit, restore direct event triggers in the converted specialist workflows, remove `ci-components.yml`, the classifier action, classifier/config/tests and generated evidence, then run full exact-head CI before merging the revert.

## Closeout

The implementation scope is complete, all findings are resolved, the validated implementation head is green, the task record is archived, and task ownership is released. PR #1191 remains the sole delivery vehicle for merge and post-merge verification.
