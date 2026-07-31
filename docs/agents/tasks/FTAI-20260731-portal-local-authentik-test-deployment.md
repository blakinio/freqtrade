---
task_id: FTAI-20260731-portal-local-authentik-test-deployment
status: active
branch: deploy/portal-authentik-local-test-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: null
owned_paths:
  - .github/workflows/portal-authentik-deployment.yml
  - .github/workflows/portal-authentik-local-test-deploy.yml
  - deploy/synology/portal-authentik/local_test_deploy.py
  - deploy/synology/portal-authentik/run-requests/local-test-deploy-20260731-v1.json
  - tests/ai_platform/portal/deployment/test_authentik_local_test_deploy.py
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-test-deployment.md
---

# Local Authentik test deployment on Synology

## Goal

Deploy the pinned Authentik and PostgreSQL stack on the owner-controlled Synology staging host for LAN-only identity testing. Allow the owner to complete the `akadmin` initial setup and MFA enrollment in the Authentik GUI. Do not provision public ingress, exchange credentials, withdrawals or live capital.

## Authorization

The owner explicitly authorized creation and configuration of the required local-test Authentik containers on the trusted Synology runner. This authorization covers bounded Docker image pulls, persistent local-test volumes, target-generated runtime secrets and starting or updating the Authentik server, worker and PostgreSQL containers.

The authorization does not cover Cloudflare/public exposure, destructive restore, exchange credentials, live trading or live capital.

## Safety contract

- Exact-one-file request PR required for mutation.
- Pinned Authentik and PostgreSQL image tag/digest pairs are unchanged.
- Runtime secrets are generated on the Synology target and stored only in a chmod-600 persistent runtime file.
- PostgreSQL has no host-published port.
- Authentik publishes TCP 9000 for private-LAN testing only.
- No Docker socket mount, privileged container or host network is permitted in the deployed stack.
- No bootstrap password or hash is transmitted through GitHub; the owner sets the `akadmin` password in the initial-setup GUI.
- No trading credential, withdrawal or live-capital authority is accepted.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:20:00+02:00
head: a6cd74cf0fef81ecfd2a3ce5cac1113f61e091e8
branch: deploy/portal-authentik-local-test-20260731
pr: null
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - deploy/synology/portal-authentik/compose.yml
  - deploy/synology/portal-authentik/validate.py
owned_paths:
  - .github/workflows/portal-authentik-deployment.yml
  - .github/workflows/portal-authentik-local-test-deploy.yml
  - deploy/synology/portal-authentik/local_test_deploy.py
  - deploy/synology/portal-authentik/run-requests/local-test-deploy-20260731-v1.json
  - tests/ai_platform/portal/deployment/test_authentik_local_test_deploy.py
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-test-deployment.md
proven:
  - The owner explicitly authorized a local Synology test deployment and can complete MFA enrollment in the GUI.
  - Develop was a6cd74cf0fef81ecfd2a3ce5cac1113f61e091e8 when the implementation branch was created.
  - Trusted runner evidence proves Docker 24.0.2, Compose v2, 3 CPUs, about 20.8 GB RAM and writable persistent staging storage.
  - TCP 9000 had no proven Authentik conflict and the existing portal preview uses TCP 3031.
  - The repository package pins Authentik 2026.5.5 and PostgreSQL 16.13 by full image digests.
  - The official Authentik initial-setup flow permits the owner to set the default akadmin password in the browser after a fresh Docker Compose start.
  - Local syntax validation and 8 focused local-deployment tests pass before the repository PR is opened.
derived:
  - Target-generated secrets avoid exposing an administrator password or runtime secret through GitHub.
  - A separate exact-one-file mutation request can safely deploy the local stack after repository CI passes.
unknown:
  - The exact Synology LAN address the owner will use in the browser.
  - Whether TCP 9000 has been claimed by a non-Docker host process since the last preflight.
  - Whether the pinned images are already cached on the target.
conflicts:
  - The earlier real-target task blocked all mutation because it was read-only; the owner has now explicitly authorized a bounded local-test deployment.
first_failure:
  marker: LOCAL_TEST_DEPLOYMENT_NOT_YET_EXECUTED
  evidence: The mutation workflow and deployer require repository review and merge before the exact-one-file request can run on the trusted target.
rejected_hypotheses:
  - Commit runtime secrets or administrator passwords.
  - Publish PostgreSQL on the host.
  - Configure Cloudflare or public DNS as part of this local test.
  - Enable exchange credentials, withdrawals or live capital.
changed_paths:
  - .github/workflows/portal-authentik-deployment.yml
  - .github/workflows/portal-authentik-local-test-deploy.yml
  - deploy/synology/portal-authentik/local_test_deploy.py
  - tests/ai_platform/portal/deployment/test_authentik_local_test_deploy.py
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-test-deployment.md
validation:
  - command: python -m py_compile deploy/synology/portal-authentik/local_test_deploy.py tests/ai_platform/portal/deployment/test_authentik_local_test_deploy.py
    result: PASS
    evidence: Local syntax validation passed.
  - command: python -m pytest -q -o addopts='' tests/ai_platform/portal/deployment/test_authentik_local_test_deploy.py
    result: PASS
    evidence: Eight focused tests passed.
blockers: []
next_action: Open and merge the repository implementation PR after exact-head CI, then run the exact-one-file local-test deployment request on the trusted Synology runner.
```
