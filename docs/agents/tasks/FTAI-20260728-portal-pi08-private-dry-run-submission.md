---
task_id: FTAI-20260728-portal-pi08-private-dry-run-submission
status: implementing
branch: feat/portal-pi08-private-dry-run-submission
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: null
depends_on:
  - FTAI-20260728-portal-pi07-vault-credential-broker
  - FTAI-20260724-portal-pi01-runtime-read-reconciliation
  - FTAI-20260727-portal-bm03-bot-command-persistence
owned_paths:
  - ai_platform/portal/execution_submission/**
  - tests/ai_platform/portal/execution_submission/**
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
  - docs/agents/tasks/FTAI-20260728-portal-pi08-private-dry-run-submission.md
---

# PI-08 private dry-run submission

## Goal

Submit only exact, unexpired, risk-approved intents to the exact private Freqtrade dry-run runtime through PI-07 credentials, while preserving idempotency and treating every accepted transport response as unproven until authoritative reconciliation.

## Acceptance criteria

1. Submission binds the approved intent to exact tenant, bot, config revision, runtime, runtime revision, correlation and idempotency identity.
2. Runtime state must be current, kill switch inactive and environment non-production.
3. PI-07 resolves credentials for the exact connection/runtime; withdrawals and non-dry-run credentials remain impossible.
4. The private transport requires HTTPS, private addressing, CA verification, no redirects, bounded timeout/body and no proxy-environment routing.
5. Runtime configuration is independently verified as `dry_run=true` before submission.
6. Exact duplicate delivery replays the stored attempt; conflicting use of an idempotency key is rejected.
7. HTTP acceptance produces only an acknowledgement with `execution_proven=false` and pending reconciliation.
8. Timeout or malformed/ambiguous response creates one ambiguous attempt and cannot be blindly retried.
9. Success requires exact current/synced authoritative runtime order or trade evidence; absent, partial, stale or mismatched evidence remains pending or fails closed.
10. No browser receives private endpoints, credentials or direct Freqtrade access; no live-capital path is added.

## Non-goals

- no BM-07 position/order command activation;
- no browser API route or direct Freqtrade access;
- no production/live execution, withdrawals or P14 authority;
- no claim that deterministic CI proves real Synology/Vault/Freqtrade target acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T23:30:00+02:00
branch: feat/portal-pi08-private-dry-run-submission
pr: null
status: implementing
base_head: 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b
proven:
  - PI-07 repository acceptance is complete and supplies bounded tenant-scoped credential leases.
  - ApprovedExecutionIntent already freezes approval, tenant, trade-intent and correlation binding.
  - BM execution contracts already distinguish attempt, acknowledgement, ambiguity and authoritative reconciliation.
  - BM-03 stores accepted command intent and supports pending-reconciliation transition without claiming execution success.
derived:
  - PI-08 can be additive and consume frozen contracts without changing public APIs.
  - Submission acknowledgement and execution success must remain separate records.
unknown:
  - Real target endpoint, TLS material and runtime credentials remain owner-managed deployment inputs.
conflicts: []
blockers: []
next_action: Implement exact-bound submission contracts, private dry-run transport, idempotent store, service and reconciliation tests.
```
