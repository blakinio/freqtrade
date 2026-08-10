# FTAI-20260810 — PAPER Continuous Bootstrap Isolation

```yaml
task_id: FTAI-20260810-paper-continuous-bootstrap-isolation
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: agent-governance
task_kind: isolation_repair
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
parent_pr: 1448
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_gate: 3
```

## Objective

Close the bounded isolation created after parent PR #1448 exhausted its repair budget. The change may improve only continuous-programme coordination and durable checkpoint accounting. PAPER remains the only authorized operational trading mode; LIVE remains unreachable/fail-closed.

## Acceptance

- root bootstrap recognizes a trusted continuous-programme exception without weakening the default cap;
- CI/review observations are durable per task and exact SHA across later invocations, reruns and A→B→A history;
- observation entries are monotonic and non-evicting across Git history;
- every new or touched task record uses checkpoint v2 while untouched legacy v1 stays read-compatible;
- coordinator and PAPER executor use the same durable-history rule;
- manual prompt evaluation is labelled manual/static when no repeated-trial harness exists;
- exact-head CI, fresh independent Codex review and zero unresolved material review threads are required before merge;
- runtime/browser E2E is NOT_APPLICABLE because this is governance/checkpoint-only work.

## Repair history

1. Cycle 1 aligned root bootstrap and continuous-mode coordination.
2. Cycle 2 introduced checkpoint v2 keyed CI/review history and A→B→A regression coverage.
3. Cycle 3 adds Git-history monotonicity enforcement, touched-task v2 migration enforcement, non-evicting history semantics, updated task templates/handoff guidance and an honest manual/static prompt-eval record.

Fresh cycle-2 Codex findings addressed by cycle 3:

- `PRRT_kwDOTdDTU86YB0WL` — prevent rewriting prior-SHA counters;
- `PRRT_kwDOTdDTU86YB0WQ` — restrict v1 compatibility to genuinely legacy untouched records;
- `PRRT_kwDOTdDTU86YB0WU` — do not claim repeated prompt trials when no harness exists;
- `PRRT_kwDOTdDTU86YB0WZ` — preserve observation history beyond the old 32-head ceiling.

## Prompt-as-code record

```yaml
prompt_contract:
  version: paper-continuous-execution-v2
  changed_surfaces:
    - repository bootstrap instructions
    - anti-stall continuation rule
    - autonomous programme coordinator contract
    - PAPER executor prompt
    - durable checkpoint schema, validator and history workflow
  objective: continue dependency-safe PAPER work during external waits without renewing ordinary polling budgets or losing prior-SHA history
  baseline_version: paper-continuous-execution-v1
  eval_suite: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  rollback_version: paper-continuous-execution-v1
```

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:07:00Z
head: a17497b42a7d52122331440ae2ef56be27795085
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T21:07:00Z
last_progress_at: 2026-08-10T21:07:00Z
ci_checks_for_current_head: 1
review_checks_for_current_head: 0
observation_counters_by_sha:
  fe95d6d9ede5ab64bf964e2e36eff5d384ea1b8b:
    ci: 1
    review: 1
  7b048f4fd01951893a5ff8ad0da0e6ebbc758517:
    ci: 0
    review: 0
  b9549121fb43a3c2f9f370ac225c084f3af01c15:
    ci: 1
    review: 1
  a17497b42a7d52122331440ae2ef56be27795085:
    ci: 1
    review: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - parent PR 1448 continuous programme governance
  - root bootstrap authority ordering
  - durable exact-SHA observation history
  - checkpoint v2 migration and monotonicity
  - PAPER executor prompt evaluation
owned_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/TASK_TEMPLATE.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - tools/agents/checkpoint.py
  - tools/agents/validate_checkpoint_history.py
  - tests/ci/test_agent_checkpoint_observation_history.py
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - .github/workflows/agent-checkpoint-history.yml
proven:
  - Parent PR 1448 exhausted three repair cycles and PR 1451 is its existing bounded stacked isolation.
  - Root bootstrap continuous authority is coordination-only and cannot self-grant from an unmerged edit.
  - Checkpoint v2 stores CI and review counters by exact SHA.
  - tools/agents/validate_checkpoint_history.py compares task checkpoints across the PR Git history and rejects removed or decreased prior-SHA counters.
  - The dedicated Agent checkpoint history workflow uses full Git history and validates touched task migration plus deterministic regressions.
  - New and touched task records are required to use v2; untouched v1 records remain read-compatible.
  - Observation history is non-evicting; the parser bound is defensive only and no 32-head archival loss remains authorized.
  - The prompt eval explicitly records that no nondeterministic repeated-trial harness is available and does not call the manual matrix an automated prompt pass.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - Cycle 3 addresses every currently known material Codex finding without expanding runtime, deployment, credential or live-capital authority.
  - Any new material defect after cycle 3 must move to a fresh isolation rather than a fourth repair in this task.
unknown:
  - Terminal exact-head CI result on the checkpoint-successor head.
  - Fresh independent Codex disposition on the checkpoint-successor head.
conflicts: []
first_failure:
  marker: cycle-2 review showed mutable/evictable observation history and unrestricted v1 write compatibility
  evidence: PRRT_kwDOTdDTU86YB0WL PRRT_kwDOTdDTU86YB0WQ PRRT_kwDOTdDTU86YB0WU PRRT_kwDOTdDTU86YB0WZ
rejected_hypotheses:
  - Reset counters per owner invocation; rejected because it permits unbounded same-SHA polling.
  - Keep a 32-SHA eviction ceiling; rejected because returning to an evicted SHA would lose consumed budget.
  - Treat all v1 checkpoints as valid new writes; rejected in favor of untouched-legacy read compatibility only.
  - Claim repeated model trials without an available harness; rejected by evidence and PROMPT_EVAL_STANDARD.
changed_paths:
  - .github/workflows/agent-checkpoint-history.yml
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/tasks/TASK_TEMPLATE.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - tests/ci/test_agent_checkpoint_history_monotonic.py
  - tests/ci/test_agent_checkpoint_observation_history.py
  - tools/agents/checkpoint.py
  - tools/agents/validate_checkpoint_history.py
validation:
  - command: parent PR 1448 exact-head CI before isolation
    result: PASS
    evidence: Freqtrade 31426530949; Risk-aware 31426531704; CodeQL 31426530964; zizmor 31426531062
  - command: independent Codex review of cycle-2 head b9549121fb43a3c2f9f370ac225c084f3af01c15
    result: FAIL
    evidence: four open cycle-3 findings named in Repair history
  - command: manual same-scenario prompt/governance matrix
    result: PASS
    evidence: documented manual/static evaluation; no executable nondeterministic prompt harness available
  - command: Agent checkpoint history plus Freqtrade/Risk-aware exact-head CI for pre-checkpoint a17497b42a7d52122331440ae2ef56be27795085
    result: NOT_RUN
    evidence: runs 31432065543 31432065532 31432065752 were queued at first aggregate observation; checkpoint commit intentionally creates a successor generation
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance/checkpoint/prompt coordination only; no runtime browser deployment or trading behavior changes
blockers: []
next_action: Resolve PR 1451 checkpoint-successor exact head, resolve the four cycle-3 review threads as remediated, request fresh Codex review, and validate exact-head CI. If clear, archive this task in the stacked PR, validate the archival successor, then merge PR 1451 into the parent branch and finish parent PR 1448 closeout.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: paper-20260810-2307
  session_started_at: 2026-08-10T21:07:00Z
  checkpointed_at: 2026-08-10T21:07:00Z
  last_progress_at: 2026-08-10T21:07:00Z
  phase: cycle_3_final_validation
  exact_head: a17497b42a7d52122331440ae2ef56be27795085
  pull_request: 1451
  active_operation: resolve checkpoint-successor head then fresh Codex review and exact-head CI
  external_run_ids: [31432065543, 31432065532, 31432065752]
  operation_started_at: 2026-08-10T21:07:00Z
  wait_deadline_at: 2026-08-10T21:52:00Z
  check_generation: pre_checkpoint_cycle_3
  checks_used: 1
  status: ready
  safe_to_resume: true
  resume_condition: PR 1451 successor exact head exists after this checkpoint commit
  next_action: Resolve the live PR 1451 head once, then request fresh Codex review and inspect the new exact-head CI generation.
```
