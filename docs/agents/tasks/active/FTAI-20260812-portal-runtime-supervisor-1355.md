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

The final implementation includes strict lifecycle-only requests, exact generation/digest/version fencing, durable command replay fingerprints, durable independent active-generation fencing, fail-closed PAPER and retirement authorization, restart-safe lifecycle reconstruction, immutable ownership checks before runtime/network mutation, bounded machine-readable driver failure classes, finite host/engine command deadlines, and a protected host-local UDS boundary with `SO_PEERCRED`, bounded framing/concurrency/shutdown and fixed `/run/quant-platform` ancestor validation.

All temporary repair workflows/scripts have been removed from the PR diff. The only change after the last terminal product candidate was a typing-only correction in the default command-timeout regression test; dedicated run `31612864807` passed that test's mypy and focused pytest validation before the temporary workflow was removed.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-12T15:35:00Z
phase: validate
execution_mode: chat_github
context_pressure: medium
context_growth: stable
decomposition_decision: phased
head_before_checkpoint: 4f21cab641c77b3888ad2b757deecdba1c35fed9
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
  - strict lifecycle-only generation-bound request surface rejects caller-controlled raw engine parameters
  - exact identity/version/digest fencing, independent active-generation authorities, and replay conflict protection are fail closed
  - retryable engine failures preserve durable command fingerprints without permanently caching retryable outcomes
  - PAPER authorization gates exposure-creating provision/run while authenticated containment stays available; retirement is separately authorized
  - RUNNING reconciliation re-attests; restart-observed CREATED/STARTING/PAUSED/STOPPED states reconstruct safely
  - immutable ownership is verified before stop, retire, container deletion and network deletion
  - bounded driver reason codes preserve machine-readable failure classes without exception text
  - UDS uses SO_PEERCRED, bounded one-line framing, request deadlines, bounded workers/inflight admission, and bounded fail-closed shutdown
  - production UDS root is fixed at /run/quant-platform and every existing ancestor is lstat-validated before bind
  - ordinary concrete subprocess-backed Docker/nftables/Btrfs operations have a finite 30-second default command deadline
  - command/bot keyed lock registries preserve serialization without retaining historical keys
  - terminal focused repair workflow 31611284951 passed Ruff, mypy, diff check and 82 focused tests on product commit 833ade05ba09d23066edde1de06ccdd981f42002
  - typing-only timeout-test correction was directly inspected and dedicated run 31612864807 passed before cleanup
  - all known material review threads are resolved after direct code inspection
  - temporary repair workflows/scripts are absent from the clean candidate diff
unknown:
  - fresh independent audit result on the final checkpoint head created by this commit
  - final exact-head Runtime Isolation E2E and required CI/security results on the final checkpoint head
conflicts: []
repair_cycles_for_current_gate: 6
identical_failure_retries: 0
ci_checks_for_current_head: 0
unchanged_state_checks: 0
blockers: []
next_action: Request exactly one fresh independent audit of the final clean checkpoint head. If it reports zero material findings, aggregate exact-head Runtime Isolation E2E and all required CI/security gates, verify zero unresolved review threads and behind_by=0, then merge PR #1496 without bypass and perform the terminal lifecycle archive/registry reconciliation.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 5
  session_id: chat-github-20260812-1617
  session_started_at: 2026-08-12T14:17:00Z
  checkpointed_at: 2026-08-12T15:35:00Z
  last_progress_at: 2026-08-12T15:35:00Z
  phase: validate
  exact_head: 4f21cab641c77b3888ad2b757deecdba1c35fed9
  pull_request: 1496
  active_operation: fresh exact-head audit and exact-head CI
  external_run_ids: [31611284951, 31612864807]
  operation_started_at: null
  wait_deadline_at: null
  check_generation: final-delivery
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: PR #1496 remains open on the same branch and no new material finding is unresolved
  next_action: Run one fresh exact-head Codex review and aggregate the exact-head required CI/E2E gates; merge only on zero material findings and all-green required evidence.
```
