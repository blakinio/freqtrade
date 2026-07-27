---
task_id: FTAI-20260727-freqtrade-synology-runner-isolation
status: validating
branch: feat/freqtrade-synology-runner-isolation-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#477"
  - "#482"
  - "#485"
owned_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - deploy/synology/freqtrade-runner/**
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
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

Separate the Freqtrade repository, AI platform, portal and active staging preflights from OteryN by giving Freqtrade its own runner image, Compose package, host state path, container state path and GitHub variable contract without mutating the OteryN project.

## Boundaries

- Do not modify `blakinio/Oteryn-Platform`, its runner registration, project, containers, volumes or state path.
- Do not remove or recreate the live Freqtrade runner before the dedicated image and Compose package are reviewed and published.
- Do not submit PI-06 deployment, bootstrap, restore or OKX collection requests.
- Do not expose secrets or trading credentials.

## Acceptance

1. A dedicated image `ghcr.io/blakinio/freqtrade-deploy-runner:develop` is built from this repository.
2. The canonical Compose project is `freqtrade-deploy-runner` and registers only `blakinio/freqtrade` as `freqtrade-synology-staging` with label `freqtrade-staging`.
3. The dedicated host path is `/volume1/docker/freqtrade/state` and the runner path is `/var/lib/freqtrade-staging-state`.
4. The runner image contains Docker CLI, Compose v2, Python 3, `age` and `openssl`.
5. PI-06 and OKX staging preflights use only `FREQTRADE_STAGING_STATE_DIR` and the Freqtrade-owned state root.
6. Static tests reject OteryN image, repository, variable and state references in the dedicated runner package and active workflows.
7. OteryN remains unchanged.
8. Exact-head repository CI, runner-image build and security analysis pass before merge.
9. Owner-managed Synology replacement and fresh bounded preflights remain separate after merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T17:02:00+02:00
head: 3743703b0ac5b1069e72edf6ae648a6c8c37b0b4
branch: feat/freqtrade-synology-runner-isolation-20260727
pr: "#485 open; #477 merged; #482 closed without merge"
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - PR 485 exact-head CI
owned_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - deploy/synology/freqtrade-runner/**
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
proven:
  - OteryN owns a separate runner package with image ghcr.io/blakinio/oteryn-deploy-runner:main, project oteryn-deploy-runner, runner oteryn-synology-staging and path /var/lib/oteryn-staging-state.
  - The Freqtrade runner project reused the OteryN runner image, and active PI-06 and OKX preflights reused the OteryN-named state contract.
  - The owner explicitly requested complete separation of Freqtrade and its portal from OteryN.
  - Superseded checkpoint PR 482 was closed without merge.
  - PR 477 merged its bounded python3 repair, releasing the OKX workflow and test paths.
  - PR 485 now contains the dedicated Freqtrade runner package plus PI-06 and OKX state-contract migration without Synology mutation.
  - Exact-head security analysis, AI Platform CI, Portal Authentik Deployment CI and dedicated runner image build passed on pre-OKX head 5e88e0895dd93b38bd4b9e586a6b83cc6c948d87.
derived:
  - Freqtrade requires a repository-owned runner image and canonical Compose package rather than a copied OteryN image.
  - The existing Freqtrade runner registration volumes can be preserved while only its image and state mount are replaced.
  - OteryN must remain untouched throughout the migration.
unknown:
  - Exact-head CI and security-analysis result for the final PR 485 head.
  - Synology application of the dedicated Freqtrade Compose package and image.
  - Writable capacity and atomic probe result for /var/lib/freqtrade-staging-state after owner deployment.
  - PI-06 DNS, public variables and protected secret validity after runner isolation.
conflicts: []
first_failure:
  marker: CROSS_PROJECT_RUNNER_ASSET_REUSE
  evidence: The Freqtrade runner project used the OteryN deploy-runner image and active preflights used the OteryN-named state variable and path.
rejected_hypotheses:
  - Rename, stop or modify the working OteryN runner.
  - Delete the current Freqtrade runner before a reviewed replacement exists.
  - Share one runner project, state path or image between OteryN and Freqtrade.
  - Run deployment or collection before fresh isolated-runner preflights pass.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-image.yml
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
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
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
validation:
  - command: PR 485 final exact-head Freqtrade CI, AI Platform CI, Portal Authentik Deployment CI, runner-image build and security analysis
    result: NOT_RUN
    evidence: Final workflows were triggered after the OKX migration and checkpoint update.
  - command: owner-managed Synology runner replacement and fresh PI-06 and OKX preflights
    result: NOT_RUN
    evidence: Forbidden before PR 485 is reviewed, merged and its image is published.
blockers:
  - Owner must apply the reviewed Freqtrade runner Compose package on Synology after merge while preserving the existing runner registration volumes.
next_action: Observe PR 485 final exact-head validation; repair only the first concrete failure, then merge and verify publication of the dedicated develop image before any Synology mutation.
```
