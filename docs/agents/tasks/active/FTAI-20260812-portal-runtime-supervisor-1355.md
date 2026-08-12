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

All material findings from the repeated independent audits have been repaired. The terminal repair additionally:

- persists a command-id semantic fingerprint independently from retryable `ENGINE_OPERATION_FAILED` outcomes, so identical retries re-evaluate while conflicting bodies remain fenced across SQLite-backed restart;
- applies a finite 30-second default deadline to ordinary host/engine subprocess commands while preserving shorter explicit probe deadlines;
- bounds UDS worker shutdown to five seconds, cancels queued work, and retains the owned socket fail closed if running lifecycle work does not drain;
- anchors the production socket directly under `/run/quant-platform` and validates the full ancestor chain with `lstat`, root/euid ownership, real-directory type, and no group/other write before creation/bind.

Temporary repair workflows/scripts have been removed from the PR diff. The branch is based on `develop@c0c484a1fe9139e6039e0c79512c3b0527c32446` with `behind_by=0` before this checkpoint update.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-12T15:22:00Z
phase: validate
execution_mode: chat_github
context_pressure: medium
context_growth: stable
decomposition_decision: phased
head_before_checkpoint: 7f1cd441173c474bc76327058815c1a89eb2aed4
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
  - strict lifecycle-only generation-bound request surface rejects raw engine authority
  - exact identity/version/digest fencing, independent active-generation authorities, and replay conflict protection are fail closed
  - retryable engine failures preserve durable command fingerprints without permanently caching retryable outcomes
  - PAPER authorization gates exposure-creating provision/run while authenticated containment remains available; retirement is separately authorized
  - RUNNING reconciliation re-attests; restart-observed CREATED/STARTING/PAUSED/STOPPED states reconstruct safely
  - immutable ownership is verified before stop, retire, container deletion and network deletion
  - bounded driver reason codes preserve machine-readable failure classes without exception text
  - UDS uses SO_PEERCRED, bounded one-line framing, request deadlines, bounded workers/inflight admission, and bounded shutdown
  - production UDS root is fixed at /run/quant-platform and every existing ancestor is validated before bind
  - ordinary concrete subprocess-backed Docker/nftables/Btrfs operations have a finite 30-second default command deadline
  - command/bot keyed lock registries preserve serialization without retaining historical keys
  - focused terminal repair workflow 31611284951 passed Ruff, mypy, diff check and 82 focused tests on product commit 833ade05ba09d23066edde1de06ccdd981f42002
  - all known material review threads are resolved after direct code inspection
  - temporary repair workflows/scripts are absent from the clean candidate diff
unknown:
  - fresh independent audit result on this final checkpoint head
  - final exact-head Runtime Isolation E2E and required CI/security results on this checkpoint head
conflicts: []
repair_cycles_for_current_gate: 5
identical_failure_retries: 0
ci_checks_for_current_head: 0
unchanged_state_checks: 0
blockers: []
next_action: Request exactly one fresh independent audit of the final clean checkpoint head. If zero material findings, aggregate exact-head Runtime Isolation E2E and required CI/security gates, then merge PR #1496 without bypass and complete terminal lifecycle archival.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 4
  session_id: chat-github-20260812-1617
  session_started_at: 2026-08-12T14:17:00Z
  checkpointed_at: 2026-08-12T15:22:00Z
  last_progress_at: 2026-08-12T15:22:00Z
  phase: validate
  exact_head: 7f1cd441173c474bc76327058815c1a89eb2aed4
  pull_request: 1496
  active_operation: fresh exact-head audit
  external_run_ids: [31611284951]
  operation_started_at: null
  wait_deadline_at: null
  check_generation: terminal-candidate
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: PR #1496 remains open on the same branch and no new material finding is unresolved
  next_action: Request one fresh exact-head Codex review; on zero material findings, verify exact-head CI/E2E and merge without bypass.
```
