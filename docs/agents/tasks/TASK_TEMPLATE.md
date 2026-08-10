---
task_id: FTAI-YYYYMMDD-short-slug
status: implementing
branch: <task-branch>
base_branch: develop
created: YYYY-MM-DD
updated: YYYY-MM-DD
related_pr: ""
owned_paths:
  - <path/glob>
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  # Add task-specific architecture, contract, risk, or program files here.
search_first: []
optional_reads: []
---

# <Task title>

## Goal

<Smallest complete outcome.>

## Acceptance criteria

- <criterion>

## Context checkpoint

Checkpoint version 2 is required for every new task and every legacy task record once it is modified. It persists ordinary CI/review observations by exact commit SHA so later owner invocations, Chat replacement, same-SHA reruns and A -> B -> A returns cannot renew an exhausted observation budget. `ROTATE` is an invocation result, never a task status.

```yaml
checkpoint_version: 2
updated_at: YYYY-MM-DDTHH:MM:SSZ
head: <lowercase-40-hex-commit-sha>
branch: <task-branch>
pr: none
status: investigating # investigating|implementing|validating|ready|waiting|blocked|completed
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  <same-exact-head-sha>:
    ci: 0
    review: 0
context_routes:
  - none
owned_paths:
  - <path/glob>
proven:
  - <current verified fact>
derived: []
unknown:
  - <material unresolved fact or none>
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses: []
changed_paths: []
validation:
  - command: not-run
    result: NOT_RUN # PASS|FAIL|BLOCKED|NOT_RUN|NOT_APPLICABLE
    evidence: task not yet implemented # concrete reason required for NOT_APPLICABLE
blockers: []
next_action: <exactly one concrete next step>
```

The current-head scalar counters must equal the corresponding entry in `observation_counters_by_sha`. Never remove a prior exact-SHA entry or decrease either stored counter. A new exact SHA gets a new entry; returning to an old SHA reuses its stored entry.

## Live-capital boundary

This task record does not authorize model promotion, strategy promotion, production deployment, live trading, capital allocation, withdrawals, or exchange-credential changes.
