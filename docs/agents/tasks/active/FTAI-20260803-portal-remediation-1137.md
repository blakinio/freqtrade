# FTAI-20260803 Portal Remediation — Issue 1137

```yaml
task_id: FTAI-20260803-portal-remediation-1137
programme_id: FTAI-20260803-portal-remediation
issue: 1137
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: validate_and_merge
status: validating
priority: medium
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
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
implementation_head: 49a226f47d25b72318364a1734dcd5d78c7df877
pr: 1154
related_prs:
  - pr: 1156
    purpose: integrate current develop after Issue 1127 closeout
    state: merged
    merge_commit: 63901617f2277624373ab31525032ea83352f86b
owned_paths:
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/identity/service_base.py
  - tests/ai_platform/portal/identity/test_oidc_state_claim.py
  - .github/workflows/portal-oidc-state-claim.yml
  - .github/workflows/portal-oidc-state-claim-postgresql.yml
  - docs/ai_platform/portal/OIDC_STATE_CLAIM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
shared_path_leases:
  - mechanism: oidc_login_state_claim
    producer_issue: 1137
    status: held_until_repository_merge
producer_dependencies:
  - existing portal_oidc_login_flows schema
consumer_constraints:
  - do not add a competing migration authority; Issue 1122 owns shared production migrations
  - do not hold a database transaction across provider I/O
  - do not make a claimed state reusable after timeout or process failure
  - do not persist raw state, code, verifier, tokens or provider responses
  - Issue 1132 may claim overlapping identity paths only after this repository merge and lease release
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding and repair

The exact-base implementation performed a non-locking read/check/write transition. Two independent transactions could therefore observe the same pending OIDC login flow and each proceed toward provider exchange.

The repair replaces that transition with one conditional `UPDATE ... RETURNING` whose predicate requires the keyed state identity, `consumed_at IS NULL` and `expires_at > now`. The claim transaction commits before any provider request. Losing callbacks receive the same bounded invalid/expired response and cannot decrypt the verifier, call the provider, create or update identity state, issue a Portal session or emit login success.

The keyed state hash is reused only as the audit correlation identifier. Raw browser state, authorization code, verifier, provider payload and session material remain excluded. A committed claim is terminal: timeout, provider rejection or process death requires a new login flow and never reopens the original state/code.

## Acceptance inventory

- [x] State claim is one production-dialect-safe conditional update with an affected-row/returned-row ownership check.
- [x] The predicate requires matching state identity, `consumed_at IS NULL` and an unexpired row.
- [x] Exactly one concurrent transaction receives the login flow; every loser receives the bounded invalid/replay result.
- [x] Losing callbacks perform no provider exchange, principal update, membership change, Portal session creation or login-success effect.
- [x] Provider I/O remains outside database transactions and row locks.
- [x] Provider timeout, exchange failure or process interruption after claim leaves the browser state terminally consumed.
- [x] Sequential replay and expired-state behavior remain indistinguishable.
- [x] File-backed SQLite is proven through independent connections.
- [x] PostgreSQL 16.13 is executed through two independent connections and proves exactly one durable claim owner.
- [x] Same-code/distinct-code overlap, rollback, expiry, provider failure, missing membership and duplicate-session prevention are covered.
- [x] Audit events use one keyed correlation identifier and exclude raw state, code, verifier and token material.
- [x] Exact control-plane image validation produces a non-empty machine-checked artifact.
- [x] Fresh Portal Completeness Audit and GitHub Actions workflow-security analysis pass on the implementation head.
- [ ] Final full exact-head CI passes after this checkpoint commit.
- [ ] Protected Authentik staging concurrency is executed with synthetic identities under the protected-target boundary.
- [ ] PR #1154 merges without auto-closing Issue #1137 while protected acceptance remains outstanding.
- [ ] Repository ownership/lease releases and the programme continues with Issue #1132.

## Validation evidence

Validated implementation head before this checkpoint: `49a226f47d25b72318364a1734dcd5d78c7df877`.

- Portal OIDC State Claim run `30824017390`: success.
  - exact-image artifact `8860035312`;
  - digest `sha256:d6af01bb25fbeb45330070906b01bdf47905abbf8eb10f989cd72cc28acee659`;
  - one provider owner, one rejected callback and one Portal session;
  - `secret_values_recorded=false`, `live_capital_authorized=false`.
- Portal OIDC State Claim PostgreSQL run `30824017512`: success.
  - PostgreSQL 16.13, two independent connections;
  - outcomes exactly `claimed` and `rejected`;
  - durable claim count exactly one;
  - artifact `8860036269`;
  - digest `sha256:5467a557f139d2b0096352f0f4c222ae2cce33eddcf9e34dc1b1bd2944309d97`;
  - `raw_state_recorded=false`, `secret_values_recorded=false`, `live_capital_authorized=false`.
- AI Platform CI run `30824017347`: success.
- Portal Completeness Audit run `30824017455`: success.
- GitHub Actions Security Analysis run `30824017355`: success.
- Freqtrade CI run `30824017369`: still running when this checkpoint was written; the checkpoint commit must receive a fresh exact-head run.
- Coordinator changed-path review: no unresolved repository-owned material finding after adding real PostgreSQL execution.
- PR comments, reviews and review threads: none unresolved at the checkpoint.

## Protected-target boundary

The repository contains trusted Synology deployment and diagnostic workflows, but the existing public Authentik flow intentionally keeps password/TOTP browser acceptance owner-controlled. No current authorized request can manufacture or disclose those protected credentials. Therefore repository implementation may merge after exact-head gates, but Issue #1137 must remain open and classified `WAITING` until a protected staging run uses a synthetic identity and proves concurrent callbacks against the protected Authentik target. Fixture or isolated provider emulation must not be reported as that acceptance.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-03T14:45:00Z
branch: fix/portal-1137-atomic-oidc-state-claim
head_before_checkpoint: 49a226f47d25b72318364a1734dcd5d78c7df877
pr: 1154
status: validating
proven:
  - atomic conditional claim is implemented and provider I/O starts only after claim commit
  - overlapping callbacks produce one provider exchange and one Portal session in exact-image validation
  - independent file-backed SQLite connections produce one claimant and one rejected loser
  - independent PostgreSQL 16.13 connections produce one durable claimant and one rejected loser
  - claim/rejection/denial/success evidence uses a keyed correlation identifier without raw state or credential material
  - exact-image, AI Platform, Portal Completeness and workflow-security checks passed on implementation head 49a226f47d25b72318364a1734dcd5d78c7df877
derived:
  - repository-owned implementation is ready for final exact-head CI and merge
  - protected Authentik staging acceptance is separable from repository merge but not from Issue closure
unknown:
  - protected Authentik staging concurrency outcome using a synthetic protected-target identity
conflicts: []
first_failure:
  marker: oidc-state-read-check-write-race
  evidence: superseded by atomic update and PostgreSQL/SQLite concurrency proof
rejected_hypotheses:
  - SQL compilation alone proves production-dialect behavior; rejected and replaced with real PostgreSQL execution
  - isolated Authentik health emulation is protected staging callback acceptance; rejected because it performs no protected callback login
  - owner password or TOTP material may be automated or recorded; rejected by the protected identity boundary
changed_paths:
  - .github/workflows/portal-oidc-state-claim-postgresql.yml
  - .github/workflows/portal-oidc-state-claim.yml
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/identity/service_base.py
  - tests/ai_platform/portal/identity/test_oidc_state_claim.py
  - docs/ai_platform/portal/OIDC_STATE_CLAIM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
blockers:
  - authority: protected Authentik staging identity acceptance
    scope: Issue closure only after repository merge
    repository_work_remaining: false after exact-head CI and merge
next_action: Run final exact-head CI for this checkpoint, update PR #1154 so it does not auto-close Issue #1137, merge the repository implementation, then record Issue #1137 as WAITING, release the identity claim lease and start Issue #1132.
```
