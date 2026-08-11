# FTAI-20260809 — Portal runtime isolation and resource boundaries

```yaml
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1354
lane: freqtrade-portal
task_kind: implementation
phase: validate
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: phased
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
base_branch: develop
trusted_base_sha: 960610f4607c4a27d402f5be5f12a211991f2fd7
branch: fix/portal-runtime-isolation-1354
pr: 1464
related_issues:
  - 1355
  - 1413
related_prs:
  - 1367
  - 1395
  - 1416
  - 1425
  - 1431
  - 1457
  - 1460
  - 1464
live_capital_authorized: false
production_deployment_authorized: false
host_firewall_mutation_authorized: false
```

## Objective

Implement the ADR-020 generation-bound runtime isolation envelope for Portal-managed dry-run Freqtrade runtimes so process, filesystem, CPU/memory/swap/PID, tmpfs/log and network controls are explicit, immutable, fail closed when unsupported, and are proven by structural/effective negative integration evidence rather than configuration intent alone.

## Owned paths

- `ai_platform/portal/execution/**`
- `tests/ai_platform/portal/execution/**`
- Portal-managed hardened runtime image/profile artifacts required by #1354
- task-specific isolation integration/E2E evidence, including `.github/workflows/portal-runtime-isolation-e2e.yml` and its workflow-registry entry
- this task record

Do not implement #1355 Runtime Supervisor sole-authority API/UDS/lifecycle serialization in this task. Do not mutate a real host firewall, protected deployment, credentials or live capital.

## Acceptance inventory

- One immutable runtime-isolation plan/profile is required for every provisioned generation and its digest must equal the generation-bound `isolation_plan_digest`.
- Container creation is non-root, `privileged=false`, no-new-privileges, capability-drop ALL/add none, read-only root, no host PID/IPC/UTS/network/device/container-engine socket, no public/host-published Freqtrade port and restart policy `no`.
- Canonical config remains read-only and generation state remains the only durable writable bind; `/tmp` is bounded tmpfs with `noexec,nosuid,nodev`.
- Memory plus swap, PID and CPU hard bounds are explicit; a host/backend that cannot prove required hard containment fails closed with stable reason codes.
- Logs are bounded by an enforcing Docker logging backend rather than unbounded default growth.
- Network semantics are deny-by-default and generation-scoped; a normal bridge alone is not accepted as market-egress enforcement. Unsupported approved egress enforcement fails closed rather than silently weakening isolation.
- Runtime material cannot supply arbitrary engine flags, mounts, command/entrypoint, environment, ports, capabilities or network mode.
- Structural attestation verifies observed image/security/mount/network/restart/resource/log settings before application release.
- Effective attestation proves actual kernel/backend memory/swap/PID/CPU/tmpfs/log/network enforcement where observable; configuration/inspect intent alone is not accepted when stronger evidence exists.
- Negative tests prove privilege escalation, writable root/config, forbidden mounts/ports/network/capabilities and missing hard-control backends are rejected.
- Real Docker E2E exercises the hardened runtime boundary without private exchange credentials or public Freqtrade exposure.
- Exact-head required CI, fresh independent audit and zero unresolved review threads are required before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T08:22:00Z
head: UNKNOWN
branch: fix/portal-runtime-isolation-1354
pr: 1464
status: validating
context_routes:
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - issue 1354
  - pull request 1464
owned_paths:
  - ai_platform/portal/execution/**
  - tests/ai_platform/portal/execution/**
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - .github/workflow-registry.yaml
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
proven:
  - historical delivery PR 1431 is closed and superseded; replacement delivery PR 1464 is open
  - integration-only PR 1460 is terminal and merge commit 7da94b84b3dca6f4136bc5583a4df99fa7ddfcf8 makes the feature branch a true descendant of develop@960610f4607c4a27d402f5be5f12a211991f2fd7
  - compare at that integration point was behind_by=0 and retained only runtime-isolation scope plus workflow registry and this task record
  - immutable isolation profile/plan, fail-closed host capability resolution, hardened Docker creation, exact-image verification, structural/effective attestation and external storage/network boundaries are implemented
  - prior exact-head Portal Runtime Isolation E2E run 31444289148 passed on af6b7a87f43b7e9e752f67690b97f6c0ff2bf8f1
  - prior Freqtrade CI run 31444289109 found stale Ruff formatting/noqa in test_runtime_isolation_e2e.py and missing workflow-registry tracking; both defects are repaired
  - previous audits already repaired fixed quarantine command/generation label attestation and replaced raw-docker-only E2E with real DockerCliRuntimeDriver provisioning
  - this checkpoint commit itself advances branch HEAD, so the live PR head is authoritative until final closeout records an immutable candidate SHA
derived:
  - no production or LIVE authority is required for remaining validation
unknown:
  - exact-head CI result for PR 1464 after this checkpoint update
  - result of fresh independent audit on the final exact head
conflicts:
  - historical PR 1431 text claimed PR 1460 as replacement delivery, while live refs prove 1460 was develop-to-feature synchronization only; PR 1464 is the actual replacement delivery lane
first_failure:
  marker: replacement-pr-exact-head-validation-pending
  evidence: PR 1464 was opened after repairing the two concrete failures from run 31444289109
rejected_hypotheses:
  - PR 1460 as delivery PR; rejected because its head was develop and its base was the feature branch
changed_paths:
  - .github/workflow-registry.yaml
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/host_isolation.py
  - ai_platform/portal/execution/isolation.py
  - ai_platform/portal/execution/runtime_image/**
  - tests/ai_platform/portal/execution/**
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
validation:
  - command: compare develop@960610f4607c4a27d402f5be5f12a211991f2fd7...fix/portal-runtime-isolation-1354 before checkpoint update
    result: PASS
    evidence: status ahead, behind_by=0; runtime-isolation diff only
  - command: Portal Runtime Isolation E2E run 31444289148 on af6b7a87f43b7e9e752f67690b97f6c0ff2bf8f1
    result: PASS
    evidence: dedicated real-Docker driver/image workflow completed successfully
  - command: Freqtrade CI run 31444289109 on af6b7a87f43b7e9e752f67690b97f6c0ff2bf8f1
    result: FAIL
    evidence: exact defects were stale Ruff formatting/noqa and missing workflow-registry entry; both have since been repaired
  - command: exact-head CI for replacement PR 1464
    result: NOT_RUN
    evidence: checkpoint mutation must first establish the final candidate generation
  - command: fresh independent audit on replacement PR 1464
    result: NOT_RUN
    evidence: run only after exact candidate diff is stable
blockers:
  - none
next_action: Inspect PR 1464 exact-head CI, repair the first real failure if any, then run a fresh independent diff audit and final closeout gates.
```
