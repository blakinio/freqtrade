---
task_id: FTAI-20260727-portal-synology-preview-identity-fixture
status: ready
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

The original read-only diagnostic proved that `freqtrade-portal-staging` on `192.168.1.2:3031` used fixture data but lacked fixture identity configuration, so `/api/identity/login` returned HTTP 503. PR #526 repaired only that bounded fixture-preview defect.

The trusted `develop` deployment now runs exact image revision `aa181630a048d3c0d9c34880d1bae9166f4ec612` with fixture identity enabled, no fabricated control-plane URL, read-only Liquid20 data, non-root UID 1000 and the existing rollback boundary. The live workflow passed fixture login, session, administration-page and protected Liquid20 acceptance probes.

Real Authentik/control-plane identity remains outside this repair and is represented only by the separate PI-06 task.

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

All acceptance conditions passed for merge commit `aa181630a048d3c0d9c34880d1bae9166f4ec612`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T23:20:00+02:00
head: aa181630a048d3c0d9c34880d1bae9166f4ec612
branch: develop
pr: "#526 merged"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
  - PR 526 merge commit aa181630a048d3c0d9c34880d1bae9166f4ec612
  - exact-head CI run 30305022514
  - exact-head security run 30305022367
  - trusted-develop deployment run 30306048713
  - deployment artifact 8668531815
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
proven:
  - PR 524 closed without merge after read-only evidence proved the deterministic fixture-preview identity 503 without target mutation.
  - Artifact 8666739554 contained one ruff-format patch; commit 3b64f436c1e2a14ba6f9e9b3a8b8c3322288238c applied it and removed the diagnostic workflow.
  - PR 526 was synchronized with develop at b7a03ee2cb98311a6dc36e53c5f5d2206eaff0b4.
  - Exact-head Freqtrade CI run 30305022514 passed pre-commit, documentation and Python 3.11-3.14 jobs.
  - Exact-head GitHub Actions Security Analysis run 30305022367 passed.
  - PR 526 merged to develop as aa181630a048d3c0d9c34880d1bae9166f4ec612.
  - Trusted-develop deployment run 30306048713 passed build/deploy and the independent Liquid20 plus fixture-identity probe.
  - Commit status portal-synology-lan-preview is success for aa181630a048d3c0d9c34880d1bae9166f4ec612.
  - Artifact 8668531815 proves the exact image, 192.168.1.2:3031 mapping, read-only Liquid20 mount, UID 1000 and identity=fixture.
  - The live probe passed login 303, fixture cookies, tenant-demo session 200, platform administration 200 and protected Liquid20 401 SESSION_MISSING assertions.
  - No PORTAL_CONTROL_PLANE_URL is configured by this fixture deployment.
derived:
  - The bounded fixture-preview identity repair is complete and deployed.
  - Real Authentik/control-plane identity was not claimed or deployed by this task.
  - Any further identity work belongs exclusively to the separate PI-06 task and its fresh target evidence.
unknown:
  - Final current state of the separate PI-06 Authentik/control-plane target preflight and deployment work.
conflicts: []
first_failure:
  marker: FIXTURE_PREVIEW_IDENTITY_NOT_ENABLED
  evidence: The original live container had fixture data mode without fixture identity mode and returned the reported identity backend 503.
rejected_hypotheses:
  - Set a fabricated PORTAL_CONTROL_PLANE_URL to suppress the error.
  - Claim real Authentik or the identity-enabled control plane is deployed.
  - Weaken the unauthenticated 401 SESSION_MISSING Liquid20 boundary.
  - Combine this fixture repair with the dedicated-runner or PI-06 work.
  - Retain or merge the temporary diagnostic workflow.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
validation:
  - command: PR 526 exact-head Freqtrade CI run 30305022514
    result: PASS
    evidence: Pre-commit, documentation and Python 3.11-3.14 jobs completed successfully at b7a03ee2cb98311a6dc36e53c5f5d2206eaff0b4.
  - command: PR 526 exact-head GitHub Actions Security Analysis run 30305022367
    result: PASS
    evidence: Zizmor completed successfully at b7a03ee2cb98311a6dc36e53c5f5d2206eaff0b4.
  - command: merge PR 526 with expected head b7a03ee2cb98311a6dc36e53c5f5d2206eaff0b4
    result: PASS
    evidence: GitHub merged PR 526 to develop as aa181630a048d3c0d9c34880d1bae9166f4ec612.
  - command: trusted-develop Portal Synology LAN Preview run 30306048713
    result: PASS
    evidence: Build/deploy and independent Liquid20 plus fixture identity acceptance completed successfully.
  - command: portal-synology-lan-preview commit status on aa181630a048d3c0d9c34880d1bae9166f4ec612
    result: PASS
    evidence: Final commit status is success and targets deployment run 30306048713.
  - command: deployment artifact 8668531815 inspection
    result: PASS
    evidence: Exact image is healthy on 192.168.1.2:3031 with read-only Liquid20 data, UID 1000, read group 0 and fixture identity.
blockers: []
next_action: Continue real Authentik/control-plane identity only under FTAI-20260727-portal-pi06-authentik-synology-target-preflight after obtaining fresh PI-06 target evidence; make no further changes under this completed fixture-preview repair.
```
