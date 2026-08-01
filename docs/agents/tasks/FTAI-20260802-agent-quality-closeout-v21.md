---
task_id: FTAI-20260802-agent-quality-closeout-v21
status: validating
branch: docs/agent-quality-closeout-v21-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: "#988"
required_reads:
  - AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/AGENT_QUALITY_AND_CLOSEOUT.md
search_first:
  - agent quality closeout
  - vertical slice audit e2e pr hygiene
---

# FTAI-20260802 — Agent quality and closeout v2.1

## Objective

Make outcome-based evals, trust boundaries, full-stack vertical slices, independent audit, real E2E, exact-final-head CI, related-PR cleanup, and terminal task closure mandatory for substantial agent work while preserving trading and protected-data boundaries.

## Acceptance

- [x] Add the normative v2.1 contract.
- [x] Make the prompting handover require it.
- [x] Cover all agreed quality and closeout gates.
- [ ] Pass exact-head required CI.
- [ ] Merge and terminally close this task.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-02T00:24:00+02:00
head: cc846ce508bafa8853d029847c89844b568546bb
branch: docs/agent-quality-closeout-v21-20260802
pr: "#988"
status: validating
phase: validate
session_id: chat-20260802-quality-v21
session_role: coordinator
execution_mode: chat
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
owned_paths:
  - docs/agents/AGENT_QUALITY_AND_CLOSEOUT.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/tasks/FTAI-20260802-agent-quality-closeout-v21.md
proven:
  - The v2.1 contract exists and is mandatory in the handover.
  - PR 988 owns the governance contract, handover integration, and task record.
derived:
  - Future substantial work must pass the integrated quality and closeout gate.
unknown:
  - Exact-head CI results after this PR binding update.
conflicts: []
changed_paths:
  - docs/agents/AGENT_QUALITY_AND_CLOSEOUT.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/tasks/FTAI-20260802-agent-quality-closeout-v21.md
validation: []
blockers: []
next_action: verify exact-head CI for PR 988, then complete merge and terminal closeout
```
