---
task_id: FTAI-20260726-portal-pi06-authentik-synology-deployment
status: active
branch: feat/portal-pi06-authentik-synology-deployment
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - deploy/synology/portal-authentik/
  - tests/ai_platform/portal/deployment/test_authentik_synology_deployment.py
  - .github/workflows/portal-authentik-deployment.yml
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-authentik-synology-deployment.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
---

# PI-06 Authentik/Synology Deployment

## Goal

Add a bounded, secret-free and deterministic Authentik/PostgreSQL deployment package for the accepted Synology target. Provide private networking, immutable image references, fail-closed configuration validation, restricted one-shot bootstrap, health checks, encrypted backup, checksum-verified restore, recovery and rollback runbooks without provisioning owner resources or claiming real identity acceptance.

## Boundaries

- No committed passwords, client secrets, keys, recovery material, private endpoints or user identities.
- No real Synology, Authentik, DNS, TLS, Cloudflare or GitHub environment mutation.
- No Docker socket mount, managed Docker outpost, public database port or public wildcard Authentik listener.
- No Cloudflare P11 acceptance, PI-05, PI-07, PI-08, P14 or live capital.
- Repository tests and Compose rendering are not real login, MFA, recovery, backup-retention or restore evidence.
- Frozen Phase 5/6 and protected holdout boundaries remain unchanged.

## Acceptance

1. Authentik and PostgreSQL use exact versions and full multi-platform image digests.
2. PostgreSQL is reachable only over an internal Compose network and has no host port.
3. Authentik publishes only loopback HTTP for owner-managed local ingress.
4. Required runtime secrets are placeholders in Git and validation fails closed for missing, weak or placeholder runtime values.
5. Bootstrap accepts a one-shot password hash only on an empty database and recreates services without bootstrap material.
6. Server, worker and PostgreSQL have health checks and deterministic dependency ordering.
7. Backups stream database and volume data directly into encryption and emit checksums without plaintext SQL files.
8. Restore requires an explicit destructive confirmation, verifies checksums and runs post-restore health checks.
9. Focused tests, Compose rendering, repository CI and security analysis pass on the exact final head.
10. Real target login, MFA, logout, revocation, recovery and restore remain explicitly blocked until owner-managed resources exist.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T20:00:00+02:00
head: 11ad81870c0b199b0739af9dcfa239cb32d455cc
branch: feat/portal-pi06-authentik-synology-deployment
pr: null
status: active
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
owned_paths:
  - deploy/synology/portal-authentik/
  - tests/ai_platform/portal/deployment/test_authentik_synology_deployment.py
  - .github/workflows/portal-authentik-deployment.yml
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-authentik-synology-deployment.md
proven:
  - Current develop at declaration is 11ad81870c0b199b0739af9dcfa239cb32d455cc after the isolated OKX shadow source merge.
  - Open PRs 376 and 109 own residual PyTorch and inert design-reference paths; neither owns this package. PR 339 merged before branch creation and remains disjoint.
  - PI-06 repository backend merged in PR 341 and same-origin BFF/browser sessions merged in PR 361.
  - Authentik is the accepted product IdP; Cloudflare Access remains supplemental.
  - Official Authentik 2026.5 documentation requires sequential major upgrades, supports explicit IPv4 listeners and documents hashed bootstrap passwords.
derived:
  - Repository deployment artifacts and deterministic validation can be completed without owner credentials or network access.
  - Real Synology and identity acceptance cannot be inferred from Compose rendering or fixture tests.
unknown:
  - Target Synology architecture, free CPU/RAM/storage and Container Manager state.
  - Owner-selected DNS names, TLS/Tunnel route, real OIDC client secret, users and MFA devices.
  - Real encrypted backup retention and isolated restore result.
conflicts: []
first_failure:
  marker: null
  evidence: null
rejected_hypotheses:
  - Commit generated secrets or private target endpoints.
  - Mount docker.sock for managed outposts.
  - Publish PostgreSQL or Authentik on a wildcard host listener.
  - Treat repository checks as real Authentik or P11 acceptance.
changed_paths: []
validation: []
blockers:
  - Real target acceptance requires owner-managed Synology resources, secrets, users and MFA devices.
next_action: Publish the secret-free deployment package, run exact-head targeted and repository CI, merge it, then record target login, MFA, revocation, recovery and restore as a separate owner-managed acceptance task.
```
