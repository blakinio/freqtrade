# FTAI-20260809 — Portal runtime isolation and resource boundaries

```yaml
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1354
lane: freqtrade-portal
task_kind: implementation
phase: implement
status: implementing
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
trusted_base_sha: bf92b3b11772eaef7f471ae284b804f25ca6d2d0
branch: fix/portal-runtime-isolation-1354
pr: null
related_issues:
  - 1355
  - 1413
related_prs:
  - 1367
  - 1395
  - 1416
  - 1425
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
checkpoint_version: 2
updated_at: 2026-08-09T20:07:00Z
head: bf92b3b11772eaef7f471ae284b804f25ca6d2d0
branch: fix/portal-runtime-isolation-1354
pr: none
status: implementing
context_routes:
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - issue 1354
owned_paths:
  - ai_platform/portal/execution/**
  - tests/ai_platform/portal/execution/**
proven:
  - develop includes merged #1353 generation-scoped storage separation
  - executable RuntimeGeneration already binds isolation plan, Gateway and market-data egress identities from #1413
  - current Docker CLI driver mounts config/state but lacks process/resource/tmpfs/log/network hardening and effective attestation
  - binding architecture forbids silent fallback and treats plain Docker bridge/inspect intent as insufficient enforcement
unknown:
  - smallest legacy-driver implementation that can satisfy #1354 without taking over #1355 Supervisor authority
first_failure:
  marker: current driver lacks generation-bound hard isolation envelope
  evidence: ai_platform/portal/execution/driver.py at trusted base
changed_paths:
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
validation: []
blockers:
  - none
next_action: Implement the immutable isolation-plan contract and fail-closed Docker driver enforcement/attestation boundary, then add focused negative tests.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: 20260809T200700Z-chat-github
  session_started_at: 2026-08-09T200645Z
  checkpointed_at: 2026-08-09T200700Z
  last_progress_at: 2026-08-09T200700Z
  phase: implementation
  exact_head: bf92b3b11772eaef7f471ae284b804f25ca6d2d0
  pull_request: none
  active_operation: repository implementation
  external_run_ids: []
  operation_started_at: 2026-08-09T200700Z
  wait_deadline_at: null
  check_generation: isolation-v1
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: branch remains owned and exact implementation head is reconcilable
  next_action: Implement the immutable isolation-plan contract and fail-closed Docker driver enforcement/attestation boundary, then add focused negative tests.
```
