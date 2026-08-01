---
task_id: FTAI-20260801-autonomous-program-continuation-v2
status: validating
branch: docs/autonomous-program-continuation-v2-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: "#975"
required_reads:
  - AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
search_first:
  - autonomous program continuation
  - short invocation registry
  - task lifecycle archive
---

# FTAI-20260801 — Autonomous program continuation v2

## Objective

Make one short owner invocation authorize a long, low-noise autonomous programme run that checkpoints safely, completes and archives terminal tasks, crosses barriers, and continues with the next ready work until a real stop condition is reached.

## Scope

Documentation and agent-governance contracts only. No strategy execution, protected-holdout access, credentials, orders, live capital, deployment, upstream-core, or application mutation is authorized.

## Acceptance criteria

- [x] Distinguish one bounded worker session from one long owner invocation.
- [x] Define `run_scope: autonomous_program` and continue-until-real-stop semantics.
- [x] Require terminal task finalization, archival, ownership release, barrier review, and next-READY continuation.
- [x] Route WickHunter and other resolvable short commands into execution instead of returning a long prompt.
- [x] Preserve every trading, protected-data, credential, order, deployment, and live-capital boundary.
- [ ] Pass exact-head required CI.
- [ ] Merge and archive or terminally close this governance task according to Freqtrade convention.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:22:00+02:00
head: a27be52f0d1124855db389543485c0d52e5929fc
branch: docs/autonomous-program-continuation-v2-20260801
pr: "#975"
status: validating
phase: validate
session_id: chat-20260801-autonomous-v2
session_role: coordinator
execution_mode: chat
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
context_routes:
  - agent-governance
owned_paths:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/tasks/FTAI-20260801-autonomous-program-continuation-v2.md
proven:
  - The standard distinguishes bounded worker sessions from a multi-task owner invocation.
  - The autonomous contract requires terminal task finalization, archival, barrier review, and continuation with the next READY task.
  - WickHunter and other resolvable short commands route into execution rather than returning a prompt.
  - Trading safety and authority restrictions remain unchanged.
derived:
  - One short programme command can drive long foreground work without treating each checkpoint or completed task as an owner-interaction boundary.
unknown:
  - Required exact-head CI result for PR 975 after front-matter normalization.
conflicts: []
first_failure:
  marker: none
  evidence: no exact-head failure has been classified on the normalized task head
rejected_hypotheses:
  - weaken worker stop conditions to obtain long programme continuation
  - treat checkpoints as mandatory pauses
  - claim hidden background execution after the final response
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
