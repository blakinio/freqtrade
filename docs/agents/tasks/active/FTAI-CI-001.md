---
task_id: FTAI-CI-001
title: Inventory and retire historical GitHub Actions workflows
status: in_progress
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
  - .github/workflows/ftai-ci-001-bootstrap.yml
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
next_action: run the bounded bootstrap inventory and retirement, remove the bootstrap, then validate the final exact head
---

# FTAI-CI-001 durable task record

The implementation branch owns only workflow lifecycle governance, inventory evidence and the bounded bootstrap required to call the authenticated Actions API. The bootstrap must disable itself and be removed before merge.

Runtime E2E is not applicable because this task changes repository CI governance rather than application behavior. Outcome verification consists of the exact API catalog, per-ID retirement results, registry completeness, focused tests, exact-head CI, security analysis and terminal PR state.
