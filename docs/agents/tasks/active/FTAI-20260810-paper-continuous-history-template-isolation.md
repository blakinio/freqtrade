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
isolation_reason: exhausted parent isolation plus exact-head task-template classifier failure
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_gate: 2
```

## Objective

Close the fresh PR #1451 validation isolation without weakening checkpoint identity. Durable active/archive task records must be history-validated, governance templates must not be parsed as persisted task state, and monotonic history must be seeded from the PR base so the first commit cannot reset an existing v2 task.

## Acceptance

- active/archive task records are classified as durable task state;
- `TASK_TEMPLATE.md` and unrelated governance examples are excluded from persisted-task discovery;
- PR history comparison is seeded from the base commit before the first PR commit is evaluated;
- prior exact-SHA entries cannot disappear or decrease across the base→head history;
- touched/new durable task records use checkpoint v2;
- focused regressions and Agent checkpoint history workflow pass on exact final head;
- fresh Codex review has no open material finding;
- runtime/browser E2E is `NOT_APPLICABLE` because this is governance validation only;
- PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.

## Repair history

1. Cycle 1 fixed the proven `TASK_TEMPLATE.md` misclassification and added direct namespace-classification assertions.
2. Self-audit before finalization found that monotonic comparison started at the first `base..head` commit instead of the PR base itself. The validator now seeds `previous_by_task` from the base commit, and a deterministic regression proves a first-commit counter decrease is rejected.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:18:00Z
head: 849fc573eeef6a691287bf9cc264b9d1050d788b
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T21:07:00Z
last_progress_at: 2026-08-10T21:18:00Z
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  e5c820b42af0b02c3b885671415d4309bc51cec4:
    ci: 0
    review: 0
  b1203adf23afbd833044a3a6ca985191f591e44b:
    ci: 0
    review: 0
  849fc573eeef6a691287bf9cc264b9d1050d788b:
    ci: 0
    review: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PR 1451 checkpoint history validation
  - durable task-record namespace classification
  - PR-base monotonic history seeding
owned_paths:
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
proven:
  - Parent isolation exhausted its repair budget and transferred ownership here.
  - Run 31432576481 isolated task-template classification as the only checkpoint-history workflow failure on the prior candidate.
  - Task discovery now includes only active/archive persisted task-record namespaces.
  - Tests explicitly exclude TASK_TEMPLATE and unrelated governance docs.
  - PR-base snapshots now seed monotonic comparison before the first changed commit.
  - A regression simulates base ci=2 and first PR commit ci=0 and requires rejection.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - Both known validation gaps are addressed without weakening exact-SHA checks.
unknown:
  - Terminal exact-head CI and fresh independent Codex disposition on the checkpoint-successor head.
conflicts: []
first_failure:
  marker: task-template false positive followed by self-audited missing PR-base seed
  evidence: run 31432576481 job 93599243414; review of validate_history base initialization
rejected_hypotheses:
  - Weaken exact-SHA validation; rejected because only path classification was wrong.
  - Compare only commits after the base; rejected because the first PR commit could reset existing v2 history.
  - Repair in exhausted parent isolation; rejected by three-cycle limit.
changed_paths:
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-history-template-isolation.md
validation:
  - command: Agent checkpoint history parent cycle-3 candidate
    result: FAIL
    evidence: run 31432576481 job 93599243414; six focused tests passed and only TASK_TEMPLATE placeholder classification failed
  - command: deterministic classifier and PR-base monotonic regressions
    result: NOT_RUN
    evidence: tests updated; exact-head CI pending
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance-validation-only isolation; no runtime browser deployment or trading behavior changes
blockers: []
next_action: Resolve checkpoint-successor exact head, request fresh Codex review and inspect one aggregate CI snapshot. If clear, archive both #1451 isolation tasks and validate the archival successor before merge into parent branch.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: paper-20260810-2307-template-isolation
  session_started_at: 2026-08-10T21:13:00Z
  checkpointed_at: 2026-08-10T21:18:00Z
  last_progress_at: 2026-08-10T21:18:00Z
  phase: final_exact_head_validation
  exact_head: 849fc573eeef6a691287bf9cc264b9d1050d788b
  pull_request: 1451
  active_operation: fresh Codex review and exact-head CI on checkpoint successor
  external_run_ids: []
  operation_started_at: 2026-08-10T21:18:00Z
  wait_deadline_at: 2026-08-10T22:03:00Z
  check_generation: template_isolation_cycle_2_pre_checkpoint
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: checkpoint-successor exact head exists after this commit
  next_action: Resolve live PR 1451 head once, request fresh Codex review, then inspect one aggregate CI snapshot for that exact head.
```
