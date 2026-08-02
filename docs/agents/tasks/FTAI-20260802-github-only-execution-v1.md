---
task_id: FTAI-20260802-github-only-execution-v1
status: validating
branch: docs/github-only-execution-v1-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: "PENDING"
owned_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/tasks/FTAI-20260802-github-only-execution-v1.md
---

# GitHub-only execution v1

## Goal

Make the GitHub connection and GitHub Actions the mandatory fallback execution path when Codex or a local terminal is unavailable, without weakening trading-capital safety, authorization, scope, validation, or anti-stall limits.

## Acceptance

- [x] Add the normative GitHub-only execution contract.
- [x] Require it from the root bootstrap.
- [x] Route local agent execution through it.
- [x] Preserve bounded validation, capital safety, merge, secret, and production restrictions.
- [ ] Pass exact-head CI.
- [ ] Present a merge-ready PR without merging.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-02T11:43:00+02:00
head: a0ec62bea67c5d464d7be5df10e586885f106ba3
branch: docs/github-only-execution-v1-20260802
pr: PENDING
status: validating
phase: validate
session_id: chat-20260802-github-only-execution-v1
session_role: coordinator
execution_mode: chat-github
run_scope: coordinated_governance_rollout
continuation_policy: continue_until_real_stop
task_completion_policy: prepare_validated_pr_without_merge
user_communication: low_noise
context_routes:
  - agent-governance
owned_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/tasks/FTAI-20260802-github-only-execution-v1.md
proven:
  - The contract and mandatory routing have been added on the dedicated branch.
  - Live trading capital, merge and production remain unauthorized without explicit authority.
derived:
  - Missing Codex or local terminal can no longer be used as a generic blocker.
unknown:
  - Exact-head workflow results after PR creation.
conflicts: []
first_failure:
  marker: none
  evidence: no validation failure observed
rejected_hypotheses:
  - GitHub-only execution authorizes live-capital interaction
  - GitHub-only execution permits unbounded CI retries
changed_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/tasks/FTAI-20260802-github-only-execution-v1.md
validation: []
blockers: []
invocation_started_at: 2026-08-02T11:43:00+02:00
last_progress_at: 2026-08-02T11:43:00+02:00
runtime_limit_minutes: 60
no_progress_minutes: 15
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
next_action: open the draft PR, bind this task to its number, and verify exact-head checks
```
