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

Isolate fresh P1 findings returned after parent PR #1448 exhausted its three repair cycles. Align the root bootstrap with the bounded trusted continuous-programme exception and make ordinary CI/review observation budgets durable per task + exact SHA across later invocations, same-SHA check generations and SHA A → B → A history.

This task is coordination/governance only. PAPER remains the only authorized operational trading mode. LIVE remains unreachable/fail-closed.

## Acceptance

- Root `AGENTS.override.md` preserves the default one-additional-task cap when no trusted override exists.
- Only explicit owner authority or a programme contract already merged on the trusted base may activate continuous rotation.
- Continuous rotation changes task-count coordination only; one writer, dependency/path/ownership preflight and all safety/validation budgets remain intact.
- Checkpoint v2 persists ordinary CI and review observations in `observation_counters_by_sha` keyed by exact lowercase 40-hex SHA.
- Same-SHA reruns, new run IDs, later owner invocations and Chat replacement never reset an entry.
- A genuinely new SHA creates a new entry; returning A → B → A reuses A's existing entry.
- Current-head scalar counters must match the selected head's stored entry.
- Legacy checkpoint v1 remains readable during migration.
- PAPER executor and autonomous coordinator use the same durable-history rule.
- Prompt/governance eval covers the cross-invocation and A → B → A failure modes.
- Runtime/browser E2E is `NOT_APPLICABLE`: no runtime, browser, deployment or trading path changes.

## Repair history

- Parent review P1 `PRRT_kwDOTdDTU86YBBiZ`: root bootstrap contradicted subordinate continuous-mode policy.
- Parent review P1 `PRRT_kwDOTdDTU86YBBib`: later invocations could receive fresh same-SHA polling allowance.
- Isolation repair cycle 1 aligned root bootstrap and anti-stall prose.
- Fresh isolation review P1 `PRRT_kwDOUOD7us6YB0xE`: downstream autonomous/PAPER executors still allowed later-invocation renewal.
- Fresh isolation review P1 `PRRT_kwDOUOD7us6YB0xK`: scalar-only current-head counters lost history through A → B → A.
- Isolation repair cycle 2 introduces checkpoint contract v2, validator enforcement, deterministic A/B/A regression, synchronized coordinator/executor wording and updated prompt eval.

## Prompt-as-code record

```yaml
prompt_contract:
  version: paper-continuous-execution-v2
  changed_surfaces:
    - repository bootstrap instructions
    - anti-stall continuation rule
    - autonomous programme coordinator contract
    - PAPER executor prompt
    - durable checkpoint schema and validator
  objective: continue dependency-safe PAPER work while external gates wait without renewing ordinary polling budgets across later invocations or prior-SHA returns
  baseline_version: paper-continuous-execution-v1
  eval_suite: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  rollback_version: paper-continuous-execution-v1
```

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T20:37:50Z
head: 7b048f4fd01951893a5ff8ad0da0e6ebbc758517
branch: fix/paper-continuous-bootstrap-isolation-20260810
pr: 1451
status: validating
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:37:50Z
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  fe95d6d9ede5ab64bf964e2e36eff5d384ea1b8b:
    ci: 1
    review: 1
  7b048f4fd01951893a5ff8ad0da0e6ebbc758517:
    ci: 0
    review: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - parent PR 1448 continuous programme governance
  - root bootstrap task-count authority
  - durable per-task exact-SHA CI and review observation history
  - checkpoint v2 migration compatibility
  - PAPER executor prompt eval
owned_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - tests/ci/test_agent_checkpoint_observation_history.py
  - tools/agents/checkpoint.py
proven:
  - Parent PR 1448 exact head 49332fadbffcda3c310b2a8031eb298413c1d65e had green Freqtrade, Risk-aware, CodeQL and zizmor CI before isolation.
  - Parent task records three repair cycles, requiring this separate stacked isolation rather than a fourth parent repair.
  - PR 1451 is stacked on the parent branch and cannot bypass parent validation.
  - Root bootstrap now recognizes only trusted owner or already-merged base authority for continuous rotation while preserving the default cap otherwise.
  - Checkpoint contract v2 defines observation_counters_by_sha with CI and review counters per exact SHA and v1 read compatibility.
  - tools/agents/checkpoint.py enforces v2 history shape, current-head presence and scalar/history equality.
  - The deterministic regression covers valid A/B/A reuse, rejected A reset and legacy v1 readability.
  - Autonomous programme and PAPER executor contracts now inherit stored task/SHA history across later invocations and prior-SHA returns.
  - Prompt eval v2 adds S15 later-invocation and S16 A/B/A safety cases plus deterministic regression inventory.
derived:
  - The two fresh isolation P1 findings are addressed by repair cycle 2 without expanding runtime, merge, safety or live-capital authority.
  - Continuous execution remains coordination-only and one-writer by default.
unknown:
  - Exact-head CI result on the successor created by this checkpoint update.
  - Fresh independent Codex disposition on the successor exact head.
conflicts: []
first_failure:
  marker: parent and first isolation candidate did not preserve ordinary observation budget through later invocations and prior-SHA returns
  evidence: Codex threads PRRT_kwDOTdDTU86YBBiZ PRRT_kwDOTdDTU86YBBib PRRT_kwDOUOD7us6YB0xE PRRT_kwDOUOD7us6YB0xK
rejected_hypotheses:
  - Apply a fourth repair directly to parent task; rejected by the three-cycle parent limit.
  - Reset counters per owner invocation; rejected because same-SHA polling would become unbounded.
  - Keep only scalar current-head counters; rejected because A → B → A loses A history.
  - Make checkpoint v2 immediately invalidate every v1 task; rejected in favor of bounded read compatibility.
changed_paths:
  - AGENTS.override.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-bootstrap-isolation.md
  - tests/ci/test_agent_checkpoint_observation_history.py
  - tools/agents/checkpoint.py
validation:
  - command: parent PR 1448 exact-head CI before isolation
    result: PASS
    evidence: Freqtrade 31426530949; Risk-aware 31426531704; CodeQL 31426530964; zizmor 31426531062
  - command: isolation PR 1451 first aggregate CI observation on fe95d6d9ede5ab64bf964e2e36eff5d384ea1b8b
    result: NOT_RUN
    evidence: Freqtrade 31429305702 and Risk-aware 31429305890 were queued at the one recorded observation; no extra same-SHA polling performed
  - command: fresh Codex review of fe95d6d9ede5ab64bf964e2e36eff5d384ea1b8b
    result: FAIL
    evidence: P1 PRRT_kwDOUOD7us6YB0xE and P1 PRRT_kwDOUOD7us6YB0xK; addressed by repair cycle 2 successor
  - command: manual prompt/governance scenario matrix
    result: PASS
    evidence: PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md; 17 same baseline/candidate scenarios, no safety regression in static review; no nondeterministic prompt harness available
  - command: deterministic checkpoint observation-history regression
    result: NOT_RUN
    evidence: tests/ci/test_agent_checkpoint_observation_history.py added; exact-head CI pending
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: governance/checkpoint-only isolation; no runtime, browser, deployment or trading behavior changes
blockers: []
next_action: Resolve PR 1451 successor exact head, resolve the two cycle-2 review threads as remediated, request fresh Codex review and collect the first aggregate exact-head CI observation. If clear, archive this isolation task in the stacked PR and validate the archival successor before merging it into parent branch #1448.
```
