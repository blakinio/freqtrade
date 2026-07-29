---
task_id: FTAI-20260729-portal-pi06-emulated-target-acceptance
status: ready
branch: test/portal-pi06-emulated-target-acceptance
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 678
depends_on:
  - FTAI-20260726-portal-pi06-authentik-synology-deployment
owned_paths:
  - deploy/synology/portal-authentik/compose.emulated.yml
  - deploy/synology/portal-authentik/emulated_acceptance.sh
  - deploy/synology/portal-authentik/emulated-acceptance-contract-v1.json
  - tests/ai_platform/portal/deployment/test_pi06_emulated_target_acceptance.py
  - .github/workflows/portal-pi06-emulated-target-acceptance.yml
  - docs/ai_platform/portal/runbooks/PI06_EMULATED_TARGET_ACCEPTANCE.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260729-portal-pi06-emulated-target-acceptance.md
---

# PI-06 emulated target acceptance

## Goal

Run the existing Authentik/Synology package in isolated real containers, replay portal identity and MFA fail-closed behavior, and prepare a secret-free manual Google Authenticator acceptance step without representing emulation as real target evidence.

## Acceptance criteria

1. Authentik server, worker and PostgreSQL run from the pinned images in isolated temporary resources.
2. Only a dedicated loopback Authentik port is published and PostgreSQL remains private.
3. Privileged mode, host networking and Docker socket access are absent.
4. Steady-state containers contain no bootstrap password hash.
5. Application storage survives a server restart.
6. Portal browser tests prove MFA-missing and stale-step-up mutations fail closed.
7. The generated report contains no credentials or MFA material.
8. Manual TOTP enrollment and fresh-login challenge remain explicit owner evidence.
9. No claim is made for real Synology, OIDC callback, restore, P11, P14 or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T13:00:00+02:00
head: 7c193b14d9899fcd9e1ecb98f86cb9397bca52d4
branch: test/portal-pi06-emulated-target-acceptance
pr: 678
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md
  - docs/ai_platform/portal/runbooks/PI06_EMULATED_TARGET_ACCEPTANCE.md
owned_paths:
  - deploy/synology/portal-authentik/compose.emulated.yml
  - deploy/synology/portal-authentik/emulated_acceptance.sh
  - deploy/synology/portal-authentik/emulated-acceptance-contract-v1.json
  - tests/ai_platform/portal/deployment/test_pi06_emulated_target_acceptance.py
  - .github/workflows/portal-pi06-emulated-target-acceptance.yml
  - docs/ai_platform/portal/runbooks/PI06_EMULATED_TARGET_ACCEPTANCE.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260729-portal-pi06-emulated-target-acceptance.md
proven:
  - PI-06 repository identity, BFF/browser and Authentik/Synology deployment packages are complete.
  - The owner authorized an emulation-first acceptance package and can perform manual TOTP enrollment with Google Authenticator.
  - Real Authentik server, worker and PostgreSQL containers passed health, loopback ingress, private database, privilege, bootstrap-material and restart-persistence probes on current develop.
  - Chromium identity replay passed anonymous, expired, revoked, MFA-missing, stale-step-up and cross-tenant fail-closed policy checks on current develop.
  - The bounded report artifact 8720948382 contains only non-production status evidence and keeps real MFA, Synology, OIDC and restore claims forbidden.
  - Portal PI-06 Emulated Target Acceptance 30444633782 passed on exact implementation head 7c193b14d9899fcd9e1ecb98f86cb9397bca52d4.
  - Portal Authentik Deployment 30444633729 passed on the exact implementation head.
  - AI Platform CI 30444633719 passed on the exact implementation head.
  - Freqtrade CI 30444633743 passed pre-commit, documentation, Python 3.11 through 3.14, coverage, distribution build and final CI gate on the exact implementation head.
  - Workflow security analysis 30444633726 passed on the exact implementation head.
derived:
  - The non-secret and non-target portion of PI-06 acceptance is closed through repeatable real-container emulation and browser policy evidence on current develop.
  - Real target acceptance is reduced to owner-operated TOTP, OIDC, Synology, recovery, backup and isolated-restore probes.
unknown:
  - Real Synology runtime availability, DNS/TLS route and portal OIDC client configuration.
  - Manual Google Authenticator enrollment, wrong-code rejection and fresh-login challenge result.
  - Encrypted backup and isolated restore result.
conflicts: []
first_failure:
  marker: resolved_pi06_test_format_and_typing
  evidence: initial validation found Ruff formatting and mypy JSON typing only; exact formatter output and TypedDict definitions were applied before all final implementation gates passed
rejected_hypotheses:
  - Emulation cannot be labeled real Synology or real MFA acceptance.
  - A successful TOTP challenge cannot authorize P11, P14 or live capital.
changed_paths:
  - deploy/synology/portal-authentik/compose.emulated.yml
  - deploy/synology/portal-authentik/emulated_acceptance.sh
  - deploy/synology/portal-authentik/emulated-acceptance-contract-v1.json
  - tests/ai_platform/portal/deployment/test_pi06_emulated_target_acceptance.py
  - .github/workflows/portal-pi06-emulated-target-acceptance.yml
  - docs/ai_platform/portal/runbooks/PI06_EMULATED_TARGET_ACCEPTANCE.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260729-portal-pi06-emulated-target-acceptance.md
validation:
  - command: Portal PI-06 Emulated Target Acceptance 30444633782
    result: PASS
    evidence: real-container emulation, bounded artifact upload and Chromium MFA policy replay completed successfully
  - command: Portal Authentik Deployment 30444633729
    result: PASS
    evidence: existing Authentik/Synology deployment validation completed successfully
  - command: AI Platform CI 30444633719
    result: PASS
    evidence: exact implementation head completed successfully
  - command: Freqtrade CI 30444633743
    result: PASS
    evidence: pre-commit, documentation, Python matrix, coverage, distribution build and final gate completed successfully
  - command: GitHub Actions security analysis 30444633726
    result: PASS
    evidence: exact implementation head completed successfully
blockers: []
next_action: Owner performs the manual Google Authenticator enrollment, wrong-code rejection and fresh-login TOTP challenge from PI06_EMULATED_TARGET_ACCEPTANCE.md, records only secret-free pass/fail evidence, then continues with separately authorized real Synology, OIDC, backup and isolated-restore probes.
```
