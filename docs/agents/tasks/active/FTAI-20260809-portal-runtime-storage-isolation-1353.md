# FTAI-20260809 — Portal runtime storage isolation

```yaml
task_id: FTAI-20260809-portal-runtime-storage-isolation-1353
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1353
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
trusted_base_sha: 39d741061a9f2ca17259d85609e83ca46b94f28f
branch: fix/portal-runtime-storage-isolation-1353
head: 51dcac10044130aab5a0231977fc389a52eb5d28
pr: 1425
related_issues:
  - 1354
  - 1355
  - 1413
related_prs:
  - 1367
  - 1395
  - 1416
live_capital_authorized: false
production_deployment_authorized: false
```

## Objective

Implement the ADR-020 trust/storage split for Portal-managed dry-run runtimes so Freqtrade cannot mutate Portal-authoritative identity evidence or canonical runtime inputs, durable Freqtrade state is generation-scoped, and runtime replacement cannot silently reuse or redefine an old generation.

## Owned paths

- `ai_platform/portal/execution/**`
- `tests/ai_platform/portal/execution/**`
- task-specific Portal execution integration/E2E tests
- this task record

Do not implement #1354 hard resource/network/process isolation or #1355 Runtime Supervisor authority in this task.

## Acceptance inventory

- Freqtrade cannot modify Portal-authoritative runtime manifest/generation evidence.
- Canonical config is mounted read-only for one exact RuntimeGeneration and is not stored in a runtime-writable directory.
- Durable runtime DB/state is physically separate, generation-scoped and explicitly selected by `db_url`.
- Runtime manifest/control evidence is never mounted into Freqtrade.
- Replacement uses a distinct generation/runtime identity; old generation state/evidence remains historical and cannot become current implicitly.
- Replacement is fail-closed unless the previous generation is stopped/missing; no magical running-generation replacement.
- Lifecycle/private-read operations resolve only the current control-owned generation record.
- Restart/recovery reuses the same generation-scoped durable state without allowing runtime state to redefine control identity.
- Path derivation is deterministic from trusted identities and resists traversal/path escape by never using raw IDs as filesystem path components.
- Tests prove mount separation/read-only config/manifest absence, explicit persistent DB path, replacement semantics and stale-generation rejection.
- A real Docker E2E attempts to mutate immutable config from inside a container, verifies control evidence is absent, and verifies state remains writable.
- Exact-head required CI and relevant Portal component integration pass.
- No live capital, private exchange credentials, public Freqtrade exposure, production deployment, #1354 resource/network hardening or #1355 Supervisor authority.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-09T18:31:00Z
head: 51dcac10044130aab5a0231977fc389a52eb5d28
branch: fix/portal-runtime-storage-isolation-1353
pr: 1425
status: validating
context_routes:
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md sections 10-11
  - issue 1353 and ADR-020
owned_paths:
  - ai_platform/portal/execution/**
  - tests/ai_platform/portal/execution/**
proven:
  - provisioning now requires trusted desired_runtime_generation_id
  - runtime ID and all filesystem roots use hashed trusted identities rather than raw IDs
  - immutable config, durable generation state and control evidence use disjoint roots
  - Docker receives only read-only /runtime/config and writable /runtime/state mounts
  - runtime-manifest.json is control-owned and never mounted
  - dry-run db_url is fixed to /runtime/state/tradesv3.dryrun.sqlite
  - current generation advances only after successful provision
  - running/paused/starting old generations cannot be replaced
  - stale historical record updates cannot repoint current-generation authority
  - same-generation recovery reuses durable state
  - new real-container E2E asserts config write denial, control-record absence and writable state
  - mypy passed on first implementation head
first_failure:
  marker: Freqtrade CI pre-commit
  evidence: run 31329068993 job 93284230947
  cause: one E501 line in workspace.py and ruff-format changes in workspace.py/test_driver.py
  remediation: applied exact ruff formatting in commits 0cc6a0e and 9f71e5b
repair_cycles_for_current_gate: 1
ci_checks_for_current_head: 1
unchanged_state_checks: 0
identical_failure_retries: 0
context_reconstruction_attempts: 0
stall_warnings: 0
changed_paths:
  - ai_platform/portal/execution/adapter.py
  - ai_platform/portal/execution/config.py
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/runtime.py
  - ai_platform/portal/execution/workspace.py
  - tests/ai_platform/portal/execution/test_adapter.py
  - tests/ai_platform/portal/execution/test_config.py
  - tests/ai_platform/portal/execution/test_driver.py
  - tests/ai_platform/portal/execution/test_private_read.py
  - tests/ai_platform/portal/execution/test_runtime_storage_e2e.py
  - tests/ai_platform/portal/execution/test_workspace.py
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-storage-isolation-1353.md
validation:
  - command: first implementation exact-head CI
    result: FAIL_REPAIRED
    evidence: run 31329068993; mypy PASS; only ruff/format failure
  - command: current exact-head workflow discovery
    result: RUNNING
    evidence: current head 51dcac10044130aab5a0231977fc389a52eb5d28; runs 31329254083, 31329254188 and associated Portal/security workflows
blockers:
  - none
next_action: Inspect current-head component and required CI results; repair the first actionable failure, then perform fresh acceptance audit and current-develop refresh before final closeout.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: 20260809T181100Z-chat-github
  session_started_at: 2026-08-09T18:11:00Z
  checkpointed_at: 2026-08-09T18:31:00Z
  last_progress_at: 2026-08-09T18:31:00Z
  phase: component_validation
  exact_head: 51dcac10044130aab5a0231977fc389a52eb5d28
  pull_request: 1425
  active_operation: exact-head GitHub Actions validation
  external_run_ids:
    - 31329254083
    - 31329254188
  operation_started_at: 2026-08-09T18:30:00Z
  wait_deadline_at: 2026-08-09T19:00:00Z
  check_generation: implementation-plus-e2e-v1
  checks_used: 1
  status: active
  safe_to_resume: true
  resume_condition: current-head workflows become terminal or expose first actionable failure
  next_action: Inspect the aggregate current-head CI state and repair the first actionable failure; if green, fresh-audit the exact diff.
```
