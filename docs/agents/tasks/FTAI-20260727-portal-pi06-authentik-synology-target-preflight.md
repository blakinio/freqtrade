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
updated_at: 2026-07-27T13:33:00+02:00
base_develop: 01004e9b64fb571f283fd7f763805df963cd388d
branch: develop
infrastructure_pr: "#431"
request_pr: "#445"
status: blocked
terminal_run: 30262205600
terminal_job: 89964505267
request_head: b17175835b04586f4b4b5eaa65e639eea09a889e
artifact:
  id: 8651340321
  name: portal-pi06-target-preflight-445
  digest: sha256:a40a96edd18e219278f46cc9192c16cc9cc9387ad6ae245327955591b253a569
proven:
  - PR 431 merged the read-only target-preflight infrastructure after exact-head CI.
  - PR 452 aligned the frozen contract with runner freqtrade-synology-staging and label freqtrade-staging.
  - PR 454 enabled cancellation of stale per-PR runs.
  - PR 458 routed through the proven custom runner label while retaining exact runner-name and Linux checks inside the probe.
  - PR 459 changed exact-one-file validation to compare from the pull request merge base.
  - Terminal run 30262205600 was assigned to freqtrade-synology-staging.
  - Exact-one-file scope and recognized-trading-credential refusal passed.
  - Runner name and Linux checks passed; runner arch was X64 and Docker arch x86_64.
  - Docker socket, Docker server and Compose v2 were available.
  - Host reported 3 CPU cores and 20816465920 bytes memory.
  - No Authentik named volumes, named networks, running containers or unrelated port-9000 publisher were present.
  - The bounded report recorded no secret values and executed no container mutation, bootstrap, restore or live-capital behavior.
  - PR 445 was closed without merge after terminal artifact capture.
readiness:
  ready_for_controlled_deployment: false
  blockers:
    - OTERYN_STAGING_STATE_DIR is not configured as /var/lib/oteryn-staging-state.
    - The expected durable state directory is not visible from the runner context.
    - Tool age is missing from the runner environment.
    - PI06_AUTHENTIK_PUBLIC_BASE_URL is missing from synology-staging variables.
    - PI06_PORTAL_PUBLIC_BASE_URL is missing from synology-staging variables.
    - PI06_PORTAL_IDENTITY_CLIENT_ID is missing from synology-staging variables.
    - PI06_AUTHENTIK_POSTGRES_PASSWORD is missing from synology-staging secrets.
    - PI06_AUTHENTIK_SECRET_KEY is missing from synology-staging secrets.
    - PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH is missing from synology-staging secrets.
    - PI06_PORTAL_OIDC_CLIENT_SECRET is missing from synology-staging secrets.
    - PI06_PORTAL_SESSION_HMAC_KEY_B64 is missing from synology-staging secrets.
    - PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64 is missing from synology-staging secrets.
    - PI06_AUTHENTIK_AGE_RECIPIENT is missing from synology-staging secrets.
unknown:
  - DNS readiness after the public URLs are provisioned.
  - Storage free space and atomic probe result after the durable state directory is mounted/configured.
  - Secret format validity after protected values are provisioned.
  - Compose render result after protected values and age are present.
  - Deployment, OIDC, MFA, session, revocation, recovery, backup and isolated restore acceptance.
conflicts: []
first_failure:
  marker: OWNER_MANAGED_PI06_TARGET_INPUTS_MISSING
  evidence: The terminal non-sensitive report listed the missing state mapping, age tool, three public variables and seven protected secrets.
rejected_hypotheses:
  - Treat the idle runner as offline.
  - Recreate or rename the working Synology runner.
  - Create a duplicate request PR or GitHub-hosted fallback.
  - Generate, print or commit protected values.
  - Proceed to deployment, bootstrap or restore while readiness is false.
validation:
  - command: terminal PI-06 target preflight run 30262205600 job 89964505267
    result: BLOCKED
    evidence: Runner and Docker checks passed; bounded artifact 8651340321 recorded only owner-managed readiness blockers.
  - command: request PR 445 lifecycle
    result: PASS
    evidence: Exact one-file request was closed without merge after terminal evidence capture.
blockers:
  - Owner must provision the listed environment variable, durable state path, age tool and protected identity secrets.
next_action: Provision the exact listed owner-managed inputs without exposing their values, then declare a fresh one-file bounded preflight request. Do not create a deployment request until a new report sets ready_for_controlled_deployment to true.
```
