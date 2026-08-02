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

Checkpoint structure remains version 1. Policy revision 2 adds `waiting`, `completed`, and `NOT_APPLICABLE` without invalidating existing checkpoints. `ROTATE` is an invocation result, never a task status.

```yaml
checkpoint_version: 1
updated_at: YYYY-MM-DDTHH:MM:SSZ
head: UNKNOWN
branch: <task-branch>
pr: none
status: investigating # investigating|implementing|validating|ready|waiting|blocked|completed
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

## Live-capital boundary

This task record does not authorize model promotion, strategy promotion, production deployment, live trading, capital allocation, withdrawals, or exchange-credential changes.
