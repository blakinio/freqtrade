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
updated_at: 2026-07-27T17:44:00+02:00
head: 6bf8730c9d2d09d2dfd247ddd28f5bc24b070e06
branch: develop
pr: "#485 merged; #482 closed without merge; #462 merged; #445 closed without merge"
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - PR 485 exact-head runs and merge
  - PR 445 terminal run 30262205600 artifact 8651340321
owned_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
proven:
  - Historical terminal run 30262205600 proved the runner identity, Linux X64, Docker server, Compose v2, host capacity and absence of conflicting Authentik state without mutation or secret recording.
  - PR 445 was closed without merge after terminal artifact capture, and PR 462 merged the result record.
  - The owner requested complete separation of Freqtrade and its portal from OteryN.
  - PR 482 was closed without merge because it retained the OteryN-named state contract.
  - PR 485 merged the dedicated Freqtrade runner package and changed PI-06 to FREQTRADE_STAGING_STATE_DIR=/var/lib/freqtrade-staging-state.
  - PR 485 exact-head Freqtrade CI, AI Platform CI, Portal Authentik Deployment CI, dedicated runner image build and security analysis passed.
  - No Synology or OteryN target mutation occurred from PR 485.
derived:
  - Historical host evidence remains informative, but the dedicated image and Freqtrade-owned mount require a fresh bounded PI-06 preflight after cutover.
  - The OteryN image and /var/lib/oteryn-staging-state are no longer valid PI-06 targets.
  - Deployment remains forbidden until the isolated runner report sets ready_for_controlled_deployment to true.
unknown:
  - Successful push-to-develop publication of the dedicated runner image tags.
  - Dedicated Freqtrade runner cutover on Synology.
  - Storage free space and atomic probe result under /var/lib/freqtrade-staging-state.
  - DNS readiness after public URLs are provisioned.
  - Protected secret format validity and Compose render result after values are present.
  - Deployment, OIDC, MFA, session, revocation, recovery, backup and isolated-restore acceptance.
conflicts: []
first_failure:
  marker: DEDICATED_FREQTRADE_RUNNER_NOT_DEPLOYED
  evidence: Repository isolation merged, but the live freqtrade-deploy-runner project has not yet been confirmed on the dedicated image and Freqtrade-owned state mount.
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
    evidence: Runner and Docker checks passed under the previous state mapping; no mutation or secret recording occurred.
  - command: PR 485 exact-head validation and merge
    result: PASS
    evidence: Required CI, dedicated runner image build and security analysis passed; merged as 6bf8730c9d2d09d2dfd247ddd28f5bc24b070e06.
  - command: owner-managed isolated runner deployment and fresh exact-one-file PI-06 preflight
    result: NOT_RUN
    evidence: Target mutation remains owner-managed and has not been performed.
blockers:
  - Dedicated develop image publication must be confirmed before the live Freqtrade runner project is replaced.
  - Owner must update only freqtrade-deploy-runner to the dedicated image and /volume1/docker/freqtrade/state mount while preserving runner_config and runner_work.
  - Owner must configure FREQTRADE_STAGING_STATE_DIR=/var/lib/freqtrade-staging-state plus the three PI-06 public variables and seven protected secrets.
next_action: Confirm the dedicated develop image publication, then replace only the freqtrade-deploy-runner project on Synology and submit one fresh exact-one-file PI-06 preflight request; do not modify OteryN.
```
