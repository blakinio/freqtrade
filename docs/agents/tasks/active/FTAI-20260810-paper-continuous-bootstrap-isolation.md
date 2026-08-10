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
updated_at: 2026-08-10T20:22:30Z
head: 1a6f06660ad1f4f0c343ca6a3eb48d4f85cccc19
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:22:30Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
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
  - Root AGENTS.override.md now keeps the default cap but defines the trusted continuous exception at the highest bootstrap level, with one writer, dependency/path/ownership preflight, and no safety or validation budget expansion.
  - ANTI_STALL_AND_EXECUTION_BUDGET.md now states that ordinary CI/review counters are durable per task and exact SHA across later owner invocations, Chat replacement and same-SHA check generations; only a new exact commit SHA resets the ordinary per-head counter.
  - Stacked PR 1451 targets the parent PR 1448 branch rather than develop, so the isolation repair cannot bypass the parent task's review boundary.
derived:
  - Both parent findings are addressed in one narrow isolation repair without touching runtime, browser, deployment or trading code.
unknown:
  - independent Codex disposition and exact-head CI result on the successor created by this checkpoint
conflicts:
  - none; branch is stacked on the exact parent PR 1448 head
first_failure:
  marker: parent governance contract is internally inconsistent at its highest-priority bootstrap and continuation boundary
  evidence: Codex review on 49332fadbffcda3c310b2a8031eb298413c1d65e; threads PRRT_kwDOTdDTU86YBBiZ and PRRT_kwDOTdDTU86YBBib
rejected_hypotheses:
  - Apply a fourth repair directly to parent task; rejected by max three repair cycles and the parent checkpoint.
  - Reset ordinary counters for each owner invocation; rejected because that enables unbounded same-SHA polling.
changed_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
validation:
  - command: preflight parent PR 1448 live state and review threads
    result: PASS
    evidence: parent head 49332fadbffcda3c310b2a8031eb298413c1d65e; exact-head CI green; two new unresolved P1 findings isolated here
  - command: implementer contract falsification
    result: PASS
    evidence: no-override default remains one additional task; trusted override changes only task-count coordination; same-SHA counters explicitly survive later owner invocations
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance-only repair; no runtime, browser, deployment or trading path changes
blockers:
  - none before stacked PR exact-head CI and fresh independent review
next_action: Resolve live PR 1451 successor head, request independent Codex review, and collect the first bounded exact-head CI observation. If clear, archive this isolation task in the stacked PR, validate the archival successor, merge it into the parent branch, then resume parent PR 1448 final validation.
```
