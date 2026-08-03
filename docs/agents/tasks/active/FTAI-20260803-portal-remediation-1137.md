# FTAI-20260803 Portal Remediation — Issue 1137

```yaml
task_id: FTAI-20260803-portal-remediation-1137
programme_id: FTAI-20260803-portal-remediation
issue: 1137
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: reproduce
status: implementing
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
base_head: 2b5824d7c9633eedcadf8510d0339406b4d3bf82
pr: none
owned_paths:
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/service.py
  - tests/ai_platform/portal/identity/test_identity_lifecycle.py
  - tests/ai_platform/portal/identity/test_oidc_state_claim.py
  - docs/ai_platform/portal/OIDC_STATE_CLAIM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
shared_path_leases:
  - mechanism: oidc_login_state_claim
    producer_issue: 1137
    status: held
producer_dependencies:
  - existing portal_oidc_login_flows schema
consumer_constraints:
  - do not add a competing migration authority; Issue 1122 owns shared production migrations
  - do not hold a database transaction across provider I/O
  - do not make a claimed state reusable after timeout or process failure
  - do not persist raw state, code, verifier, tokens or provider responses
  - programme-file reconciliation remains serialized behind Issue 1127 closeout
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding reproduced

On exact base `2b5824d7c9633eedcadf8510d0339406b4d3bf82`, `IdentityRepository.consume_login_flow()` performs a non-locking `session.get()` followed by checks, assignment to `consumed_at` and `flush()`. Its generated update has no `WHERE consumed_at IS NULL AND expires_at > :now` compare-and-swap predicate. Two independent transactions can therefore read the same pending row and each commit a successful transition.

`IdentityService.complete_login()` commits state consumption before invoking the provider, which correctly keeps provider I/O outside the database transaction. The safe smallest complete repository-owned repair is therefore an atomic conditional claim that terminally consumes the state before exchange. A provider timeout or process crash remains fail-closed: the original browser state is not reusable, and the user must begin a fresh login flow. This avoids a schema migration and does not compete with Issue #1122.

## Acceptance inventory

- [ ] State claim is one production-dialect-safe conditional update with an affected-row check.
- [ ] The predicate requires matching state identity, `consumed_at IS NULL` and an unexpired row.
- [ ] Exactly one concurrent transaction receives the decrypted login flow; every loser receives the same bounded invalid/replay result.
- [ ] Losing callbacks perform no provider exchange, principal update, membership change, Portal session creation or login-success audit effect.
- [ ] Provider I/O remains outside all database transactions and row locks.
- [ ] Provider timeout, exchange failure or process death after claim leaves the state terminally consumed; recovery requires a new login flow, never code/state replay.
- [ ] Sequential replay and expired-state behavior remain indistinguishable and reveal no account, tenant or session existence.
- [ ] SQLite behavior is proven with independent sessions/connections; production-dialect SQL compilation proves the conditional predicate.
- [ ] Tests cover same code, distinct codes with one state, concurrent workers, rollback/lock contention and no duplicate session issuance.
- [ ] Audit/correlation evidence contains only existing request/correlation identifiers and no raw state, code, verifier or token.
- [ ] Focused identity tests, full AI Platform CI, exact-image/API-mode identity checks and fresh changed-path audit pass.
- [ ] PR merges, Issue #1137 closes, task archives and the claim lease releases.

## Safety

- Claim identity is the existing one-way state hash and is not exported.
- Raw authorization code, browser state, PKCE verifier, ID/access token and provider response remain outside audit and error payloads.
- A claim is short and committed before provider I/O.
- Failure after claim cannot reopen or lease the browser-provided state to another callback.
- No production identity provider, credential or protected deployment is modified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T12:43:00Z
head: 2b5824d7c9633eedcadf8510d0339406b4d3bf82
branch: fix/portal-1137-atomic-oidc-state-claim
pr: none
status: implementing
proven:
  - consume_login_flow is a read-check-write race on the exact base
  - complete_login commits before provider exchange and therefore does not hold provider I/O inside a transaction
  - existing schema has a unique state_hash and nullable consumed_at suitable for a conditional update
  - sequential replay coverage exists but no same-state concurrent callback test exists
  - no duplicate task, branch or implementation PR exists for Issue 1137
derived:
  - a conditional update can provide exclusive terminal claim without a schema migration
  - fail-closed terminal consumption after provider timeout satisfies non-reuse and deterministic recovery through a new login flow
unknown:
  - exact supported production dialect SQL rowcount behavior, to prove through compiled SQL and CI integration database coverage
conflicts: []
first_failure:
  marker: oidc-state-read-check-write-race
  evidence: IdentityRepository.consume_login_flow on exact base
rejected_hypotheses:
  - a row lock should span provider exchange; rejected because provider I/O must remain outside database transactions
  - consumed state should be reopened after provider timeout; rejected because browser state/code replay must never become recovery authority
  - a new status migration is mandatory; rejected pending proof because the complete fail-closed terminal-claim behavior fits the existing consumed_at schema
changed_paths:
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
validation:
  - command: exact-base static concurrency reproduction
    result: FAIL_EXPECTED
    evidence: no conditional update, version check or affected-row ownership test
blockers: []
next_action: Replace the read-check-write consume path with an atomic conditional update and add independent-session concurrent callback tests proving one provider owner and one Portal session.
```
