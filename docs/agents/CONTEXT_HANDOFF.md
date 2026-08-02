# Agent Context Handoff

Chat history is disposable. Git state, the active task checkpoint, the live PR, and deterministic validation evidence are durable state.

## Contract revision

Checkpoint structure remains version 1. Policy revision 2 is backward-compatible: it adds task statuses `waiting` and `completed`, validation result `NOT_APPLICABLE`, and separates task status from terminal invocation result. Existing valid version 1 checkpoints remain valid.

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
2. Update it after material discoveries, changes, validation or CI changes, branch, head or PR changes, blockers, and before session replacement.
3. Validate with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
4. Generate the next-agent prompt with `python tools/agents/resume.py --task <task-path>`.
5. The next agent verifies only live state that can invalidate `next_action`, then continues from that action.

Never pass the previous chat transcript as the handoff.

## Checkpoint schema

```yaml
checkpoint_version: 1
updated_at: YYYY-MM-DDTHH:MM:SSZ
head: <commit-sha-or-UNKNOWN>
branch: <branch>
pr: <number-or-none>
status: investigating|implementing|validating|ready|waiting|blocked|completed
context_routes:
  - <task-relevant route or none>
owned_paths:
  - <path/glob>
proven:
  - <verified fact>
derived:
  - <derived conclusion>
unknown:
  - <unresolved fact>
conflicts:
  - <evidence conflict>
first_failure:
  marker: <first unmet invariant or none>
  evidence: <reference or none>
rejected_hypotheses:
  - <hypothesis and evidence>
changed_paths:
  - <path>
validation:
  - command: <command or workflow>
    result: PASS|FAIL|BLOCKED|NOT_RUN|NOT_APPLICABLE
    evidence: <reference; reason required for NOT_APPLICABLE>
blockers:
  - <blocker or none>
next_action: <exactly one concrete next step>
```

Use `waiting` for an external event with no active worker, `blocked` for a real decision, permission, safety, resource, or exhausted-repair barrier, `ready` when a fresh session can execute `next_action`, and `completed` only after closeout gates pass.

Do not repeat a full preflight when checkpoint and live state agree. Re-run broad discovery only after a material state change, long interruption, session replacement, or a conflict between durable and live state.

Do not store full logs, diffs, source files, old chat, repeated CI history, whole-repository inventories, or superseded hypotheses. `tools/agents/checkpoint.py` enforces compactness ceilings.

A complete handoff identifies the current branch, head and PR; evidence states; first failure; changed paths; validation; task status; blockers; and exactly one next action.
