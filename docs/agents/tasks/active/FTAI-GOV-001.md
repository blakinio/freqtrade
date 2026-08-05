---
task_id: FTAI-GOV-001
title: Enforce repository contribution, security and branch-hygiene policy
status: validating
repository: blakinio/freqtrade
base_branch: develop
branch: chore/FTAI-GOV-001-repository-policy-20260805
issue: 1264
project_lane: freqtrade-assurance
phase: validate
session_id: chat-20260805-1816
session_role: implementer
execution_mode: chat
execution_reason: GitHub-only bounded repository policy and focused Python changes
policy_version: 2
task_kind: implementation
context_pressure: medium
context_growth: stable
context_score: 8
estimate_confidence: high
decomposition_decision: phased
decomposition_reason: one coherent governance deliverable with staged exact-head validation
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
owned_paths:
  - .github/CODEOWNERS
  - .github/SECURITY.md
  - .github/actions/classify-changes/action.yml
  - .github/dependabot.yml
  - tools/ci/validate_pr_title.py
  - tools/ci/branch_hygiene.py
  - tests/ci/test_validate_pr_title.py
  - tests/ci/test_branch_hygiene.py
  - docs/ci/REPOSITORY_GOVERNANCE.md
  - docs/agents/tasks/active/FTAI-GOV-001.md
overlap_boundaries:
  - do not modify .github/PULL_REQUEST_TEMPLATE.md owned by PR #1215
  - do not modify workflow registry or workflow lifecycle paths owned by PR #1261
  - do not modify ci.yml while PR #1258 owns its online-test policy change
acceptance:
  - invalid pull request titles fail the existing required CI path
  - valid platform and Dependabot titles pass focused tests
  - CODEOWNERS and SECURITY policy exist
  - branch hygiene is dry-run by default and deletes only fully merged safe candidates
  - solo-maintainer review limitation is documented without creating an impossible gate
  - exact-head required CI passes
safety:
  - no branch deletion is executed by this task
  - no workflow is added before workflow registry ownership is reconciled
  - no branch protection or required check is weakened
  - no deployment, credential, trading, withdrawal or live-capital operation
invocation_started_at: 2026-08-05T18:16:00+02:00
last_progress_at: 2026-08-05T18:20:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
recovery:
  policy_version: 1
  generation: 1
  session_id: chat-20260805-1816
  session_started_at: 2026-08-05T18:16:00+02:00
  checkpointed_at: 2026-08-05T18:20:00+02:00
  last_progress_at: 2026-08-05T18:20:00+02:00
  phase: final exact-head CI repair
  exact_head: pending repair commit
  pull_request: 1270
  active_operation: exact-head CI after deterministic Ruff import-spacing repair
  external_run_ids:
    - 31024332392
    - 31024333860
  operation_started_at: 2026-08-05T18:16:00+02:00
  wait_deadline_at: 2026-08-05T19:01:00+02:00
  check_generation: post-ruff-import-spacing-repair
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: fresh required checks exist for the repaired exact head
  next_action: observe aggregate required CI for the repaired exact head and merge only after every gate passes
next_action: persist the deterministic Ruff import-spacing repair and validate fresh exact-head CI
---

# FTAI-GOV-001 durable task record

## Context checkpoint

The live repository has one collaborator, `blakinio`. Therefore one required approval or required Code Owner review cannot be enabled safely yet. PR #1215 owns the pull-request template, PR #1258 owns the current `ci.yml` online-test change and PR #1261 owns workflow lifecycle files. This task uses non-overlapping paths and routes title validation through the existing required classifier action rather than creating another workflow or editing `ci.yml`.

Runtime E2E is not applicable because the task changes repository governance and deterministic CI policy rather than application behavior. Focused tests, the exact final diff, the required `CI Gate`, review-thread state and terminal PR lifecycle are the applicable outcome evidence.

## Focused validation

- Pre-persistence Python compile validation: PASS.
- Pre-persistence focused policy tests: 28 passed.
- Fresh exact-diff audit: PASS after repairing default-branch evidence and deletion-race handling.
- Exact-head run `31024332392` isolated one deterministic formatting gate: Ruff `I001` required the repository-configured two blank lines after import blocks in `tools/ci/branch_hygiene.py` and `tools/ci/validate_pr_title.py`.
- The repair changes only import-block spacing; runtime behavior and safety predicates are unchanged.
- No branch deletion, workflow creation or native GitHub settings mutation was executed.
