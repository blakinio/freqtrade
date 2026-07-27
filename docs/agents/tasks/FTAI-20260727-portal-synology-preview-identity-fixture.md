---
task_id: FTAI-20260727-portal-synology-preview-identity-fixture
status: validating
branch: fix/portal-synology-preview-identity-fixture-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
---

# Synology LAN preview identity repair

## Goal

Remove the misleading `Portal identity backend is not configured` failure from the fixture-only Synology LAN preview without pretending that the blocked PI-06 Authentik/control-plane deployment is complete.

## Proven state

A read-only diagnostic of `freqtrade-portal-staging` proved:

- one Freqtrade portal container is running on `192.168.1.2:3031`;
- exact image revision is `d78778f6dfda103131d37d9be4bc5e6eaa185616`;
- `PORTAL_WEB_DATA_MODE=fixture` and `PORTAL_ENVIRONMENT=staging` are present;
- `PORTAL_IDENTITY_FIXTURE_MODE` and `PORTAL_CONTROL_PLANE_URL` are absent;
- `/api/identity/login` returns HTTP 503 with `Portal identity backend is not configured`;
- no diagnostic mutation occurred.

The real PI-06 identity target remains blocked pending dedicated-runner cutover, fresh target preflight, protected settings, Authentik deployment/bootstrap and acceptance.

## Repair

1. Keep this deployment explicitly fixture-only by setting `PORTAL_ENVIRONMENT=test` and `PORTAL_IDENTITY_FIXTURE_MODE=enabled` alongside `PORTAL_WEB_DATA_MODE=fixture`.
2. Do not set or fabricate `PORTAL_CONTROL_PLANE_URL`.
3. Validate the candidate and final container by performing fixture login, opaque cookie creation, session read and administration-page access.
4. Preserve the unauthenticated `401 SESSION_MISSING` boundary for protected Liquid20 APIs.
5. Preserve non-root runtime, read-only Liquid20 mount, no Docker socket and rollback behavior.
6. State explicitly that real Authentik/control-plane identity remains disabled.

## Acceptance

- fixture login returns 303 rather than 503;
- fixture session returns 200 for tenant `tenant-demo`;
- `/platform/admin` returns 200 with the fixture session;
- no `PORTAL_CONTROL_PLANE_URL` is present;
- deployment and independent workflow probes pass on the live Synology target;
- `portal-synology-lan-preview` commit status is successful;
- PI-06 remains blocked and is not represented as deployed.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T22:59:00+02:00
head: 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c
branch: fix/portal-synology-preview-identity-fixture-20260727
pr: "#526 open"
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
  - PR 526 exact-head checks
  - PR 524 terminal diagnostic artifact 8666419512 and closure
  - pre-commit diagnostic run 30301454767 artifact 8666739554
  - Freqtrade CI run 30303855131
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
proven:
  - PR 524 closed without merge after read-only Synology evidence capture; no target mutation occurred.
  - The only detected Freqtrade portal container is freqtrade-portal-staging on 192.168.1.2:3031 at revision d78778f6dfda103131d37d9be4bc5e6eaa185616.
  - The live container has fixture data mode but lacks PORTAL_IDENTITY_FIXTURE_MODE and PORTAL_CONTROL_PLANE_URL, and /api/identity/login returns the reported 503.
  - Artifact 8666739554 proved that ruff-format required only the bounded one-line test formatting change.
  - Commit 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c applied that exact patch and removed the temporary diagnostic workflow.
  - Exact-head Freqtrade CI run 30303855131 and GitHub Actions Security Analysis run 30303855150 passed for commit 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c.
  - PR 526 has not deployed to Synology because the deployment workflow runs only after merge to develop.
derived:
  - The repository repair is complete and remains limited to fixture identity, live acceptance probes and the exact pre-commit formatting correction.
  - Develop advanced independently, so branch synchronization and a fresh exact-head CI pass are required before merge.
  - A successful merge to develop will trigger the controlled Synology preview deployment and fixture identity probe.
  - Real Authentik/control-plane identity remains outside this repair and stays blocked under PI-06.
unknown:
  - Final exact-head CI result after synchronizing develop into PR 526.
  - Live Synology deployment result and identity endpoint behavior after PR 526 merges.
  - Final state of the separate dedicated-runner cutover and fresh PI-06 target preflight.
conflicts: []
first_failure:
  marker: BRANCH_UPDATE_REQUIRED
  evidence: All checks passed at 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c, but branch protection requires the latest develop commits before merge.
rejected_hypotheses:
  - Set a fabricated PORTAL_CONTROL_PLANE_URL to suppress the error.
  - Claim real Authentik or the identity-enabled control plane is deployed.
  - Weaken the unauthenticated 401 SESSION_MISSING Liquid20 boundary.
  - Modify OteryN or combine this portal preview repair with the runner cutover.
  - Retain or merge the temporary diagnostic workflow.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
validation:
  - command: PR 524 read-only Synology identity runtime diagnostic run 30300705848
    result: PASS
    evidence: Artifact 8666419512 proved the live port, revision, environment and deterministic identity 503 without mutation.
  - command: PR 526 pre-commit diagnostic run 30301454767
    result: PASS
    evidence: Artifact 8666739554 contained one ruff-format patch and the complete bounded diagnostic record.
  - command: PR 526 exact-head Freqtrade CI run 30303855131
    result: PASS
    evidence: Pre-commit, documentation and Python 3.11-3.14 jobs completed successfully at 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c.
  - command: PR 526 exact-head GitHub Actions Security Analysis run 30303855150
    result: PASS
    evidence: Zizmor completed successfully at 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c.
  - command: trusted-develop Synology preview deployment and fixture identity acceptance
    result: NOT_RUN
    evidence: Deployment remains gated on merge to develop.
blockers:
  - Synchronize the latest develop commits into PR 526 and obtain fresh exact-head required checks.
  - Post-merge Synology deployment and fixture identity acceptance must pass before task closure.
next_action: Synchronize develop into PR 526, require fresh exact-head CI and security success, then merge and verify the trusted-develop Synology fixture identity deployment.
```
