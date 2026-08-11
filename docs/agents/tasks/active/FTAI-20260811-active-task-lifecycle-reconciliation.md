---
task_id: FTAI-20260811-active-task-lifecycle-reconciliation
programme_id: FTAI-20260805-platform-continuous-assurance
project_lane: freqtrade-assurance
status: implementing
task_kind: governance_reconciliation
priority: high
repository: blakinio/freqtrade
base_branch: develop
trusted_base_sha: cc529499a92819ef6849ca21930c73281cb27295
branch: docs/active-task-lifecycle-reconciliation-20260811
created: 2026-08-11
live_capital_authorized: false
production_deployment_authorized: false
---

# Active task lifecycle reconciliation

## Objective

Reconcile `docs/agents/tasks/active/` against live GitHub state and archive only bounded task records whose own acceptance is already terminal. Preserve genuinely waiting or continuous programme records as active and do not modify product/runtime behavior.

## Candidate terminal records

- `FTAI-20260802-agent-governance-sync.md`: record itself says `completed`; PR #1037 merged as `46bd2f35609af1ce01e159300b7dc9d8e1b863b1`; ownership released.
- `FTAI-20260808-wickhunter-unified-runtime-mode.md`: bounded producer PR #1397 merged as `f46d10e30302b7310fe2a6e235c2ca05a0281a0a`; exact final head `5eee605343b2fbcd1e1e6231ed80315195bd5eba` passed Freqtrade CI, Risk-aware component CI, CodeQL and zizmor and received a clean final Codex review. The larger Issue #1396 remains separate consumer/programme work and does not keep this producer task active.

## Nonterminal records preserved

- `FTAI-20260803-portal-remediation-1137.md`: waiting on protected Authentik staging acceptance; repository work is complete but external protected acceptance is not authorized by this governance task.
- `FTAI-20260803-portal-remediation-program.md`: durable remediation programme remains incomplete.
- `FTAI-20260804-liquidations-monitor-stale-self-heal.md`: PR #1200 merged and exact-head gates passed, but its task contract requires a real post-merge Synology health-dispatch/recovery proof. Current live evidence is insufficient to truthfully assert that exact acceptance, so the record remains active pending a separate operational reconciliation.
- `FTAI-20260805-platform-continuous-assurance.md`: continuous assurance programme is intentionally active.

## Acceptance

- archive only terminal bounded records with exact merge/audit/CI evidence;
- keep waiting/continuous/externally-unproven records under `active/`;
- no product, workflow, runtime, deployment, credential or trading behavior changes;
- fresh independent review has no material finding;
- exact-head governance CI passes;
- ownership for this reconciliation is released after merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T13:30:00+02:00
head: pending_after_task_record
branch: docs/active-task-lifecycle-reconciliation-20260811
pr: pending
status: implementing
context_routes:
  - docs/agents/tasks/active
  - PR #1037
  - PR #1200
  - PR #1397
owned_paths:
  - docs/agents/tasks/active/FTAI-20260802-agent-governance-sync.md
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
  - docs/agents/tasks/archive/FTAI-20260802-agent-governance-sync.md
  - docs/agents/tasks/archive/FTAI-20260808-wickhunter-unified-runtime-mode.md
  - docs/agents/tasks/active/FTAI-20260811-active-task-lifecycle-reconciliation.md
proven:
  - PR 1037 is merged and its task record already declares completion and released ownership
  - PR 1397 is merged; final head 5eee605343b2fbcd1e1e6231ed80315195bd5eba has clean Codex review and all required CI success
  - Issue 1137 remains genuinely waiting on protected acceptance
  - continuous programme records remain nonterminal by contract
  - liquidations task post-merge operational acceptance is not sufficiently proven for archival in this reconciliation
unknown: []
conflicts: []
blockers: []
next_action: materialize the two proven archive moves, request fresh review, run exact-head CI, merge, then verify active/archive truth and branch cleanup.
```

## Safety

PAPER-only. No protected-environment operation, private credential, real order, withdrawal, deployment or LIVE/live-capital authority is introduced.
