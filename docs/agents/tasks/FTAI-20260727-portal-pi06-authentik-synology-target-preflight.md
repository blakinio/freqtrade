---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: blocked
branch: develop
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#431"
  - "#445"
owned_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
---

# PI-06 Authentik/Synology target preflight

## Goal

Verify the established Synology self-hosted runner, Docker/Compose prerequisites, durable state path, protected identity configuration names and secret formats before any deployment, bootstrap or restore mutation.

## Boundaries

- No container start, stop, recreate, pull, removal or image mutation.
- No persistent target directory creation; only a temporary storage probe that is removed.
- No secret value, password, client secret, private key, endpoint or user identity in Git or artifacts.
- No Authentik bootstrap, OIDC application creation, login, MFA, recovery, backup or restore claim.
- No Cloudflare P11, PI-07, PI-08, P14, exchange credential or live-capital behavior.
- The exact-one-file request PR is closed without merge only after terminal evidence is captured.
- No duplicate trigger, hosted-runner fallback, proxy or runner-label substitution.

## Acceptance

1. The workflow is exact-request gated and targets `oteryn-synology-staging` in `synology-staging`.
2. It rejects recognized exchange credential environment before executing the probe.
3. It verifies Docker socket/server, Compose v2, supported architecture, CPU, memory and required tools.
4. It verifies the durable state path, 4 GiB free space and atomic fsync/rename/read-back cleanup.
5. It detects partial Authentik volume/network state and unrelated port-9000 publishers without mutation.
6. It validates required PI-06 variables and secret formats without recording their values.
7. It builds a chmod-600 temporary steady-state environment and runs fail-closed validation plus `docker compose config --quiet`.
8. The artifact contains only bounded non-sensitive readiness metadata and explicit blocker names.
9. Focused tests, repository CI and security analysis pass on the exact final infrastructure head.
10. A separate one-file request produces terminal runner evidence before any deployment task is declared.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T11:25:00+02:00
infrastructure_head: 564a73ba016b038e750fe44f1434b8d0e198abb5
infrastructure_merge: 15bb0ecc0fa61f8fb87a55f06aec46bb810a9f5f
request_head: a2cf19d861eeb1f1816b26c71aaacae21759a799
branch: develop
infrastructure_pr: "#431"
request_pr: "#445"
status: blocked
context_routes:
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_DEPLOYMENT.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
owned_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
proven:
  - PR 431 merged to develop as 15bb0ecc0fa61f8fb87a55f06aec46bb810a9f5f.
  - Exact infrastructure head 564a73ba016b038e750fe44f1434b8d0e198abb5 passed Portal Authentik Deployment CI 24, AI Platform CI 1852, Security Analysis 2122 and Freqtrade CI 2259.
  - Freqtrade CI 2259 passed pre-commit, Python 3.11 through 3.14, documentation, distribution build and CI Gate.
  - PR 445 adds exactly deploy/synology/portal-authentik/run-requests/target-preflight-20260727-v1.json.
  - PR 445 scheduled Portal PI-06 Synology Target Preflight run 30253743388 and job 89937454422.
  - Job 89937454422 remains queued with no executed step; therefore no target command, storage probe or secret-format check has run.
  - The same owner-managed runner outage was independently recorded for the OKX staging preflight in merged PR 444.
derived:
  - Repository implementation is valid and merged; the current failure boundary is runner availability rather than preflight code.
  - A passing terminal preflight may permit a separate controlled deployment request but does not authorize bootstrap, restore, P11 or target acceptance.
unknown:
  - Whether all required PI-06 protected variables and secrets exist in synology-staging.
  - Actual Docker, storage, DNS and tool readiness on oteryn-synology-staging.
  - Terminal preflight artifact and concrete blocker list.
  - Login, MFA, session lifecycle, membership revocation, recovery and encrypted backup/isolated-restore acceptance.
conflicts: []
first_failure:
  marker: SELF_HOSTED_RUNNER_QUEUED_NO_STEPS
  evidence: Portal PI-06 Synology Target Preflight run 30253743388, job 89937454422, stayed queued and exposed no steps; no target-side execution occurred.
rejected_hypotheses:
  - Create a duplicate trigger PR while 445 is authoritative.
  - Fall back to a GitHub-hosted runner or substitute runner labels.
  - Run bootstrap before a non-mutating target preflight.
  - Print or upload protected secret values for diagnostics.
  - Treat runner reachability as OIDC, MFA, recovery or restore acceptance.
validation:
  - command: Portal Authentik Deployment CI 24 on head 564a73ba016b038e750fe44f1434b8d0e198abb5
    result: PASS
    evidence: Deployment package validation and focused tests passed.
  - command: AI Platform CI 1852 on head 564a73ba016b038e750fe44f1434b8d0e198abb5
    result: PASS
    evidence: Compile, tests, Ruff lint, Ruff format and documentation checks passed.
  - command: GitHub Actions Security Analysis 2122 on head 564a73ba016b038e750fe44f1434b8d0e198abb5
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI 2259 on head 564a73ba016b038e750fe44f1434b8d0e198abb5
    result: PASS
    evidence: Pre-commit, Python 3.11-3.14, docs, distribution build and CI Gate passed.
  - command: Portal PI-06 Synology Target Preflight run 30253743388 job 89937454422
    result: BLOCKED
    evidence: Queued with no executed step because oteryn-synology-staging is unavailable.
blockers:
  - Restore owner-managed runner oteryn-synology-staging with labels self-hosted, Linux and oteryn-staging.
next_action: Keep PR 445 open as the sole authoritative request. After the runner is restored, let its existing job complete, inspect the bounded non-sensitive artifact, record the concrete readiness result, and close PR 445 without merge. Do not declare deployment or target acceptance from preflight alone.
```
