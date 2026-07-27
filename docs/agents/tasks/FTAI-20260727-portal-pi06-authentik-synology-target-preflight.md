---
task_id: FTAI-20260727-portal-pi06-authentik-synology-target-preflight
status: fixing
branch: fix/portal-pi06-route-by-custom-runner-label
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#431"
  - "#445"
  - "#452"
  - "#454"
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

1. The workflow is exact-request gated and routes through the proven custom label `freqtrade-staging` in `synology-staging`.
2. The running probe rejects any runner whose name is not `freqtrade-synology-staging` or whose `runner.os` is not Linux.
3. It rejects recognized exchange credential environment before executing the probe.
4. It verifies Docker socket/server, Compose v2, supported architecture, CPU, memory and required tools.
5. It verifies the durable state path, 4 GiB free space and atomic fsync/rename/read-back cleanup.
6. It detects partial Authentik volume/network state and unrelated port-9000 publishers without mutation.
7. It validates required PI-06 variables and secret formats without recording their values.
8. It builds a chmod-600 temporary steady-state environment and runs fail-closed validation plus `docker compose config --quiet`.
9. The artifact contains only bounded non-sensitive readiness metadata and explicit blocker names.
10. Focused tests, repository CI and security analysis pass on the exact final infrastructure head.
11. The one-file request produces terminal runner evidence before any deployment task is declared.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T13:00:00+02:00
base_develop: 834782d11a6de586336fa3fbbbca7d4f2572450c
branch: fix/portal-pi06-route-by-custom-runner-label
infrastructure_pr: "#431"
request_pr: "#445"
status: fixing
proven:
  - PR 431 merged the read-only target-preflight infrastructure after full exact-head CI.
  - PR 452 corrected the runner name to freqtrade-synology-staging and the custom label to freqtrade-staging.
  - PR 454 enabled cancellation of stale per-PR preflight runs.
  - Owner-provided GitHub settings show freqtrade-synology-staging online and Idle, with the visible custom label freqtrade-staging.
  - Original run 30253743388 and corrected pending run 30258042706 were cancelled after PR 454 merged.
  - Run 30259106073 still queued while requesting the three-label intersection self-hosted/Linux/freqtrade-staging.
  - GitHub routes a multi-label runs-on job only to a runner matching every specified label.
  - The exact name and Linux checks already exist inside target_preflight.py, so routing through the unique custom label does not weaken target identity validation.
derived:
  - Route by the proven custom label only, then fail closed inside the probe on runner-name or operating-system mismatch.
  - Passing preflight permits only a separate controlled deployment request; it does not authorize bootstrap, restore, P11 or target acceptance.
unknown:
  - Whether all required PI-06 protected variables and secrets exist in synology-staging.
  - Actual Docker, storage, DNS and tool readiness on freqtrade-synology-staging.
  - Terminal preflight artifact and concrete blocker list.
  - Login, MFA, session lifecycle, membership revocation, recovery and encrypted backup/isolated-restore acceptance.
conflicts: []
first_failure:
  marker: MULTI_LABEL_RUNNER_ROUTE_NOT_MATCHED
  evidence: The runner is online and Idle with proven label freqtrade-staging, while run 30259106073 remains queued under the self-hosted/Linux/freqtrade-staging intersection.
rejected_hypotheses:
  - Treat queued status as proof that the runner is offline.
  - Recreate or rename the working Synology runner.
  - Remove the in-probe exact runner-name or Linux checks.
  - Create a duplicate trigger PR or GitHub-hosted fallback.
  - Run bootstrap before a non-mutating target preflight.
validation:
  - command: exact-head focused tests and repository CI
    result: PENDING
    evidence: Custom-label routing correction is being validated on this branch.
  - command: terminal self-hosted target preflight
    result: NOT_RUN
    evidence: Routing correction must merge and PR 445 must be reopened first.
blockers:
  - Merge the custom-label routing correction after green CI.
next_action: Validate and merge this routing correction, close and reopen the sole request PR 445, inspect the bounded terminal artifact, and close PR 445 without merge after evidence capture.
```
