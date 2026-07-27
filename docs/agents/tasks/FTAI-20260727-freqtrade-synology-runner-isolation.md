---
task_id: FTAI-20260727-freqtrade-synology-runner-isolation
status: blocked
branch: develop
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
- Do not replace the live Freqtrade runner until the dedicated `develop` image publication is confirmed.
- Do not submit PI-06 deployment, bootstrap, restore or OKX collection requests before fresh isolated-runner preflights pass.
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
updated_at: 2026-07-27T17:42:00+02:00
head: 6bf8730c9d2d09d2dfd247ddd28f5bc24b070e06
branch: develop
pr: "#485 merged; #477 merged; #482 closed without merge"
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - PR 485 exact-head runs and merge
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
  - OteryN retains its independent image ghcr.io/blakinio/oteryn-deploy-runner:main, project oteryn-deploy-runner, runner oteryn-synology-staging and state path /var/lib/oteryn-staging-state.
  - PR 485 merged the dedicated Freqtrade runner package and migrated active PI-06 and OKX preflights to FREQTRADE_STAGING_STATE_DIR and /var/lib/freqtrade-staging-state.
  - The Freqtrade package owns image ghcr.io/blakinio/freqtrade-deploy-runner:develop, project freqtrade-deploy-runner, runner freqtrade-synology-staging and host path /volume1/docker/freqtrade/state.
  - PR 485 exact-head Freqtrade CI, AI Platform CI, Portal Authentik Deployment CI, dedicated runner image build and security analysis passed.
  - PR 485 changed repository state only; no Synology or OteryN target mutation occurred.
  - PR 482 was closed without merge because it retained the OteryN-named state contract.
derived:
  - Repository ownership is separated; the remaining cutover is an owner-managed replacement of only the Freqtrade runner project.
  - Existing Freqtrade runner registration volumes should be preserved during the image and state-mount replacement.
  - Fresh PI-06 and OKX preflights are required after the isolated runner cutover.
unknown:
  - Successful push-to-develop publication of the dedicated runner image tags.
  - Synology application of the dedicated Freqtrade Compose package and image.
  - Writable capacity and atomic probe result for /var/lib/freqtrade-staging-state after cutover.
  - PI-06 public-variable and protected-secret readiness after runner isolation.
conflicts: []
first_failure:
  marker: OWNER_MANAGED_FREQTRADE_RUNNER_CUTOVER_PENDING
  evidence: Repository isolation merged, but the live freqtrade-deploy-runner project still requires the dedicated image and Freqtrade-owned state mount.
rejected_hypotheses:
  - Rename, stop or modify the working OteryN runner.
  - Share one runner image, project or state path between OteryN and Freqtrade.
  - Delete runner registration volumes during cutover.
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
  - command: PR 485 exact-head Freqtrade CI run 30279376321
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11-3.14 core jobs, distribution build and CI Gate passed.
  - command: PR 485 exact-head AI Platform CI 30279380875, Portal Authentik Deployment 30279380806, runner image build 30279375628 and security analysis 30279375680
    result: PASS
    evidence: All required exact-head workflows completed successfully.
  - command: PR 485 merge
    result: PASS
    evidence: Merged to develop as 6bf8730c9d2d09d2dfd247ddd28f5bc24b070e06.
  - command: owner-managed Synology cutover and fresh isolated preflights
    result: NOT_RUN
    evidence: Target mutation remains owner-managed and has not been performed.
blockers:
  - Dedicated develop image publication must be confirmed before the live Freqtrade runner project is replaced.
  - Owner must update only freqtrade-deploy-runner, preserve runner_config and runner_work, and mount /volume1/docker/freqtrade/state at /var/lib/freqtrade-staging-state.
next_action: Confirm the dedicated develop image publication, then replace only the freqtrade-deploy-runner project on Synology while preserving its runner registration volumes; do not modify OteryN.
```
