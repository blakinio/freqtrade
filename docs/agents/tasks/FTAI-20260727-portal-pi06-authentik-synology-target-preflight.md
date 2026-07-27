---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: blocked
branch: feat/freqtrade-synology-runner-isolation-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#431"
  - "#445"
  - "#452"
  - "#454"
  - "#458"
  - "#459"
  - "#462"
  - "#482"
  - "#485"
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

Verify the dedicated Freqtrade Synology runner, Docker/Compose prerequisites, Freqtrade-owned durable state path, protected identity configuration names and secret formats before any deployment, bootstrap or restore mutation.

## Boundaries

- No container start, stop, recreate, pull, removal or image mutation.
- No persistent target directory creation; only a temporary storage probe that is removed.
- No secret value, password, client secret, private key, endpoint or user identity in Git or artifacts.
- No Authentik bootstrap, OIDC application creation, login, MFA, recovery, backup or restore claim.
- No OteryN runner, image, project, state path or repository mutation.
- No Cloudflare P11, PI-07, PI-08, P14, exchange credential or live-capital behavior.
- The exact-one-file request PR is closed without merge after terminal evidence capture.

## Acceptance

1. The workflow is exact-request gated and routes through `freqtrade-staging` in `synology-staging`.
2. The running probe rejects any runner whose name is not `freqtrade-synology-staging` or whose `runner.os` is not Linux.
3. It rejects recognized exchange credential environment before executing the probe.
4. It verifies Docker socket/server, Compose v2, architecture, CPU, memory and required tools.
5. It verifies `/var/lib/freqtrade-staging-state`, free space and atomic fsync/rename/read-back cleanup.
6. It detects partial Authentik volume/network state and unrelated port-9000 publishers without mutation.
7. It validates required PI-06 variables and secret formats without recording their values.
8. It emits a bounded non-sensitive artifact with explicit readiness blockers.
9. Focused tests, repository CI and security analysis pass on the final infrastructure heads.
10. The request PR is closed without merge after terminal evidence capture.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T16:45:00+02:00
head: 5fa53ee488825295c31feb6c4857088416d18ce1
branch: feat/freqtrade-synology-runner-isolation-20260727
pr: "#485 open; #482 closed without merge; #462 merged; #445 closed without merge"
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - PR 485 exact-head CI
  - PR 445 terminal run 30262205600 artifact 8651340321
owned_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
proven:
  - PRs 431, 452, 454, 458 and 459 merged the bounded preflight, corrected runner routing and stale-run/request-scope fixes after CI.
  - Terminal run 30262205600 executed on freqtrade-synology-staging with Linux X64 and Docker x86_64.
  - Exact-one-file scope, trading-credential refusal, runner identity, Docker server and Compose v2 checks passed.
  - Host capacity was 3 CPU cores and 20816465920 bytes memory.
  - No Authentik named volumes, networks, running containers or unrelated port-9000 publisher existed.
  - Artifact 8651340321 recorded no secret values and no mutations.
  - PR 445 was closed without merge after terminal artifact capture.
  - PR 462 merged the terminal task result into develop.
  - The owner requested that Freqtrade and its portal be completely separated from OteryN.
  - PR 482 was closed without merge because its next action retained the OteryN-named state contract.
  - PR 485 introduces a dedicated Freqtrade runner image, Compose project and `/var/lib/freqtrade-staging-state` PI-06 contract without target mutation.
derived:
  - Historical runner and Docker evidence remains valid, but the new Freqtrade-owned image and mount require a fresh bounded preflight after owner deployment.
  - The OteryN image and `/var/lib/oteryn-staging-state` are no longer valid PI-06 targets.
  - Deployment remains forbidden until the isolated runner report sets ready_for_controlled_deployment to true.
unknown:
  - Exact-head CI and security result for PR 485.
  - Dedicated Freqtrade runner image publication and Synology project replacement.
  - Storage free space and atomic probe result under /var/lib/freqtrade-staging-state.
  - DNS readiness after public URLs are provisioned.
  - Protected secret format validity and Compose render result after values are present.
  - Deployment, OIDC, MFA, session, revocation, recovery, backup and isolated-restore acceptance.
conflicts: []
first_failure:
  marker: DEDICATED_FREQTRADE_RUNNER_NOT_DEPLOYED
  evidence: The repository contract now requires the Freqtrade-owned runner image and /var/lib/freqtrade-staging-state, but Synology has not yet applied PR 485.
rejected_hypotheses:
  - Continue using the OteryN runner image or state path for Freqtrade.
  - Rename, stop or modify the OteryN runner.
  - Create a deployment request before isolated-runner readiness passes.
  - Generate, print or commit protected values.
changed_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
validation:
  - command: historical terminal PI-06 target preflight run 30262205600 job 89964505267
    result: PASS
    evidence: Runner and Docker checks passed under the old state mapping; no mutation or secret recording occurred.
  - command: PR 485 dedicated runner package, focused tests, Freqtrade CI and security analysis
    result: NOT_RUN
    evidence: Exact-head workflows are pending.
  - command: owner-managed isolated runner deployment and fresh exact-one-file PI-06 preflight
    result: NOT_RUN
    evidence: Forbidden before PR 485 merges and the dedicated runner project is applied.
blockers:
  - PR 485 must pass exact-head validation and merge before Synology is changed.
  - Owner must update only the freqtrade-deploy-runner project to the dedicated image and `/volume1/docker/freqtrade/state` mount while preserving runner registration volumes.
  - Owner must configure FREQTRADE_STAGING_STATE_DIR=/var/lib/freqtrade-staging-state plus the three PI-06 public variables and seven protected secrets.
next_action: Observe PR 485 exact-head validation; after it merges, replace only the Freqtrade runner project on Synology and then submit one fresh exact-one-file PI-06 preflight request.
```
