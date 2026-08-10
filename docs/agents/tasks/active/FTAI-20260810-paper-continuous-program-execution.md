# FTAI-20260810 — PAPER Continuous Programme Execution

```yaml
task_id: FTAI-20260810-paper-continuous-program-execution
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: agent-governance
task_kind: agent_governance
phase: validation
status: validating
priority: high
prompting_standard_version: 2.1
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: docs/paper-continuous-program-execution-20260810
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
owner_authorization:
  granted_at: 2026-08-10T21:14:00+02:00
  scope: allow the PAPER implementation programme to continue across dependency-safe independent tasks instead of ending the owner invocation whenever one task waits on external CI or review
```

## Objective

Persist the owner's continuous-execution authorization as a bounded governance capability. Preserve all existing safety, authority, exact-head CI, repair, no-progress and wall-clock limits while allowing the PAPER coordinator to checkpoint a waiting task and move to another dependency-safe `READY` task without forcing an owner-facing stop.

This task does not self-authorize any LIVE, credential, production or protected-environment action. The current invocation already has explicit owner authority; the merged governance change makes the behaviour durable for future PAPER invocations.

## Prompt contract

```yaml
prompt_contract:
  version: paper-continuous-execution-v1
  changed_surfaces:
    - repository anti-stall continuation rule
    - autonomous programme coordinator rule
    - PAPER platform executor prompt
  objective: reduce artificial owner-facing stops caused solely by external waits while preserving per-task validation and safety budgets
  baseline_version:
    anti_stall: 2
    autonomous_program: 2.2
    paper_executor: 1
  candidate_version:
    anti_stall: 3
    autonomous_program: 2.3
    paper_executor: 2
  eval_suite: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  rollback_version:
    anti_stall: 2
    autonomous_program: 2.2
    paper_executor: 1
```

## Acceptance inventory

- `A1`: default repository behaviour remains bounded to the existing additional-task rule when no trusted continuous-programme override is active.
- `A2`: a trusted explicit owner instruction or trusted-base programme contract may enable `continuous_program_execution: true`.
- `A3`: the override never resets or enlarges per-exact-head CI checks, unchanged-state checks, repair-cycle limits, no-progress limits, command timeouts, authority or safety boundaries.
- `A4`: before rotating away from a waiting task, the coordinator persists exact durable state and releases unnecessary ownership/worker resources.
- `A5`: only dependency-safe, non-conflicting `READY` work may be selected; dependent work and ownership conflicts remain blocked; default writer concurrency stays one.
- `A6`: waiting work may be revisited only after a material external-state change or new exact head; polling counters remain attached to their task/head generation.
- `A7`: the PAPER executor enables continuous programme execution while preserving PAPER-only operation, optional bounded SHADOW and unreachable/fail-closed LIVE.
- `A8`: baseline and candidate are evaluated against the same representative manual scenario matrix with zero safety regression; automation absence is stated explicitly.
- `A9`: exact-head CI, independent review and PR hygiene pass before merge.

## Owned paths

```yaml
owned_paths:
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
```

## Safety invariants

- `PAPER` remains the only authorized operational trading mode.
- `SHADOW` remains optional and purpose-bound.
- `LIVE` remains unreachable/fail-closed.
- No real exchange order, live capital, private trading credential, protected Synology/Cloudflare/Auth/Vault/DNS mutation or production deployment is authorized.
- Continuous execution changes coordination only; it does not weaken completion, review, audit, E2E or exact-head gates.

## Validation evidence

```yaml
implementation_head_before_checkpoint: 8f324a703170460f49b353c22ab5944c64bd0686
changed_file_count: 5
changed_paths:
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
branch_compare:
  base: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
  status: ahead
  behind_by: 0
prompt_eval:
  method: manual_static_contract_review
  automated_harness_available: false
  cases: 12
  safety_regressions: 0
  intended_improvements:
    - external-wait rotation to independent READY work
    - more than one sequential independent PAPER task within remaining foreground budget
proven:
  - default non-override behaviour retains the one-additional-task rule
  - continuous mode does not enlarge per-head CI checks repair cycles no-progress runtime authority audit E2E or merge gates
  - task switching cannot reset counters and waiting work cannot be polled again solely because time passed
  - dependency-safe and ownership/path-conflict preflight remain mandatory
  - PAPER executor enables one-writer continuous wait rotation
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed
unknown:
  - exact-head CI result on the final task-record successor
  - independent Codex review disposition
```

## Checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:22:24+02:00
last_progress_at: 2026-08-10T21:22:24+02:00
status: validating
next_action: Open the bounded governance PR, request independent Codex review, validate exact final diff and exact-head CI, then merge/archive if clear while continuing dependency-safe PAPER work during external waits.
```
