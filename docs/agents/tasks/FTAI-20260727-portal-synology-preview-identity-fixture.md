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

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T22:05:00+02:00
branch: fix/portal-synology-preview-identity-fixture-20260727
status: validating
first_failure:
  marker: FIXTURE_PREVIEW_IDENTITY_NOT_ENABLED
  evidence: Live Synology report proved fixture data mode but no fixture identity flag or control-plane URL; /api/identity/login returned the exact 503 shown by the owner.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
validation:
  - command: exact-head repository CI and security analysis
    result: NOT_RUN
  - command: trusted-develop Synology preview deployment and fixture identity probe
    result: NOT_RUN
blockers:
  - Exact-head CI and security analysis must pass before merge.
next_action: Open the bounded repair PR, validate its exact head, merge it and verify the live Synology preview status and identity endpoints.
```
