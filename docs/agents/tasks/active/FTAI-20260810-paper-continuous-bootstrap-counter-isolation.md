# FTAI-20260810 — PAPER Continuous Bootstrap/Counter Isolation

```yaml
task_id: FTAI-20260810-paper-continuous-bootstrap-counter-isolation
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
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: docs/paper-continuous-program-execution-20260810
delivery_pr: 1448
parent_task: FTAI-20260810-paper-continuous-program-execution
isolation_reason: parent governance task exhausted three repair cycles and fresh Codex review found two additional P1 precedence/continuation defects
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Reuse PR #1448 and close only the two fresh review defects without broadening authority: the trusted continuous exception must exist in the mandatory root bootstrap, and ordinary same-SHA CI/unchanged-state observation counters must survive later owner/replacement invocations instead of restarting per invocation.

## Acceptance inventory

- `I1`: preserve all already-proven continuous-execution safety, ownership, audit, E2E, merge and LIVE boundaries.
- `I2`: `AGENTS.override.md` preserves the default one-additional-task cap but delegates to the trusted bounded continuous override when active.
- `I3`: same-SHA ordinary CI and unchanged-state counters are durable across continuation/replacement owner invocations; only a genuinely new exact commit SHA reopens those ordinary counters.
- `I4`: foreground invocation runtime remains a fresh invocation budget, but it cannot reset per-task/per-SHA polling, retry or repair state.
- `I5`: manual same-scenario eval explicitly covers root-bootstrap precedence and cross-invocation same-SHA continuation.
- `I6`: exact-head CI, independent Codex review and zero unresolved material threads are required before merge.
- `I7`: runtime/browser E2E remains `NOT_APPLICABLE`; governance-only change.

## Owned paths

```yaml
owned_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-counter-isolation.md
shared_read_only:
  - docs/agents/AGENTS.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
```

## Repair evidence

```yaml
repair_cycles_for_current_gate: 1
remediated_threads:
  - PRRT_kwDOTdDTU86YBBiZ
  - PRRT_kwDOTdDTU86YBBib
changes:
  - root AGENTS.override.md now preserves the default task cap while explicitly delegating to trusted continuous_program_execution
  - anti-stall policy now keys ordinary CI/unchanged-state counters to task plus exact SHA across later owner replacement and recovery invocations
  - fresh invocation wall-clock budget is explicitly separated from inherited same-SHA task counters
  - manual eval now includes S15 root-bootstrap precedence and S16 cross-invocation same-SHA continuation
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:45:00Z
head: b6bd44ea988540e2dd1c162394a168986366409e
branch: docs/paper-continuous-program-execution-20260810
pr: 1448
status: validating
invocation_started_at: 2026-08-10T20:37:00Z
last_progress_at: 2026-08-10T20:45:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 1
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PAPER programme coordinator
  - root bootstrap precedence
  - durable same-SHA observation counters
owned_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-counter-isolation.md
proven:
  - Parent task exhausted three repair cycles and transferred ownership here.
  - PR 1448 remains the sole delivery PR.
  - Root bootstrap now recognizes the same bounded trusted continuous override as scoped governance.
  - Same-SHA ordinary CI/unchanged-state counters persist across later owner replacement recovery and continuation invocations.
  - Only a genuinely new exact commit SHA reopens ordinary per-head observation counters; fresh invocation runtime does not reset task/head counters.
  - Eval S15 and S16 cover both fresh P1 findings.
  - PAPER remains the only authorized operational mode; LIVE remains unreachable/fail-closed.
derived:
  - Both fresh Codex P1 findings are addressed without widening runtime or trading authority.
unknown:
  - Fresh Codex disposition and exact-head CI on the checkpoint successor head.
conflicts:
  - none
first_failure:
  marker: fresh independent review found root-bootstrap precedence and cross-invocation counter reset defects
  evidence: PRRT_kwDOTdDTU86YBBiZ; PRRT_kwDOTdDTU86YBBib
rejected_hypotheses:
  - Patch the exhausted parent as a fourth repair cycle; rejected by anti-stall repair cap.
  - Treat a later owner invocation as permission to reset same-SHA polling counters; rejected because durable continuation must inherit task/head state.
changed_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-counter-isolation.md
validation:
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: agent-governance only
blockers:
  - none before fresh exact-head CI and independent Codex review
next_action: Resolve live PR 1448 successor head, resolve the two remediated threads, request fresh Codex review, and inspect the new exact-head CI generation once.
```
