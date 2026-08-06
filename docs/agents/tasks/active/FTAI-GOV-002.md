---
task_id: FTAI-GOV-002
title: Enable GitHub-native security settings
status: waiting
repository: blakinio/freqtrade
base_branch: develop
implementation_branch: ci/FTAI-GOV-002-codeql-20260806
checkpoint_branch: docs/FTAI-GOV-002-waiting-20260806
issue: 1272
implementation_pull_request: 1288
implementation_head: 34c33654d42c916a5bd7f09feca1136c64e5a34c
implementation_merge: 0091f901ef6055a12888e456fa0c6126c6fdd5f6
project_lane: freqtrade-assurance
phase: administrator_wait
session_id: chat-20260806-governance-closeout
session_role: closeout
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
  completion_claim: repository_managed_portion_complete
owned_paths: []
acceptance:
  - explicit CodeQL scanning covers Python and JavaScript/TypeScript
  - CodeQL workflow is pinned and present in the canonical workflow registry
  - repository-native settings are verified or recorded with an exact administrator blocker
  - required review rules remain disabled until a second independent maintainer exists
safety:
  - no branch protection or required check is weakened
  - no placeholder collaborator is added
  - no credential, deployment, trading, withdrawal or live-capital operation
last_progress_at: 2026-08-06T10:18:00+02:00
waiting:
  blocker: connected GitHub integration exposes no mutation for repository security toggles, repository metadata, collaborators or rulesets; a second trusted maintainer identity is also not authorized
  external_owner: blakinio
  safe_to_resume: true
  resume_condition: owner completes the administrator checklist in docs/ci/GITHUB_NATIVE_SECURITY_ADMIN.md and identifies a second trusted maintainer
  next_action: Repository owner completes the administrator checklist in docs/ci/GITHUB_NATIVE_SECURITY_ADMIN.md, identifies a second trusted maintainer, and then requests verification of Issue #1272.
next_action: Repository owner completes the administrator checklist in docs/ci/GITHUB_NATIVE_SECURITY_ADMIN.md, identifies a second trusted maintainer, and then requests verification of Issue #1272.
---

# FTAI-GOV-002 durable task record

## Repository-managed result

PR #1288 merged explicit CodeQL scanning for Python and JavaScript/TypeScript, registered the workflow as a canonical active entry and added the administrator runbook. The implementation merged into `develop` as `0091f901ef6055a12888e456fa0c6126c6fdd5f6`.

## Exact-head validation

```yaml
implementation_head: 34c33654d42c916a5bd7f09feca1136c64e5a34c
result: PASS
checks:
  - CodeQL Security Analysis run 31082786047
  - Freqtrade CI run 31082786144
  - Risk-aware component CI run 31082786222
  - GitHub Actions Security Analysis with zizmor run 31082785993
audit:
  result: PASS
  material_findings_open: 0
  changed_paths: 4
reviews:
  unresolved_threads: 0
  requested_changes: 0
e2e:
  result: PASS
  evidence:
    - component backend integration
    - Chromium desktop and responsive journeys
    - universal Portal backend and Chromium journeys
```

## Verified administrator blocker

- Private vulnerability reporting is disabled.
- Repository topics are empty and the description still identifies upstream Freqtrade.
- Exactly one direct collaborator exists: `blakinio`, with administrator permission.
- Dependabot-alert and CodeQL-default-setup inspection return `403 Resource not accessible by integration`.
- The connected GitHub tool exposes no supported mutation for these security settings, repository metadata, collaborator invitations or ruleset changes.
- A second independent maintainer cannot be invented or selected by the implementing agent.

The task therefore remains `waiting`, not `completed`. Repository-owned paths and implementation ownership are released. Issue #1272 remains the canonical open administrator checklist.
