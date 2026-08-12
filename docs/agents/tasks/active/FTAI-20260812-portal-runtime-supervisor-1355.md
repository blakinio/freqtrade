---
task_id: FTAI-20260812-portal-runtime-supervisor-1355
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
task_kind: implementation
priority: critical
repository: blakinio/freqtrade
base_branch: develop
branch: codex/portal-runtime-supervisor-1355
related_pr: 1496
issue: 1355
created: 2026-08-12
updated: 2026-08-12
live_capital_authorized: false
production_deployment_authorized: false
---

# Runtime Supervisor producer

## Result

Issue #1355 implements the ADR-020 generation-bound Runtime Supervisor over the merged #1354 runtime-isolation driver. The delivery remains PAPER-only and grants no LIVE, production-deployment, exchange-credential, order, withdrawal, or live-capital authority.

The latest repair closes the three material findings raised by the fresh audit of `d01ad8de3b877da345fd30f140f794a44d2c7147`:

- UDS lifecycle execution is dispatched through a bounded worker/inflight pool, preserving the accept loop for other bots;
- Docker stop/retire uses one immutable ownership check and immutable container ID before mutation;
- command and bot keyed locks are reference-counted and removed after their final concurrent user, preserving serialization without historical growth.

All temporary repair workflows and scripts have been removed from the PR diff. Current branch remains based on `develop@c0c484a1fe9139e6039e0c79512c3b0527c32446` with `behind_by=0` before this checkpoint update.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-12T14:50:00Z
phase: validate
execution_mode: chat_github
context_pressure: medium
context_growth: stable
decomposition_decision: phased
head_before_checkpoint: 43e7944eaf83bf3f49082c7e39693e2d8b54bea0
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: validating
owned_paths:
  - ai_platform/portal/runtime_supervisor/**
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/runtime.py
  - ai_platform/portal/execution/host_isolation.py
  - tests/ai_platform/portal/runtime_supervisor/**
  - tests/ai_platform/portal/execution/**
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - tools/portal_audit/ledger/**
  - docs/agents/tasks/active/FTAI-20260812-portal-runtime-supervisor-1355.md
open_material_findings: []
proven:
  - strict generation-bound request schema rejects caller-controlled raw engine parameters
  - PAPER authorization remains mandatory for exposure-creating operations while authenticated containment stays available
  - journal and trusted-provider active-generation authorities are checked independently
  - running reconciliation invokes driver re-attestation
  - restart-observed CREATED/STARTING generations are reconstructed fail closed
  - stop and retirement verify immutable runtime ownership before mutation/deletion
  - bounded machine-readable driver failure reason codes are preserved without exception text
  - UDS connection handling uses bounded workers and bounded inflight admission instead of synchronous lifecycle execution in the accept loop
  - command/bot lock registries retain only active concurrent keys and preserve same-key serialization
  - repair workflow run 31608427201 completed successfully and pushed product repair commit 74b10f380375f6a5be7e14a949f8561b172792c0
  - temporary repair workflow and scripts were removed; final pre-checkpoint diff has no repair instrumentation
  - all three fresh-audit review threads were resolved after direct code inspection
unknown:
  - fresh independent audit result on the final clean checkpoint head
  - exact-head final CI/E2E result on the final clean checkpoint head
conflicts: []
repair_cycles_for_current_gate: 3
identical_failure_retries: 0
ci_checks_for_current_head: 0
unchanged_state_checks: 0
blockers: []
next_action: Request a fresh independent exact-head Codex audit. If it returns zero material findings, verify the exact-head Runtime Isolation E2E and all required CI/security gates, then merge without bypass.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 3
  session_id: chat-github-20260812-1617
  session_started_at: 2026-08-12T14:17:00Z
  checkpointed_at: 2026-08-12T14:50:00Z
  last_progress_at: 2026-08-12T14:50:00Z
  phase: validate
  exact_head: 43e7944eaf83bf3f49082c7e39693e2d8b54bea0
  pull_request: 1496
  active_operation: fresh exact-head audit
  external_run_ids: [31608427201]
  operation_started_at: null
  wait_deadline_at: null
  check_generation: final-closeout
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: PR #1496 remains open on the same task branch and no newer material finding is unresolved
  next_action: Request and inspect one fresh exact-head Codex review, then proceed to exact-head CI only if material findings remain zero.
```
