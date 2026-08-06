---
task_id: FTAI-GOV-001
title: Enforce repository contribution, security and branch-hygiene policy
status: final_ci
repository: blakinio/freqtrade
base_branch: develop
branch: chore/FTAI-GOV-001-repository-policy-20260805
issue: 1264
pull_request: 1270
project_lane: freqtrade-assurance
phase: final_ci
session_id: chat-20260806-closeout
session_role: closeout
execution_mode: chat
execution_reason: GitHub-only synchronization, exact-head validation and terminal closeout
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
  - do not modify unrelated runtime or deployment paths
acceptance:
  - invalid pull request titles fail the existing required CI path
  - valid platform and Dependabot titles pass focused tests
  - CODEOWNERS and SECURITY policy exist
  - branch hygiene is dry-run by default and deletes only fully merged safe candidates
  - solo-maintainer review limitation is documented without creating an impossible gate
  - exact-head required CI passes
safety:
  - no branch deletion is executed by this task
  - no branch protection or required check is weakened
  - no deployment, credential, trading, withdrawal or live-capital operation
last_progress_at: 2026-08-06T08:25:00+02:00
recovery:
  policy_version: 1
  generation: 3
  session_id: chat-20260806-closeout
  session_started_at: 2026-08-06T08:25:00+02:00
  checkpointed_at: 2026-08-06T08:25:00+02:00
  last_progress_at: 2026-08-06T08:25:00+02:00
  phase: final exact-head CI after synchronization with develop
  exact_head: 32226d878f57ffe115ea42ff443cc96f080e9ece
  pull_request: 1270
  active_operation: verify exact-head CI, mark ready and merge
  external_run_ids: []
  check_generation: post-develop-3030cf4-sync
  status: active
  safe_to_resume: true
  resume_condition: required checks complete on exact head 32226d878f57ffe115ea42ff443cc96f080e9ece
  next_action: publish synchronized head, verify all required checks, merge PR #1270 and archive task
next_action: publish synchronized head, verify all required checks, merge PR #1270 and archive task
---

# FTAI-GOV-001 durable task record

## Context checkpoint

The repository has one collaborator, `blakinio`. Required independent approval and required Code Owner review remain intentionally disabled because the author cannot independently approve their own pull request. Exact-head CI, fresh audit and resolved review threads remain mandatory.

Runtime E2E is not applicable because the task changes repository governance and deterministic CI policy rather than application runtime behaviour. Focused tests, component CI, security analysis, complete changed-path inspection and terminal PR/task lifecycle are the applicable outcome evidence.

## Validation evidence

- Pre-persistence Python compile validation: PASS.
- Focused policy tests: 28 passed.
- Fresh exact-diff audit: PASS after repairing default-branch evidence and deletion-race handling.
- Exact-head `44ea3d5cd15c8dc6046cdd8526208bb0d1cdcdf6`: full CI PASS before base synchronization.
- Exact-head `041d529e2c2e1f547a9c2b465ad0d31d01e4c14d`: Freqtrade CI, Risk-aware component CI and zizmor PASS.
- `develop` later advanced to `3030cf4914cc093a6b8c546efd7e4cc5fb69457b`; a conflict-free merge tree preserves every current `develop` path plus the exact ten governance paths.
- New synchronized head: `32226d878f57ffe115ea42ff443cc96f080e9ece`.
- Review submissions and review threads previously inspected: none.
- No branch deletion, workflow creation, native security-setting mutation, deployment, credential, trading, withdrawal or live-capital action was executed.
