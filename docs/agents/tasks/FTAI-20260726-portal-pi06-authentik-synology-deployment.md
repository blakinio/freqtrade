---
task_id: FTAI-20260726-portal-pi06-authentik-synology-deployment
status: reviewing
branch: feat/portal-pi06-authentik-synology-deployment
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 385
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
updated_at: 2026-07-26T21:12:00+02:00
head: 8d7e4e1f6b06bc51db2f5820c79cfd6631d1a6c2
branch: feat/portal-pi06-authentik-synology-deployment
pr: 385
status: reviewing
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
  - Develop at declaration was 11ad81870c0b199b0739af9dcfa239cb32d455cc after isolated OKX PR 339; open PRs 376 and 109 owned disjoint paths.
  - PI-06 repository backend merged in PR 341 and same-origin BFF/browser sessions merged in PR 361.
  - The package pins Authentik 2026.5.5 and PostgreSQL 16.13-alpine3.23 by full multi-platform digests.
  - PostgreSQL has no host port and uses an internal network; Authentik publishes loopback HTTP only.
  - No Redis, docker.sock, host network, privileged container or timezone mount is present.
  - Bootstrap is hash-only, one-shot and empty-database restricted; backup streams directly into age encryption and restore verifies checksums.
  - Candidate head 8d7e4e1f6b06bc51db2f5820c79cfd6631d1a6c2 passed Portal Authentik Deployment CI 10, AI Platform CI 1678 and security 1889.
derived:
  - Repository deployment artifacts and deterministic validation are complete without owner credentials or network access.
  - Real Synology and identity acceptance cannot be inferred from Compose rendering or repository tests.
unknown:
  - Target Synology architecture, free CPU/RAM/storage and Container Manager state.
  - Owner-selected DNS names, TLS/Tunnel route, real OIDC client secret, users and MFA devices.
  - Real encrypted backup retention and isolated restore result.
conflicts: []
first_failure:
  marker: RUFF_FORMATTING_ONLY
  evidence: Initial deployment tests, Compose rendering and security passed, while AI Platform Ruff and repository pre-commit rejected import spacing, six long lines and exact Ruff formatting in validate.py and its focused test. Exact Ruff output was applied and both temporary diagnostic workflows were removed; candidate CI 10 and AI Platform CI 1678 then passed Ruff and Ruff-format.
rejected_hypotheses:
  - Commit generated secrets or private target endpoints.
  - Mount docker.sock for managed outposts.
  - Publish PostgreSQL or Authentik on a wildcard host listener.
  - Treat repository checks as real Authentik or P11 acceptance.
  - Retain temporary diagnostic workflows in the final diff.
changed_paths:
  - .github/workflows/portal-authentik-deployment.yml
  - deploy/synology/portal-authentik/.env.example
  - deploy/synology/portal-authentik/.gitignore
  - deploy/synology/portal-authentik/README.md
  - deploy/synology/portal-authentik/backup.sh
  - deploy/synology/portal-authentik/bootstrap.sh
  - deploy/synology/portal-authentik/compose.yml
  - deploy/synology/portal-authentik/deployment-contract-v1.json
  - deploy/synology/portal-authentik/portal-identity.env.example
  - deploy/synology/portal-authentik/restore.sh
  - deploy/synology/portal-authentik/validate.py
  - docs/agents/tasks/FTAI-20260726-portal-pi06-authentik-synology-deployment.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_deployment.py
validation:
  - command: Portal Authentik Deployment CI 10 on candidate head 8d7e4e1f6b06bc51db2f5820c79cfd6631d1a6c2
    result: PASS
    evidence: Runtime/example validation, Compose rendering, Ruff, Ruff-format and all 9 focused tests passed.
  - command: AI Platform CI 1678 on candidate head 8d7e4e1f6b06bc51db2f5820c79cfd6631d1a6c2
    result: PASS
    evidence: AI tests, compile, Ruff, Ruff-format, codespell and JSON validation passed.
  - command: GitHub Actions Security Analysis 1889 on candidate head 8d7e4e1f6b06bc51db2f5820c79cfd6631d1a6c2
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI on exact final review head
    result: PENDING
    evidence: Final pre-commit, documentation and Python matrix are required before merge.
blockers:
  - Real target acceptance requires owner-managed Synology resources, secrets, users and MFA devices.
next_action: Require all exact-head CI for PR 385 to pass, squash-merge the repository deployment package, then close it while leaving real login, MFA, revocation, recovery and restore in a separate owner-managed acceptance task.
```
