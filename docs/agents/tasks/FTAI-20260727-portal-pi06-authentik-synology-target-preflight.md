---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: fixing
branch: fix/portal-pi06-synology-runner-identity
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
- No duplicate trigger or GitHub-hosted fallback.

## Acceptance

1. The workflow is exact-request gated and targets `freqtrade-synology-staging` through labels `self-hosted`, `Linux`, `freqtrade-staging` in `synology-staging`.
2. It rejects recognized exchange credential environment before executing the probe.
3. It verifies Docker socket/server, Compose v2, supported architecture, CPU, memory and required tools.
4. It verifies the durable state path, 4 GiB free space and atomic fsync/rename/read-back cleanup.
5. It detects partial Authentik volume/network state and unrelated port-9000 publishers without mutation.
6. It validates required PI-06 variables and secret formats without recording their values.
7. It builds a chmod-600 temporary steady-state environment and runs fail-closed validation plus `docker compose config --quiet`.
8. The artifact contains only bounded non-sensitive readiness metadata and explicit blocker names.
9. Focused tests, repository CI and security analysis pass on the exact final infrastructure head.
10. The one-file request produces terminal runner evidence before any deployment task is declared.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T12:00:00+02:00
base_develop: 1a428979ecbe50984b7807dc2a4491453515f9b7
branch: fix/portal-pi06-synology-runner-identity
infrastructure_pr: "#431"
request_pr: "#445"
status: fixing
proven:
  - PR 431 merged the read-only target-preflight infrastructure as 15bb0ecc0fa61f8fb87a55f06aec46bb810a9f5f after full exact-head CI.
  - PR 445 scheduled run 30253743388 and job 89937454422, but the job remained queued with no executed step.
  - Owner-provided GitHub runner settings show an idle repository runner named freqtrade-synology-staging with custom label freqtrade-staging.
  - The merged workflow incorrectly requested custom label oteryn-staging and the frozen contract incorrectly required runner name oteryn-synology-staging.
  - The queued state was caused by repository-side runner identity drift, not evidence that the Synology runner was offline.
  - The durable state variable and path remain OTERYN_STAGING_STATE_DIR=/var/lib/oteryn-staging-state; only runner identity changes.
derived:
  - After this correction merges, the existing one-file request must be synchronized to the corrected frozen contract and allowed to run on the idle Synology runner.
  - Passing preflight permits only a separate controlled deployment request; it does not authorize bootstrap, restore, P11 or target acceptance.
unknown:
  - Whether all required PI-06 protected variables and secrets exist in synology-staging.
  - Actual Docker, storage, DNS and tool readiness on freqtrade-synology-staging.
  - Terminal preflight artifact and concrete blocker list.
  - Login, MFA, session lifecycle, membership revocation, recovery and encrypted backup/isolated-restore acceptance.
conflicts:
  - PR 448 records the earlier ambiguous assignment diagnosis against this same task path and must be closed as superseded by the proven identity correction.
first_failure:
  marker: RUNNER_IDENTITY_CONTRACT_DRIFT
  evidence: Workflow required [self-hosted, Linux, oteryn-staging], while the idle configured runner is freqtrade-synology-staging with label freqtrade-staging.
rejected_hypotheses:
  - Treat queued status alone as proof that the runner is offline.
  - Rename or recreate the working Synology runner to preserve a stale repository contract.
  - Create a duplicate trigger PR or GitHub-hosted fallback.
  - Run bootstrap before a non-mutating target preflight.
  - Print or upload protected secret values for diagnostics.
validation:
  - command: exact-head focused tests and repository CI
    result: PENDING
    evidence: Runner identity correction is being validated on this branch.
  - command: terminal self-hosted target preflight
    result: NOT_RUN
    evidence: Corrected infrastructure must merge and PR 445 must be synchronized first.
blockers:
  - Merge the exact runner identity correction after green CI.
next_action: Validate and merge the runner identity correction, update the sole request file in PR 445 to freqtrade-synology-staging/freqtrade-staging, allow the existing workflow to run, inspect the bounded artifact, and close PR 445 without merge after terminal evidence capture.
```
