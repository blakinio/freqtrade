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
updated_at: 2026-07-30T09:20:00+02:00
head: 71164a99891988ac3d370422ddde737c75bddfe6
branch: deploy/portal-real-target-acceptance-20260730
pr: null
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/ai_platform/portal/runbooks/PI07_VAULT_SYNOLOGY.md
  - docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md
owned_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - deploy/synology/portal/run-requests/real-target-readonly-preflight-20260730-v1.json
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
proven:
  - develop head at task start was 7240762e134d8db42b83030491ae52ec0d02cad6.
  - The trusted runner is reachable and Docker/Compose inspection succeeds.
  - PI-06 preflight run 30521552962 produced artifact 8750953672 without target mutation or secret disclosure.
  - Required PI-06 public variables, protected secrets and FREQTRADE_STAGING_STATE_DIR were absent on 2026-07-30.
  - No Authentik containers, networks or volumes existed during the PI-06 preflight.
  - The existing Synology portal deployment workflow is fixture-only and intentionally omits the control-plane URL.
  - Repository PI-06, PI-07, PI-08, BM-07 and BM-09 software packages exist, but repository evidence is not target acceptance.
derived:
  - Real deployment mutation is unsafe until the owner-controlled identity configuration and durable storage gate pass.
  - A broader secret-free target inventory can still be completed autonomously before the owner gate is resolved.
unknown:
  - Exact current portal image ID, health, restart policy and sanitized configuration fingerprint.
  - Presence and health of portal API/database, Vault, Cloudflare Tunnel and private Freqtrade dry-run runtime.
  - Public hostname, real OIDC/MFA, canonical database state, migrations, browser acceptance, restart/reboot and rollback proof.
conflicts: []
first_failure:
  marker: OWNER_PI06_TARGET_CONFIGURATION_MISSING
  evidence: The real target preflight found the required PI-06 variables/secrets and durable state-directory configuration absent.
rejected_hypotheses:
  - Fixture preview, emulated Authentik, localhost tests or repository CI cannot satisfy real target acceptance.
  - Missing credentials or public infrastructure cannot be invented.
  - Live-capital trading, withdrawals and production credentials remain prohibited.
changed_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
validation:
  - command: python3 -m py_compile deploy/synology/portal/real_target_preflight.py
    result: PASS
  - command: python3 -m pytest -q tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: 5 passed
blockers:
  - marker: OWNER_PI06_TARGET_CONFIGURATION_MISSING
    evidence: FREQTRADE_STAGING_STATE_DIR, three PI-06 public variables and seven PI-06 protected secrets are absent.
next_action: Open and validate the bounded read-only preflight implementation PR against current develop.
```
