---
task_id: FTAI-20260802-anti-stall-budget-v1
status: implementing
branch: docs/anti-stall-budget-v1-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: ""
owned_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/tasks/FTAI-20260802-anti-stall-budget-v1.md
---

# Anti-stall and execution budget v1

## Goal

Prevent autonomous agents from polling, retrying, repairing, or selecting tasks indefinitely while preserving repository and trading safety.

## Acceptance

- [x] Add the normative anti-stall contract.
- [x] Require it from the automatically loaded root bootstrap.
- [x] Route local agent execution through it.
- [x] Limit CI checks, identical failures, repair cycles, context reconstruction, command duration, runtime and no-progress time.
- [ ] Pass exact-head required workflows.
- [ ] Merge and terminally close this task.

## Budget checkpoint

```yaml
invocation_started_at: 2026-08-02T10:29:00+02:00
last_progress_at: 2026-08-02T10:29:00+02:00
runtime_limit_minutes: 60
no_progress_minutes: 15
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
next_action: open the implementation PR and verify exact-head checks
```
