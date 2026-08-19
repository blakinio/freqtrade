# FTAI-20260818 — Synology persistent runtime + GitHub-hosted build/disposable plane

```yaml
task_id: FTAI-20260818-synology-runtime-github-build-plane-1604
project_lane: ai-platform-runtime
status: completed
phase: closeout
issue: 1604
base_branch: develop
trusted_base: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
implementation_branch: arch/1604-synology-runtime-github-build-plane
implementation_pr: 1611
validated_head: 255db9d31a6ba8d18275e7e4ce2fe7a4249be62a
merge_commit: 8d8651d5b0448a4aa959274182f90ed89c26d009
execution_mode: github_only
risk_class: governance_or_ci
completed_at: 2026-08-19T14:09:22+02:00
ownership_released: true
blockers: []
```

## Objective

Reconcile the current Developer Quant Platform runtime/CI topology with the owner decision that persistent Portal, Freqtrade bot/simulation, persistent WickHunter/inference, long-lived collectors/workers and supporting stateful application containers remain on Synology, while compatible stateless/disposable CI, test, scan, build, GHCR publication and bounded jobs use GitHub-hosted Actions by default.

## Delivered

- Added and accepted ADR-025 as the binding current runtime/CI-placement overlay.
- Restored `LOCAL | SYNOLOGY` as the current persistent runtime-location vocabulary.
- Preserved ADR-024 as historical evidence while superseding only its unimplemented dedicated-Linux current target.
- Removed the requirement to provision or cut over to a separate dedicated Linux runtime host for current Portal completion.
- Kept GitHub-hosted Actions as the default stateless/disposable CI/build/test/scan/job plane and explicitly rejected GitHub Actions as 24/7 application hosting.
- Kept persistent application containers on Synology and narrowed retained Synology self-hosted runner authority to target-specific deploy/health/persistence/rollback operations where needed.
- Preserved the hosted build-plane work merged in PR #1609 and immutable GHCR handoff direction.
- Retained `deploy/runtime/**` only as an optional future portability reference.
- Repaired `tests/freqtradebot/test_worker.py::test_throttle_sleep_time` deterministically with `time_machine.travel(..., tick=False)` after exact-head CI exposed hosted-runner wall-clock drift; production Worker runtime code was unchanged.
- Reconciled open Liquid20 repair PR #1610 wording after ADR-025 merge so Synology is described as the canonical persistent runtime rather than transitional-only compute.

## Acceptance

```yaml
acceptance:
  dedicated_linux_required_for_current_portal: false
  synology_persistent_runtime_canonical: true
  github_hosted_stateless_default: true
  github_actions_persistent_hosting: false
  synology_self_hosted_runner_scope: deploy_only_or_target_specific
  hosted_build_plane_from_pr_1609_preserved: true
  real_money_execution_introduced: false
  private_trading_credentials_introduced: false
  automatic_model_activation_introduced: false
  capital_authority_introduced: false
```

## Exact-head validation

Validated implementation head: `255db9d31a6ba8d18275e7e4ce2fe7a4249be62a`.

- Freqtrade CI run `32230397065`: **PASS**.
- Risk-aware component CI run `32230397219`, attempt 2: **PASS**.
  - Portal Web validation and Chromium regression: PASS.
  - Exact Portal image migration/state/API/restart: PASS.
  - OIDC exact-image and PostgreSQL claim probes: PASS.
  - AI Platform tests/lint/sensitive-data scan: PASS.
  - Portal schema SQLite and PostgreSQL rollback/restore: PASS.
  - Program closure backend, Chromium and exact-head closure gate: PASS.
  - Strategy Engine complete validation: PASS.
  - Portal completeness audit: PASS.
  - Universal Portal backend and Chromium E2E: PASS.
  - aggregate Component CI Gate: PASS.
- CodeQL run `32230397066`: **PASS**.
- GitHub Actions security analysis with zizmor run `32230397098`: **PASS**.
- Fresh final-diff audit on the exact validated head: **PASS**, no unresolved material/P0/P1 finding.

## Merge and post-merge proof

- PR #1611 was squash-merged to `develop` as `8d8651d5b0448a4aa959274182f90ed89c26d009`.
- Post-merge verification confirmed `develop` HEAD exactly equals that merge commit.
- GitHub reports the merge commit signature as verified.
- Issue #1604 was closed as `completed` after acceptance verification and terminal closeout evidence was posted.
- The implementation source branch `arch/1604-synology-runtime-github-build-plane` is no longer present after merge.

## Residual work outside this task

PR #1610 / Issue #1608 remain a separate Liquid20 GHCR package-ownership repair. Their implementation direction is compatible with ADR-025: build/publish on GitHub-hosted infrastructure and deploy the persistent runtime to Synology. They do not block completion of #1604.

## Closeout

The architecture decision, exact-head validation, merge, post-merge verification, issue closure, wording reconciliation and source-branch cleanup are complete. This task record is archived and task ownership is released.
