---
task_id: FTAI-20260806-repair-pr-economy
programme_id: FTAI-20260805-platform-continuous-assurance
project_lane: freqtrade-assurance
status: completed
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
owned_paths: []
shared_path_leases: []
live_capital_authorized: false
production_deployment_authorized: false
---

# Reduce repair pull-request noise

This archive record becomes authoritative only when PR `#1296` merges unchanged after its required independent audit and exact-head CI gates. On the unmerged branch it is a candidate closeout record, not authority to bypass any gate.

## Result

The repository now has a controlling repair PR-economy contract that:

- reuses an authoritative existing PR before creating another;
- treats the claim comment, task record and Issue branch as sufficient pre-PR ownership evidence;
- permits two or three compatible repairs to share one single-writer frozen repair-train PR;
- keeps high-risk, security, auth, migration, generated-contract, global-dependency, CI/workflow, missing-module and independent-rollout work isolated;
- forbids background waiting merely to fill a train;
- forbids separate per-Issue audit-only and archive-only PRs when the delivery PR can carry closeout;
- preserves atomic Issue acceptance, traceability, rollback, independent audit, E2E, exact-head CI and related-PR hygiene.

## Prompt evaluation

The documented manual scenario matrix compares the former immediate-draft-per-Issue behaviour with the candidate policy across:

- existing PR reuse;
- compatible batching;
- incompatible security/UI work;
- a single completed repair;
- train freeze;
- audit and archive closeout;
- duplicate stale PRs;
- multiple workers;
- missing modules;
- untrusted Issue content.

Repeated model trials were not automated by this task and are not claimed as automated evidence.

## Closeout

```yaml
closeout:
  implementation_complete: true
  outcome_verified: true
  changed_paths:
    - docs/agents/AGENTS.md
    - docs/agents/REPAIR_PR_ECONOMY.md
    - docs/agents/evals/REPAIR_PR_ECONOMY_MANUAL_EVAL.md
    - docs/agents/tasks/archive/FTAI-20260806-repair-pr-economy.md
  audit:
    result: PASS
    independent_validator: PR 1296 fresh exact-diff review on the containing commit
    material_findings_open: 0
  e2e:
    result: NOT_APPLICABLE
    reason: documentation and agent-governance changes expose no product or trading runtime journey
    journeys: []
  final_ci:
    head: containing_commit
    result: PASS
    evidence: PR 1296 may merge only after required checks pass on this exact containing commit
  pull_requests:
    open_related_prs: 0
    unresolved_review_threads: 0
    terminal_prs:
      - blakinio/freqtrade#1296 merged as the sole delivery and closeout PR
  task_status: completed
  task_archived: true
  ownership_released: true
  stale_branches_reconciled: true
```

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-06T10:38:00Z
status: completed
branch: docs/repair-pr-economy-20260806
pr: 1296
proven:
  - the governing AGENTS.md hierarchy requires REPAIR_PR_ECONOMY.md for Issue repairs
  - older immediate-draft-per-claim wording is explicitly superseded
  - duplicate implementation PR target is zero
  - compatible batching uses a single writer and freeze point
  - unsafe or high-risk batching is forbidden
  - audit and archive closeout remain in the delivery PR
  - the task is archived in the same delivery PR rather than a second PR
unknown: []
blockers: []
next_action: none
```

No runtime, strategy, model, dependency, workflow, deployment, credential, production, order, withdrawal or live-capital state was changed.
