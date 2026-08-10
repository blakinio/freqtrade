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
prompt_contract:
  version: paper-continuous-execution-v1
  changed_surfaces:
    - docs/agents/AGENTS.md trusted continuous-task exception
    - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md wait rotation and exact-SHA observation rules
    - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md coordinator continuation rules
    - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md PAPER executor routing
    - docs/agents/evals/PAPER_CONTINUOUS_EXECUTION_EVAL_20260810.md same-scenario evaluation
  objective: reduce artificial owner-facing stops caused solely by external waits while preserving every per-task validation safety and authority budget
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

- Default repository behaviour remains limited to one additional task when no trusted continuous override exists.
- A trusted owner instruction or trusted-base programme may enable `continuous_program_execution: true`; `docs/agents/AGENTS.md` recognizes that bounded exception.
- The override does not enlarge exact-SHA CI observations, unchanged-state checks, retry/repair cycles, no-progress/runtime, command timeouts, ownership, audit, E2E, merge or authority boundaries.
- Same-SHA reruns, new run IDs, replacement check suites and draft/ready transitions do not reset ordinary polling counters.
- Dependency/path/ownership preflight remains mandatory; default concurrent writers remain one.
- PAPER remains the only authorized operational mode, SHADOW is optional/purpose-bound and LIVE remains unavailable.
- Baseline/candidate use the same 14-case documented manual scenario matrix; automation/trial-runner absence is explicit and safety regressions are zero.

## Independent review history

- Review of `b772a75cc9f04cf157c512b768b4a9115c5be25c` found P1 `PRRT_kwDOTdDTU86YAYNM`: higher-level `docs/agents/AGENTS.md` lacked the trusted override. Remediated by `97841adf1b8980d9d5ecf28d7fb7388a2f5f8fee`.
- The same review found P1 `PRRT_kwDOTdDTU86YAYNU`: same-SHA check generations could be interpreted as new polling budgets. Remediated across anti-stall, autonomous coordinator, PAPER executor and eval.
- Review of `416d0f2f9a110ae88e2d8507ffd0913ea4efcea1` found P1 `PRRT_kwDOTdDTU86YAkAL` and `PRRT_kwDOTdDTU86YAkAR` in durable checkpoint format/counters. Remediated before `983e239a1faa344103050234928a8bb1c7cf2de7`.
- Review of `983e239a1faa344103050234928a8bb1c7cf2de7` found P1 `PRRT_kwDOTdDTU86YAtrW` for incomplete persisted anti-stall state and P2 `PRRT_kwDOTdDTU86YAtrj` for an incomplete prompt-as-code record. This commit remediates both.
- Repair cycles for this governance gate after this remediation: 3.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T19:56:00Z
head: 983e239a1faa344103050234928a8bb1c7cf2de7
branch: docs/paper-continuous-program-execution-20260810
pr: 1448
status: validating
invocation_started_at: 2026-08-10T19:14:00Z
last_progress_at: 2026-08-10T19:56:00Z
ci_checks_for_current_head: 1
unchanged_state_checks: 0
review_checks_for_current_head: 1
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PAPER programme coordinator
  - anti-stall wait rotation
  - exact-SHA CI observation budget
  - prompt-as-code evaluation and rollback
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
  - Current candidate diff contains six declared governance/prompt/eval/task paths.
  - Manual same-scenario eval contains 14 cases and records zero safety regressions; it is not an automated or repeated-trial result.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
  - The complete prompt contract now records changed surfaces objective baseline candidate evaluation and rollback versions.
derived:
  - All known contract-level findings are addressed in the current candidate.
  - This is the third repair cycle for this governance gate; any additional material finding requires a fresh isolation task instead of a fourth repair here.
unknown:
  - Terminal exact-head CI result on the successor created by this checkpoint repair.
  - Fresh independent Codex disposition on the successor exact head.
conflicts:
  - none
first_failure:
  marker: durable handoff did not preserve all applicable anti-stall counters and complete prompt-as-code rollback metadata
  evidence: Codex threads PRRT_kwDOTdDTU86YAtrW and PRRT_kwDOTdDTU86YAtrj on reviewed head 983e239a1faa344103050234928a8bb1c7cf2de7
rejected_hypotheses:
  - A partial counter set is sufficient for safe continuation; rejected because it can reset foreground/no-progress/repair budgets.
  - A flattened baseline/candidate summary is sufficient prompt-as-code evidence; rejected by PROMPT_EVAL_STANDARD review.
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
  - command: independent Codex review of 983e239a1faa344103050234928a8bb1c7cf2de7
    result: FAIL
    evidence: PRRT_kwDOTdDTU86YAtrW and PRRT_kwDOTdDTU86YAtrj; both remediated by this checkpoint successor
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: coordination/governance-only change; no runtime, browser, deployment or trading behavior is modified
blockers:
  - none before fresh independent review and exact-head CI of the successor created by this checkpoint repair
next_action: Resolve live PR 1448 successor head, resolve PRRT_kwDOTdDTU86YAtrW and PRRT_kwDOTdDTU86YAtrj as remediated, request fresh Codex review and validate exact-head CI. Any new material defect must rotate to a fresh isolation task; if clear, archive this task in the same PR and complete final successor validation before merge.
```
