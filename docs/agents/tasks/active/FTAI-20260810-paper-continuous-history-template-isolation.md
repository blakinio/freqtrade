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

Reuse stacked PR #1451 and repair only the proven task-record classification defect. `tools/agents/validate_checkpoint_history.py` must enforce monotonic checkpoint history for persisted active/archive task records while excluding `TASK_TEMPLATE.md` and other governance examples containing placeholder values.

## Acceptance

- active task records under `docs/agents/tasks/active/*.md` are classified as task records;
- archived task records under `docs/agents/tasks/archive/*.md` are classified as task records;
- `docs/agents/tasks/TASK_TEMPLATE.md` is not classified as a persisted task record;
- the existing monotonicity, v2 migration and non-eviction invariants remain unchanged;
- focused checkpoint-history regressions and the Agent checkpoint history workflow pass on the exact final head;
- fresh independent Codex review has no open material finding before merge;
- runtime/browser E2E is `NOT_APPLICABLE` because this repair changes only governance validation;
- PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.

## Evidence

- Agent checkpoint history run `31432576481`, job `93599243414`: focused deterministic tests passed `6 passed`; the only failing validator errors were `TASK_TEMPLATE.md: invalid observation SHA '<same-exact-head-sha>'`.
- Repair commit `e5c820b42af0b02c3b885671415d4309bc51cec4` restricts task history discovery to active/archive task-record namespaces.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:13:00Z
head: e5c820b42af0b02c3b885671415d4309bc51cec4
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T21:07:00Z
last_progress_at: 2026-08-10T21:13:00Z
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  e5c820b42af0b02c3b885671415d4309bc51cec4:
    ci: 0
    review: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PR 1451 checkpoint history validation
  - persisted task-record path classification
  - checkpoint v2 monotonic history
owned_paths:
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
proven:
  - Parent isolation reached repair cycle 3 and cannot accept a fourth repair.
  - Exact-head CI isolated one classifier defect after all six focused history tests passed.
  - TASK_TEMPLATE.md is a governance template, not durable task state.
  - The repair keeps active/archive task records inside history enforcement.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - A narrow path classifier plus regression is sufficient; no checkpoint schema or runtime change is required.
unknown:
  - Exact-head CI and fresh Codex result after the classifier regression is added.
conflicts: []
first_failure:
  marker: checkpoint history validator parsed template placeholder as an exact SHA
  evidence: run 31432576481 job 93599243414
rejected_hypotheses:
  - Weaken exact-SHA validation globally; rejected because only the template classification is wrong.
  - Continue as repair cycle 4 in the parent isolation; rejected by the three-cycle gate limit.
changed_paths:
  - tools/agents/validate_checkpoint_history.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
validation:
  - command: Agent checkpoint history on parent cycle-3 head 64b94a99eb1c820e09226b735b0134bc247aafbf
    result: FAIL
    evidence: run 31432576481 job 93599243414; focused tests passed and only TASK_TEMPLATE placeholder classification failed
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance-validation-only repair; no runtime browser deployment or trading behavior changes
blockers: []
next_action: Add a deterministic regression for active/archive versus TASK_TEMPLATE classification, checkpoint the parent ownership transfer, then request fresh Codex review and exact-head CI for the successor head.
```
