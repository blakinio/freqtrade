---
task_id: FTAI-CI-001
title: Inventory and retire historical GitHub Actions workflows
status: review_ready
repository: blakinio/freqtrade
base_branch: develop
branch: feat/FTAI-CI-001-workflow-lifecycle-20260805
issue: 1252
pull_request: 1261
synchronized_base_sha: 7fe304c098aa69b523ec33cf37909a20d5953df0
mode: implementation_and_operational_cleanup
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
owned_paths:
  - .github/workflow-registry.yaml
  - tools/ci/workflow_catalog.py
  - tools/ci/validate_workflows.py
  - tests/ci/test_workflow_catalog.py
  - docs/ci/WORKFLOW_LIFECYCLE.md
  - docs/agents/evidence/FTAI-CI-001/workflow-catalog.json
  - docs/agents/tasks/active/FTAI-CI-001.md
safety:
  - no name-pattern-only workflow disabling
  - retain records owned by open pull requests
  - retain queued, requested, waiting, pending and in-progress runs
  - fail closed when latest-run lookup fails or its status is incomplete
  - no deployment, runtime, credential, trading or live-capital mutation
acceptance:
  - every current workflow is registered and owned
  - every Actions API record is classified
  - no unknown active record remains
  - safe historical records are disabled with ID-level evidence
  - temporary workflows have expiry, owner, tracking and retirement metadata
  - registry completeness, expiry and retirement failures are enforced by CI
  - exact-head CI and workflow security analysis pass
catalog_result:
  generated_at: 2026-08-06T06:57:40.780532+00:00
  source_head: db8f9db71421c8b578fc4da45a3c90334badf459
  total_records: 603
  current_or_bounded_records: 82
  active_records_after: 80
  historical_records: 521
  disabled_records_after: 523
  retired_in_final_run: 13
  retirement_failures: 0
  unknown_active_records: 0
finalizer:
  workflow_id: 328397016
  run_id: 31079052561
  job_id: 92543425939
  result: success
  self_disabled: true
  file_removed: true
validation:
  workflow_catalog_tests: 20_passed
  workflow_registry_validation: passed
  diff_check: passed
next_action: complete exact-head pull-request CI, merge PR 1261, close Issue 1252, and archive this task record
---

# FTAI-CI-001 durable task record

## Result

The authenticated Actions inventory classified all 603 workflow records visible at the final execution point. It identified 521 historical/deleted records and 82 current or bounded records. Thirteen remaining safe historical records were disabled by exact workflow ID during the final run, leaving 523 records disabled and 80 active. No unknown active record and no retirement failure remained.

The finalizer completed successfully, disabled its own workflow ID `328397016`, and was removed from the implementation branch. It is not part of the intended merge diff.

## Controls added

- machine-readable registry for every current workflow file;
- owner, purpose, trigger, permissions, risk, lifecycle and review metadata;
- explicit expiry, tracking and retirement contract for temporary workflows;
- authenticated point-in-time catalog evidence with latest-run and open-PR ownership;
- fail-closed retirement when latest-run lookup fails, returns an incomplete state, reports an active run, or remains owned by an open pull request;
- CI validation for registry completeness, stale entries, expiry, unknown active records and retirement failures;
- focused tests for classification and retirement safety.

Runtime E2E is not applicable because this task changes repository CI governance rather than application behavior. Remaining outcome verification consists only of exact-head CI, workflow security analysis, review and terminal PR state.
