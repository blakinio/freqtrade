---
task_id: FTAI-CI-001
title: Inventory and retire historical GitHub Actions workflows
status: review_ready
repository: blakinio/freqtrade
base_branch: develop
branch: feat/FTAI-CI-001-workflow-lifecycle-20260805
issue: 1252
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
  - no deployment, runtime, credential, trading or live-capital mutation
acceptance:
  - every current workflow is registered and owned
  - every Actions API record is classified
  - no unknown active record remains
  - safe historical records are disabled with ID-level evidence
  - temporary workflows have expiry, owner, tracking and retirement metadata
  - registry completeness and expiry are enforced by CI
  - exact-head CI and workflow security analysis pass
catalog_result:
  generated_at: 2026-08-05T15:17:33.977372+00:00
  source_head: 72a71b49076b58e5be00c87def5f493d135cf80d
  total_records: 590
  current_or_bounded_active_records: 82
  historical_records_retired: 508
  retirement_failures: 0
  unknown_active_records: 0
bootstrap:
  workflow_id: 327913109
  run_id: 31019497210
  result: success
  self_disabled: true
  file_removed: true
next_action: synchronize with the final architecture review merge, open the implementation PR, and validate its exact head
---

# FTAI-CI-001 durable task record

## Result

The authenticated Actions inventory classified all 590 catalog records visible at the execution point. It safely disabled 508 historical records by exact workflow ID. Eighty-two records remained active because they were current repository workflows or bounded records owned by open pull requests. No unknown active record and no retirement failure remained.

The temporary bootstrap completed successfully, disabled its own workflow ID and was removed from the implementation branch. It is not part of the intended merge diff.

## Controls added

- machine-readable registry for every current workflow file;
- owner, purpose, trigger, permissions, risk, lifecycle and review metadata;
- explicit expiry, tracking and retirement contract for temporary workflows;
- authenticated point-in-time catalog evidence with latest-run and open-PR ownership;
- fail-closed CI validation for registry completeness, stale entries, expiry and unknown active records;
- focused tests for classification and retirement safety.

Runtime E2E is not applicable because this task changes repository CI governance rather than application behavior. Remaining outcome verification consists of synchronization with current `develop`, exact-head CI, workflow security analysis, review and terminal PR state.
