---
task_id: FTAI-GOV-002
title: Enable GitHub-native security settings
status: validating
repository: blakinio/freqtrade
base_branch: develop
branch: ci/FTAI-GOV-002-codeql-20260806
issue: 1272
project_lane: freqtrade-assurance
phase: final_ci
session_id: chat-20260806-governance-closeout
session_role: implementation-and-closeout
execution_mode: github
policy_version: 2
task_kind: infrastructure
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
  - .github/workflows/codeql.yml
  - .github/workflow-registry.yaml
  - docs/ci/GITHUB_NATIVE_SECURITY_ADMIN.md
  - docs/agents/tasks/active/FTAI-GOV-002.md
acceptance:
  - explicit CodeQL scanning covers Python and JavaScript/TypeScript
  - CodeQL workflow is pinned and present in the canonical workflow registry
  - repository-native settings are verified or recorded with an exact administrator blocker
  - required review rules remain disabled until a second independent maintainer exists
safety:
  - no branch protection or required check is weakened
  - no placeholder collaborator is added
  - no credential, deployment, trading, withdrawal or live-capital operation
last_progress_at: 2026-08-06T09:39:00+02:00
next_action: validate and merge the CodeQL PR, then persist WAITING state for the remaining GitHub administrator actions
---

# FTAI-GOV-002 durable task record

## Current outcome

The repository-managed portion adds explicit CodeQL scanning for Python and JavaScript/TypeScript and records it in the canonical workflow lifecycle registry.

The remaining Issue #1272 controls require GitHub administrator mutations unavailable through the connected integration. Private vulnerability reporting is verified disabled; repository metadata remains upstream-oriented; topics are empty; and only one direct administrator exists. Dependabot-alert and CodeQL-default-setup endpoints return `403 Resource not accessible by integration`.

## Validation plan

- validate workflow syntax, registry completeness, action pins and permissions;
- execute CodeQL for both declared languages on the exact PR head;
- run required repository CI and workflow security analysis;
- inspect review threads and merge only on a green unchanged head;
- update this record to `waiting` after merge with exactly one administrator next action.
