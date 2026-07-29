---
task_id: FTAI-20260728-portal-pi08-private-dry-run-submission
status: validating
branch: feat/portal-pi08-private-dry-run-submission
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: 669
depends_on:
  - FTAI-20260728-portal-pi07-vault-credential-broker
  - FTAI-20260724-portal-pi01-runtime-read-reconciliation
  - FTAI-20260727-portal-bm03-bot-command-persistence
owned_paths:
  - ai_platform/portal/execution_submission/**
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/execution_submission/**
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
  - docs/agents/tasks/FTAI-20260728-portal-pi08-private-dry-run-submission.md
---

# PI-08 private dry-run submission

## Goal

Submit only exact, unexpired, risk-approved intents to the exact private Freqtrade dry-run runtime through PI-07 credentials, while preserving idempotency and treating every accepted transport response as unproven until authoritative reconciliation.

## Acceptance criteria

1. Submission binds the approved intent to exact tenant, bot, config revision, runtime, runtime revision, correlation and idempotency identity.
2. Runtime state must be current, healthy, kill switch inactive and environment non-production.
3. PI-07 resolves credentials for the exact connection, exchange and runtime; withdrawals and non-dry-run credentials remain impossible.
4. The private transport requires HTTPS, private addressing, CA verification, no redirects, bounded timeout/body and no proxy-environment routing.
5. Runtime configuration is independently verified as `dry_run=true` before submission.
6. Exact duplicate delivery replays the stored attempt; conflicting use of an idempotency key is rejected.
7. HTTP acceptance produces only an acknowledgement with `execution_proven=false` and pending reconciliation.
8. Timeout or malformed/ambiguous response creates one ambiguous attempt and cannot be blindly retried.
9. Success requires exact current/synced authoritative runtime order evidence; absent, partial, stale or mismatched evidence remains pending or fails closed.
10. No browser receives private endpoints, credentials or direct Freqtrade access; no live-capital path is added.

## Non-goals

- no BM-07 position/order command activation;
- no browser API route or direct Freqtrade access;
- no production/live execution, withdrawals or P14 authority;
- no claim that deterministic CI proves real Synology/Vault/Freqtrade target acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T08:39:00+02:00
validated_code_head: null
merged_commit: null
branch: feat/portal-pi08-private-dry-run-submission
pr: 669
status: validating
base_head: 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
proven:
  - PI-07 repository acceptance is complete and supplies bounded tenant-scoped credential leases.
  - PI-08 reserves a tenant-scoped attempt before network I/O and enforces uniqueness for idempotency, command and approved intent.
  - Private transport requires HTTPS, private addressing, explicit CA verification, no redirects and no proxy environment.
  - Runtime dry-run configuration is independently checked before force-entry submission.
  - Acknowledgement remains execution_proven=false and authoritative reconciliation is a separate terminal gate.
  - Exact replay cannot invoke the transport twice; ambiguity is persisted without blind retry.
derived:
  - The additive adapter can activate PI-08 through trusted server composition while the default Freqtrade adapter remains fail-closed.
  - BM-07 remains blocked until this exact implementation head passes required CI and is merged.
unknown:
  - Real target endpoint, TLS material, Vault initialization and runtime credentials remain owner-managed deployment inputs.
conflicts: []
first_failure: null
changed_paths:
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/execution_submission/**
  - tests/ai_platform/portal/execution_submission/**
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
  - docs/agents/tasks/FTAI-20260728-portal-pi08-private-dry-run-submission.md
validation:
  - command: AI Platform CI on PR 669
    result: PENDING
  - command: Freqtrade CI on PR 669
    result: PENDING
  - command: GitHub Actions security analysis on PR 669
    result: PENDING
blockers: []
next_action: Inspect exact-head PR 669 CI and review findings, fix every failure, then mark ready and squash merge PI-08 before starting BM-07.
```
