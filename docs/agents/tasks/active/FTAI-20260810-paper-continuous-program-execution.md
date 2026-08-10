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
delivery_pr: 1448
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
    - governing docs/agents AGENTS task-count rule
    - repository anti-stall continuation rule
    - autonomous programme coordinator rule
    - PAPER platform executor prompt
  objective: reduce artificial owner-facing stops caused solely by external waits while preserving per-task validation and safety budgets
  baseline_version:
    agents_scope: default one-additional-task rule
    anti_stall: 2
    autonomous_program: 2.2
    paper_executor: 1
  candidate_version:
    agents_scope: trusted continuous exception
    anti_stall: 3
    autonomous_program: 2.3
    paper_executor: 2
  eval_suite: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  rollback_version:
    agents_scope: default one-additional-task rule
    anti_stall: 2
    autonomous_program: 2.2
    paper_executor: 1
```

## Acceptance inventory

- `A1`: default repository behaviour remains bounded to the existing additional-task rule when no trusted continuous-programme override is active.
- `A2`: a trusted explicit owner instruction or trusted-base programme contract may enable `continuous_program_execution: true`, and the governing `docs/agents/AGENTS.md` explicitly recognizes that exception.
- `A3`: the override never resets or enlarges per-exact-commit-SHA CI checks, unchanged-state checks, repair-cycle limits, no-progress limits, command timeouts, authority or safety boundaries; same-SHA reruns/check generations do not reset polling.
- `A4`: before rotating away from a waiting task, the coordinator persists exact durable state and releases unnecessary ownership/worker resources.
- `A5`: only dependency-safe, non-conflicting `READY` work may be selected; dependent work and ownership conflicts remain blocked; default writer concurrency stays one.
- `A6`: within one owner invocation, ordinary polling of waiting work may resume only after a new exact commit SHA; same-SHA reruns, new run IDs, replacement check suites and draft/ready transitions do not reopen the polling budget. A later invocation has its own bounded counters.
- `A7`: the PAPER executor enables continuous programme execution while preserving PAPER-only operation, optional bounded SHADOW and unreachable/fail-closed LIVE.
- `A8`: baseline and candidate are evaluated against the same representative manual scenario matrix with zero safety regression; automation absence is stated explicitly.
- `A9`: exact-head CI, fresh independent review and PR hygiene pass before merge.

## Owned paths

```yaml
owned_paths:
  - docs/agents/AGENTS.md
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

## Independent review remediation

```yaml
reviewed_head: b772a75cc9f04cf157c512b768b4a9115c5be25c
reviewer: chatgpt-codex-connector
submitted_at: 2026-08-10T19:27:03Z
findings:
  - severity: P1
    thread: PRRT_kwDOTdDTU86YAYNM
    summary: higher-level docs/agents/AGENTS.md still unconditionally limited the invocation to one additional task, so subordinate continuous-execution wording could not make the behaviour durable
    remediation:
      - docs/agents/AGENTS.md now preserves the default rule but explicitly delegates to the bounded trusted continuous override
      - waiting-task step also permits safe selection of another READY task only under that override
    remediation_commit: 97841adf1b8980d9d5ecf28d7fb7388a2f5f8fee
  - severity: P1
    thread: PRRT_kwDOTdDTU86YAYNU
    summary: same-SHA workflow reruns/check generations could be misread as a fresh ordinary polling budget
    remediation:
      - anti-stall counters are now keyed to exact commit SHA across all run IDs/check generations within one invocation
      - autonomous coordinator and PAPER executor use the same exact-SHA rule
      - manual eval adds the same-SHA boundary case
    remediation_commits:
      - dc822522bf5f747bcc5a79a0acb9812030441618
      - d3ccd32efc936a3eaaecbe110aa09446bca91f09
      - ec9178a6294f184b2b3dd7115d079f37d599e452
      - 0fc3602720c8e4eb7ea1dae9999544f4c533cd34
repair_cycles_for_current_gate: 1
```

## Validation evidence

```yaml
pre_review_head: b772a75cc9f04cf157c512b768b4a9115c5be25c
pre_review_exact_head_ci:
  freqtrade_ci: 31423832632 success
  risk_aware_component_ci: 31423834503 success
  codeql: 31423832665 success
  zizmor: 31423833005 success
  note: these runs are pre-remediation evidence only and are not final exact-head CI
prompt_eval:
  method: manual_static_contract_review
  automated_harness_available: false
  nondeterministic_trials_available: false
  cases: 14
  candidate_expected_outcomes_met: 14
  safety_regressions: 0
  review_discovered_cases_added:
    - same-SHA rerun/check-generation polling boundary
    - governing AGENTS trusted-override authority
proven:
  - default non-override behaviour retains the one-additional-task rule
  - governing docs/agents/AGENTS.md now recognizes only the bounded trusted continuous exception
  - continuous mode does not enlarge exact-SHA CI checks repair cycles no-progress runtime authority audit E2E or merge gates
  - task switching same-SHA reruns and check-generation changes cannot reset ordinary polling counters
  - dependency-safe and ownership/path-conflict preflight remain mandatory
  - PAPER executor enables one-writer continuous wait rotation
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed
unknown:
  - exact-head CI result on the final remediation successor
  - fresh independent Codex re-review disposition
```

## Checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-10T21:32:41+02:00
last_progress_at: 2026-08-10T21:32:41+02:00
status: validating
next_action: Verify the final changed-file set, resolve the two remediated P1 threads, request fresh Codex review on the current exact head and collect bounded exact-head CI; if clear, archive this task in the same PR and perform final successor validation before merge.
```
