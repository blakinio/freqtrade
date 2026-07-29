---
task_id: FTAI-20260728-portal-pi08-private-dry-run-submission
status: completed
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

## Acceptance delivered

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

## Non-goals preserved

- no BM-07 position/order command activation in the PI-08 package;
- no browser API route or direct Freqtrade access;
- no production/live execution, withdrawals or P14 authority;
- no claim that deterministic CI proves real Synology/Vault/Freqtrade target acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T09:22:00+02:00
validated_code_head: 1aeb3478586afb03a458a579517ddf46f46a76a9
merged_commit: 530f61caf9d5d4644068a93baa0b7a09298f24c6
branch: feat/portal-pi08-private-dry-run-submission
pr: 669
status: completed
base_head: 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
proven:
  - PI-08 implementation PR 669 squash-merged as 530f61caf9d5d4644068a93baa0b7a09298f24c6.
  - Exact head 1aeb3478586afb03a458a579517ddf46f46a76a9 passed AI Platform CI 30430203047.
  - Exact head passed Freqtrade CI 30430203036 including pre-commit, documentation, Python 3.11 through 3.14, full 3.12 coverage, distribution build and final CI gate.
  - Exact head passed GitHub Actions security analysis 30430203022.
  - There were no review submissions or unresolved review threads.
  - Submission is private, dry-run-only, idempotent, ambiguity-aware and reconciled only from authoritative PI-01 evidence.
derived:
  - BM-07 position/order command activation is now dependency-unblocked at the repository-software layer.
  - Real Synology/Vault/Freqtrade target acceptance remains a separate owner-managed evidence package.
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
  - command: AI Platform CI 30430203047
    result: PASS
  - command: Freqtrade CI 30430203036
    result: PASS
  - command: GitHub Actions security analysis 30430203022
    result: PASS
blockers: []
next_action: Start BM-07 position/order command activation from current develop using the merged PI-08 contracts and preserve the same dry-run, credential, idempotency, ambiguity and reconciliation boundaries.
```
