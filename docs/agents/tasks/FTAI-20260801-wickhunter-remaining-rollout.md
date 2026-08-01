---
task_id: FTAI-20260801-wickhunter-remaining-rollout
project_lane: freqtrade-wickhunter
status: ready
branch: develop
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 941
depends_on: []
owned_paths:
  - docs/agents/plans/WICKHUNTER_REMAINING_ROLLOUT.md
  - docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-remaining-rollout.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md
  - docs/agents/PROMPTING_HANDOVER.md
required_reads:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/PROJECT_LANES.json
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/plans/WICKHUNTER_REMAINING_ROLLOUT.md
  - docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md
---

# WickHunter remaining rollout coordinator

## Objective

Coordinate the dependency-ordered completion of WH-02, WH-03, WH-04, WH-05, WH-07, WH-08 and WH-09 through shadow/paper readiness with no more than two simultaneous code-writing workers.

## Invocation

The repository owner may invoke this task with only:

```text
Uruchom WickHunter.
```

or:

```text
Kontynuuj WickHunter autonomicznie.
```

The coordinator resolves the next phase from this checkpoint and the linked package checkpoints. The owner never needs to paste the generated worker prompt.

## Responsibilities

- verify live Git, PR, CI, task freshness and path ownership at each barrier;
- select only tasks whose dependencies are terminal;
- keep waiting tasks without active workers;
- ensure shared contracts have exactly one writer;
- cap code-writing parallelism at two;
- prefer fresh validator sessions on the same task;
- close request-only operational PRs without merge after terminal outcomes;
- update the durable wave/barrier state;
- escalate only material owner decisions.

## Package graph

```text
WH-02 -> WH-03 -> WH-04
              \-> WH-05 baseline -> WH-05 model-aware after WH-04
WH-02 + WH-03 + WH-04 + WH-05 + completed WH-06 -> WH-07
WH-07 contract -> WH-08
WH-07 + WH-08 -> WH-09
```

WH-07 and WH-08 may perform read-only discovery before their implementation dependencies are complete. They checkpoint `waiting` and exit after discovery.

## Acceptance

- all eight rollout task records pass checkpoint validation;
- every task has one current `next_action`;
- dependencies and writable paths do not conflict;
- short invocation routing is documented in the authoritative handover;
- the coordinator documentation passed exact-head checks and merged normally;
- no product runtime, credential, order or live-capital authority changes.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T15:38:00+02:00
project_lane: freqtrade-wickhunter
phase: integrate
session_id: coordinator-20260801-002
session_role: coordinator
execution_mode: chat
execution_reason: live barrier coordination and task dispatch from durable repository state
status: ready
branch: develop
head: 5187a2475f35cb5de31f742056ca0b1929ebbd58
base_branch: develop
related_pr: 941
context_pressure: medium
context_growth: stable
decomposition_decision: split
decomposition_reason: seven packages have independent durable outputs and explicit dependency barriers
validation_level: full
heavy_validation_runs: 1
proven:
  - WH-00, WH-01 and WH-06 are completed
  - request-only PR 935 materialized and independently verified the exact WH-02 aggregate-trade path, then closed unmerged
  - seven product packages remain
  - eight durable tasks and 22 bounded session phases are recorded in the repository
  - short owner invocations are registered and integrated into PROMPTING_HANDOVER.md
  - PR 941 changed only the declared eleven documentation/task paths
  - PR 941 exact-head Freqtrade CI and zizmor completed successfully
  - PR 941 merged normally as 5187a2475f35cb5de31f742056ca0b1929ebbd58
derived:
  - at most two simultaneous code writers preserve useful parallelism without ownership collisions
  - Wave 1 may combine WH-02 work with read-only WH-07 discovery
unknown:
  - live state of open PRs, CI and ownership at the next invocation
  - final owned code paths until each package performs its required ownership preflight
conflicts:
  - WH-08 implementation must not overlap an active Portal PR
first_relevant_error: null
changed_paths:
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/plans/WICKHUNTER_REMAINING_ROLLOUT.md
  - docs/agents/prompts/WICKHUNTER_SHORT_INVOCATIONS.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-remaining-rollout.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md
validation:
  - command: exact-head Freqtrade CI on PR 941
    result: PASS
  - command: exact-head GitHub Actions security analysis on PR 941
    result: PASS
  - command: changed-path and review-thread audit
    result: PASS
blockers: []
next_action: run the Wave 1 barrier selection from live state and dispatch only the READY phases recorded by the package checkpoints
```
