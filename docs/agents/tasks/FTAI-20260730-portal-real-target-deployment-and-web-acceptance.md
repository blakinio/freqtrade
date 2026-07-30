---
task_id: FTAI-20260730-portal-real-target-deployment-and-web-acceptance
status: active
branch: deploy/portal-real-target-acceptance-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 758
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
updated_at: 2026-07-31T00:06:00+02:00
head: 7d4f41f3bbfa1088dd52e79b5d33c8af5b22606a
branch: deploy/portal-real-target-acceptance-20260730
pr: 758
status: blocked
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
  - PR #758 is open and mergeable at repository implementation head 7d4f41f3bbfa1088dd52e79b5d33c8af5b22606a.
  - Before this checkpoint refresh, current develop was e19327315cd40d11bcaaa48b11dc53afa80d78e8 and the branch was 14 commits ahead and 1 behind with only four task paths changed.
  - PR #831 repaired the Portal Universal E2E validation dependency contract and was squash-merged to develop as e19327315cd40d11bcaaa48b11dc53afa80d78e8.
  - PR #831 exact-head Portal Universal E2E run 30585717293 passed both backend-scenario and Chromium.
  - PR #831 exact-head Freqtrade CI run 30585717334 and security run 30585717246 passed.
  - The original Ruff import, security-audit, complexity and formatting findings were repaired only in the preflight implementation and focused test.
  - Prior exact-head AI Platform CI, security and Portal Web CI passed for the preflight implementation.
  - Prior real-target evidence showed missing PI-06 variables, protected secrets and durable state configuration, with no Authentik target resources present.
  - No real-target preflight request or deployment mutation was executed in this task continuation.
  - The task remains read-only and authorizes no trading credentials, withdrawals or live capital.
derived:
  - The unrelated Portal Universal E2E dependency blocker is resolved in develop.
  - Updating this checkpoint creates a new PR #758 head and triggers CI against a merge ref containing the dependency repair.
  - Real-target mutation remains gated on owner-controlled PI-06 configuration and a separately governed exact-one-file read-only preflight request.
unknown:
  - Whether the owner has since populated the PI-06 variables, protected secrets and durable state path.
  - Current real-target presence and health of Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade dry-run runtime.
  - Final exact-head CI result for PR #758 after the dependency repair enters its merge ref.
conflicts:
  - The previous checkpoint treated the Portal Universal E2E dependency defect as active; PR #831 has resolved it in develop.
first_failure:
  marker: PR758_EXACT_HEAD_CI_PENDING_AFTER_DEPENDENCY_FIX
  evidence: PR #758 requires a fresh head event so CI evaluates the merge ref containing develop commit e19327315cd40d11bcaaa48b11dc53afa80d78e8.
rejected_hypotheses:
  - A fixture preview, emulated Authentik or repository-only validation can satisfy real-target acceptance.
  - Missing owner-controlled secrets or public infrastructure can be invented.
  - Live-capital trading, withdrawals and production credentials are authorized.
changed_paths:
  - .github/workflows/portal-real-target-readonly-preflight.yml
  - deploy/synology/portal/real_target_preflight.py
  - tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
  - docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md
validation:
  - command: python3 -m py_compile deploy/synology/portal/real_target_preflight.py tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: Local syntax validation passed after the exact Ruff formatter repair.
  - command: python3 -m pytest -q tests/ai_platform/portal/deployment/test_portal_real_target_readonly_preflight.py
    result: PASS
    evidence: Focused local suite passed with 5 tests.
  - command: GitHub Actions Portal Universal E2E run 30585717293
    result: PASS
    evidence: The dependency repair passed backend-scenario and Chromium on exact PR #831 head.
  - command: GitHub Actions Freqtrade CI run 30585717334
    result: PASS
    evidence: The dependency repair passed the repository CI workflow.
  - command: GitHub Actions security run 30585717246
    result: PASS
    evidence: The dependency repair passed workflow security analysis.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md --require-checkpoint
    result: PASS
    evidence: The checkpoint schema and exactly-one-next-action contract were preserved from the last validated task record.
blockers:
  - Owner-controlled PI-06 variables, protected secrets and durable state configuration remain unverified after their last proven absence.
  - Real-target service presence and health remain unknown because no separately governed preflight request was executed.
next_action: Run exact-head PR #758 CI against develop containing PR #831, then merge the repository-only preflight if all required checks pass while keeping real-target mutation blocked.
```
