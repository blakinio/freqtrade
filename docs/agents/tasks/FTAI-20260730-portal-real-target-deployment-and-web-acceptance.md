---
task_id: FTAI-20260730-portal-real-target-deployment-and-web-acceptance
status: active
branch: deploy/portal-real-target-acceptance-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
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
updated_at: 2026-07-30T23:46:00+02:00
head: f9b162315e4a00f0f16233f25b723758bfbd20bf
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
  - PR #758 is open and mergeable at validated implementation head f9b162315e4a00f0f16233f25b723758bfbd20bf.
  - Current develop is 4ef04c40406197409b00a5142f5023b3b95ac9e5; the branch is 13 commits ahead and 0 behind with only four task paths changed.
  - The branch was synchronized by non-forced fast-forward updates through GitHub virtual merge commits.
  - The original Ruff import, security-audit, complexity and formatting findings were repaired only in the preflight implementation and focused test.
  - Exact-head AI Platform CI run 30584361200 passed after 1007 tests, Ruff check and Ruff format.
  - Exact-head security run 30584361203 passed.
  - Exact-head Freqtrade CI run 30584361192 passed pre-commit, CI scope and documentation jobs; its core matrix remained in progress at checkpoint time.
  - Exact-head Portal Web CI run 30584361312 passed.
  - Exact-head Portal Universal E2E run 30584361194 passed Chromium but failed its backend scenario because jsonschema was not installed.
  - Prior real-target evidence showed missing PI-06 variables, protected secrets and durable state configuration, with no Authentik target resources present.
  - No real-target preflight request or deployment mutation was executed in this task continuation.
  - The task remains read-only and authorizes no trading credentials, withdrawals or live capital.
derived:
  - The CI repairs resolve the original task-owned lint and formatting gate.
  - The Portal Universal E2E backend failure is an unrelated workflow dependency-contract defect outside the four changed task paths.
  - Real-target mutation remains gated on owner-controlled PI-06 configuration and a separately governed exact-one-file read-only preflight request.
unknown:
  - Whether the owner has since populated the PI-06 variables, protected secrets and durable state path.
  - Current real-target presence and health of Authentik, Vault, Cloudflare Tunnel, portal API/database and private Freqtrade dry-run runtime.
  - Final conclusion of Freqtrade CI run 30584361192 after its core matrix completes.
conflicts:
  - The prior checkpoint head and develop relationship were stale; live PR, branch comparison and CI now govern the task.
first_failure:
  marker: PR758_PORTAL_UNIVERSAL_E2E_JSONSCHEMA_MISSING
  evidence: Run 30584361194 job 91012147140 failed 3 backend tests with ModuleNotFoundError for jsonschema while the Chromium journey passed.
rejected_hypotheses:
  - A fixture preview, emulated Authentik or repository-only validation can satisfy real-target acceptance.
  - Missing owner-controlled secrets or public infrastructure can be invented.
  - The unrelated Portal Universal E2E dependency failure should be repaired by expanding this task beyond its owned paths.
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
  - command: GitHub Actions AI Platform CI run 30584361200
    result: PASS
    evidence: Exact implementation head completed successfully, including 1007 tests, Ruff and Ruff format.
  - command: GitHub Actions security run 30584361203
    result: PASS
    evidence: Exact implementation head security analysis completed successfully.
  - command: GitHub Actions Freqtrade CI run 30584361192 pre-commit, scope and documentation jobs
    result: PASS
    evidence: All three jobs completed successfully on the exact implementation head.
  - command: GitHub Actions Portal Web CI run 30584361312
    result: PASS
    evidence: Exact implementation head portal web workflow completed successfully.
  - command: GitHub Actions Portal Universal E2E run 30584361194
    result: FAIL
    evidence: Chromium passed; backend scenario failed only because jsonschema was absent from validation dependencies.
  - command: GitHub Actions Freqtrade CI run 30584361192 core matrix
    result: BLOCKED
    evidence: Matrix remained in progress at checkpoint time; no task-owned failure was observed.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-portal-real-target-deployment-and-web-acceptance.md --require-checkpoint
    result: PASS
    evidence: Validated locally before checkpoint publication.
blockers:
  - Portal Universal E2E backend-scenario lacks the jsonschema validation dependency in an unrelated workflow.
  - Owner-controlled PI-06 variables, protected secrets and durable state configuration remain unverified after their last proven absence.
  - Real-target service presence and health remain unknown because no separately governed preflight request was executed.
next_action: Open a separate scoped repair for the Portal Universal E2E validation dependency contract, rerun PR #758 exact-head CI, and keep real-target mutation blocked.
```
