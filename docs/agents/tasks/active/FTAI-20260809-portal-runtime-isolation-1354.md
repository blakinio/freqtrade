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
trusted_base_sha: 21427e6b7f1cbe5e5882a007101ce6fe0c2f5784
branch: fix/portal-runtime-isolation-1354
pr: 1431
related_issues:
  - 1355
  - 1413
related_prs:
  - 1367
  - 1395
  - 1416
  - 1425
  - 1457
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
- task-specific isolation integration/E2E evidence
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
checkpoint_version: 3
updated_at: 2026-08-10T23:24:22Z
head: aec5d3c496e5e32cc664b411526849f93c7936b9
branch: fix/portal-runtime-isolation-1354
pr: 1431
status: validating
context_routes:
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - issue 1354
owned_paths:
  - ai_platform/portal/execution/**
  - tests/ai_platform/portal/execution/**
proven:
  - develop at 21427e6b7f1cbe5e5882a007101ce6fe0c2f5784 includes merged #1353 storage separation and the Synology runtime preflight repair
  - PR 1431 is the existing implementation lane for issue 1354; no duplicate implementation PR was created
  - feature history was repaired after synchronization and is again a clean descendant of develop with only the runtime-isolation scope in its diff
  - immutable isolation profile/plan, fail-closed host capability resolution, hardened Docker creation, exact-image verification, structural/effective attestation and external storage/network boundaries are implemented
  - fresh audit found structural attestation did not verify the fixed quarantine command or generation identity labels; the driver now verifies exact Entrypoint/Cmd and required labels before Docker start
  - fresh audit found the original E2E exercised raw docker run rather than DockerCliRuntimeDriver; the E2E now provisions through the real driver with an exact digest image, pre-release quarantine, hard cgroup controls, read-only config, bounded state and hard-deny public network fixture
unknown:
  - exact-head CI outcome for the latest audit-remediation head
  - whether final independent audit finds any additional material gap after CI feedback
first_failure:
  marker: audit-remediation-awaiting-exact-head-validation
  evidence: PR 1431 head after driver/test remediation; required workflows are pending
changed_paths:
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/host_isolation.py
  - ai_platform/portal/execution/isolation.py
  - ai_platform/portal/execution/runtime_image/Dockerfile
  - ai_platform/portal/execution/runtime_image/__init__.py
  - ai_platform/portal/execution/runtime_image/build.py
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
  - tests/ai_platform/portal/execution/test_driver.py
  - tests/ai_platform/portal/execution/test_host_isolation.py
  - tests/ai_platform/portal/execution/test_isolation.py
  - tests/ai_platform/portal/execution/test_runtime_image.py
  - tests/ai_platform/portal/execution/test_runtime_isolation_e2e.py
validation:
  - command: compare develop@21427e6b7f1cbe5e5882a007101ce6fe0c2f5784...a799187bec5e20010cead1351c82c7d08cd080a6
    result: PASS
    evidence: branch was exactly one commit ahead, zero behind, with twelve runtime-isolation paths only
  - command: exact-head PR CI after audit remediation
    result: RUNNING
    evidence: GitHub Actions runs were created for the latest PR head; inspect first failing gate before any completion claim
  - command: fresh post-validation independent audit
    result: NOT_RUN
    evidence: must run after exact-head validation feedback and any repairs
blockers:
  - none
next_action: Inspect exact-head CI for the audit-remediation head, repair the first real failure if any, then perform a fresh independent diff audit and final E2E/CI closeout before merging PR 1431.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: 20260811T012422+0200-chat-github
  session_started_at: 2026-08-11T010300+0200
  checkpointed_at: 2026-08-11T012422+0200
  last_progress_at: 2026-08-11T012422+0200
  phase: validation
  exact_head: aec5d3c496e5e32cc664b411526849f93c7936b9
  pull_request: 1431
  active_operation: exact-head CI after audit remediation
  external_run_ids:
    - 31442179581
    - 31442179321
    - 31442179351
    - 31442179332
    - 31442179371
    - 31442179327
    - 31442179325
  operation_started_at: 2026-08-11T012000+0200
  wait_deadline_at: null
  check_generation: isolation-v2
  checks_used: 1
  status: active
  safe_to_resume: true
  resume_condition: branch remains owned and PR 1431 exact head remains reconcilable
  next_action: Inspect exact-head CI, repair first failure if present, then run fresh audit and closeout.
```
