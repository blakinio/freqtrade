# FTAI-20260810 — PAPER Continuous Bootstrap Isolation

```yaml
task_id: FTAI-20260810-paper-continuous-bootstrap-isolation
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: agent-governance
task_kind: isolation_repair
phase: implementation
status: implementing
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: docs/paper-continuous-program-execution-20260810
trusted_base_sha: 49332fadbffcda3c310b2a8031eb298413c1d65e
delivery_branch: fix/paper-continuous-bootstrap-isolation-20260810
delivery_pr: pending
parent_pr: 1448
paper_gate: programme_governance
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Isolate the two fresh P1 findings returned after the parent PR #1448 exhausted its three repair cycles. Make the trusted root bootstrap recognize the same bounded continuous-programme exception already defined below it, and make ordinary same-SHA CI observation counters durable across later owner invocations instead of refreshable per invocation.

This task does not enlarge safety, authority, wall-clock, retry, repair, review, E2E, merge, ownership or live-capital boundaries. PAPER remains the only authorized operational trading mode; LIVE remains unreachable/fail-closed.

## Acceptance

- Root `AGENTS.override.md` keeps the default one-additional-task cap when no trusted continuous override exists.
- A trusted explicit owner instruction or programme contract already merged on the trusted base may replace only that fixed task-count rule with bounded continuous rotation.
- The override remains coordination-only, writer concurrency remains one by default, and dependency/path/ownership preflight remains mandatory.
- Ordinary CI/review observation counters are durable per task and exact commit SHA across later owner invocations and same-SHA reruns/check generations.
- Only a genuinely new exact commit SHA resets the ordinary per-head observation counter.
- Parent PR #1448 receives the isolation result only after this stacked PR has independent review, exact-head CI, zero unresolved material threads and closeout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:15:45Z
head: 49332fadbffcda3c310b2a8031eb298413c1d65e
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: pending
status: implementing
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:15:45Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - parent PR 1448 continuous programme governance
  - root bootstrap task-count authority
  - durable per-task per-SHA observation counters
owned_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
proven:
  - Parent PR 1448 exact head 49332fadbffcda3c310b2a8031eb298413c1d65e has green Freqtrade CI, Risk-aware component CI, CodeQL and zizmor.
  - Parent task record explicitly records repair_cycles_for_current_gate 3, so new material findings require fresh isolation rather than a fourth parent repair.
  - Codex thread PRRT_kwDOTdDTU86YBBiZ shows root AGENTS.override.md still unconditionally caps one additional task.
  - Codex thread PRRT_kwDOTdDTU86YBBib shows the anti-stall wording permits later invocations to obtain fresh same-SHA counters.
derived:
  - Both findings can be repaired without touching runtime, browser, deployment or trading code.
unknown:
  - stacked PR number and exact-head validation result
conflicts:
  - none; branch is stacked on the exact parent PR 1448 head
first_failure:
  marker: parent governance contract is internally inconsistent at its highest-priority bootstrap and continuation boundary
  evidence: Codex review on 49332fadbffcda3c310b2a8031eb298413c1d65e; threads PRRT_kwDOTdDTU86YBBiZ and PRRT_kwDOTdDTU86YBBib
rejected_hypotheses:
  - Apply a fourth repair directly to parent task; rejected by max three repair cycles and the parent checkpoint.
  - Reset ordinary counters for each owner invocation; rejected because that enables unbounded same-SHA polling.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
validation:
  - command: preflight parent PR 1448 live state and review threads
    result: PASS
    evidence: parent head 49332fadbffcda3c310b2a8031eb298413c1d65e; exact-head CI green; two new unresolved P1 findings isolated here
blockers:
  - none
next_action: Amend root bootstrap and anti-stall contract narrowly, open a stacked PR to the parent branch, request independent Codex review and exact-head CI, then merge the isolation only if all gates are clear.
```
