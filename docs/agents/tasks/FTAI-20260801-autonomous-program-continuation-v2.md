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
updated_at: 2026-08-01T21:10:00Z
head: UNKNOWN
branch: docs/autonomous-program-continuation-v2-20260801
pr: none
status: implementing
phase: implement
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
  - Current v2 prompting rules checkpoint durable state but do not explicitly require a coordinator to archive a completed task and continue to the next READY task in the same owner invocation.
  - WickHunter short invocation already demonstrates repository-backed programme resumption.
derived:
  - A normative autonomous-program loop can generalize the successful WickHunter behavior without weakening trading safety boundaries.
unknown:
  - Exact final CI result for this documentation branch.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses: []
changed_paths:
  - docs/agents/tasks/FTAI-20260801-autonomous-program-continuation-v2.md
validation:
  - command: documentation and checkpoint validation
    result: NOT_RUN
    evidence: pending coherent documentation update
blockers: []
next_action: update the prompting standard, coordinator handover, and autonomous programme continuation contract
```
