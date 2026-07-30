---
task_id: FTAI-20260730-portal-real-target-deployment-and-web-acceptance
status: active
branch: deploy/portal-real-target-acceptance-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
owned_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - deploy/synology/portal/run-requests/real-target-readonly-preflight-20260730-v1.json
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
---

# Real target portal deployment and web acceptance

## Goal

Deploy and accept the real API-backed AI Trading Portal on the owner-controlled Synology target through Authentik, Vault, Cloudflare Tunnel and private Freqtrade dry-run boundaries. Never authorize live capital.

## Current target gate

The bounded PI-06 target preflight was rerun through PR #756 on the real `freqtrade-synology-staging` runner. Docker and Compose were reachable, the host had sufficient CPU and memory, no Authentik port conflict existed and the `age` tool was present. The preflight remained blocked because the protected PI-06 variables and secrets were absent, `FREQTRADE_STAGING_STATE_DIR` was unset and the durable state directory was unavailable. No Authentik containers, networks or volumes existed.

The last repository-proven portal deployment is the Synology LAN preview. Its deployment contract explicitly sets `PORTAL_WEB_DATA_MODE=fixture`, `PORTAL_ENVIRONMENT=test`, `PORTAL_IDENTITY_FIXTURE_MODE=enabled` and omits `PORTAL_CONTROL_PLANE_URL`. It is not real-target acceptance.

## Bounded implementation

Add a secret-free, read-only target inventory that:

- runs only from an exact-one-file request PR on the trusted Synology runner;
- inventories only portal-related containers and services;
- records environment names, safe mode values and presence booleans without values;
- fingerprints mount sources instead of recording private paths;
- records image IDs, restart policies, health, sanitized ports, networks, resource limits and rollback metadata;
- checks portal fixture/API mode and presence of Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade runtime;
- never mutates containers, storage, identity, secrets, credentials or trading state;
- fails the readiness gate while real acceptance blockers remain.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T23:06:00+02:00
head: 403aa55be0daae4bd17d042384c449cc16c939cc
branch: deploy/portal-real-target-acceptance-20260730
pr: 758
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - .github/workflows/portal-authentik-deployment.yml
owned_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - deploy/synology/portal/run-requests/real-target-readonly-preflight-20260730-v1.json
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
proven:
  - PR #758 is open and mergeable on branch deploy/portal-real-target-acceptance-20260730 at authored head 403aa55be0daae4bd17d042384c449cc16c939cc.
  - Current develop is 0e6de6a2a6e441b4f334103ffff6fd071aa773f8; the branch is 5 commits ahead and 282 commits behind.
  - PR #758 security workflow 30522725306 passed; Freqtrade CI 30522724745 and AI Platform CI 30522724917 failed on the old exact head.
  - Freqtrade pre-commit job 90806705013 reported 8 Ruff findings and ruff-format changes in the preflight implementation and test.
  - The PI-06 Synology target preflight uses the existing self-hosted freqtrade-staging runner and synology-staging environment.
  - The portal Authentik workflow currently validates the Compose package on ubuntu-24.04; it does not perform real target deployment.
  - Prior real target evidence showed missing PI-06 variables, protected secrets and durable state configuration, with no Authentik target resources present.
  - The task remains read-only and authorizes no deployment mutation, trading credentials, withdrawals or live capital.
derived:
  - A new dedicated runner is not required for Authentik; the existing approved Synology runner is the intended target executor for a separately governed deployment package.
  - PR #758 must be synchronized and repaired before its evidence can govern any later real target mutation.
unknown:
  - Whether the owner has since populated the PI-06 variables, secrets and durable state path.
  - Current real target presence and health of Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade dry-run runtime.
  - Exact-head CI outcome after synchronization with current develop.
conflicts:
  - The prior checkpoint recorded no PR and instructed opening one, but PR #758 is already open and stale against current develop.
first_failure:
  marker: PR758_PRECOMMIT_RUFF_FAILED
  evidence: Run 30522724745 job 90806705013 failed first on Ruff import, security-audit and complexity findings, then ruff-format changed two files.
rejected_hypotheses:
  - A fixture preview, emulated Authentik or repository-only validation can satisfy real target acceptance.
  - Missing owner-controlled secrets or public infrastructure can be invented.
  - A second runner is necessary merely to create the isolated portal-authentik Compose project.
  - Live-capital trading, withdrawals and production credentials are authorized.
changed_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
validation:
  - command: python3 -m py_compile deploy/synology/portal/real_target_preflight.py
    result: PASS
    evidence: Pre-PR local syntax validation recorded in the task.
  - command: python3 -m pytest -q tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: Pre-PR focused suite recorded 5 passed.
  - command: GitHub Actions security run 30522725306
    result: PASS
    evidence: Exact authored head security workflow completed successfully.
  - command: GitHub Actions Freqtrade CI run 30522724745
    result: FAIL
    evidence: Pre-commit Ruff and format failures plus downstream core-test failures on the stale merge ref.
  - command: GitHub Actions AI Platform CI run 30522724917
    result: FAIL
    evidence: Exact authored head workflow completed with failure; revalidation is required after synchronization.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md --require-checkpoint
    result: PASS
    evidence: Validated 1 checkpoint task(s).
blockers:
  - PR #758 is 282 commits behind current develop and its old exact-head CI is red.
  - Owner-controlled PI-06 variables, secrets and durable state configuration were absent in the last real target preflight.
next_action: Synchronize PR #758 normally with develop@0e6de6a2a6e441b4f334103ffff6fd071aa773f8, apply only evidenced CI repairs, and rerun exact-head validation before any deployment mutation.
```
