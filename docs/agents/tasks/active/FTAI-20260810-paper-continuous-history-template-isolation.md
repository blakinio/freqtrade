# FTAI-20260810 — PAPER Continuous History Template Isolation

```yaml
task_id: FTAI-20260810-paper-continuous-history-template-isolation
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: agent-governance
task_kind: repair_isolation
phase: validation
status: validating
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: docs/paper-continuous-program-execution-20260810
trusted_base_sha: 49332fadbffcda3c310b2a8031eb298413c1d65e
delivery_branch: fix/paper-continuous-bootstrap-isolation-20260810
delivery_pr: 1451
parent_task: FTAI-20260810-paper-continuous-bootstrap-isolation
parent_pr: 1448
isolation_reason: parent isolation exhausted three repair cycles and exact-head CI proved the history validator incorrectly classified TASK_TEMPLATE.md as a persisted task record
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_gate: 1
```

## Objective

Reuse stacked PR #1451 and repair only the proven task-record classification defect. The Git-history validator must enforce monotonic checkpoint history for durable active/archive task records while excluding the task template and other governance examples containing placeholder values.

## Acceptance

- active and archived task records are classified as durable task state;
- `docs/agents/tasks/TASK_TEMPLATE.md` and unrelated governance documents are not classified as persisted task records;
- exact-SHA validation remains strict for real task records;
- existing monotonicity, v2 migration and non-eviction invariants remain unchanged;
- focused checkpoint-history regressions and Agent checkpoint history workflow pass on the exact final head;
- fresh independent Codex review has no open material finding before merge;
- runtime/browser E2E is `NOT_APPLICABLE` because this repair changes only governance validation;
- PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.

## Implementation evidence

- run `31432576481`, job `93599243414`: six focused regressions passed; only template placeholder classification failed.
- commit `e5c820b42af0b02c3b885671415d4309bc51cec4` restricts history discovery to `docs/agents/tasks/active/` and `docs/agents/tasks/archive/` records.
- commit `b1203adf23afbd833044a3a6ca985191f591e44b` adds deterministic classification assertions for active, archive, `TASK_TEMPLATE.md`, and unrelated governance docs.
- exhausted parent task is blocked and ownership is transferred to this successor.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:16:00Z
head: b1203adf23afbd833044a3a6ca985191f591e44b
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T21:07:00Z
last_progress_at: 2026-08-10T21:16:00Z
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  e5c820b42af0b02c3b885671415d4309bc51cec4:
    ci: 0
    review: 0
  b1203adf23afbd833044a3a6ca985191f591e44b:
    ci: 0
    review: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PR 1451 checkpoint history validation
  - durable task-record namespace classification
  - checkpoint v2 monotonic history
owned_paths:
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
proven:
  - Parent isolation reached repair cycle 3 and transferred ownership here.
  - Exact-head CI isolated template classification as the only Agent checkpoint history failure on the cycle-3 candidate.
  - History discovery now includes only active/archive task-record namespaces.
  - A focused regression explicitly rejects TASK_TEMPLATE and unrelated governance docs as task records.
  - Exact-SHA validation remains unchanged for real task records.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - The defect is repaired without weakening checkpoint identity or migration rules.
unknown:
  - Terminal exact-head CI and fresh independent Codex disposition on the checkpoint-successor head.
conflicts: []
first_failure:
  marker: checkpoint history validator parsed task-template placeholder as exact SHA
  evidence: run 31432576481 job 93599243414
rejected_hypotheses:
  - Weaken exact-SHA validation globally; rejected because only task-record classification was wrong.
  - Continue as repair cycle 4 in the exhausted parent isolation; rejected by governance.
changed_paths:
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
validation:
  - command: Agent checkpoint history parent cycle-3 candidate
    result: FAIL
    evidence: run 31432576481 job 93599243414; six focused tests passed and only task-template placeholder classification failed
  - command: deterministic task-record classifier regression
    result: NOT_RUN
    evidence: added in tests/ci/test_agent_checkpoint_history_monotonic.py; exact-head CI pending
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance-validation-only repair; no runtime browser deployment or trading behavior changes
blockers: []
next_action: Resolve the checkpoint-successor exact head, request fresh Codex review, and inspect the first aggregate exact-head CI generation. If clear, archive both PR-1451 isolation tasks and perform final archival-head validation before merge into parent branch.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: paper-20260810-2307-template-isolation
  session_started_at: 2026-08-10T21:13:00Z
  checkpointed_at: 2026-08-10T21:16:00Z
  last_progress_at: 2026-08-10T21:16:00Z
  phase: final_exact_head_validation
  exact_head: b1203adf23afbd833044a3a6ca985191f591e44b
  pull_request: 1451
  active_operation: fresh Codex review and exact-head CI on checkpoint successor
  external_run_ids: []
  operation_started_at: 2026-08-10T21:16:00Z
  wait_deadline_at: 2026-08-10T22:01:00Z
  check_generation: template_isolation_pre_checkpoint
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: checkpoint-successor exact head exists after this commit
  next_action: Resolve live PR 1451 head once, request fresh Codex review, then inspect one aggregate CI snapshot for that exact head.
```
