---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: validating
branch: feat/portal-pi06-authentik-synology-target-preflight
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#431"
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
updated_at: 2026-07-27T10:43:00+02:00
head: caf4c24af8599340f66e0ca1355d2a326c5afeec
base_develop: 6d4883f63e0db2d64480827ef54f6c0e4c0a848b
branch: feat/portal-pi06-authentik-synology-target-preflight
pr: "#431"
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
  - Develop 6d4883f63e0db2d64480827ef54f6c0e4c0a848b contains only disjoint post-declaration Binance smoke and epoch-timerange changes.
  - Open PR 424 independently maps runner oteryn-synology-staging, labels self-hosted/Linux/oteryn-staging, environment synology-staging and OTERYN_STAGING_STATE_DIR.
  - PR 424 owns only OKX staging-preflight paths and does not overlap this task.
  - PR 431 adds an exact-one-file PI-06 request gate and a read-only probe with no Docker mutation commands.
  - Secrets are scoped only to the local probe step; validation and the artifact expose names and booleans only.
  - AI Platform CI 1831, Portal Authentik Deployment CI 19 and security 2100 passed after exact Ruff formatting.
  - Freqtrade CI 2237 isolated pre-commit failures to import ordering and C901 in check_docker; all other hooks passed.
  - The Docker checks were split into bounded capacity, named-inventory and container-inventory helpers; Ruff 0.15.21 fixed import order and the one-shot workflow removed itself.
derived:
  - Terminal preflight can prove actual runner and protected-input readiness without fabricating target acceptance.
  - Passing preflight permits a separate controlled deployment request but does not authorize bootstrap, restore or P11.
unknown:
  - Exact-head CI and security outcome after the pre-commit refactor.
  - Whether all required PI-06 protected variables and secrets exist in synology-staging.
  - Actual Docker, storage, DNS and tool readiness on oteryn-synology-staging.
  - Terminal preflight artifact and concrete blocker list.
conflicts: []
first_failure:
  marker: PRECOMMIT_RUFF_I001_C901
  evidence: Freqtrade CI 2237 showed all pre-commit hooks passing except Ruff import ordering and check_docker complexity 19 over limit 12. Import order was auto-fixed and check_docker was decomposed without changing mutation boundaries.
rejected_hypotheses:
  - Suppress C901 instead of reducing the function's responsibilities.
  - Run bootstrap before a non-mutating target preflight.
  - Print or upload protected secret values for diagnostics.
  - Reuse or modify the OKX preflight owned by PR 424.
  - Treat runner reachability as OIDC, MFA, recovery or restore acceptance.
changed_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
validation:
  - command: AI Platform CI 1831 on head 5601f5715b043878ded7c213366da2b5e626d151
    result: PASS
    evidence: Compile, focused tests, Ruff lint, Ruff format and documentation checks passed.
  - command: Portal Authentik Deployment CI 19 on head 5601f5715b043878ded7c213366da2b5e626d151
    result: PASS
    evidence: Existing package validation and focused deployment tests passed.
  - command: GitHub Actions Security Analysis 2100 on head 5601f5715b043878ded7c213366da2b5e626d151
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI 2237 pre-commit on head 5601f5715b043878ded7c213366da2b5e626d151
    result: FAIL
    evidence: Exact log showed only I001 and C901; both are resolved by head caf4c24af8599340f66e0ca1355d2a326c5afeec.
  - command: exact-head repository CI and security analysis
    result: RUNNING
    evidence: This owner-authored checkpoint commit re-triggers normal workflows after the bot-authored refactor commit was marked action_required.
  - command: terminal self-hosted target preflight
    result: NOT_RUN
    evidence: Infrastructure must merge before the exact-one-file request is created.
blockers: []
next_action: Fix only confirmed exact-head CI or review failures on PR 431, merge when green, then create the exact-one-file target-preflight request PR and close it without merge after the terminal artifact is captured.
```
