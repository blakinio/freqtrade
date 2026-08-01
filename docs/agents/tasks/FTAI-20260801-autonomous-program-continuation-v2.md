---
task_id: FTAI-20260801-autonomous-program-continuation-v2
status: completed
branch: develop
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
completed: 2026-08-01
related_pr: "#975"
merge_commit: bb171c2babdd0c051ea9f9039e4a67def813aca7
required_reads:
  - AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
search_first:
  - autonomous program continuation
  - short invocation registry
  - task lifecycle archive
---

# FTAI-20260801 — Autonomous program continuation v2

## Objective

Make one short owner invocation authorize a long, low-noise autonomous programme run that checkpoints safely, completes and archives terminal tasks, crosses barriers, and continues with the next ready work until a real stop condition is reached.

## Terminal result

The normative autonomous programme loop, prompting run-scope fields, and short-command handover semantics were merged to `develop` through PR #975 as `bb171c2babdd0c051ea9f9039e4a67def813aca7`.

The merged contract:

- separates bounded worker sessions from one long owner invocation;
- treats checkpoints, commits, PRs, green CI, merges, and task archives as milestones rather than automatic owner-interaction boundaries;
- requires task finalization, archival or terminal state, ownership release, barrier review, and continuation with the next `READY` work;
- preserves every protected-holdout, credential, order, deployment, trading, and live-capital boundary;
- does not claim hidden background execution after the final response.

## Acceptance criteria

- [x] Distinguish one bounded worker session from one long owner invocation.
- [x] Define `run_scope: autonomous_program` and continue-until-real-stop semantics.
- [x] Require terminal task finalization, archival, ownership release, barrier review, and next-READY continuation.
- [x] Route WickHunter and other resolvable short commands into execution instead of returning a long prompt.
- [x] Preserve every trading, protected-data, credential, order, deployment, and live-capital boundary.
- [x] Pass exact-head Freqtrade CI and zizmor.
- [x] Merge the governance contract and terminally close this task.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:31:00+02:00
head: bb171c2babdd0c051ea9f9039e4a67def813aca7
branch: develop
pr: "#975"
status: completed
phase: close
session_id: chat-20260801-autonomous-v2-close
session_role: coordinator
execution_mode: chat
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
context_routes:
  - agent-governance
owned_paths: []
proven:
  - PR 975 merged the autonomous programme continuation contract as bb171c2babdd0c051ea9f9039e4a67def813aca7.
  - Freqtrade CI and zizmor succeeded on exact feature head 8fd0e5115505e2f62772bb7c3c72a66ebd395a3e.
  - The merged files are PROMPTING_STANDARD.md, PROMPTING_HANDOVER.md, AUTONOMOUS_PROGRAM_CONTINUATION.md, and this task record.
  - Trading safety and authority restrictions remain unchanged.
derived:
  - Future resolvable short programme commands can execute long foreground coordinator loops without requiring task-by-task owner prompts.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: no terminal blocker
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
  - command: Freqtrade CI run 30718977941
    result: PASS
    evidence: exact feature head 8fd0e5115505e2f62772bb7c3c72a66ebd395a3e
  - command: zizmor run 30718977943
    result: PASS
    evidence: exact feature head 8fd0e5115505e2f62772bb7c3c72a66ebd395a3e
blockers: []
next_action: apply the merged autonomous programme contract to the next registered short invocation
```
