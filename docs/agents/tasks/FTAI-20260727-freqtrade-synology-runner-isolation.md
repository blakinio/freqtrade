---
task_id: FTAI-20260727-freqtrade-synology-runner-isolation
status: validating
branch: feat/freqtrade-synology-runner-isolation-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#482"
owned_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/freqtrade-runner/**
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
---

# Freqtrade Synology runner isolation

## Goal

Separate the Freqtrade repository, AI platform and portal deployment runner from OteryN by giving Freqtrade its own runner image, Compose package, host state path, container state path and GitHub variable contract without mutating the OteryN project.

## Boundaries

- Do not modify `blakinio/Oteryn-Platform`, its runner registration, project, containers, volumes or state path.
- Do not remove or recreate the live Freqtrade runner before the dedicated image and Compose package are reviewed and published.
- Do not submit a PI-06 deployment, bootstrap or restore request.
- Do not expose secrets or trading credentials.
- Do not edit the OKX preflight workflow/test while PR #477 owns those paths.

## Acceptance

1. A dedicated image `ghcr.io/blakinio/freqtrade-deploy-runner:develop` is built from this repository.
2. The canonical Compose project is `freqtrade-deploy-runner` and registers only `blakinio/freqtrade` as `freqtrade-synology-staging` with label `freqtrade-staging`.
3. The dedicated host path is `/volume1/docker/freqtrade/state` and the runner path is `/var/lib/freqtrade-staging-state`.
4. The runner image contains Docker CLI, Compose v2, Python 3, `age` and `openssl`.
5. The PI-06 preflight uses only `FREQTRADE_STAGING_STATE_DIR` and the Freqtrade-owned state root.
6. Static tests reject OteryN image, repository, label and state references in the dedicated runner package.
7. OteryN remains unchanged.
8. Exact-head repository CI and security analysis pass before merge.
9. Owner-managed Synology replacement and a fresh bounded preflight remain separate after merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T16:40:00+02:00
head: fabd50e80661780a3e73d8669b26181a5bb910a5
branch: feat/freqtrade-synology-runner-isolation-20260727
pr: "not opened"
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
owned_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/freqtrade-runner/**
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
proven:
  - OteryN owns a separate runner package with image ghcr.io/blakinio/oteryn-deploy-runner:main, project oteryn-deploy-runner, runner oteryn-synology-staging and path /var/lib/oteryn-staging-state.
  - The Freqtrade repository already routes jobs to runner freqtrade-synology-staging through label freqtrade-staging.
  - The current Freqtrade runner project reused the OteryN runner image and the PI-06 contract reused OTERYN_STAGING_STATE_DIR and /var/lib/oteryn-staging-state.
  - The owner explicitly requested complete separation of Freqtrade and its portal from OteryN.
  - Superseded checkpoint PR 482 was closed without merge.
derived:
  - Freqtrade requires a repository-owned runner image and canonical Compose package rather than a copied OteryN image.
  - The existing Freqtrade runner registration volumes can be preserved while only its image and state mount are replaced.
  - OteryN must remain untouched throughout the migration.
unknown:
  - Exact-head CI and security-analysis result for the isolation package.
  - Synology application of the dedicated Freqtrade Compose package and image.
  - Writable capacity and atomic probe result for /var/lib/freqtrade-staging-state after owner deployment.
  - PI-06 DNS, public variables and protected secret validity after runner isolation.
conflicts:
  - Open PR 477 owns the OKX staging-preflight workflow and test, so its OTERYN state-path migration must be serialized after that PR reaches a terminal state.
first_failure:
  marker: CROSS_PROJECT_RUNNER_ASSET_REUSE
  evidence: The Freqtrade runner project used the OteryN deploy-runner image and PI-06 used the OteryN-named state variable and path.
rejected_hypotheses:
  - Rename, stop or modify the working OteryN runner.
  - Delete the current Freqtrade runner before a reviewed replacement exists.
  - Share one runner project, state path or image between OteryN and Freqtrade.
  - Edit the OKX preflight paths concurrently with PR 477.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/freqtrade-runner/.env.example
  - deploy/synology/freqtrade-runner/.gitignore
  - deploy/synology/freqtrade-runner/Dockerfile
  - deploy/synology/freqtrade-runner/README.md
  - deploy/synology/freqtrade-runner/compose.yml
  - deploy/synology/freqtrade-runner/entrypoint.sh
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
validation:
  - command: repository exact-head CI and security analysis
    result: NOT_RUN
    evidence: PR has not been opened yet.
  - command: owner-managed Synology runner replacement and PI-06 preflight
    result: NOT_RUN
    evidence: Forbidden before the repository package is reviewed and merged.
blockers:
  - Owner must apply the reviewed Freqtrade runner Compose package on Synology after merge while preserving the existing runner registration volumes.
  - PR 477 must reach a terminal state before the OKX preflight can be migrated from the OteryN-named state contract.
next_action: Open a PR for this bounded isolation package and require exact-head CI, runner-image build validation and security analysis before any Synology mutation.
```
