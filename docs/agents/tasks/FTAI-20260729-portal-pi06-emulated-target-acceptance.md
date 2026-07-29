---
task_id: FTAI-20260729-portal-pi06-emulated-target-acceptance
status: validating
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
updated_at: 2026-07-29T12:27:00+02:00
head: 3707c4c3fbd694bcc19470df727951458faa1b78
branch: test/portal-pi06-emulated-target-acceptance
pr: 678
status: validating
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
  - Exact implementation head c894fc5a13fccbeea0ffec578bbcf89cd9e3b8c2 passed real-container emulation, Chromium identity replay, Authentik deployment, AI Platform, Freqtrade and workflow-security gates.
  - The bounded report artifact 8719904975 contains only non-production status evidence and keeps real MFA, Synology, OIDC and restore claims forbidden.
  - The branch was rebased by recreation onto current develop eae105601d2408f7f1b7c3cd9e42736592f3d59d after unrelated ASE-00 work advanced the base.
derived:
  - The non-secret and non-target portion of PI-06 acceptance is repeatable on the current repository base.
  - Real target acceptance can be reduced to owner-operated TOTP, OIDC, Synology, recovery, backup and isolated-restore probes after post-rebase validation.
unknown:
  - Post-rebase exact-head workflow result for PR 678.
  - Real Synology runtime availability, DNS/TLS route and portal OIDC client configuration.
  - Manual Google Authenticator enrollment, wrong-code rejection and fresh-login challenge result.
  - Encrypted backup and isolated restore result.
conflicts: []
first_failure:
  marker: resolved_pi06_test_format_and_typing
  evidence: initial validation found Ruff formatting and mypy JSON typing only; exact formatter output and TypedDict definitions passed all pre-rebase gates
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
  - command: Pre-rebase Portal PI-06 Emulated Target Acceptance 30442035069
    result: PASS
    evidence: real-container emulation, bounded artifact upload and Chromium MFA policy replay completed successfully
  - command: Pre-rebase Portal Authentik Deployment 30442035033
    result: PASS
    evidence: existing Authentik/Synology deployment validation completed successfully
  - command: Pre-rebase AI Platform CI 30442035026
    result: PASS
    evidence: exact implementation head completed successfully
  - command: Pre-rebase Freqtrade CI 30442035011
    result: PASS
    evidence: pre-commit, documentation, Python matrix, coverage, distribution build and final gate completed successfully
  - command: Pre-rebase GitHub Actions security analysis 30442035137
    result: PASS
    evidence: exact implementation head completed successfully
  - command: Post-rebase exact-head validation
    result: PENDING
    evidence: branch recreated on current develop and awaiting PR workflows
blockers: []
next_action: Inspect PR 678 post-rebase exact-head workflows, fix every failure, then squash merge and leave only the manual Google Authenticator and real-target probes for owner execution.
```
