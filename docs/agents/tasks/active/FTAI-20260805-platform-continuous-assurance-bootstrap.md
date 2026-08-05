---
task_id: FTAI-20260805-platform-continuous-assurance-bootstrap
status: validating
branch: docs/platform-continuous-assurance-agents-20260805
base_branch: develop
base_sha: e9c04506f8dce9df26ae63006229e0d48f1f4209
created: 2026-08-05
updated: 2026-08-05
related_pr: "1243"
programme_lane: freqtrade-assurance
task_kind: documentation
execution_mode: github
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
owned_paths:
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
  - docs/agents/PROJECT_LANES.json
  - docs/agents/tasks/active/FTAI-20260805-platform-continuous-assurance-bootstrap.md
required_reads:
  - AGENTS.md
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/TERMINAL_CI_AND_COMMUNICATION_OVERRIDE.md
---

# Bootstrap the AI Platform Continuous Assurance agents

## Objective

Persist three reusable, short-command-resolvable agent roles for platform audit, parallel Issue repair, and architecture/CI advice, together with a race-resistant Issue claim and path/conflict-group lease protocol.

## Acceptance inventory

- A canonical durable programme defines role boundaries, safety, coverage, Issue schema, grouping, claim, renewal, release, stale takeover and parallelism.
- Exactly three complete canonical role prompts exist: Assurance Auditor, Repair Worker, and Architecture and CI Advisor.
- A short-invocation registry lets the owner start or continue each role without pasting the long prompt.
- Audit findings can be grouped with existing repository labels and machine-readable area/conflict metadata.
- Parallel repair remains limited to disjoint owned/shared paths and conflict groups.
- An Issue claim remains distinguishable even when several agents use the same GitHub account.
- A missing-module bootstrap PR cannot be empty, placeholder-only, fake-UI-only or self-approved by the auditor.
- The new programme is discoverable through `PROJECT_LANES.json`.
- No runtime, strategy, exchange, deployment, secret, production or live-capital behaviour changes.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-05T13:48:00Z
head: d1e8d15f7896c101686960fea3edf0fcf2163627
branch: docs/platform-continuous-assurance-agents-20260805
pr: 1243
status: validating
phase: validate
session_id: agent-20260805-platform-assurance-bootstrap
session_role: implementer
execution_mode: github
lease_expires_at: 2026-08-05T14:33:00Z
context_pressure: medium
context_growth: stable
decomposition_decision: single
context_routes:
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
owned_paths:
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
  - docs/agents/PROJECT_LANES.json
  - docs/agents/tasks/active/FTAI-20260805-platform-continuous-assurance-bootstrap.md
proven:
  - repository already provides programme, type, priority, risk and queue-state labels required by the protocol
  - repository execution policy defines 45-minute leases and 30-minute checkpoint cadence
  - assignee identity alone cannot distinguish several agent sessions using the same GitHub account
  - PR 1243 changes exactly the five declared documentation and governance paths
derived:
  - the authoritative repair lock must use unique claim_id and session_id values plus task, branch and PR state
  - optional area labels improve navigation but machine-readable Issue metadata must remain authoritative
unknown:
  - final required CI result for the exact PR head
conflicts:
  - none
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - assignee or one mutable label alone is a sufficient distributed lock; it cannot distinguish same-account workers or resolve races safely
changed_paths:
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_PROGRAM.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_AGENTS.md
  - docs/agents/prompts/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_SHORT_INVOCATIONS.md
  - docs/agents/PROJECT_LANES.json
  - docs/agents/tasks/active/FTAI-20260805-platform-continuous-assurance-bootstrap.md
validation:
  - command: parse docs/agents/PROJECT_LANES.json as JSON
    result: PASS
    evidence: schema version 2 parsed with six lanes and freqtrade-assurance as the new first matching lane
  - command: fresh documentation and governance audit of PR 1243
    result: PASS
    evidence: exactly three role prompts; short commands resolve through live state; claims handle same-account races; missing-module and safety boundaries are explicit; no material finding open
  - command: required exact-head CI
    result: NOT_RUN
    evidence: pending on the published PR head
blockers:
  - none
next_action: verify required CI on the exact current PR head and merge only after every closeout gate passes
```

## Safety

This task changes agent governance and documentation only. It authorizes no production deployment, protected-environment approval, secret mutation, model or strategy promotion, exchange operation, order submission, withdrawal or live-capital action.
