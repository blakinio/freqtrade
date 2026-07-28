---
task_id: FTAI-20260728-portal-pi07-vault-credential-broker
status: validating
branch: feat/portal-pi07-vault-credential-broker
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 666
depends_on:
  - FTAI-20260727-portal-bm06-exchange-connection-product
owned_paths:
  - ai_platform/portal/credentials/**
  - deploy/synology/portal-vault/**
  - tests/ai_platform/portal/credentials/**
  - tests/ai_platform/portal/deployment/test_vault_synology_deployment.py
  - docs/ai_platform/portal/PI07_VAULT_CREDENTIAL_BROKER.md
  - docs/ai_platform/portal/runbooks/PI07_VAULT_SYNOLOGY.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260728-portal-pi07-vault-credential-broker.md
---

# PI-07 Vault credential broker

## Goal

Implement the approved HashiCorp Vault-backed runtime credential boundary for private dry-run runtimes without exposing secret values, Vault paths or private runtime addresses to browsers or public contracts.

## Accepted owner decision

On 2026-07-28 the repository owner selected HashiCorp Vault with these mandatory controls:

- TLS-only communication;
- private Docker network on the Synology/Linux deployment target;
- audit logging enabled;
- credential rotation at most every 90 days;
- withdrawal permissions disabled and rejected when enabled or unproven;
- dry-run execution only.

## Acceptance criteria

1. An opaque credential reference resolves only through a tenant-scoped Vault KV v2 path constructed server-side.
2. Vault authentication uses mounted AppRole material and a bounded token lease; credentials never enter browser/public models, logs or exception text.
3. TLS verification is mandatory and public, credential-bearing or non-HTTPS Vault endpoints are rejected.
4. Resolved credentials are available only inside a bounded in-memory lease and are cleared when the lease closes.
5. Revoked, unavailable, cross-tenant, malformed, withdrawal-enabled, non-dry-run and rotation-overdue credentials fail closed.
6. Credential inspection implements the existing BM-06 `CredentialReferenceStatusPort` without reading secret values when metadata is sufficient.
7. A Synology Compose package uses integrated Raft storage, an internal-only network, no published Vault port, immutable image pinning and two audit devices.
8. Bootstrap/runbook material enables KV v2, AppRole, least-privilege policy, audit and 90-day rotation metadata without committing credentials, root tokens, unseal keys or TLS private keys.
9. Focused tests cover tenant isolation, TLS/private endpoint validation, AppRole token handling, secret non-serialization, withdrawal denial, dry-run enforcement, rotation and deployment invariants.

## Non-goals

- no private Freqtrade order submission; that remains PI-08;
- no position/order command activation; that remains BM-07;
- no live capital or withdrawals;
- no public Vault ingress or browser-to-Vault route;
- no committed root token, unseal key, AppRole secret ID, exchange key or TLS private key;
- no claim that repository validation proves an actual Synology deployment.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T22:55:00+02:00
validated_code_head: null
merged_commit: null
branch: feat/portal-pi07-vault-credential-broker
pr: 666
status: validating
base_head: bdee5cce80e12f49a1f72ca462e072a8510bbddc
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
proven:
  - BM-06 already exposes an opaque credential reference and a secret-free CredentialReferenceStatusPort seam.
  - Existing portal contracts reject secret values and withdrawal-enabled exchange observations.
  - The owner explicitly selected HashiCorp Vault, TLS-only private networking, audit, 90-day rotation, withdrawal-disabled and dry-run-only behavior.
  - The deployment target is Linux containers, primarily Docker on Synology.
  - Tenant-scoped KV v2 resolution, AppRole authentication, bounded in-memory leases and fail-closed policy checks are implemented.
  - The Synology package pins HashiCorp Vault 2.0.3 by the exact multi-platform digest and exposes no host port.
  - Focused PI-07 broker and deployment tests pass in AI Platform CI.
  - Ruff lint passes and exact Ruff 0.15.21 formatting has been applied by a self-removing workflow; no temporary workflow remains in the PR diff.
derived:
  - PI-07 remains additive under ai_platform/portal/credentials and does not alter public exchange-connection contracts.
  - Vault KV v2 metadata drives current, rotation-required and revoked inspection while secret values remain available only to the broker resolve path.
unknown:
  - Target TLS certificate material and actual exchange/runtime credentials remain owner-managed inputs.
  - Real Synology initialization, unseal, AppRole issuance, audit retention and restore acceptance require target access and are not repository evidence.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Store Vault tokens or exchange credentials in browser-readable state or committed env files.
  - Publish Vault port 8200 on the Synology host or route it through Cloudflare.
  - Permit non-TLS Vault access, withdrawals, live mode or credentials older than 90 days.
  - Combine PI-07 with PI-08 submission in one unreviewed package.
changed_paths:
  - ai_platform/portal/credentials/**
  - deploy/synology/portal-vault/**
  - tests/ai_platform/portal/credentials/test_vault_broker.py
  - tests/ai_platform/portal/deployment/test_vault_synology_deployment.py
  - docs/ai_platform/portal/PI07_VAULT_CREDENTIAL_BROKER.md
  - docs/ai_platform/portal/runbooks/PI07_VAULT_SYNOLOGY.md
  - docs/agents/tasks/FTAI-20260728-portal-pi07-vault-credential-broker.md
validation:
  - AI Platform tests passed on all implementation heads inspected before exact-head validation.
  - Ruff lint passed before the final exact-format commit.
  - Final exact-head AI Platform CI, Freqtrade CI and security analysis are pending.
blockers: []
next_action: Require all final exact-head checks to pass, verify current develop ancestry and review threads, then mark PR 666 ready and squash merge PI-07.
```
