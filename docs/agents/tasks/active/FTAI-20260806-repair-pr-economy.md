---
task_id: FTAI-20260806-repair-pr-economy
programme_id: FTAI-20260805-platform-continuous-assurance
project_lane: freqtrade-assurance
status: implementing
task_kind: agent_governance
priority: high
repository: blakinio/freqtrade
base_branch: develop
base_head: 186b1473789571300a32bf635b88f1e2795ae16b
branch: docs/repair-pr-economy-20260806
created: 2026-08-06
updated: 2026-08-06
prompting_standard_version: 2.1
execution_policy_version: 2
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
owned_paths:
  - docs/agents/AGENTS.md
  - docs/agents/REPAIR_PR_ECONOMY.md
  - docs/agents/evals/REPAIR_PR_ECONOMY_MANUAL_EVAL.md
  - docs/agents/tasks/active/FTAI-20260806-repair-pr-economy.md
  - docs/agents/tasks/archive/FTAI-20260806-repair-pr-economy.md
shared_path_leases:
  - agent-governance
live_capital_authorized: false
production_deployment_authorized: false
---

# Reduce repair pull-request noise

## Objective

Make Issue repair delivery use the smallest safe number of Pull Requests while preserving atomic Issues, exclusive ownership, independent audit, exact-head CI, rollback and terminal closeout.

## Acceptance inventory

- Repair agents reuse an existing delivery PR before creating another.
- A claim, task record and branch are sufficient ownership evidence; a draft PR is not mandatory at claim time.
- Compatible completed repairs may be integrated through one single-writer repair-train PR.
- High-risk or incompatible work remains isolated in a dedicated PR.
- Audit, validation and task archival do not create one extra PR per repaired Issue.
- The policy explicitly supersedes older immediate-draft instructions without weakening safety or completeness gates.
- Representative positive, negative and boundary cases are recorded for prompt-policy evaluation.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-06T10:31:00Z
status: implementing
proven:
  - develop head is 186b1473789571300a32bf635b88f1e2795ae16b
  - current continuous-assurance Repair Worker text opens a draft PR immediately after every winning claim
  - Issue 1294 already identifies PR 1291 as the preferred repair vehicle, proving reuse is required in live state
unknown: []
blockers: []
next_action: Add the controlling PR-economy policy, evaluation matrix and governing AGENTS.md reference on the dedicated branch.
```
