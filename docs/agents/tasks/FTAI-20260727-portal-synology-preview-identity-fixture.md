---
task_id: FTAI-20260727-portal-synology-preview-identity-fixture
status: validating
branch: fix/portal-synology-preview-identity-fixture-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - .github/workflows/diag-portal-preview-precommit.yml
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
updated_at: 2026-07-27T22:14:00+02:00
head: 2e97ba120ca443b3fc949cf480cbfff00b57583d
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
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - .github/workflows/diag-portal-preview-precommit.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
proven:
  - PR 524 closed without merge after read-only Synology evidence capture; no target mutation occurred.
  - The only detected Freqtrade portal container is freqtrade-portal-staging on 192.168.1.2:3031 at revision d78778f6dfda103131d37d9be4bc5e6eaa185616.
  - The live container has fixture data mode but lacks PORTAL_IDENTITY_FIXTURE_MODE and PORTAL_CONTROL_PLANE_URL, and /api/identity/login returns the reported 503.
  - PR 526 is open at head 2e97ba120ca443b3fc949cf480cbfff00b57583d with fixture identity, no fabricated control-plane URL, rollback and live acceptance probes.
  - Exact-head GitHub Actions Security Analysis run 30301454635 passed.
  - Previous PR head Freqtrade CI run 30301234881 failed only at pre-commit job 90094397569.
  - Diagnostic run 30301454767 completed successfully and published one-day artifact 8666739554 containing the pre-commit log and patch.
  - PR 526 has not deployed to Synology because the deployment workflow runs only after merge to develop.
derived:
  - The remaining repository repair should be limited to the exact pre-commit patch captured in artifact 8666739554 and removal of the temporary diagnostic workflow.
  - A successful merge to develop will trigger the existing controlled Synology preview deployment and its fixture identity probe.
  - Real Authentik/control-plane identity remains outside this fixture-preview repair and must stay represented as blocked PI-06 work.
unknown:
  - The exact failing pre-commit hook and generated patch contents until artifact 8666739554 is read.
  - Final result of exact-head Freqtrade CI run 30301454630, which was still in progress at checkpoint time.
  - Live Synology deployment result and identity endpoint behavior after PR 526 merges.
  - Final state of the separate dedicated-runner cutover PR 516 and fresh PI-06 target preflight.
conflicts: []
first_failure:
  marker: PRE_COMMIT_AUTOFIX_REQUIRED
  evidence: Previous PR head failed only the pre-commit gate; exact output and patch are now preserved in artifact 8666739554 for bounded application.
rejected_hypotheses:
  - Set a fabricated PORTAL_CONTROL_PLANE_URL to suppress the error.
  - Claim real Authentik or the identity-enabled control plane is deployed.
  - Weaken the unauthenticated 401 SESSION_MISSING Liquid20 boundary.
  - Modify OteryN or combine this portal preview repair with the runner cutover.
  - Merge the temporary diagnostic workflow.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - .github/workflows/diag-portal-preview-precommit.yml
  - deploy/synology/portal/deploy-preview.sh
  - tests/ai_platform_integration/test_portal_synology_auth_probe.py
  - docs/agents/tasks/FTAI-20260727-portal-synology-preview-identity-fixture.md
validation:
  - command: PR 524 read-only Synology identity runtime diagnostic run 30300705848
    result: PASS
    evidence: Artifact 8666419512 proved the live port, revision, environment and deterministic identity 503 without mutation.
  - command: PR 526 previous-head Freqtrade CI run 30301234881 pre-commit job 90094397569
    result: FAIL
    evidence: Repository checks reached the pre-commit gate, which failed before merge or target deployment.
  - command: PR 526 exact-head pre-commit diagnostic run 30301454767
    result: PASS
    evidence: Artifact 8666739554 contains the bounded log, patch and exit-code record.
  - command: PR 526 exact-head GitHub Actions Security Analysis run 30301454635
    result: PASS
    evidence: Zizmor completed successfully at head 2e97ba120ca443b3fc949cf480cbfff00b57583d.
  - command: PR 526 exact-head Freqtrade CI run 30301454630
    result: NOT_RUN
    evidence: The run was still in progress when this checkpoint was written.
  - command: trusted-develop Synology preview deployment and fixture identity acceptance
    result: NOT_RUN
    evidence: Deployment is intentionally gated on a reviewed merge to develop.
blockers:
  - Artifact 8666739554 must be read and its exact pre-commit patch applied.
  - The temporary diagnostic workflow must be removed before merge.
  - Final exact-head repository CI must pass before PR 526 can merge.
  - Post-merge Synology deployment and fixture identity acceptance must pass before task closure.
next_action: Download artifact 8666739554 from run 30301454767, apply only its exact pre-commit patch to PR 526, and remove .github/workflows/diag-portal-preview-precommit.yml in the same focused commit.
```
