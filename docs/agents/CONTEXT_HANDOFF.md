# Agent Context Handoff

Chat history is disposable. Git state, the active task checkpoint, the live PR, and deterministic validation evidence are durable state.

## Contract revision

Checkpoint **version 2** is the write contract for every new or touched task record. It adds durable per-task, exact-SHA CI/review observation history. Untouched legacy version 1 records remain readable during migration, but once such a task record is changed it must be migrated to version 2 in the same change.

Checkpoint task statuses:

```text
investigating | implementing | validating | ready | waiting | blocked | completed
```

Terminal invocation results:

```text
DONE | WAITING | BLOCKED | ROTATE
```

`ROTATE` is not a checkpoint status. Before returning it, persist `ready`, `waiting`, or `blocked` with exactly one concrete `next_action`.

## Portable continuation flow

For every substantial task:

1. Keep one compact `## Context checkpoint` in the active task record.
2. Use checkpoint version 2 for every new or modified task record.
3. Update it after material discoveries, changes, validation or CI changes, branch, head or PR changes, blockers, and before session replacement.
4. Preserve `observation_counters_by_sha` entries for every previously observed exact SHA. Entries may not be removed and their `ci`/`review` counters may not decrease.
5. Validate the current checkpoint with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
6. For PR changes to task records, validate Git-history monotonicity with `python tools/agents/validate_checkpoint_history.py --base <base-sha> --head <head-sha>`; CI runs this with full Git history.
7. Generate the next-agent prompt with `python tools/agents/resume.py --task <task-path>`.
8. The next agent verifies only live state that can invalidate `next_action`, then continues from that action.

Never pass the previous chat transcript as the handoff.

## Checkpoint schema

```yaml
checkpoint_version: 2
updated_at: YYYY-MM-DDTHH:MM:SSZ
head: <lowercase-40-hex-commit-sha>
branch: <branch>
pr: <number-or-none>
status: investigating|implementing|validating|ready|waiting|blocked|completed
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
observation_counters_by_sha:
  <same-exact-head-sha>:
    ci: 0
    review: 0
context_routes:
  - <task-relevant route or none>
owned_paths:
  - <path/glob>
proven:
  - <verified fact>
derived: []
unknown:
  - <material unresolved fact or none>
conflicts: []
first_failure:
  marker: <first unmet invariant or none>
  evidence: <reference or none>
rejected_hypotheses: []
changed_paths: []
validation:
  - command: <command or workflow>
    result: PASS|FAIL|BLOCKED|NOT_RUN|NOT_APPLICABLE
    evidence: <reference; reason required for NOT_APPLICABLE>
blockers: []
next_action: <exactly one concrete next step>
```

The current-head scalar counters must equal that head's entry in `observation_counters_by_sha`. A genuinely new exact SHA gets a new entry. Returning A -> B -> A reuses A's stored counters. Owner continuation, replacement Chat session, workflow rerun, new run ID, draft/ready transition, or a same-SHA check generation never resets them.

Observation history is durable and non-evicting for the lifetime of the task. Do not delete an old SHA entry merely to keep the checkpoint small; compactness rules apply to evidence lists, not to required observation history.

Use `waiting` for an external event with no active worker, `blocked` for a real decision, permission, safety, resource, or exhausted-repair barrier, `ready` when a fresh session can execute `next_action`, and `completed` only after closeout gates pass.

Do not repeat a full preflight when checkpoint and live state agree. Re-run broad discovery only after a material state change, long interruption, session replacement, or a conflict between durable and live state.

Do not store full logs, diffs, source files, old chat, repeated CI history, whole-repository inventories, or superseded hypotheses. `tools/agents/checkpoint.py` enforces compactness ceilings for the bounded evidence fields while the exact-SHA observation map remains durable.

A complete handoff identifies the current branch, head and PR; evidence states; first failure; changed paths; validation; task status; blockers; exact-SHA observation history; and exactly one next action.
