# Agent Context Handoff

Chat history is disposable. Git state, the active task checkpoint, the live PR and deterministic validation evidence are durable state.

For every substantial task:

1. Keep one compact `## Context checkpoint` in the active task record.
2. Update it after material discoveries, changes, validation/CI changes, branch/head/PR changes, blockers, and before session replacement.
3. Validate with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
4. Generate the next-agent prompt with `python tools/agents/resume.py --task <task-path>`.
5. The next agent verifies only live state that can invalidate `next_action`, then continues from that action.

Never pass the previous chat transcript as the handoff.

Checkpoint v1 contains branch/head/PR/status, `PROVEN`, `DERIVED`, `UNKNOWN`, `CONFLICT`, first failure, changed paths, validation, blockers, and exactly one concrete `next_action`.

Do not repeat a full preflight when checkpoint and live state agree. Re-run broad discovery only after material external state change, long interruption/session replacement, or evidence that durable state conflicts with live state.

Do not store full logs, diffs, whole source files, old chat, repeated CI history, whole-repository inventories, or superseded hypotheses. `tools/agents/checkpoint.py` enforces compactness ceilings.
