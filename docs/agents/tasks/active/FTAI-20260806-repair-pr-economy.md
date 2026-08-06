---
task_id: FTAI-20260806-repair-pr-economy
programme_id: FTAI-20260805-platform-continuous-assurance
project_lane: freqtrade-assurance
status: validating
task_kind: agent_governance
priority: high
repository: blakinio/freqtrade
base_branch: develop
base_head: 186b1473789571300a32bf635b88f1e2795ae16b
branch: docs/repair-pr-economy-20260806
related_pr: 1296
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

## Validation evidence

- PR `#1296` contains exactly the four declared governance paths.
- Static prompt-policy matrix covers existing-PR reuse, compatible batching, incompatible isolation, single-item delivery, freeze, audit/archive closeout, stale duplicates, multiple workers, missing modules and untrusted Issue content.
- Runtime E2E is `NOT_APPLICABLE` because no product or trading runtime changes.
- Exact-head CI and fresh documentation/governance audit remain pending on the final candidate head.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-06T10:35:00Z
status: validating
branch: docs/repair-pr-economy-20260806
pr: 1296
candidate_head: eb3db6a95dc3185d34566b032df73761537ed5df
proven:
  - controlling policy exists at docs/agents/REPAIR_PR_ECONOMY.md
  - governing docs/agents/AGENTS.md requires the policy and explicitly supersedes immediate-draft-per-claim wording
  - duplicate implementation PR target is zero
  - compatible repairs use a single-writer frozen repair train
  - high-risk and incompatible repairs remain isolated
  - audit and archive-only per-Issue PRs are forbidden
unknown:
  - final exact-head CI result
  - final independent documentation/governance audit result
blockers: []
next_action: Complete fresh exact-diff audit, archive this task in PR 1296, then require final exact-head CI before merge.
```
