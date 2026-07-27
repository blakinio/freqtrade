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
- The exact-one-file request PR is closed without merge after terminal evidence capture.

## Acceptance

1. The workflow is exact-request gated and routes through `freqtrade-staging` in `synology-staging`.
2. The running probe rejects any runner whose name is not `freqtrade-synology-staging` or whose `runner.os` is not Linux.
3. It rejects recognized exchange credential environment before executing the probe.
4. It verifies Docker socket/server, Compose v2, architecture, CPU, memory and required tools.
5. It verifies the durable state path, free space and atomic fsync/rename/read-back cleanup.
6. It detects partial Authentik volume/network state and unrelated port-9000 publishers without mutation.
7. It validates required PI-06 variables and secret formats without recording their values.
8. It emits a bounded non-sensitive artifact with explicit readiness blockers.
9. Focused tests, repository CI and security analysis pass on the final infrastructure heads.
10. The request PR is closed without merge after terminal evidence capture.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T13:45:00+02:00
head: 4fabc02670a21b6291b43081d5424b0970c575f5
branch: develop
pr: "#462 merged; #445 closed without merge"
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
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
  - Artifact 8651340321 digest sha256:a40a96edd18e219278f46cc9192c16cc9cc9387ad6ae245327955591b253a569 recorded no secret values and no mutations.
  - PR 445 was closed without merge after terminal artifact capture.
  - PR 462 merged the terminal task result into develop as 4fabc02670a21b6291b43081d5424b0970c575f5.
derived:
  - Repository-side runner routing is resolved; remaining readiness failures require owner-managed target inputs.
  - A new exact-one-file preflight is required after provisioning, and deployment remains forbidden until ready_for_controlled_deployment is true.
unknown:
  - DNS readiness after public URLs are provisioned.
  - Storage free space and atomic probe result after the durable state path is configured and visible.
  - Protected secret format validity and Compose render result after values and age are present.
  - Deployment, OIDC, MFA, session, revocation, recovery, backup and isolated-restore acceptance.
conflicts: []
first_failure:
  marker: OWNER_MANAGED_PI06_TARGET_INPUTS_MISSING
  evidence: Terminal artifact 8651340321 listed the missing state mapping, age tool, three public variables and seven protected secrets.
rejected_hypotheses:
  - Treat the idle runner as offline.
  - Rename or recreate the working Synology runner.
  - Create a duplicate request PR or GitHub-hosted fallback.
  - Generate, print or commit protected values.
  - Proceed to deployment, bootstrap or restore while readiness is false.
changed_paths:
  - .github/workflows/portal-authentik-synology-target-preflight.yml
  - deploy/synology/portal-authentik/target_preflight.py
  - docs/ai_platform/portal/PI06_AUTHENTIK_SYNOLOGY_TARGET_PREFLIGHT.md
  - tests/ai_platform/portal/deployment/test_authentik_synology_target_preflight.py
  - docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md
validation:
  - command: infrastructure PR exact-head CI and security analysis
    result: PASS
    evidence: PRs 431, 452, 454, 458 and 459 merged after required checks.
  - command: terminal PI-06 target preflight run 30262205600 job 89964505267
    result: BLOCKED
    evidence: Runner and Docker checks passed; artifact 8651340321 reported only owner-managed readiness blockers.
  - command: request PR 445 lifecycle
    result: PASS
    evidence: The exact-one-file request was closed without merge after evidence capture.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-portal-pi06-authentik-synology-target-preflight.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint validates against GOVERNANCE_CONTRACT.json.
blockers:
  - Owner must configure OTERYN_STAGING_STATE_DIR=/var/lib/oteryn-staging-state and expose the durable path to the runner.
  - Owner must install age and provision the three PI-06 variables plus seven protected secrets named in artifact 8651340321.
next_action: After the owner confirms all listed inputs are provisioned without exposing values, verify only those inputs and submit one fresh exact-one-file PI-06 preflight request; do not create a deployment request unless its report is ready.
```
