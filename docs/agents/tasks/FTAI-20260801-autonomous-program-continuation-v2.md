# FTAI-20260801 — Autonomous program continuation v2

## Objective

Make one short owner invocation authorize a long, low-noise autonomous programme run that checkpoints safely, completes and archives terminal tasks, crosses barriers, and continues with the next ready work until a real stop condition is reached.

## Scope

Documentation and agent-governance contracts only.

Owned paths:

- `docs/agents/PROMPTING_STANDARD.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md`
- this task record

No strategy execution, protected-holdout access, credentials, orders, live capital, deployment, upstream-core, or application mutation is authorized.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T21:19:00Z
head: aafb2a482b8ccc48cfad9d2d7c65ca723b073fd5
branch: docs/autonomous-program-continuation-v2-20260801
pr: 975
status: validating
phase: validate
session_id: chat-20260801-autonomous-v2
session_role: coordinator
execution_mode: chat
context_routes:
  - agent-governance
owned_paths:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/tasks/FTAI-20260801-autonomous-program-continuation-v2.md
proven:
  - The standard now distinguishes bounded worker sessions from a multi-task owner invocation.
  - The new contract requires terminal task finalization, archival, barrier review, and continuation with the next READY task.
  - WickHunter and other resolvable short commands now route into execution rather than returning a prompt.
  - Trading safety and authority restrictions remain unchanged.
derived:
  - One short programme command can now drive long foreground work without treating each checkpoint or completed task as an owner-interaction boundary.
unknown:
  - Required exact-head CI result for PR 975.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses: []
changed_paths:
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/tasks/FTAI-20260801-autonomous-program-continuation-v2.md
validation:
  - command: compare develop...docs/autonomous-program-continuation-v2-20260801
    result: PASS
    evidence: four authorized documentation/governance paths only
blockers: []
next_action: verify required exact-head checks for PR 975 and complete the repository merge gate
```
