---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: validating
branch: feat/portal-pi06-authentik-synology-target-preflight
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
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
- The future exact-one-file request PR is closed without merge after evidence capture.

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
updated_at: 2026-07-27T10:00:00+02:00
head: 9f2891ef1edc49ae9c0282101b47d33a60301196
base_develop: ff41ddc5e2fb9829e6442eaa72b12fa12461445c
branch: feat/portal-pi06-authentik-synology-target-preflight
pr: null
status: validating
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
  - Develop ff41ddc5e2fb9829e6442eaa72b12fa12461445c contains the merged PI-06 deployment package and closure evidence.
  - Open PR 424 independently maps the established runner name oteryn-synology-staging, labels self-hosted/Linux/oteryn-staging, environment synology-staging and OTERYN_STAGING_STATE_DIR.
  - PR 424 owns only OKX staging-preflight paths and does not overlap this task.
  - This branch adds an exact-one-file PI-06 request gate and a read-only probe with no Docker mutation commands.
  - Secret validation returns names only; the report explicitly records that no secret values are present.
derived:
  - A terminal preflight can prove whether the runner and protected PI-06 inputs are actually ready without fabricating target acceptance.
  - Passing preflight permits a separate controlled deployment request but does not authorize bootstrap, restore or P11.
unknown:
  - Exact-head repository CI and security outcome for this infrastructure branch.
  - Whether all required PI-06 protected variables and secrets exist in synology-staging.
  - Actual Docker, storage, DNS and tool readiness on oteryn-synology-staging.
  - Terminal preflight artifact and concrete blocker list.
conflicts: []
first_failure:
  marker: owner-access-reclassified
  evidence: The prior blocker assumed no target access, while live repository evidence shows an established Synology self-hosted runner and protected environment. Secret and host readiness remain unproven.
rejected_hypotheses:
  - Run the merged bootstrap script before a non-mutating target preflight.
  - Print or upload protected secret values for diagnostics.
  - Reuse or modify the OKX preflight workflow owned by PR 424.
  - Treat runner reachability as OIDC, MFA, recovery or restore acceptance.
changed_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
validation:
  - command: python -m py_compile deploy/synology/portal-authentik/target_preflight.py
    result: PASS
    evidence: The new probe compiled before publication.
  - command: repository exact-head CI and security analysis
    result: NOT_RUN
    evidence: Pull request has not been opened yet.
  - command: terminal self-hosted target preflight
    result: NOT_RUN
    evidence: Infrastructure must merge before the exact-one-file request is created.
blockers: []
next_action: Open the infrastructure PR, fix only confirmed exact-head CI or review failures, merge when green, then create the exact-one-file target-preflight request PR and close it without merge after the terminal artifact is captured.
```
