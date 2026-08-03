# FTAI-20260803 Portal Remediation — Issue 1137

```yaml
task_id: FTAI-20260803-portal-remediation-1137
programme_id: FTAI-20260803-portal-remediation
issue: 1137
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: protected_acceptance
status: waiting
priority: medium
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: low
decomposition_decision: single
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: backend_identity_security
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
branch: fix/portal-1137-atomic-oidc-state-claim
base_branch: develop
base_head: c19f9881127485bc4a5090510765199d972956de
implementation_head: 5dc6261e294e5324ee8baca6caff8fc3129cc0ab
pr: 1154
pr_state: merged
merge_commit: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
related_prs:
  - pr: 1156
    purpose: integrate current develop after Issue 1127 closeout
    state: merged
    merge_commit: 63901617f2277624373ab31525032ea83352f86b
owned_paths: []
shared_path_leases: []
repository_work_remaining: false
external_acceptance_remaining: true
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Repository result

PR `#1154` replaced the non-locking OIDC state read/check/write sequence with one conditional `UPDATE ... RETURNING` claim whose predicate requires the keyed state identity, `consumed_at IS NULL` and `expires_at > now`. The claim transaction commits before provider I/O. A losing callback cannot obtain the verifier, call the provider, mutate principal or membership state, issue a Portal session or emit duplicate login-success evidence.

A committed claim is terminal. Provider rejection, timeout or process interruption cannot reopen the original state or code. Audit correlation uses only the keyed state identifier; raw browser state, authorization code, PKCE verifier, provider payload and session material remain excluded.

## Acceptance inventory

- [x] Atomic conditional claim with affected-row ownership check.
- [x] Exactly one callback owner and one bounded losing result under concurrent delivery.
- [x] No provider exchange, identity mutation, session issuance or success audit by a loser.
- [x] Provider I/O occurs outside database transactions and row locks.
- [x] Timeout, failure and interruption leave the state terminally consumed.
- [x] Sequential replay and expired-state responses remain bounded and non-enumerating.
- [x] Independent file-backed SQLite connections prove exactly one owner.
- [x] Independent PostgreSQL 16.13 connections prove exactly one durable owner.
- [x] Same-code, distinct-code, rollback, expiry, provider-failure, membership and duplicate-session cases are covered.
- [x] Exact control-plane image produces non-empty machine-checked evidence.
- [x] Fresh Portal Completeness Audit and workflow-security analysis pass.
- [x] Full exact-head Freqtrade CI passes.
- [x] PR `#1154` merged without auto-closing Issue `#1137`.
- [x] Repository ownership and the OIDC state-claim lease are released.
- [ ] Protected Authentik staging concurrency passes using an authorized synthetic protected-target identity.
- [ ] Issue `#1137` closes and this task archives after protected acceptance.

## Exact-head evidence

Validated implementation head: `5dc6261e294e5324ee8baca6caff8fc3129cc0ab`.

- Freqtrade CI `30824694901`: success.
- AI Platform CI `30824694834`: success.
- Portal Completeness Audit `30824696000`: success.
- GitHub Actions Security Analysis `30824694865`: success.
- Portal OIDC State Claim exact-image run `30824694973`: success.
  - artifact `8860313666`;
  - digest `sha256:ce29f185c0fb6c9985eb665dacf8adf08fbd6b3a82645a9b46ab073bed41cbb7`.
- PostgreSQL independent-connection run `30824695775`: success.
  - artifact `8860316412`;
  - digest `sha256:bfbcc2252d228679985dc0b69fada31e6f55582601046e22ef6b643a88b2f7b9`.
- PR comments/reviews: one pin-metadata finding corrected.
- Unresolved review threads: zero.
- Merge: squash commit `f1bf851733ecc870f61c1206b0ee0fe8755c6e67`.

## Protected-target boundary

The remaining acceptance is one protected-environment operation: run two concurrent callbacks through the protected Authentik staging target using an authorized synthetic identity. Existing owner password/TOTP material is not authorized for repository automation or evidence. Isolated provider emulation, exact-image tests and local Authentik health checks are supporting evidence only and must not be reported as protected-target acceptance.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-03T15:10:00Z
status: waiting
branch: fix/portal-1137-atomic-oidc-state-claim
implementation_head: 5dc6261e294e5324ee8baca6caff8fc3129cc0ab
pr: 1154
merge_commit: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
proven:
  - repository implementation, focused validation, production-dialect concurrency proof, exact-image proof, independent audit, review hygiene and exact-head CI are complete
  - issue remains open because the protected Authentik staging criterion has not been executed
  - repository ownership and shared-path lease are released
  - no protected credential, production deployment, trading, withdrawal or live-capital mutation occurred
derived:
  - independent Issue 1132 work may now claim the overlapping identity paths
unknown:
  - protected Authentik staging concurrency outcome using an authorized synthetic identity
conflicts: []
blocker:
  authority: protected Authentik staging identity acceptance
  repository_work_remaining: false
  scope: Issue closure and task archival only
next_action: Execute the protected Authentik staging concurrent-callback test with an authorized synthetic identity, then close Issue 1137 and archive this task if it passes.
```
