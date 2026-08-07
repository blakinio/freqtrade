---
task_id: FTAI-GOV-002
title: Enable GitHub-native security settings
status: completed
repository: blakinio/freqtrade
base_branch: develop
implementation_branch: ci/FTAI-GOV-002-codeql-20260806
checkpoint_branch: docs/FTAI-GOV-002-waiting-20260806
closeout_branch: docs/FTAI-GOV-002-solo-closeout-20260806
issue: 1272
implementation_pull_request: 1288
implementation_head: 34c33654d42c916a5bd7f09feca1136c64e5a34c
implementation_merge: 0091f901ef6055a12888e456fa0c6126c6fdd5f6
waiting_checkpoint_pull_request: 1289
waiting_checkpoint_merge: 5679d18f557392d6f3673fa3f666116f48c203ba
project_lane: freqtrade-assurance
phase: close
session_id: chat-20260806-governance-solo-closeout
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
  completion_claim: complete
owned_paths: []
acceptance:
  - explicit CodeQL scanning covers Python and JavaScript/TypeScript
  - CodeQL workflow is pinned and present in the canonical workflow registry
  - applicable GitHub-native security settings are enabled with owner-provided UI evidence where API verification is unavailable
  - repository metadata identifies Quant Platform
  - solo-maintainer governance does not require an impossible self-review
safety:
  - no branch protection or required check is weakened merely to bypass a failing pull request
  - no placeholder collaborator is added
  - no credential, deployment, trading, withdrawal or live-capital operation
owner_decision:
  date: 2026-08-06
  maintainer_model: solo
  required_approving_reviews: 0
  required_code_owner_reviews: false
  rationale: the repository owner works alone and GitHub does not allow pull-request authors to approve their own changes
completed_at: 2026-08-06T10:45:00+02:00
next_action: none
---

# FTAI-GOV-002 durable task record

## Result

The GitHub-native security hardening is complete for the repository's actual solo-maintainer operating model.

PR #1288 merged explicit CodeQL scanning for Python and JavaScript/TypeScript, registered the workflow as a canonical active entry and added the administrator runbook. The implementation merged into `develop` as `0091f901ef6055a12888e456fa0c6126c6fdd5f6`.

The repository owner then enabled the applicable native security controls and updated repository metadata. Owner-provided GitHub UI evidence on 2026-08-06 shows:

- private vulnerability reporting enabled;
- dependency graph enabled;
- Dependabot alerts enabled;
- Dependabot malware alerts enabled;
- Dependabot security updates enabled;
- explicit CodeQL Advanced setup active;
- Secret Protection enabled;
- push protection enabled.

The GitHub API independently confirms private vulnerability reporting is enabled and the repository description identifies Quant Platform. Some native settings remain unreadable to the connected integration with `403 Resource not accessible by integration`; the task records that limitation rather than claiming API verification.

## Solo-maintainer decision

The owner confirmed that the repository is intentionally maintained alone. A mandatory approving review or Code Owner review would make owner-authored pull requests unmergeable because GitHub does not permit self-approval.

The accepted governance model therefore keeps independent review requirements disabled while preserving enforceable controls: pull-request delivery, strict CI where supported, CodeQL and workflow-security analysis, applicable component or E2E validation, resolved conversations, squash-only merge, linear history, force-push prohibition, protected-branch deletion prohibition and no bypass of failing checks.

Adding a second maintainer is a possible future hardening step, not an incomplete requirement of this task.

## Implementation validation

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

## Closeout

```yaml
closeout:
  implementation_complete: true
  vertical_slice_complete: true
  audit:
    result: PASS
    independent_validator: fresh governance closeout review
    material_findings_open: 0
  e2e:
    result: NOT_APPLICABLE
    reason: the remaining closeout changes only document the owner-approved governance model and archive the task
  pull_requests:
    implementation: "#1288 merged"
    waiting_checkpoint: "#1289 merged"
    unresolved_review_threads: 0
  task_status: completed
  task_archived: true
  ownership_released: true
```

Issue #1272 is the terminal record for the administrator evidence and owner-approved solo-maintainer exception.
