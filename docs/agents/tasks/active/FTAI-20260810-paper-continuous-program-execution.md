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

Persist the owner's continuous-execution authorization as a bounded governance capability. Preserve every existing safety, authority, exact-head CI, retry/repair, no-progress and wall-clock limit while allowing a waiting PAPER task to be checkpointed and another dependency-safe, non-conflicting `READY` task to proceed without forcing an owner-facing stop.

The current invocation derives this coordination authority from the explicit owner instruction above. This unmerged task cannot expand its own authority. PAPER remains the only authorized operational trading mode; LIVE remains unreachable/fail-closed.

## Prompt contract and acceptance

```yaml
prompt_contract: paper-continuous-execution-v1
baseline:
  agents_scope: default one-additional-task rule
  anti_stall: 2
  autonomous_program: 2.2
  paper_executor: 1
candidate:
  agents_scope: trusted continuous exception
  anti_stall: 3
  autonomous_program: 2.3
  paper_executor: 2
eval_suite: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
```

- Default repository behaviour remains limited to one additional task when no trusted continuous override exists.
- A trusted owner instruction or trusted-base programme may enable `continuous_program_execution: true`; `docs/agents/AGENTS.md` recognizes that bounded exception.
- The override does not enlarge exact-SHA CI observations, unchanged-state checks, retry/repair cycles, no-progress/runtime, command timeouts, ownership, audit, E2E, merge or authority boundaries.
- Same-SHA reruns, new run IDs, replacement check suites and draft/ready transitions do not reset ordinary polling counters.
- Dependency/path/ownership preflight remains mandatory; default concurrent writers remain one.
- PAPER remains the only authorized operational mode, SHADOW is optional/purpose-bound and LIVE remains unavailable.
- Baseline/candidate use the same 14-case documented manual scenario matrix; automation/trial-runner absence is explicit and safety regressions are zero.

## Independent review history

- Review of `b772a75cc9f04cf157c512b768b4a9115c5be25c` found P1 `PRRT_kwDOTdDTU86YAYNM`: higher-level `docs/agents/AGENTS.md` lacked the trusted override. Remediated by `97841adf1b8980d9d5ecf28d7fb7388a2f5f8fee`.
- The same review found P1 `PRRT_kwDOTdDTU86YAYNU`: same-SHA check generations could be interpreted as new polling budgets. Remediated across anti-stall, autonomous coordinator, PAPER executor and eval by `dc822522bf5f747bcc5a79a0acb9812030441618`, `d3ccd32efc936a3eaaecbe110aa09446bca91f09`, `ec9178a6294f184b2b3dd7115d079f37d599e452`, and `0fc3602720c8e4eb7ea1dae9999544f4c533cd34`.
- Fresh review of `416d0f2f9a110ae88e2d8507ffd0913ea4efcea1` found no new contract defect; P1 `PRRT_kwDOTdDTU86YAkAL` and `PRRT_kwDOTdDTU86YAkAR` concern only this task record's durable checkpoint format and persisted observation counters. This commit remediates both.
- Repair cycles for this governance gate: 2.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T19:38:00Z
head: 416d0f2f9a110ae88e2d8507ffd0913ea4efcea1
branch: docs/paper-continuous-program-execution-20260810
pr: 1448
status: validating
ci_checks_for_current_head: 1
unchanged_state_checks: 0
review_checks_for_current_head: 1
context_routes:
  - PAPER programme coordinator
  - anti-stall wait rotation
  - exact-SHA CI observation budget
owned_paths:
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
proven:
  - Owner explicitly authorized continuous PAPER programme execution for the current invocation.
  - Default non-override behaviour still permits at most one additional task after the entry task.
  - Trusted continuous mode changes task-count and wait rotation only; all safety and validation budgets remain bounded.
  - Ordinary CI observation counters are keyed to exact commit SHA across same-SHA reruns and check generations.
  - Governing docs/agents/AGENTS.md contains the bounded trusted continuous exception.
  - Current exact diff contains six declared governance/prompt/eval/task paths.
  - Manual same-scenario eval contains 14 cases and records zero safety regressions; it is not an automated or repeated-trial result.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - The two contract-level P1 findings from the first Codex review are closed by the current candidate.
  - The fresh review findings on 416d0f2f9a concern durable handoff formatting rather than continuous-execution semantics.
unknown:
  - Terminal exact-head CI result on the successor created by this checkpoint repair.
  - Fresh independent Codex disposition on the successor exact head.
conflicts:
  - none
first_failure:
  marker: durable checkpoint parser rejected the governance task record
  evidence: Codex threads PRRT_kwDOTdDTU86YAkAL and PRRT_kwDOTdDTU86YAkAR on reviewed head 416d0f2f9a110ae88e2d8507ffd0913ea4efcea1
rejected_hypotheses:
  - Subordinate PAPER executor wording alone can override docs/agents/AGENTS.md; rejected by first Codex review.
  - A same-SHA workflow rerun creates a fresh ordinary polling budget; rejected and explicitly forbidden.
changed_paths:
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
  - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md
  - docs/agents/tasks/active/FTAI-20260810-paper-continuous-program-execution.md
validation:
  - command: exact-head CI on pre-review head b772a75cc9f04cf157c512b768b4a9115c5be25c
    result: PASS
    evidence: Freqtrade CI 31423832632; Risk-aware 31423834503; CodeQL 31423832665; zizmor 31423833005
  - command: same-scenario prompt/governance evaluation
    result: PASS
    evidence: docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md; 14 manual static cases; zero safety regressions; automation unavailable
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: coordination/governance-only change; no runtime, browser, deployment or trading behavior is modified
  - command: exact-head CI first observation on 416d0f2f9a110ae88e2d8507ffd0913ea4efcea1
    result: NOT_RUN
    evidence: runs 31424703126, 31424703332, 31424703079 and 31424703063 were queued/pending/in-progress at first observation; successor head now requires fresh validation
blockers:
  - none
next_action: Resolve the live PR 1448 successor head, resolve the two checkpoint-only review threads as remediated, request fresh Codex review, and collect the first bounded exact-head CI observation before either archiving/merging or rotating to other dependency-safe PAPER work.
```
