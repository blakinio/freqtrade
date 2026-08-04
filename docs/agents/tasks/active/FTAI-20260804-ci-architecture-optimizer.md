# FTAI-20260804 — CI architecture audit and optimizer

```yaml
task_id: FTAI-20260804-ci-architecture-optimizer
project_lane: freqtrade-core
status: investigating
phase: investigate
base_branch: develop
base_head_at_start: c236117f2efe6326d24f6cb58c0dabfd96469370
branch: audit/ci-architecture-optimizer-20260804
pull_request: 1191
current_head: 83f8663666de80b693856dd359926d986a61cd5f
policy_version: 2
task_kind: implementation
implementation_authorized: true
execution_mode: github
execution_reason: repository-wide workflow audit and remote GitHub Actions validation
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
context_pressure: high
context_growth: stable
context_score: 11
estimate_confidence: medium
decomposition_decision: phased
decomposition_reason: one cohesive routing contract, one branch and one PR across discovery, implementation, validation and closeout
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
owned_paths:
  - .github/workflows/**
  - .github/actions/**
  - tools/ci/**
  - tests/**/ci/**
  - docs/agents/evidence/FTAI-20260804-ci-architecture-optimizer/**
  - docs/agents/tasks/active/FTAI-20260804-ci-architecture-optimizer.md
  - docs/agents/tasks/archive/FTAI-20260804-ci-architecture-optimizer.md
forbidden_effects:
  - production deployment
  - protected-environment approval
  - live trading or model promotion
  - secret or exchange-credential mutation
  - weakening security, identity, migration, deployment, trading or exact-head acceptance gates
acceptance_inventory:
  - id: CI-001
    criterion: every workflow under .github/workflows is inventoried with triggers, filters, matrices, heavy work, operational purpose and observed cost/failure evidence where available
    status: pending
  - id: CI-002
    criterion: one central tested changed-path and risk classifier emits a machine-readable routing contract
    status: pending
  - id: CI-003
    criterion: ordinary pull requests always receive a lightweight required compile/lint/type/unit gate
    status: pending
  - id: CI-004
    criterion: core, Portal backend, Portal web, schema/database, identity/OIDC, Strategy Engine, deployment and security changes select all required specialist gates
    status: pending
  - id: CI-005
    criterion: docs-only changes skip Docker, PostgreSQL and browser E2E while retaining governance/document validation
    status: pending
  - id: CI-006
    criterion: heavy matrices, exact-image builds, recovery, closure E2E and reproducibility audits run for justified high-risk, ci:full, merge-ready, scheduled or release tiers
    status: pending
  - id: CI-007
    criterion: representative positive, negative and cross-cutting contract tests prove routing and unrelated heavy-gate suppression
    status: pending
  - id: CI-008
    criterion: exact-head lightweight and heavy validation pass with an independent final routing audit
    status: pending
  - id: CI-009
    criterion: before/after selection, retained coverage, cost reduction, residual risks and rollback are documented
    status: pending
related_prs:
  - blakinio/freqtrade#1191 (draft, discovery)
related_branches:
  - ci/smart-freqtrade-test-routing (stale, 0 commits ahead of develop, 1943 commits behind; not reused)
blockers: []
next_action: inspect the first PR-triggered inventory run and download its immutable repository inventory artifact
invocation_started_at: 2026-08-04T18:33:00+02:00
last_progress_at: 2026-08-04T18:38:45+02:00
ci_checks_for_current_head: 1
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Context checkpoint

The owner authorized one phased AUDIT, IMPLEMENTATION AND VALIDATION task for CI routing optimization in `blakinio/freqtrade`, based on `develop`. Required root and agent governance contracts were read from trusted base `c236117f2efe6326d24f6cb58c0dabfd96469370`. No matching open PR or issue was found. The stale branch `ci/smart-freqtrade-test-routing` has no commits ahead of current `develop` and is not active work. Draft PR #1191 now owns the task. A temporary read-only, pinned-action inventory workflow is present only to enumerate repository workflow files and governing paths because the GitHub connector cannot list directories; it must be deleted before final merge.

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: ci-audit-20260804T1833+0200
  session_started_at: 2026-08-04T18:33:00+02:00
  checkpointed_at: 2026-08-04T18:38:45+02:00
  last_progress_at: 2026-08-04T18:38:45+02:00
  phase: investigate
  exact_head: 83f8663666de80b693856dd359926d986a61cd5f
  pull_request: 1191
  active_operation: wait for first PR-triggered inventory workflow generation
  external_run_ids: []
  operation_started_at: 2026-08-04T18:38:45+02:00
  wait_deadline_at: 2026-08-04T19:18:00+02:00
  check_generation: inventory-v1
  checks_used: 1
  status: waiting
  safe_to_resume: true
  resume_condition: PR-triggered workflow runs exist for exact head 83f8663666de80b693856dd359926d986a61cd5f
  next_action: fetch the aggregate workflow-run snapshot once, then download the inventory artifact from the inventory run
```
